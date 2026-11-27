import json
import sys
import types

import httpx
import pytest

from agent_intent_bench.adapters import ArmorIQGuard, HTTPAgent, HTTPGuard, OpenAICompatibleAgent
from agent_intent_bench.models import Action, AdapterConfig, RunConfig, ToolCall
from agent_intent_bench.session import Session


def test_native_sdk_requires_credentials_without_reading_ambient_login(monkeypatch, tmp_path):
    # An unrelated developer .env must not supply the credential being removed.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ARMORIQ_API_KEY", "synthetic-key-for-test")
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
            assert kwargs["agent_id"] == "registered-benchmark-agent"

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
    monkeypatch.setenv("ARMORIQ_AGENT_ID", "registered-benchmark-agent")
    config = AdapterConfig(kind="armoriq", options={"user_email": "tester@example.test"})
    guard = ArmorIQGuard(config)
    session = Session(scenario, RunConfig(), "native", 0)
    context = session.guard_context()
    plan = Action(
        kind="plan", plan=[ToolCall(tool="payments__commit")], args={"goal": "Commit the order"}
    )
    await guard.evaluate(plan, context)
    decision = await guard.evaluate(
        Action(tool="payments__commit", args={"quantity": 100}), context
    )
    await guard.aclose()
    assert decision.action == "block"
    assert calls[-2][-1] == "tester@example.test"
    assert calls[0][0] == "client"
    assert decision.evidence["integration"] == "native-sdk"
    # The agent's own goal goes with its plan, as ArmorClaude sends it.
    assert next(c for c in calls if c[0] == "plan")[2].startswith("Commit the order")


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
        AdapterConfig(
            kind="openai",
            endpoint="http://test/v1",
            model="test-model",
            options={"max_tokens": 1024},
        )
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
    assert all(r["max_tokens"] == 1024 for r in requests)
    await agent.aclose()


async def test_tool_arguments_that_are_not_json_reach_the_model_as_a_rejected_call(scenario):
    sent = iter(["", "not json", ""])
    names = iter(["payments__read_invoice", "payments__read_invoice", "finish"])

    def handler(request):
        call = {
            "id": "c",
            "type": "function",
            "function": {"name": next(names), "arguments": next(sent)},
        }
        message = {"role": "assistant", "tool_calls": [call]}
        return httpx.Response(200, json={"choices": [{"message": message}]})

    agent = OpenAICompatibleAgent(
        AdapterConfig(kind="openai", endpoint="http://test/v1", model="test-model")
    )
    await agent.client.aclose()
    agent.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    session = Session(scenario, RunConfig(), "arguments", 0)
    try:
        results = []
        while not session.done:
            results.append(await session.step(await agent.act(session.observation()), None))
        assert [r["status"] for r in results] == ["ok", "invalid_action", "finished"]
    finally:
        await agent.aclose()


def test_openai_agent_takes_its_system_prompt_from_options():
    from agent_intent_bench.adapters import OpenAICompatibleAgent
    from agent_intent_bench.models import AdapterConfig

    config = AdapterConfig(
        kind="openai",
        endpoint="http://127.0.0.1:1/v1",
        model="m",
        options={"system_prompt": "Only this."},
    )
    assert OpenAICompatibleAgent(config).messages[0]["content"] == "Only this."


def plan_check_guard(monkeypatch, decide, **options):
    """An ArmorIQ guard in plan-check-only mode over a fake SDK session."""

    class FakeSession:
        def start_plan(self, tool_calls, goal=None):
            pass

        def check(self, name, args, user_email=None):
            return types.SimpleNamespace(**decide(name))

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        def for_user(self, email):
            return self

        def start_session(self, options):
            return FakeSession()

        def close(self):
            pass

    fake = types.ModuleType("armoriq_sdk")
    fake.ArmorIQClient, fake.SessionOptions = FakeClient, lambda **kw: kw
    monkeypatch.setitem(sys.modules, "armoriq_sdk", fake)
    monkeypatch.setenv("ARMORIQ_API_KEY", "synthetic-key-for-test")
    options = {"user_email": "tester@example.test", "iap_only": True, **options}
    return ArmorIQGuard(AdapterConfig(kind="armoriq", options=options))


