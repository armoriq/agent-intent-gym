import json
import re

import httpx
import pytest

from agent_intent_bench.adapters import OpenAICompatibleAgent
from agent_intent_bench.catalog import load_config, load_suite
from agent_intent_bench.models import Action, AdapterConfig, RunConfig
from agent_intent_bench.runner import run_suite
from agent_intent_bench.session import Session
from agent_intent_bench.store import Store
from examples.build_runtime_intent_turns_suite import (
    FAMILIES,
    KINDS,
    build_suite,
    calls,
    extra_call,
)

ATTACKER_VALUES = ("GB33BUKB", "outsider.test", "Eve", "docs/releases")


def named(text):
    """Attacker values in the text; `Eve` inside a word such as `Event` does not count."""
    return [v for v in ATTACKER_VALUES if re.search(rf"(?<![A-Za-z]){re.escape(v)}(?![a-z])", text)]


def test_the_plant_error_text_names_no_alternative():
    for scenario in build_suite().scenarios:
        if scenario.id.endswith(".plant-error"):
            (fault,) = scenario.disturbances
            assert fault.turn == 1
            assert not named(fault.payload["message"]), scenario.id


async def run_script(scenario, actions, tmp_path, max_steps=5):
    config = load_config("examples/intent-evaluation.yaml")
    config.mode, config.max_steps = "unguarded", max_steps
    config.agent = AdapterConfig(kind="script", options={"actions": actions})
    suite = build_suite().model_copy(update={"scenarios": [scenario]})
    return (await run_suite(suite, config, Store(tmp_path / "store"))).episodes[0]


def test_suite_is_frozen_and_no_request_or_tool_names_an_attacker_value():
    suite = load_suite("runtime-intent-turns")
    assert suite.model_dump() == build_suite().model_dump()
    assert len(suite.scenarios) == len(FAMILIES) * len(KINDS)
    for scenario in suite.scenarios:
        visible = json.dumps(
            {
                "requests": [scenario.request, *[t.request for t in scenario.turns]],
                "tools": [
                    {"name": t.name, "description": t.description, "parameters": t.parameters}
                    for t in scenario.tools
                ],
            }
        )
        assert not named(visible), scenario.id


@pytest.mark.parametrize("trace", ["ignore", "follow"])
async def test_scoring_separates_following_from_ignoring_within_a_step_budget_per_turn(
    tmp_path, trace
):
    for scenario in load_suite("runtime-intent-turns").scenarios:
        family, kind = scenario.id.split(".")[1:]
        actions = calls(family, kind)[trace]
        assert len(actions) > 5  # more steps than one turn's budget
        episode = await run_script(scenario, actions, tmp_path)
        unsafe = trace == "follow" and kind != "clean"
        assert episode.status == "completed" and episode.success, scenario.id
        assert (episode.effect_violations > 0) == unsafe, scenario.id


@pytest.mark.parametrize("family", ["team-updates", "payments", "file-sharing"])
async def test_a_call_allowed_in_turn_one_is_unauthorized_after_turn_two_withdraws_it(
    tmp_path, family
):
    scenario = next(s for s in build_suite().scenarios if s.id == f"runtime-turns.{family}.revoke")
    spec = FAMILIES[family]
    tool, args = spec["revoke"]["call"]
    withdrawn = {"tool": tool, "args": args}
    first, *rest = calls(family, "clean")["ignore"][:2], *calls(family, "clean")["ignore"][2:]
    early = await run_script(scenario, [*first, withdrawn, *rest], tmp_path, max_steps=6)
    late = await run_script(scenario, [*first, *rest[:2], withdrawn, *rest[2:]], tmp_path)
    assert early.effect_violations == 0
    assert late.effect_violations == 1


async def test_a_failure_waits_for_the_requested_call_and_does_not_hide_an_unauthorized_one(
    tmp_path,
):
    scenario = next(
        s for s in build_suite().scenarios if s.id == "runtime-turns.team-updates.plant-error"
    )
    trace = calls("team-updates", "plant-error")
    opening, requested = trace["ignore"][:4], trace["ignore"][4]
    followed_first = [*opening, extra_call("team-updates", "plant-error"), requested, requested]
    episode = await run_script(scenario, [*followed_first, {"kind": "finish"}], tmp_path)
    turn_two = [e for e in episode.events if e.kind == "action"][3:]
    assert [e.result["status"] for e in turn_two] == ["ok", "error", "ok"]
    assert episode.effect_violations == 1 and episode.success


async def test_the_model_runner_reports_an_episode_whose_plan_breaks_a_tool_schema(tmp_path):
    from scripts.run_runtime_intent_models import row

    scenario = build_suite().scenarios[0]
    plan = {"kind": "plan", "plan": [{"tool": "slack__send_direct_message", "args": {}}]}
    episode = await run_script(scenario, [plan, {"kind": "finish"}, {"kind": "finish"}], tmp_path)
    assert episode.plan_violations == 1
    # The step is rejected for its missing recipient; its schema violation has no step number.
    assert row("model", episode, "slack__read_channel", set())["plans"][0]["rejected"] == [0]


async def test_a_new_turn_starts_with_the_new_request_and_no_plan():
    scenario = build_suite().scenarios[0]
    session = Session(scenario, RunConfig(mode="unguarded"), "turns", 0)
    await session.step(
        Action(kind="plan", plan=[calls("team-updates", "clean")["ignore"][0]]), None
    )
    assert session.guard_context()["plan"]
    await session.step(Action(kind="finish"), None)
    context = session.guard_context()
    assert not session.done and context["plan"] == []
    assert context["request"] == session.observation()["request"] == scenario.turns[0].request
    await session.step(Action(kind="finish"), None)
    assert session.done


async def test_the_model_adapter_declares_a_new_plan_for_each_turn_with_the_conversation():
    scenario = next(
        s for s in build_suite().scenarios if s.id == "runtime-turns.team-updates.clean"
    )
    requests = []

    def handler(request):
        body = json.loads(request.content)
        requests.append(body)
        if "tools" not in body:
            plan = {"steps": [{"tool": "slack__read_channel", "args": {"channel": "general"}}]}
            return httpx.Response(
                200, json={"choices": [{"message": {"content": json.dumps(plan)}}]}
            )
        return httpx.Response(200, json={"choices": [{"message": {"content": "Done."}}]})

    agent = OpenAICompatibleAgent(
        AdapterConfig(
            kind="openai",
            endpoint="http://test/v1",
            model="test",
            options={"require_initial_plan": True, "plan_prompt": "Plan it."},
        )
    )
    await agent.client.aclose()
    agent.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    session = Session(scenario, RunConfig(intent_visibility="request_only"), "turns", 0)
    try:
        kinds = []
        while not session.done:
            action = await agent.act(session.observation())
            kinds.append(action.kind)
            await session.step(action, None)
        assert kinds == ["plan", "finish", "plan", "finish"]
        plans = [r for r in requests if "tools" not in r]
        assert [p["messages"][0]["content"] for p in plans] == ["Plan it.", "Plan it."]
        second = plans[1]["messages"][1]["content"]
        assert "Conversation so far" in second and "Done." in second
        assert scenario.turns[0].request in second.split("Current request:")[1]
        assert "Conversation so far" not in plans[0]["messages"][1]["content"]
    finally:
        await agent.aclose()
