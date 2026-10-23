from __future__ import annotations

import asyncio
import copy
import hashlib
import inspect
import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import httpx

from ..adapters import close_adapter, create_guard
from ..errors import safe_error
from ..expressions import canonical_hash
from ..inside import ArmorIQInsideAgent
from ..models import Action
from ..session import utc_now
from ..settings import load_environment, model_identity, protection_identity, resolve_adapter
from .common import json_native, load_symbol, source_identity
from .environments import create_environment, derived_scores
from .models import BenchmarkConfig, BenchmarkResult, NativeEpisode, StateResetReceipt
from .registry import SOURCES
from .store import BenchmarkStore


class NativeHTTPAgent:
    def __init__(self, config):
        key = os.environ.get(config.api_key_env) if config.api_key_env else None
        if config.api_key_env and not key:
            raise ValueError(f"Set {config.api_key_env}")
        self.client = httpx.AsyncClient(
            base_url=config.endpoint,
            timeout=120,
            headers={"Authorization": f"Bearer {key}"} if key else {},
        )

    async def act(self, observation):
        response = await self.client.post("/act", json={"observation": json_native(observation)})
        response.raise_for_status()
        payload = response.json()
        return payload["action"]

    async def aclose(self):
        await self.client.aclose()


async def call_agent(agent, observation):
    result = agent.act(copy.deepcopy(observation))
    return await result if inspect.isawaitable(result) else result


def native_seed(config: BenchmarkConfig, task_id: str, repeat: int):
    # Subset/order-invariant, identical across guard conditions.
    return int(hashlib.sha256(f"{config.seed}:{task_id}:{repeat}".encode()).hexdigest()[:8], 16)


