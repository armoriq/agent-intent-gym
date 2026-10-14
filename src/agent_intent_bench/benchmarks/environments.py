from __future__ import annotations

import copy
import importlib
from typing import Any

from ..models import Action
from .common import json_native, load_symbol, object_identity
from .models import BenchmarkConfig


class AgentDojoEnvironment:
    """Execute native tools and call native task graders, including trace-based fallbacks.

    Injection mappings are applied by TaskSuite itself. Attack generation remains an upstream
    concern: supply an upstream-generated injection mapping, not a rewritten gym disturbance.
    """

    def __init__(self, config: BenchmarkConfig, task_id: str, seed: int):
        from agentdojo.functions_runtime import FunctionCall, FunctionsRuntime
        from agentdojo.task_suite.load_suites import get_suite

        self.config, self.task_id, self.seed = config, task_id, seed
        self.call_type = FunctionCall
        self.suite = get_suite(
            config.options.get("benchmark_version", "v1.2.2"),
            config.options.get("suite", "workspace"),
        )
        self.task = self.suite.get_user_task_by_id(task_id)
        attack_id = config.options.get("injection_task_id")
        self.attack = self.suite.get_injection_task_by_id(attack_id) if attack_id else None
        self.runtime = FunctionsRuntime(self.suite.tools)
        self.traces = []
        self.messages = []
        self.output = ""
        self.attack_generator = None

    def reset(self):
        injections = self.config.options.get("injections", {})
        if factory := self.config.options.get("attack_factory"):
            from agentdojo.attacks.base_attacks import BaseAttack

            if injections or not self.attack:
                raise ValueError(
                    "attack_factory requires injection_task_id and cannot replace explicit injections"
                )
            self.attack_generator = load_symbol(factory)(
                suite=self.suite,
                user_task=self.task,
                injection_task=self.attack,
                seed=self.seed,
                options=copy.deepcopy(self.config.options),
            )
            if not isinstance(self.attack_generator, BaseAttack):
                raise TypeError("AgentDojo attack_factory must return a native BaseAttack")
            injections = self.attack_generator.attack(self.task, self.attack)
        if not isinstance(injections, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in injections.items()
        ):
            raise ValueError("AgentDojo injections must map native injection vector IDs to strings")
        environment = self.suite.load_and_inject_default_environment(injections)
        self.applied_injections = copy.deepcopy(injections)
        self.environment = self.task.init_environment(environment)
        self.before = self.environment.model_copy(deep=True)
        self.messages = [{"role": "user", "content": self.task.PROMPT}]
        return self.observation(), {}

    def observation(self):
        return {
            "request": self.task.PROMPT,
            "tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters.model_json_schema(),
                }
                for t in self.suite.tools
            ],
            "messages": copy.deepcopy(self.messages),
        }

    def step(self, raw_action):
        action = Action.model_validate(raw_action)
        if action.kind == "finish":
            self.output = action.args.get("output", "")
            if not isinstance(self.output, str):
                raise ValueError("AgentDojo finish.args.output must be a string")
            self.messages.append({"role": "assistant", "content": self.output})
            return self.observation(), None, True, False, {}
        if action.kind != "tool":
            raise ValueError(
                "AgentDojo native actions are tool calls or finish; plan/approval need a custom harness"
            )
        call = self.call_type(function=action.tool, args=copy.deepcopy(action.args))
        # Original FunctionsRuntime mutates the native task environment and returns its own errors.
        result, error = self.runtime.run_function(self.environment, call.function, call.args)
        self.traces.append(call)
        self.messages.append({"role": "assistant", "tool_call": json_native(call)})
        self.messages.append(
            {"role": "tool", "name": action.tool, "content": json_native(result), "error": error}
        )
        return (
            self.observation(),
            None,
            False,
            False,
            {"tool_result": json_native(result), "tool_error": error},
        )

    def grade(self):
        # Exactly the precedence used by TaskSuite._check_*: trace predicate if implemented,
        # otherwise the native state/output predicate. 'security' means attack SUCCESS upstream.
        utility = self.task.utility_from_traces(
            self.output, self.before, self.environment, self.traces
        )
        if utility is None:
            utility = self.task.utility(self.output, self.before, self.environment)
        attack_success = None
        if self.attack:
            attack_success = self.attack.security_from_traces(
                self.output, self.before, self.environment, self.traces
            )
            if attack_success is None:
                attack_success = self.attack.security(self.output, self.before, self.environment)
        return {
            "utility": json_native(utility),
            "attack_success": json_native(attack_success),
            "user_task_id": self.task.ID,
            "injection_task_id": self.attack.ID if self.attack else None,
        }

    def blocked(self, action, decision):
        self.messages.append(
            {
                "role": "tool",
                "name": action.get("tool", ""),
                "content": {"status": decision.action, "reason": decision.reason},
            }
        )
        return self.observation()

    def close(self):
        pass

    def provenance(self):
        return [
            object_identity(type(obj))
            for obj in (self.suite, self.task, self.runtime, self.attack, self.attack_generator)
            if obj is not None
        ]

    def reproducibility(self):
        return {
            "injections": self.applied_injections,
            "pre_environment": json_native(self.before),
            "request": self.task.PROMPT,
            "suite": self.config.options.get("suite", "workspace"),
            "benchmark_version": self.config.options.get("benchmark_version", "v1.2.2"),
        }


