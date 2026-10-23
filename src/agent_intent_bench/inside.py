"""ArmorIQ inside an agent, with the benchmark retaining its native executor.

An external harness MUST call evaluate before execution and respect block/hold.
act alone deliberately returns proposals, never proof of authorization.
"""

import copy
import inspect

from .adapters import ArmorIQGuard, close_adapter


class ArmorIQInsideAgent:
    def __init__(self, agent, guard_config):
        self.guard = ArmorIQGuard(guard_config)
        self.agent = agent

    async def act(self, observation):
        result = self.agent.act(copy.deepcopy(observation))
        return await result if inspect.isawaitable(result) else result

    @property
    def usage(self):
        return getattr(self.agent, "usage", {})

    async def evaluate(self, action, context):
        return await self.guard.evaluate(copy.deepcopy(action), copy.deepcopy(context))

    async def execute(self, action, context, executor, *, mode="enforce"):
        """External agent integration: check exact args, then use its own executor.

        Returns (decision, result); blocked calls never reach the executor.
        Model plans must be submitted using evaluate(Action(kind='plan', ...)).
        """
        if mode not in {"enforce", "monitor"}:
            raise ValueError("Inside execution supports enforce or monitor")
        proposal = copy.deepcopy(action)
        decision = await self.evaluate(proposal, context)
        if mode == "enforce" and decision.action != "allow":
            return decision, None
        result = executor(copy.deepcopy(proposal))
        return decision, await result if inspect.isawaitable(result) else result

    async def aclose(self):
        try:
            await close_adapter(self.agent)
        finally:
            await close_adapter(self.guard)