def manifest_for(config):
    source = SOURCES[config.benchmark]
    installed = {}
    for distribution in source["distributions"]:
        try:
            installed[distribution] = version(distribution)
        except PackageNotFoundError:
            installed[distribution] = None
    symbols = []
    for reference in [
        config.agent.factory,
        config.environment_factory,
        config.state_reset_factory,
        config.action_mapper,
        config.plan_factory,
        config.options.get("attack_factory"),
        config.guard.factory if config.guard else None,
    ]:
        if reference:
            symbols.append(source_identity(reference))
    sources = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in Path(__file__).parent.glob("*.py")
    }
    instrumentation_sources = {
        name: hashlib.sha256((Path(__file__).parent.parent / name).read_bytes()).hexdigest()
        for name in ("adapters.py", "inside.py", "settings.py")
    }
    sdk_source_hash = None
    try:
        import armoriq_sdk

        sdk_root = Path(armoriq_sdk.__file__).parent
        sdk_source_hash = canonical_hash(
            {
                str(p.relative_to(sdk_root)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(sdk_root.rglob("*.py"))
            }
        )
    except ImportError:
        pass
    return {
        "upstream": source,
        "installed_distributions": installed,
        "integration_sources": symbols,
        "adapter_source_hashes": sources,
        "instrumentation_source_hashes": instrumentation_sources,
        "sdk_source_hash": sdk_source_hash,
        "config_hash": canonical_hash(config.model_dump()),
        "model_identity": model_identity(config.agent),
        "protection_identity": protection_identity(config.guard)
        if config.mode != "unguarded"
        else None,
        "instrumentation": config.instrumentation,
        "sdk_versions": {name: _version(name) for name in ("armoriq-sdk", "armoriq-sdk-dev")},
        "grading": "Native scores preserved; derived scores and guard decisions are separate",
        "agent_is_fixture": bool(config.agent.options.get("fixture"))
        or config.agent.factory == "examples.benchmarks.native_agent:create_agent",
        "benchmark_protocol": "Gym-owned agent loop; native task/attack grading. Not an official upstream leaderboard submission.",
        "guard_evaluation": "No independent per-proposal labels; detection/overblocking are unmeasured",
        "timeout_semantics": "Async agent/guard calls bounded; native blocking calls and cleanup cooperate at step boundaries",
        "reviewed_revision_is_installed_revision": False,
    }


def _version(name):
    try:
        return version(name)
    except PackageNotFoundError:
        return None


async def run_episode(config, task_id, repeat, stop):
    seed = native_seed(config, task_id, repeat)
    episode = NativeEpisode(
        id=uuid.uuid4().hex[:12],
        task_id=task_id,
        repeat=repeat,
        seed=seed,
        status="error",
        guard_decisions={"allow": 0, "block": 0, "hold": 0},
    )
    env = agent = guard = None
    deadline = time.monotonic() + config.episode_timeout
    history = []
    native_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="intent-native")

    async def native_call(function, *args):
        return await asyncio.get_running_loop().run_in_executor(
            native_executor, partial(function, *args)
        )

    try:
        if stop.is_set():
            episode.status = "cancelled"
            return episode
        if config.state_reset_factory:
            # Restore external state before creating the native task or spending model tokens.
            # No condition/mode is passed: the same snapshot must serve every condition.
            reset = load_symbol(config.state_reset_factory)
            receipt = await native_call(
                partial(reset, task_id=task_id, seed=seed, options=copy.deepcopy(config.options))
            )
            episode.state_reset = StateResetReceipt.model_validate(receipt)
        env = await native_call(create_environment, config, task_id, seed)
        resolved_agent = resolve_adapter(config.agent)
        agent = (
            load_symbol(config.agent.factory)(config=resolved_agent, seed=seed)
            if config.agent.kind == "python"
            else NativeHTTPAgent(resolved_agent)
        )
        if config.guard and config.mode != "unguarded":
            if config.instrumentation == "inside":
                agent = ArmorIQInsideAgent(agent, config.guard)
                guard = agent
            else:
                guard = create_guard(config.guard)
        mapper = load_symbol(config.action_mapper) if config.action_mapper else None
        observation, reset_info = await native_call(env.reset)
        episode.native_sources = await native_call(env.provenance)
        episode.native_setup = json_native(await native_call(env.reproducibility))
        episode.transitions.append({"kind": "reset", "info": json_native(reset_info)})
        episode.status = "truncated"
        feedback = None
        plan = copy.deepcopy(config.guard_plan)
        public_request = observation.get("request") or observation.get("goal") or ""
        if not isinstance(public_request, str):
            public_request = str(json_native(public_request))
        if config.plan_factory:
            # Exactly the same planning call in every condition, including baseline.
            planner = load_symbol(config.plan_factory)
            base_agent = agent.agent if isinstance(agent, ArmorIQInsideAgent) else agent
            proposed = planner(
                agent=base_agent,
                envelope=copy.deepcopy(
                    {
                        "benchmark": config.benchmark,
                        "task_id": task_id,
                        "seed": seed,
                        "step": 0,
                        "observation": observation,
                    }
                ),
            )
            if inspect.isawaitable(proposed):
                proposed = await asyncio.wait_for(proposed, config.step_timeout)
            plan = Action.model_validate({"kind": "plan", "plan": proposed}).plan
            episode.transitions.append(
                {"kind": "agent_plan", "plan": json_native(plan), "native_step_executed": False}
            )
        if guard and plan:
            context = {
                "episode_id": episode.id,
                "request": public_request,
                "intent": config.contract.model_dump(),
                "state": {},
                "history": [],
                "approvals": [],
                "plan": [],
                "idempotency_fields": {},
            }
            plan_decision = await asyncio.wait_for(
                guard.evaluate(Action(kind="plan", plan=copy.deepcopy(plan)), context),
                config.step_timeout,
            )
            episode.transitions.append(
                {
                    "kind": "guard_plan",
                    "plan": json_native(plan),
                    "decision": plan_decision.model_dump(),
                    "native_step_executed": False,
                }
            )
            # Successful capture is not extra model feedback in the guarded condition.
            if config.mode == "enforce" and plan_decision.action != "allow":
                feedback = plan_decision.model_dump()
            if config.mode == "enforce" and plan_decision.action != "allow":
                episode.native_scores = json_native(await native_call(env.grade))
                episode.derived_scores = derived_scores(config.benchmark, episode.native_scores)
                return episode
        for step in range(config.max_steps):
            if stop.is_set():
                episode.status = "cancelled"
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            envelope = {
                "benchmark": config.benchmark,
                "task_id": task_id,
                "seed": seed,
                "step": step,
                "observation": observation,
                "guard_feedback": feedback,
            }
            action = await asyncio.wait_for(
                call_agent(agent, envelope), min(config.step_timeout, remaining)
            )
            if isinstance(action, Action):
                action = action.model_dump()
            # Validate serializability before causing a native effect; preserve action unchanged.
            serialized_action = json_native(action)
            episode.steps += 1
            decision = None
            is_finish = config.benchmark == "agentdojo" and action.get("kind") == "finish"
            if guard and (not is_finish or config.guard_responses):
                mapped = Action.model_validate(
                    mapper(copy.deepcopy(action)) if mapper else copy.deepcopy(action)
                )
                if is_finish:
                    mapped = Action(tool="agent__respond", args=copy.deepcopy(action["args"]))
                context = {
                    "episode_id": episode.id,
                    "request": public_request,
                    "intent": config.contract.model_dump(),
                    "state": {},
                    "history": copy.deepcopy(history),
                    "approvals": [],
                    "plan": [call.model_dump() for call in plan],
                    "idempotency_fields": {},
                }
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                decision = await asyncio.wait_for(
                    guard.evaluate(mapped, context), min(config.step_timeout, remaining)
                )
                episode.guard_decisions[decision.action] += 1
                # Monitoring is passive. Allow decisions need no extra model input.
                feedback = (
                    decision.model_dump()
                    if config.mode == "enforce" and decision.action != "allow"
                    else None
                )
                if config.mode == "enforce" and decision.action != "allow":
                    new_observation = await native_call(env.blocked, action, decision)
                    if new_observation is not None:
                        observation = new_observation
                    episode.transitions.append(
                        {
                            "kind": "guard_intervention",
                            "step": step,
                            "action": serialized_action,
                            "decision": decision.model_dump(),
                            "native_step_executed": False,
                        }
                    )
                    continue
            if stop.is_set():
                episode.status = "cancelled"
                break
            if time.monotonic() >= deadline:
                break
            observation, reward, terminated, truncated, info = await native_call(env.step, action)
            if guard and (not is_finish or config.guard_responses):
                history.append({"tool": mapped.tool, "args": copy.deepcopy(mapped.args)})
            episode.transitions.append(
                {
                    "kind": "native_step",
                    "step": step,
                    "action": serialized_action,
                    "reward": json_native(reward),
                    "terminated": bool(terminated),
                    "truncated": bool(truncated),
                    "info": json_native(info),
                    "decision": decision.model_dump() if decision else None,
                    "native_step_executed": True,
                }
            )
            if terminated or truncated:
                episode.status = "truncated" if truncated else "completed"
                break
        episode.native_scores = json_native(await native_call(env.grade))
        episode.derived_scores = derived_scores(config.benchmark, episode.native_scores)
    except Exception as error:
        episode.status, episode.error = "error", safe_error(error, config)
    finally:
        for adapter in (agent, guard if guard is not agent else None):
            if adapter:
                try:
                    await close_adapter(adapter)
                except Exception as error:
                    episode.status = "error"
                    episode.error = episode.error or safe_error(error, config)
        if env:
            try:
                await native_call(env.close)
            except Exception as error:
                episode.status = "error"
                episode.error = episode.error or safe_error(error, config)
        native_executor.shutdown(wait=True)
    return episode


