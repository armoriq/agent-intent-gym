import json
import sys
import types

import httpx
import pytest

from agent_intent_bench.adapters import ArmorIQGuard, HTTPAgent, HTTPGuard, OpenAICompatibleAgent
from agent_intent_bench.models import Action, AdapterConfig, RunConfig, ToolCall
from agent_intent_bench.session import Session


def test_native_sdk_requires_credentials_without_reading_ambient_login(monkeypatch):
    fake = types.ModuleType("armoriq_sdk")
    fake.ArmorIQClient = lambda **kwargs: None
    fake.SessionOptions = lambda **kwargs: None
    monkeypatch.setitem(sys.modules, "armoriq_sdk", fake)
    monkeypatch.delenv("ARMORIQ_USER_EMAIL", raising=False)
    with pytest.raises(ValueError, match="USER_EMAIL"):
        ArmorIQGuard(AdapterConfig(kind="armoriq"))


async def test_native_sdk_uses_real_session_interface_and_never_invokes_tools(
    monkeypatch, scenario
):
    calls = []

    class FakeSession:
        def start_plan(self, tool_calls, goal=None):
            calls.append(("plan", tool_calls, goal))

        def check(self, name, args, user_email=None):
            calls.append(("check", name, args, user_email))
            return types.SimpleNamespace(
                action="block", allowed=False, reason="Native policy", matched_policy="p1"
            )

    class FakeClient:
        def __init__(self, **kwargs):
            calls.append(("client", sorted(kwargs)))

        def for_user(self, email):
            calls.append(("scope", email))
            return self

        def start_session(self, options):
            calls.append(("session", options))
            return FakeSession()

        def invoke(self, *args, **kwargs):
            raise AssertionError("The gym must never execute real MCP calls")

        def close(self):
            calls.append(("close",))

    fake = types.ModuleType("armoriq_sdk")
    fake.ArmorIQClient, fake.SessionOptions = FakeClient, lambda **kw: kw
    monkeypatch.setitem(sys.modules, "armoriq_sdk", fake)
    monkeypatch.setenv("ARMORIQ_API_KEY", "synthetic-key-for-test")
    config = AdapterConfig(kind="armoriq", options={"user_email": "tester@example.test"})
    guard = ArmorIQGuard(config)
    session = Session(scenario, RunConfig(), "native", 0)
    context = session.guard_context()
    await guard.evaluate(Action(kind="plan", plan=[ToolCall(tool="payments__commit")]), context)
    decision = await guard.evaluate(
        Action(tool="payments__commit", args={"quantity": 100}), context
    )
    await guard.aclose()
    assert decision.action == "block"
    assert calls[-2][-1] == "tester@example.test"
    assert calls[0][0] == "client"
    assert decision.evidence["integration"] == "native-sdk"


async def test_http_agent_and_guard_transport_use_public_inputs(scenario):
    context = Session(scenario, RunConfig(), "transport", 0).guard_context()
    seen = []

    def handler(request):
        body = json.loads(request.content)
        seen.append(body)
        if request.url.path == "/act":
            assert "verdict" not in body["observation"]
            return httpx.Response(200, json={"action": {"kind": "finish"}})
        assert "oracle_intent" not in body["context"]
        return httpx.Response(200, json={"action": "hold", "reason": "Approval required"})

    transport = httpx.MockTransport(handler)
    agent = HTTPAgent(AdapterConfig(kind="http", endpoint="http://test/act"))
    guard = HTTPGuard(AdapterConfig(kind="http", endpoint="http://test/evaluate"))
    await agent.client.aclose()
    await guard.client.aclose()
    agent.client = httpx.AsyncClient(transport=transport)
    guard.client = httpx.AsyncClient(transport=transport)
    assert (await agent.act({"request": "task"})).kind == "finish"
    assert (await guard.evaluate(Action(tool="payments__commit"), context)).action == "hold"
    assert len(seen) == 2
    await agent.aclose()
    await guard.aclose()


async def test_model_adapter_passes_real_tool_feedback_and_tracks_usage(scenario):
    requests = []

    def handler(request):
        body = json.loads(request.content)
        requests.append(body)
        name = "payments__read_invoice" if len(requests) == 1 else "finish"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "tool_calls": [
                                {
                                    "id": str(len(requests)),
                                    "type": "function",
                                    "function": {"name": name, "arguments": "{}"},
                                }
                            ],
                        }
                    }
                ],
                "usage": {"prompt_tokens": 5, "completion_tokens": 2},
            },
        )

    agent = OpenAICompatibleAgent(
        AdapterConfig(kind="openai", endpoint="http://test/v1", model="test-model")
    )
    await agent.client.aclose()
    agent.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    session = Session(scenario, RunConfig(), "model", 0)
    action = await agent.act(session.observation())
    await session.step(action, None)
    assert (await agent.act(session.observation())).kind == "finish"
    feedback = [m for m in requests[1]["messages"] if m["role"] == "tool"][0]
    assert json.loads(feedback["content"])["status"] == "ok"
    assert agent.usage == {"input_tokens": 10, "output_tokens": 4}
    await agent.aclose()