ALLOWED = {"action": "allow", "allowed": True, "reason": "no_active_policy", "matched_policy": None}
OUTSIDE = {
    "action": "block",
    "allowed": False,
    "reason": "tool-not-in-plan: 'payments__refund' was not declared in the captured plan",
    "matched_policy": None,
}


@pytest.mark.parametrize(
    "decision",
    [
        {**ALLOWED, "reason": "allow:tools.payments"},
        {**ALLOWED, "matched_policy": "finance-policy"},
        {**OUTSIDE, "reason": "block:tools.default"},
    ],
)
async def test_plan_check_only_fails_the_episode_when_another_layer_decides(
    monkeypatch, scenario, decision
):
    guard = plan_check_guard(monkeypatch, lambda name: decision)
    context = Session(scenario, RunConfig(), "native", 0).guard_context()
    await guard.evaluate(Action(kind="plan", plan=[ToolCall(tool="payments__commit")]), context)
    with pytest.raises(RuntimeError, match="outside the plan check"):
        await guard.evaluate(Action(tool="payments__commit", args={}), context)


async def test_plan_check_only_passes_the_plan_check_decisions_through(monkeypatch, scenario):
    # The third is the backend refusing a step of a plan that changed during the session.
    decide = {
        "payments__commit": ALLOWED,
        "payments__refund": OUTSIDE,
        "payments__report": {**OUTSIDE, "reason": "intent_anchor_chain_rejected"},
    }
    guard = plan_check_guard(monkeypatch, decide.get)
    context = Session(scenario, RunConfig(), "native", 0).guard_context()
    await guard.evaluate(Action(kind="plan", plan=[ToolCall(tool="payments__commit")]), context)
    seen = [(await guard.evaluate(Action(tool=tool, args={}), context)).action for tool in decide]
    assert seen == ["allow", "block", "block"]


def test_plan_check_only_refuses_the_local_checking_mode(monkeypatch):
    with pytest.raises(ValueError, match="sdk checking mode"):
        plan_check_guard(monkeypatch, lambda name: ALLOWED, sdk_mode="local")


async def test_the_model_hears_each_request_once_and_reads_tool_results_in_the_tool_role():
    from agent_intent_bench.catalog import load_suite

    scenario = next(
        s
        for s in load_suite("runtime-intent-turns").scenarios
        if s.id == "runtime-turns.team-updates.clean"
    )
    calls = [
        ("slack__read_channel", {"channel": "general"}),
        ("slack__delete_channel", {"channel": "general"}),
        ("finish", {}),
    ]
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        name, args = calls[len(requests) - 1]
        call = {
            "id": str(len(requests)),
            "type": "function",
            "function": {"name": name, "arguments": json.dumps(args)},
        }
        return httpx.Response(
            200, json={"choices": [{"message": {"role": "assistant", "tool_calls": [call]}}]}
        )

    agent = OpenAICompatibleAgent(
        AdapterConfig(kind="openai", endpoint="http://test/v1", model="test-model")
    )
    await agent.client.aclose()
    agent.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    session = Session(scenario, RunConfig(intent_visibility="request_only"), "turns", 0)
    for _ in range(2):
        await session.step(await agent.act(session.observation()), None)
    session.next_turn()
    await agent.act(session.observation())
    first, last = requests[0]["messages"], requests[-1]["messages"]
    assert [m["role"] for m in first] == ["system", "user"]
    assert first[1]["content"] == scenario.request
    assert [m["content"] for m in last if m["role"] == "user"] == [
        scenario.request,
        scenario.turns[0].request,
    ]
    read, refused = [m for m in last if m["role"] == "tool"]
    assert json.loads(read["content"])["status"] == "ok" and "is_error" not in read
    assert json.loads(refused["content"])["status"] == "invalid_action"
    assert refused["is_error"] is True
    await agent.aclose()


BILL = "runtime-model.bill-from-file.clean"
READ = {"action": "files__read_file", "arguments": {"path": "/bills/december.txt"}}
PAY = {
    "tool": "bank__send_money",
    "args": {"recipient": "FR1420041010050500013M02606", "amount": 98.7, "subject": "Electricity"},
}


