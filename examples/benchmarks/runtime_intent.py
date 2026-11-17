"""Scripted executor and local plan-check proxies for the runtime-intent suite.

plan-tools allows a call when its tool name is in the registered plan. It stands in for
ArmorIQ IAP as it works today, which compares tool names only.
argument-rules applies only the request's argument predicates, with no tool allowlist.
The exact-plan proxy is the built-in `plan` guard (tool and arguments must match a planned call).
These are local mechanism proxies, not measurements of ArmorIQ or any other product.
"""

import copy

from agent_intent_bench.adapters import ReferenceGuard, create_guard
from agent_intent_bench.models import Action, AdapterConfig, Decision


class RuntimeIntentProbe:
    def __init__(self):
        self.steps = None

    async def act(self, observation):
        if self.steps is None:
            protocol = observation["state"]["protocol"]
            self.steps = copy.deepcopy(protocol["steps"])
            return Action(kind="plan", plan=copy.deepcopy(protocol["plan"]))
        if self.steps:
            return Action.model_validate(self.steps.pop(0))
        return Action(kind="finish")


def create_agent(config):
    return RuntimeIntentProbe()


class PlanToolsGuard:
    async def evaluate(self, action, context):
        if action.kind != "tool":
            return Decision(action="allow", reason="plan-tools:non-execution")
        if action.tool in {c["tool"] for c in context["plan"]}:
            return Decision(action="allow", reason="plan-tools:declared-tool")
        return Decision(action="block", reason="plan-tools:undeclared-tool")


class ArgumentRulesGuard:
    async def evaluate(self, action, context):
        scoped = copy.deepcopy(context)
        scoped["intent"]["rules"] = [
            r for r in scoped["intent"]["rules"] if r["kind"] == "predicate"
        ]
        return await ReferenceGuard().evaluate(action, scoped)


class AllGuards:
    """Runs each guard in order; the first decision other than allow wins."""

    def __init__(self, guards):
        self.guards = guards

    async def evaluate(self, action, context):
        decisions = [await g.evaluate(action, context) for g in self.guards]
        for decision in decisions:
            if decision.action != "allow":
                return decision
        return Decision(action="allow", reason="; ".join(d.reason for d in decisions))


LAYERS = {
    "plan-tools": PlanToolsGuard,
    "argument-rules": ArgumentRulesGuard,
    "plan-exact": lambda: create_guard(AdapterConfig(kind="plan")),
}


def create_guard_stack(config):
    return AllGuards([LAYERS[name]() for name in config.options["layers"]])
