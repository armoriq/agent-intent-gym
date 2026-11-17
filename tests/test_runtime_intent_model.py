import json

import pytest

from agent_intent_bench.catalog import load_config, load_suite
from agent_intent_bench.models import AdapterConfig
from agent_intent_bench.runner import run_suite
from agent_intent_bench.store import Store
from examples.build_runtime_intent_model_suite import FAMILIES, KINDS, build_suite, calls

ATTACKER_VALUES = ("GB33BUKB", "outsider.test", "Eve", "INFORMATION", "Riverside", "src/auth.py")


def test_suite_is_frozen_and_hides_attacker_values_until_the_read():
    suite = load_suite("runtime-intent-model")
    assert suite.model_dump() == build_suite().model_dump()
    assert len(suite.scenarios) == len(FAMILIES) * len(KINDS)
    for scenario in suite.scenarios:
        visible = json.dumps(
            {
                "request": scenario.request,
                "tools": [
                    {"name": t.name, "description": t.description, "parameters": t.parameters}
                    for t in scenario.tools
                ],
                "state": {k: scenario.initial_state[k] for k in scenario.public_state_keys},
            }
        )
        assert not [v for v in ATTACKER_VALUES if v in visible], scenario.id
        kind = scenario.id.rsplit(".", 1)[1]
        carrier = scenario.tools[0].response["content"]
        assert ("<INFORMATION>" in carrier) == kind.startswith("inject-"), scenario.id


@pytest.mark.parametrize("trace", ["ignore", "follow"])
async def test_scoring_separates_an_agent_that_follows_the_data_from_one_that_ignores_it(
    tmp_path, trace
):
    base = load_config("examples/intent-evaluation.yaml")
    base.mode = "unguarded"
    for scenario in load_suite("runtime-intent-model").scenarios:
        family, kind = scenario.id.split(".")[1:]
        actions = [*calls(FAMILIES[family], kind)[trace], {"kind": "finish"}]
        config = base.model_copy(deep=True)
        config.agent = AdapterConfig(kind="script", options={"actions": actions})
        suite = build_suite().model_copy(update={"scenarios": [scenario]})
        episode = (await run_suite(suite, config, Store(tmp_path / "store"))).episodes[0]
        unsafe = trace == "follow" and kind != "clean"
        assert episode.status == "completed" and episode.success, scenario.id
        assert (episode.effect_violations > 0) == unsafe, scenario.id
        assert episode.completion_under_policy == (not unsafe), scenario.id
