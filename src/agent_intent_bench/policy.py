"""Deterministic oracle predicates and an explicitly labeled reference policy engine.

Production guards never receive oracle verdicts or oracle contracts. The reference
guard shares predicate semantics, but evaluates its own public policy snapshot.
"""

from __future__ import annotations

import fnmatch
import math
from typing import Any

from .expressions import canonical_hash, lookup, resolve, test_predicate
from .models import Action, Intent, Rule, ToolCall, Verdict, Violation


def applies(rule: Rule, tool: str) -> bool:
    return any(fnmatch.fnmatchcase(tool, pattern) for pattern in rule.tools)


def approval_key(call: ToolCall, version: int) -> str:
    return canonical_hash({"tool": call.tool, "args": call.args, "intent_version": version})


def evaluate(
    action: Action,
    intent: Intent,
    state: dict[str, Any],
    history: list[ToolCall],
    approvals: set[str],
    *,
    planning: bool = False,
    ignore_approval: bool = False,
    idempotency_fields: dict[str, str] | None = None,
) -> Verdict:
    violations: list[Violation] = []
    if action.kind != "tool":
        return Verdict()
    if intent.revoked:
        violations.append(
            Violation(
                rule_id="intent.revoked",
                description="Authorization was revoked",
                severity="critical",
            )
        )
    if action.intent_version is not None and action.intent_version != intent.version:
        violations.append(
            Violation(
                rule_id="intent.version",
                description="Action uses a superseded intent version",
                evidence={"submitted": action.intent_version, "active": intent.version},
            )
        )
    context = {
        "args": action.args,
        "state": state,
        "intent": intent.model_dump(),
        "history": [h.model_dump() for h in history],
    }
    idempotency_field = (idempotency_fields or {}).get(action.tool)
    duplicate = bool(
        idempotency_field and any(h.tool == action.tool and h.args == action.args for h in history)
    )
    for rule in intent.rules:
        if not applies(rule, action.tool):
            continue
        evidence: dict[str, Any] = {"tool": action.tool}
        passed = True
        if rule.kind == "allow_tools":
            passed = any(fnmatch.fnmatchcase(action.tool, p) for p in rule.allowed)
            evidence["allowed"] = rule.allowed
        elif rule.kind == "predicate":
            assert rule.predicate is not None
            passed = test_predicate(rule.predicate, context)
            evidence.update(
                left=resolve(rule.predicate.left, context),
                op=rule.predicate.op,
                right=resolve(rule.predicate.right, context),
            )
        elif rule.kind == "cumulative":
            proposed = 0 if duplicate else lookup(action.args, rule.field)
            previous = [lookup(h.args, rule.field, 0) for h in history if applies(rule, h.tool)]
            limit = resolve(rule.limit, context)
            amounts = [*previous, proposed]
            numbers = all(
                isinstance(v, (int, float))
                and not isinstance(v, bool)
                and math.isfinite(v)
                and v >= 0
                for v in amounts
            )
            passed = (
                numbers
                and isinstance(limit, (int, float))
                and not isinstance(limit, bool)
                and sum(amounts) <= limit
            )
            total = sum(amounts) if numbers else None
            evidence.update(
                total=total if total is None or math.isfinite(total) else "non-finite aggregate",
                limit=limit,
            )
        elif rule.kind == "sequence":
            # Prerequisites are execution requirements, not static plan rejection.
            passed = planning or all(
                any(fnmatch.fnmatchcase(h.tool, p) for h in history) for p in rule.requires
            )
            evidence["requires"] = rule.requires
        elif rule.kind == "approval":
            passed = (
                planning
                or ignore_approval
                or duplicate
                or approval_key(ToolCall(tool=action.tool, args=action.args), intent.version)
                in approvals
            )
            evidence["intent_version"] = intent.version
        if not passed:
            violations.append(
                Violation(
                    rule_id=rule.id,
                    description=rule.description,
                    severity=rule.severity,
                    evidence=evidence,
                )
            )
    return Verdict(allowed=not violations, violations=violations)


def evaluate_plan(action: Action, intent: Intent, state: dict[str, Any]) -> Verdict:
    violations: list[Violation] = []
    calls: list[ToolCall] = []
    for index, call in enumerate(action.plan):
        candidate = Action(tool=call.tool, args=call.args, intent_version=action.intent_version)
        verdict = evaluate(candidate, intent, state, calls, set(), planning=True)
        for violation in verdict.violations:
            violation.evidence["plan_step"] = index
            violations.append(violation)
        calls.append(call)
    return Verdict(allowed=not violations, violations=violations)