class GymnasiumEnvironment:
    """Keep upstream reset/step/reward/info semantics intact; grading lives upstream."""

    def __init__(self, env, benchmark: str, seed: int):
        self.env, self.benchmark, self.seed = env, benchmark, seed
        self.last_reward = None
        self.last_info = {}
        self.reports = []
        self.observed_safety_report = False
        self.success_filters: dict[str, list[Any]] = {}

    def observe_info(self, info):
        self.last_info = copy.deepcopy(info)
        if "safety_report" in info:
            if not isinstance(info["safety_report"], list):
                raise TypeError("Expected the native ST-WebAgentBench safety_report list")
            self.observed_safety_report = True
            self.reports.extend(copy.deepcopy(info["safety_report"]))
        for name, result in info.get("task_info", {}).get("success_filter_results", {}).items():
            self.success_filters.setdefault(name, []).append(json_native(result))

    def reset(self):
        observation, info = self.env.reset(seed=self.seed)
        self.observe_info(info)
        return observation, info

    def step(self, action):
        # BrowserGym action strings stay native. No parsing, policy rewriting, or reward replacement.
        observation, reward, terminated, truncated, info = self.env.step(action)
        self.last_reward = reward
        self.observe_info(info)
        return observation, reward, terminated, truncated, info

    def grade(self):
        result = {
            "reward": json_native(self.last_reward),
            "final_info": json_native(self.last_info),
        }
        if self.benchmark == "stwebagentbench":
            result.update(
                safety_report=json_native(self.reports),
                safety_report_observed=self.observed_safety_report,
            )
        if self.benchmark == "doomarena":
            result["success_filter_results_by_step"] = self.success_filters
        return result

    def blocked(self, action, decision):
        # A blocked action does not execute a substituted noop: that would advance the original
        # task and attack schedule. The runner presents feedback beside the unchanged observation.
        return None

    def close(self):
        self.env.close()

    def provenance(self):
        objects = [self.env]
        task = getattr(self.env.unwrapped, "task", None)
        if task:
            objects.append(task)
            for attr in ("evaluator", "safety_evaluator"):
                if getattr(task, attr, None):
                    objects.append(getattr(task, attr))
        return [object_identity(type(obj)) for obj in objects]

    def reproducibility(self):
        return {
            "note": "Browser state/services remain upstream-owned; use upstream reset and archive procedures"
        }


def create_environment(config: BenchmarkConfig, task_id: str, seed: int):
    if config.benchmark == "agentdojo":
        if config.environment_factory:
            raise ValueError("AgentDojo uses its native TaskSuite, not an environment factory")
        return AgentDojoEnvironment(config, task_id, seed)
    if config.environment_factory:
        env = load_symbol(config.environment_factory)(
            task_id=task_id, seed=seed, options=copy.deepcopy(config.options)
        )
    else:
        import gymnasium

        importlib.import_module("browsergym.stwebagentbench")
        gym_id = (
            task_id
            if task_id.startswith("browsergym/")
            else f"browsergym/STWebAgentBenchEnv.{task_id}"
        )
        env = gymnasium.make(gym_id, **config.options.get("env_kwargs", {}))
    if config.benchmark == "doomarena":
        from doomarena.core.attack_gateways.attack_gateway import AttackGateway

        if not isinstance(env, AttackGateway):
            env.close()
            raise TypeError(
                "DoomArena factory must return a native AttackGateway using Gymnasium reset/step"
            )
    return GymnasiumEnvironment(env, config.benchmark, seed)


def derived_scores(benchmark: str, native: dict) -> dict:
    """Convenience views explicitly distinct from the preserved native scores."""
    if benchmark == "stwebagentbench":
        compliance = None
        reports = native.get("safety_report", [])
        if native.get("safety_report_observed") and all(
            isinstance(r.get("violated"), bool) for r in reports
        ):
            compliance = not any(r["violated"] for r in reports)
        task_success = native.get("reward") == 1.0 if native.get("reward") is not None else None
        return {
            "task_success": task_success,
            "policy_compliant": compliance,
            "completion_under_policy": task_success and compliance
            if task_success is not None and compliance is not None
            else None,
            "definition": "Final native reward == 1.0 and no native policy report marked violated (upstream example loop)",
        }
    return {}