def scripted_model(calls):
    """A model endpoint that answers each request with the next (tool, arguments) call."""
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        name, args = calls[len(requests) - 1]
        call = {
            "id": str(len(requests)),
            "type": "function",
            "function": {"name": name, "arguments": json.dumps(args)},
        }
        return httpx.Response(
            200, json={"choices": [{"message": {"role": "assistant", "tool_calls": [call]}}]}
        )

    agent = OpenAICompatibleAgent(
        AdapterConfig(
            kind="openai", endpoint="http://test/v1", model="test", options={"intent_loop": True}
        )
    )
    agent.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return agent, requests


def bill():
    from agent_intent_bench.catalog import load_suite

    return next(s for s in load_suite("runtime-intent-model").scenarios if s.id == BILL)


async def test_the_agent_registers_its_plan_in_its_own_conversation_after_the_product_directive():
    from agent_intent_bench.adapters import INTENT_DIRECTIVE

    scenario = bill()
    agent, requests = scripted_model(
        [("register_intent_plan", {"goal": "Pay the bill", "steps": [READ]})]
    )
    session = Session(scenario, RunConfig(intent_visibility="request_only"), "loop", 0)
    action = await agent.act(session.observation())
    first = requests[0]
    assert "register_intent_plan" in {t["function"]["name"] for t in first["tools"]}
    assert first["messages"][-1]["content"].startswith(scenario.request)
    assert INTENT_DIRECTIVE in first["messages"][-1]["content"]
    assert action.kind == "plan" and action.args == {"goal": "Pay the bill"}
    assert [(c.tool, c.args) for c in action.plan] == [(READ["action"], READ["arguments"])]
    await agent.aclose()


async def test_a_plan_naming_a_tool_the_agent_does_not_have_is_refused_and_the_model_asked_again():
    agent, requests = scripted_model(
        [
            ("register_intent_plan", {"goal": "Pay", "steps": [{"action": "bank__wire"}]}),
            ("finish", {}),
        ]
    )
    session = Session(bill(), RunConfig(intent_visibility="request_only"), "loop", 0)
    assert (await agent.act(session.observation())).kind == "finish"
    refused = [m for m in requests[1]["messages"] if m["role"] == "tool"][0]
    assert refused["is_error"] is True and "unknown tools: bank__wire" in refused["content"]
    await agent.aclose()


async def test_a_call_off_the_plan_is_answered_with_the_plan_to_register_and_works_after_it():
    from examples.benchmarks.runtime_intent import PlanToolsGuard

    pay_step = {"action": PAY["tool"], "arguments": PAY["args"]}
    agent, requests = scripted_model(
        [
            ("register_intent_plan", {"goal": "Pay the bill", "steps": [READ]}),
            (PAY["tool"], PAY["args"]),
            ("register_intent_plan", {"goal": "Pay the bill", "steps": [READ, pay_step]}),
            (PAY["tool"], PAY["args"]),
            ("finish", {}),
        ]
    )
    config = RunConfig(mode="enforce", intent_visibility="request_only")
    session = Session(bill(), config, "loop", 0)
    guard = PlanToolsGuard()
    for _ in range(4):
        await session.step(await agent.act(session.observation()), guard)
    await agent.act(session.observation())
    answers = [m for m in requests[-1]["messages"] if m["role"] == "tool"]
    blocked, paid = answers[1], answers[3]
    assert blocked["is_error"] is True
    hint = json.loads(blocked["content"].split("```json\n")[1].split("\n```")[0])
    assert [s["action"] for s in hint["steps"]] == [READ["action"], PAY["tool"]]
    assert hint["steps"][-1]["arguments"] == PAY["args"]
    assert json.loads(paid["content"])["status"] == "ok"
    await agent.aclose()


def test_a_rejected_chain_gets_no_plan_to_register():
    agent = OpenAICompatibleAgent(
        AdapterConfig(
            kind="openai", endpoint="http://test/v1", model="test", options={"intent_loop": True}
        )
    )
    agent.registered = {"goal": "Pay", "steps": [READ]}
    blocked = {"status": "blocked", "decision": {"reason": "intent_anchor_chain_rejected"}}
    assert agent._deny(blocked, {"tool": PAY["tool"], "args": PAY["args"]}) == (
        "Blocked: intent_anchor_chain_rejected"
    )
    unplanned = {"status": "blocked", "decision": {"reason": "tool-not-in-plan: not declared"}}
    assert "To unblock" in agent._deny(unplanned, {"tool": PAY["tool"], "args": PAY["args"]})
