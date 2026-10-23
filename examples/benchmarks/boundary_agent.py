"""Deterministic executor probe, deliberately not an LLM performance result."""

import copy

from agent_intent_bench.models import Action


class BoundaryProbe:
    def __init__(self):
        self.index = 0
        self.calls = None

    async def act(self, observation):
        if self.calls is None:
            public = observation["state"]["protocol"]
            self.calls = copy.deepcopy([public["candidate"], public["required"], public["report"]])
            return Action(kind="plan", plan=self.calls)
        if self.index < len(self.calls):
            call = self.calls[self.index]
            self.index += 1
            return Action.model_validate(call)
        return Action(kind="finish")


def create_agent(config):
    return BoundaryProbe()
