"""Framework-neutral /act transport smoke test. Substitute your real agent here.

PYTHONPATH=. uv run uvicorn examples.http_agent_service:app --port 9001
Use examples/http-agent.yaml with intent_visibility: structured for this fixture.
"""

from fastapi import FastAPI

from agent_intent_bench.adapters import DemoAgent

app = FastAPI()
agents = {}


@app.post("/act")
async def act(payload: dict):
    observation = payload["observation"]
    episode_id = observation["episode_id"]
    agent = agents.setdefault(episode_id, DemoAgent("careful", 42))
    action = await agent.act(observation)
    if action.kind == "finish":
        agents.pop(episode_id, None)
    return {"action": action.model_dump()}
