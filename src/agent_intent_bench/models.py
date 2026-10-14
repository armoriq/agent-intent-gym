from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


Operator = Literal[
    "eq",
    "ne",
    "lt",
    "lte",
    "gt",
    "gte",
    "in",
    "not_in",
    "contains",
    "not_contains",
    "starts_with",
    "within_path",
    "matches",
    "subset",
    "exists",
    "truthy",
]


class Predicate(Model):
    left: Any
    op: Operator = "eq"
    right: Any = None


class Rule(Model):
    id: str = Field(min_length=1)
    description: str
    kind: Literal["predicate", "allow_tools", "cumulative", "sequence", "approval"]
    tools: list[str] = Field(default_factory=lambda: ["*"])
    severity: Literal["low", "medium", "high", "critical"] = "high"
    predicate: Predicate | None = None
    allowed: list[str] = Field(default_factory=list)
    field: str = "amount"
    limit: Any = None
    requires: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_shape(self) -> Rule:
        if self.kind == "predicate" and self.predicate is None:
            raise ValueError("predicate rules require a predicate")
        if self.kind == "cumulative" and self.limit is None:
            raise ValueError("cumulative rules require a limit")
        return self


class Intent(Model):
    id: str
    version: int = Field(default=1, ge=1)
    objective: str
    facts: dict[str, Any] = Field(default_factory=dict)
    rules: list[Rule] = Field(default_factory=list)
    revoked: bool = False

    @model_validator(mode="after")
    def unique_rules(self) -> Intent:
        ids = [r.id for r in self.rules]
        if len(ids) != len(set(ids)):
            raise ValueError("intent rule IDs must be unique")
        return self


class ToolCall(Model):
    tool: str = Field(min_length=1)
    args: dict[str, Any] = Field(default_factory=dict)


class Action(Model):
    kind: Literal["tool", "plan", "ask_user", "finish"] = "tool"
    tool: str = ""
    args: dict[str, Any] = Field(default_factory=dict)
    intent_version: int | None = Field(default=None, ge=1)
    plan: list[ToolCall] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_shape(self) -> Action:
        if self.kind == "tool" and not self.tool:
            raise ValueError("tool actions need a tool name")
        if self.kind == "plan" and not self.plan:
            raise ValueError("plan actions need at least one tool call")
        if self.kind == "ask_user" and "action" not in self.args:
            raise ValueError("ask_user needs args.action containing the requested tool call")
        return self


class Effect(Model):
    op: Literal["set", "append", "increment", "delete"] = "set"
    path: list[Any]
    value: Any = None


class ToolSpec(Model):
    name: str
    description: str
    parameters: dict[str, Any] = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }
    )
    effects: list[Effect] = Field(default_factory=list)
    response: Any = Field(default_factory=dict)
    idempotency_field: str | None = None
    preconditions: list[Predicate] = Field(default_factory=list)
    side_effect: bool = True


class Disturbance(Model):
    step: int = Field(ge=0)
    phase: Literal["before_observation", "before_action"] = "before_observation"
    kind: Literal["inject", "intent_update", "state_change", "fault", "message"]
    source: Literal["user", "organization", "tool", "attacker", "environment"] = "environment"
    payload: dict[str, Any] = Field(default_factory=dict)
    description: str = ""

    @model_validator(mode="after")
    def validate_source(self) -> Disturbance:
        if self.kind == "intent_update" and self.source not in {"user", "organization"}:
            raise ValueError("intent updates must come from an authorized user or organization")
        if self.kind == "inject" and "tool" not in self.payload:
            raise ValueError("injections need payload.tool")
        return self


class Scenario(Model):
    schema_version: Literal["1.0"] = "1.0"
    id: str = Field(pattern=r"^[a-zA-Z0-9_.-]+$")
    version: str = "1.0.0"
    name: str
    domain: str
    description: str
    tags: list[str] = Field(default_factory=list)
    family: str = "custom"
    variant: Literal["clean", "attack", "update", "control", "fault"] = "clean"
    request: str
    intent: Intent
    oracle_intent: Intent | None = None
    initial_state: dict[str, Any] = Field(default_factory=dict)
    public_state_keys: list[str] = Field(default_factory=list)
    tools: list[ToolSpec]
    initial_plan: list[ToolCall] = Field(default_factory=list)
    disturbances: list[Disturbance] = Field(default_factory=list)
    success: list[Predicate] = Field(min_length=1)
    approval_behavior: Literal["approve_valid", "deny", "unavailable"] = "approve_valid"

    @model_validator(mode="after")
    def validate_scenario(self) -> Scenario:
        names = [t.name for t in self.tools]
        if len(names) != len(set(names)):
            raise ValueError("tool names must be unique")
        if any(t.tool not in names for t in self.initial_plan):
            raise ValueError("initial_plan references an unknown tool")
        if not self.tools:
            raise ValueError("scenarios need at least one tool")
        return self


class Suite(Model):
    schema_version: Literal["1.0"] = "1.0"
    id: str
    version: str = "1.0.0"
    description: str
    scenarios: list[Scenario] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_scenarios(self) -> Suite:
        ids = [s.id for s in self.scenarios]
        if len(ids) != len(set(ids)):
            raise ValueError("scenario IDs must be unique")
        return self


