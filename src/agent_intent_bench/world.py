from __future__ import annotations

import copy
from typing import Any

from jsonschema import Draft202012Validator

from .expressions import apply_effect, canonical_hash, resolve, test_predicate
from .models import Intent, Scenario, ToolCall


class DeclarativeWorld:
    """In-memory simulator. Effects are atomic and never touch real services/files."""

    def __init__(self, scenario: Scenario):
        self.scenario = scenario
        self.state = copy.deepcopy(scenario.initial_state)
        self.tools = {tool.name: tool for tool in scenario.tools}
        self.validators = {}
        for tool in scenario.tools:
            Draft202012Validator.check_schema(tool.parameters)
            self.validators[tool.name] = Draft202012Validator(tool.parameters)
        self.idempotency: dict[str, dict[str, Any]] = {}
        self.injections: dict[str, dict[str, Any]] = {}
        self.faults: list[dict[str, Any]] = []

    def observation(self) -> dict[str, Any]:
        return {
            key: copy.deepcopy(self.state[key])
            for key in self.scenario.public_state_keys
            if key in self.state
        }

    def validate(self, call: ToolCall) -> str | None:
        try:
            canonical_hash(call.model_dump())
        except (TypeError, ValueError):
            return "Action arguments must contain finite JSON values"
        if call.tool not in self.tools:
            return "Unknown tool"
        errors = sorted(
            self.validators[call.tool].iter_errors(call.args), key=lambda e: str(e.path)
        )
        return errors[0].message if errors else None

    def execute(self, call: ToolCall, intent: Intent) -> tuple[dict[str, Any], bool]:
        error = self.validate(call)
        if error:
            return {"status": "invalid_action", "error": error}, False
        tool = self.tools[call.tool]
        context = {"args": call.args, "state": self.state, "intent": intent.model_dump()}
        if not all(test_predicate(p, context) for p in tool.preconditions):
            return {
                "status": "precondition_failed",
                "error": "Environment precondition failed",
            }, False
        key = None
        if tool.idempotency_field:
            key = f"{call.tool}:{call.args[tool.idempotency_field]}"
            if key in self.idempotency:
                entry = self.idempotency[key]
                if entry["args"] != call.args:
                    return {
                        "status": "idempotency_conflict",
                        "error": "The same idempotency key was reused with different arguments",
                    }, False
                return {**copy.deepcopy(entry["result"]), "deduplicated": True}, False
        fault = next((f for f in self.faults if f.get("tool") == call.tool), None)
        if fault and not fault.get("after_commit", False):
            self.faults.remove(fault)
            return {
                "status": "error",
                "error": fault.get("message", "Simulated tool timeout"),
            }, False
        # Resolve every effect against one pre-action snapshot, then commit atomically.
        new_state = copy.deepcopy(self.state)
        for effect in tool.effects:
            apply_effect(
                new_state, effect.op, resolve(effect.path, context), resolve(effect.value, context)
            )
        response = resolve(tool.response, context)
        result = {"status": "ok", "data": response}
        if call.tool in self.injections:
            result["untrusted_content"] = copy.deepcopy(self.injections[call.tool])
        canonical_hash(new_state)
        canonical_hash(result)
        self.state = new_state
        if key:
            self.idempotency[key] = {
                "result": copy.deepcopy(result),
                "args": copy.deepcopy(call.args),
            }
        committed = tool.side_effect
        if fault:
            self.faults.remove(fault)
            return {
                "status": "error",
                "error": fault.get("message", "Response lost after commit"),
                "outcome_unknown": True,
            }, committed
        return result, committed
