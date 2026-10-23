from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from ..models import AdapterConfig, Intent, Model, ToolCall


class BenchmarkConfig(Model):
    benchmark: Literal["agentdojo", "stwebagentbench", "doomarena"]
    task_ids: list[str] = Field(min_length=1)
    runtime: Literal["installed"] | None = None
    agent: AdapterConfig
    options: dict[str, Any] = Field(default_factory=dict)
    environment_factory: str | None = None
    state_reset_factory: str | None = None
    guard: AdapterConfig | None = None
    contract: Intent | None = None
    authorization_oracle: Intent | None = None
    action_mapper: str | None = None
    guard_plan: list[ToolCall] = Field(default_factory=list)
    plan_factory: str | None = None
    instrumentation: Literal["external", "inside"] = "external"
    guard_responses: bool = False
    mode: Literal["unguarded", "monitor", "enforce"] = "unguarded"
    seed: int = Field(default=42, ge=0)
    repeats: int = Field(default=1, ge=1, le=1000)
    max_steps: int = Field(default=100, ge=1, le=10000)
    episode_timeout: float = Field(default=600, gt=0)
    step_timeout: float = Field(default=60, gt=0)

    @model_validator(mode="after")
    def validate_integration(self):
        if self.authorization_oracle:

            def check_refs(value):
                if isinstance(value, dict):
                    if "ref" in value and str(value["ref"]).split(".")[0] not in {"args", "intent"}:
                        raise ValueError(
                            "Native authorization overlays currently support args/intent references only"
                        )
                    for child in value.values():
                        check_refs(child)
                elif isinstance(value, list):
                    for child in value:
                        check_refs(child)

            for rule in self.authorization_oracle.rules:
                if rule.kind not in {"allow_tools", "predicate"}:
                    raise ValueError(
                        "Native authorization overlays currently support per-call tool/predicate rules only"
                    )
                check_refs(rule.model_dump())
        if len(set(self.task_ids)) != len(self.task_ids):
            raise ValueError("task_ids must be unique")
        if self.agent.kind not in {"python", "http"}:
            raise ValueError("Native benchmarks accept python or http native-action agents")
        if self.agent.kind == "python" and not self.agent.factory:
            raise ValueError("Python agent requires module:factory")
        if self.agent.kind == "http" and not (self.agent.endpoint or self.agent.endpoint_env):
            raise ValueError("HTTP agent requires an endpoint")
        if self.benchmark == "doomarena" and not self.environment_factory:
            raise ValueError("DoomArena requires a factory constructing its native attack gateway")
        if self.mode != "unguarded" and (self.guard is None or self.contract is None):
            raise ValueError(
                "Guarded native runs require an explicit guard and author-owned contract"
            )
        if (
            (self.guard or self.authorization_oracle)
            and self.benchmark != "agentdojo"
            and not self.action_mapper
        ):
            raise ValueError("Browser actions require an explicit module:action_mapper for guards")
        if (
            self.guard
            and self.guard.kind == "armoriq"
            and self.mode != "unguarded"
            and not self.guard_plan
            and not self.plan_factory
        ):
            raise ValueError(
                "Native ArmorIQ runs require guard_plan or plan_factory for SDK plan capture"
            )
        if self.guard_plan and self.plan_factory:
            raise ValueError("Choose either author-owned guard_plan or agent plan_factory")
        if self.instrumentation == "inside" and self.guard and self.guard.kind != "armoriq":
            raise ValueError("ArmorIQ-inside instrumentation requires an ArmorIQ guard")
        # Apply the same credential checks as ordinary adapters to external settings.
        AdapterConfig(kind="settings", options=self.options)
        return self


class StateResetReceipt(Model):
    snapshot_id: str = Field(min_length=1)
    method: str = Field(min_length=1)


class NativeEpisode(Model):
    id: str
    task_id: str
    repeat: int
    seed: int
    status: Literal["completed", "truncated", "error", "cancelled"]
    steps: int = 0
    native_scores: dict[str, Any] = Field(default_factory=dict)
    native_sources: list[dict[str, Any]] = Field(default_factory=list)
    native_setup: dict[str, Any] = Field(default_factory=dict)
    state_reset: StateResetReceipt | None = None
    derived_scores: dict[str, Any] = Field(default_factory=dict)
    guard_decisions: dict[str, int] = Field(default_factory=dict)
    transitions: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None


class BenchmarkResult(Model):
    schema_version: Literal["native-1.0"] = "native-1.0"
    id: str
    started_at: str
    benchmark: str
    config: BenchmarkConfig
    manifest: dict[str, Any]
    episodes: list[NativeEpisode]
    summary: dict[str, Any]