def summarize(episodes):
    # Never combine rewards or native metrics across benchmarks, tasks, or incompatible protocols.
    return {
        "episodes": len(episodes),
        **{
            status: sum(e.status == status for e in episodes)
            for status in ("completed", "truncated", "error", "cancelled")
        },
        "guard_detection_rate": None,
        "guard_overblocking_rate": None,
    }


async def run_benchmark(
    config: BenchmarkConfig,
    store: BenchmarkStore | None = None,
    progress=None,
    stop: threading.Event | None = None,
    run_id=None,
):
    load_environment()
    store = store or BenchmarkStore()
    stop = stop or threading.Event()
    run_id = run_id or uuid.uuid4().hex[:12]
    from .runtime import requires_dispatch, run_in_runtime

    if requires_dispatch(config):
        return await run_in_runtime(config, store, progress, stop, run_id)
    manifest = manifest_for(config)
    result = BenchmarkResult(
        id=run_id,
        started_at=utc_now(),
        benchmark=config.benchmark,
        config=config,
        manifest=manifest,
        episodes=[],
        summary={},
    )
    store.begin(run_id, config.model_dump(mode="json"), manifest)

    def execute():
        # One dedicated thread + event loop owns reset/step/close and async agent clients.
        # This preserves Playwright's thread affinity. Native episodes run serially.
        async def evaluate():
            total = len(config.task_ids) * config.repeats
            for task_id in config.task_ids:
                for repeat in range(config.repeats):
                    episode = await run_episode(config, task_id, repeat, stop)
                    result.episodes.append(episode)
                    store.save_episode(run_id, episode)
                    if progress:
                        progress(episode.model_copy(deep=True), len(result.episodes), total)
            result.summary = summarize(result.episodes)
            store.save(result)
            return result

        return asyncio.run(evaluate())

    return await asyncio.to_thread(execute)
