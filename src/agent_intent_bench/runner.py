from __future__ import annotations

import asyncio
import hashlib
import importlib.metadata
import platform
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import __version__
from .adapters import close_adapter, create_agent, create_guard
from .catalog import validate_suite
from .errors import safe_error
from .expressions import canonical_hash
from .inside import ArmorIQInsideAgent
from .metrics import aggregate
from .models import EpisodeResult, RunConfig, RunResult, Suite
from .session import Session, utc_now
from .settings import load_environment, model_identity, protection_identity
from .store import Store

_SOURCE_HASH = canonical_hash(
    {
        str(path.relative_to(Path(__file__).parent)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(Path(__file__).parent.rglob("*.py"))
    }
)


def select_scenarios(suite: Suite, config: RunConfig):
    known = {s.id for s in suite.scenarios}
    missing = set(config.scenario_ids) - known
    if missing:
        raise ValueError(f"Unknown scenario IDs: {', '.join(sorted(missing))}")
    scenarios = [
        s
        for s in suite.scenarios
        if (not config.scenario_ids or s.id in config.scenario_ids)
        and (not config.tags or set(config.tags) <= set(s.tags))
    ]
    if not scenarios:
        raise ValueError("No scenarios match the selected IDs and tags")
    return scenarios


def manifest_for(suite: Suite, config: RunConfig) -> dict[str, Any]:
    versions = {}
    for name in (
        "agent-intent-bench",
        "pydantic",
        "textual",
        "httpx",
        "armoriq-sdk",
        "armoriq-sdk-dev",
    ):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            pass
    return {
        "gym_version": __version__,
        "scorer_version": "1.0.0",
        "source_hash": _SOURCE_HASH,
        "python": platform.python_version(),
        "packages": versions,
        "suite_hash": canonical_hash(suite.model_dump()),
        "config_hash": canonical_hash(config.model_dump()),
        "model_identity": model_identity(config.agent),
        "protection_identity": protection_identity(config.guard)
        if config.mode != "unguarded"
        else None,
        "instrumentation": config.instrumentation,
        "environment": "declarative-in-memory",
        "agent_is_fixture": config.agent.kind
        in {"careful", "gullible", "stubborn", "chaotic", "script"}
        or bool(config.agent.options.get("fixture")),
        "measurement": "Observable contract conformance, not inferred internal intent",
        "seed_note": "Seeds control gym/demo randomness. Remote providers may remain nondeterministic.",
    }


async def run_suite(
    suite: Suite,
    config: RunConfig,
    store: Store,
    progress: Callable[[EpisodeResult, int, int], None] | None = None,
    stop: asyncio.Event | None = None,
    run_id: str | None = None,
) -> RunResult:
    load_environment()
    validate_suite(suite)
    scenarios = select_scenarios(suite, config)
    if config.guard_policy and config.guard.kind != "reference":
        raise ValueError(
            "guard_policy overrides apply only to the reference guard; configure native ArmorIQ policies in ArmorIQ"
        )
    run_id = run_id or uuid.uuid4().hex[:12]
    started_at = utc_now()
    manifest = manifest_for(suite, config)
    store.begin(run_id, started_at, suite, config.model_dump(), manifest)
    stop = stop or asyncio.Event()
    semaphore = asyncio.Semaphore(config.concurrency)
    episodes: list[EpisodeResult] = []
    total = len(scenarios) * config.repeats

    async def one(scenario, repeat):
        async with semaphore:
            digest = hashlib.sha256(f"{config.seed}:{scenario.id}:{repeat}".encode()).hexdigest()
            seed = int(digest[:8], 16)
            session = Session(scenario, config, f"{run_id}-{scenario.id}-{repeat}", seed)
            agent = guard = None
            status, error = "truncated", None
            try:
                if stop.is_set():
                    status = "cancelled"
                else:
                    async with asyncio.timeout(config.episode_timeout):
                        agent = create_agent(config.agent, seed)
                        if config.mode != "unguarded":
                            if config.instrumentation == "inside":
                                agent = await asyncio.to_thread(
                                    ArmorIQInsideAgent, agent, config.guard
                                )
                                guard = agent
                            else:
                                guard = await asyncio.to_thread(
                                    create_guard, config.guard, config.guard_policy
                                )
                        for _ in range(config.max_steps):
                            if stop.is_set():
                                status = "cancelled"
                                break
                            async with asyncio.timeout(config.step_timeout):
                                action = await agent.act(session.observation())
                                if stop.is_set():
                                    status = "cancelled"
                                    break
                                from .models import Action

                                await session.step(Action.model_validate(action), guard)
                            if session.done:
                                status = "completed"
                                break
            except TimeoutError:
                error = "Time budget exceeded"
                status = "truncated"
            except asyncio.CancelledError:
                status = "cancelled"
            except Exception as exception:
                status = "error"
                error = safe_error(exception, config)
            finally:
                for adapter in (agent, guard if guard is not agent else None):
                    if adapter is not None:
                        try:
                            await close_adapter(adapter)
                        except Exception as exception:
                            session.add_event(
                                "cleanup_error", result={"type": type(exception).__name__}
                            )
            result = session.finish(status, repeat, error)
            if agent is not None:
                result.usage = getattr(agent, "usage", {})
            episodes.append(result)
            store.save_episode(run_id, result)
            if progress:
                progress(result, len(episodes), total)

    await asyncio.gather(*(one(s, repeat) for s in scenarios for repeat in range(config.repeats)))
    episodes.sort(key=lambda e: (e.scenario_id, e.repeat))
    metrics = aggregate(episodes, guarded=config.mode != "unguarded")
    metrics["input_tokens"] = sum(e.usage.get("input_tokens", 0) for e in episodes)
    metrics["output_tokens"] = sum(e.usage.get("output_tokens", 0) for e in episodes)
    result = RunResult(
        id=run_id,
        started_at=started_at,
        suite_id=suite.id,
        suite_version=suite.version,
        manifest=manifest,
        config=config,
        episodes=episodes,
        metrics=metrics,
    )
    store.save(result)
    return result


async def replay_guards(source: RunResult, config: RunConfig, store: Store) -> RunResult:
    """Replay fixed recorded contexts; effects/success are not counterfactual outcomes."""
    if config.guard_policy and config.guard.kind != "reference":
        raise ValueError("Policy overrides apply only to the reference guard")
    config = config.model_copy(
        update={"agent": source.config.agent.model_copy(deep=True), "mode": "monitor"}
    )
    run_id = uuid.uuid4().hex[:12]
    suite = Suite.model_validate(
        __import__("yaml").safe_load((store.path(source.id) / "suite.yaml").read_text())
    )
    started = utc_now()
    manifest = {
        **manifest_for(suite, config),
        "evaluation_mode": "fixed_trace",
        "source_run": source.id,
        "effect_scores": "Not computed: fixed traces do not establish counterfactual execution effects",
    }
    store.begin(run_id, started, suite, config.model_dump(), manifest)
    episodes = []
    for episode in source.episodes:
        guard = None
        events = []
        error = None
        try:
            guard = await asyncio.to_thread(create_guard, config.guard, config.guard_policy)
            for event in episode.events:
                if (
                    event.kind not in {"action", "plan"}
                    or not event.action
                    or event.context is None
                ):
                    continue
                async with asyncio.timeout(config.step_timeout):
                    start = time.monotonic()
                    decision = await guard.evaluate(event.action, event.context)
                    decision.latency_ms = (time.monotonic() - start) * 1000
                replayed = event.model_copy(deep=True)
                replayed.seq = len(events)
                replayed.decision = decision
                replayed.committed = False
                replayed.result = {"status": "replayed"}
                replayed.prev_hash = events[-1].hash if events else ""
                replayed.hash = canonical_hash(replayed.model_dump(exclude={"hash"}))
                events.append(replayed)
        except Exception as exception:
            error = safe_error(exception, config)
        finally:
            if guard:
                await close_adapter(guard)
        episodes.append(
            episode.model_copy(
                update={
                    "id": f"{run_id}-{episode.scenario_id}-{episode.repeat}",
                    "events": events,
                    "status": "error" if error else "completed",
                    "error": error,
                    "success": False,
                    "completion_under_policy": False,
                    "effect_violations": 0,
                    "critical_effect_violations": 0,
                }
            )
        )
    metrics = aggregate(episodes)
    from .traces import without_effect_scores

    metrics = without_effect_scores(metrics)
    result = RunResult(
        id=run_id,
        started_at=started,
        suite_id=suite.id,
        suite_version=suite.version,
        manifest=manifest,
        config=config,
        episodes=episodes,
        metrics=metrics,
    )
    store.save(result)
    return result