class AdapterConfig(Model):
    kind: str = "careful"
    endpoint: str | None = None
    endpoint_env: str | None = None
    factory: str | None = None
    model: str | None = None
    model_env: str | None = None
    api_key_env: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def credentials_by_environment(self) -> AdapterConfig:
        secret_fields = {"api_key", "password", "authorization", "access_token", "secret"}
        if secret_fields & {key.lower() for key in self.options}:
            raise ValueError("Adapter credentials must use api_key_env, not inline options")
        if self.endpoint:
            from urllib.parse import parse_qs, urlparse

            parsed = urlparse(self.endpoint)
            if (
                parsed.username
                or parsed.password
                or secret_fields & {key.lower() for key in parse_qs(parsed.query)}
            ):
                raise ValueError("Endpoint URLs must not contain credentials")
        return self


class RunConfig(Model):
    agent: AdapterConfig = Field(default_factory=AdapterConfig)
    guard: AdapterConfig = Field(default_factory=lambda: AdapterConfig(kind="reference"))
    mode: Literal["enforce", "monitor", "unguarded"] = "enforce"
    instrumentation: Literal["external", "inside"] = "external"
    repeats: int = Field(default=1, ge=1, le=1000)
    seed: int = Field(default=42, ge=0)
    max_steps: int = Field(default=24, ge=1, le=10000)
    episode_timeout: float = Field(default=120, gt=0)
    step_timeout: float = Field(default=30, gt=0)
    concurrency: int = Field(default=4, ge=1, le=128)
    intent_visibility: Literal["structured", "request_only"] = "structured"
    scenario_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    guard_policy: Intent | None = None
    fail_on_violation: bool = False

    @model_validator(mode="after")
    def inside_guard(self):
        if self.instrumentation == "inside" and self.guard.kind != "armoriq":
            raise ValueError("ArmorIQ-inside instrumentation requires an ArmorIQ guard")
        return self


class Violation(Model):
    rule_id: str
    description: str
    severity: str = "high"
    evidence: dict[str, Any] = Field(default_factory=dict)


class Verdict(Model):
    allowed: bool = True
    violations: list[Violation] = Field(default_factory=list)


class Decision(Model):
    action: Literal["allow", "block", "hold"]
    reason: str = ""
    policy_ids: list[str] = Field(default_factory=list)
    latency_ms: float = 0
    evidence: dict[str, Any] = Field(default_factory=dict)


class Event(Model):
    seq: int
    step: int = Field(default=0, ge=0)
    kind: str
    timestamp: str
    intent_version: int
    action: Action | None = None
    verdict: Verdict | None = None
    decision: Decision | None = None
    context: dict[str, Any] | None = None
    result: Any = None
    committed: bool = False
    state_hash: str = ""
    prev_hash: str = ""
    hash: str = ""


class EpisodeResult(Model):
    id: str
    scenario_id: str
    scenario_version: str
    domain: str
    family: str
    variant: str
    repeat: int
    seed: int
    status: Literal["completed", "truncated", "error", "cancelled"]
    success: bool = False
    completion_under_policy: bool = False
    proposal_violations: int = 0
    effect_violations: int = 0
    plan_violations: int = 0
    critical_effect_violations: int = 0
    first_drift_step: int | None = None
    steps: int = 0
    duration_ms: float = 0
    error: str | None = None
    usage: dict[str, Any] = Field(default_factory=dict)
    events: list[Event] = Field(default_factory=list)


class RunResult(Model):
    schema_version: Literal["1.0"] = "1.0"
    id: str
    started_at: str
    suite_id: str
    suite_version: str
    manifest: dict[str, Any]
    config: RunConfig
    episodes: list[EpisodeResult]
    metrics: dict[str, Any]


class TraceCase(Model):
    id: str = Field(pattern=r"^[a-zA-Z0-9_.-]+$")
    group: str = "default"
    domain: str = "custom"
    action: Action
    context: dict[str, Any]
    expected: Literal["allow", "block", "hold"]
    reason: str = "Independently labeled decision"

    @model_validator(mode="after")
    def validate_context(self) -> TraceCase:
        allowed_keys = {
            "episode_id",
            "request",
            "intent",
            "state",
            "history",
            "approvals",
            "plan",
            "idempotency_fields",
        }
        if set(self.context) - allowed_keys:
            raise ValueError("Trace context must contain only public guard-context fields")
        Intent.model_validate(self.context["intent"])
        for key in ("state", "history", "approvals", "plan"):
            if key not in self.context:
                raise ValueError(f"Trace context needs {key}")
        if self.action.kind not in {"tool", "plan"}:
            raise ValueError("Trace cases evaluate tool or plan proposals")
        return self


class TraceDataset(Model):
    schema_version: Literal["1.0"] = "1.0"
    id: str
    version: str = "1.0.0"
    description: str
    cases: list[TraceCase] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_cases(self) -> TraceDataset:
        if len({case.id for case in self.cases}) != len(self.cases):
            raise ValueError("Trace case IDs must be unique")
        return self
