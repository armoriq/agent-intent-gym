"""Replace act() with your existing agent's decision call.

Run from the repo: PYTHONPATH=. uv run intentbench run --suite smoke
    --config examples/python-agent.yaml
This example intentionally delegates to a scripted fixture for an offline smoke test.
"""

from agent_intent_bench.adapters import DemoAgent
from agent_intent_bench.models import Action, AdapterConfig


class ExistingAgentAdapter:
    def __init__(self, config: AdapterConfig):
        self.agent = DemoAgent("careful", seed=42)

    async def act(self, observation: dict) -> Action:
        # Map observation.request, observation.tools, and last_result to your agent.
        # Return a Tool Action, a declared Plan, an ask_user request, or finish.
        return await self.agent.act(observation)


def create_agent(config: AdapterConfig):
    return ExistingAgentAdapter(config)
