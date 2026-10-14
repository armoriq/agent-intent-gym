"""Run any existing agent against the session API.

Start `uv run intentbench serve`, then `uv run python examples/external_loop.py`.
Replace the scripted fixture with your existing agent loop.
"""

import asyncio
import os

from agent_intent_bench.adapters import DemoAgent
from agent_intent_bench.client import GymClient
from agent_intent_bench.models import AdapterConfig, RunConfig


async def main():
    agent = DemoAgent("careful", seed=42)
    async with GymClient(api_token=os.environ.get("INTENTBENCH_API_TOKEN")) as gym:
        observation = await gym.reset(
            "payments.approval.clean",
            config=RunConfig(agent=AdapterConfig(kind="external", options={"fixture": True})),
        )
        while True:
            action = await agent.act(observation)
            result = await gym.step(action)
            if result["done"]:
                print(f"Evaluation saved: {result['run_id']}")
                break
            observation = result["observation"]


if __name__ == "__main__":
    asyncio.run(main())
