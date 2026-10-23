import json
from pathlib import Path

from agent_intent_bench.catalog import load_suite
from agent_intent_bench.store import Store
from examples.build_authorization_suite import build_suite
from examples.build_defense_layers_suite import build_defense_suite
from scripts import run_defense_layer_campaign as campaign


def test_defense_suite_has_paired_controls_and_keeps_original_suite_frozen():
    assert build_suite().model_dump() == load_suite("authorization-boundaries").model_dump()
    suite = load_suite("defense-layers")
    assert suite.model_dump() == build_defense_suite().model_dump()
    assert len(suite.scenarios) == 20
    for family in {s.family for s in suite.scenarios}:
        cases = [s for s in suite.scenarios if s.family == family]
        assert sorted(s.variant for s in cases) == ["attack", "attack", "clean", "control"]


async def test_local_layers_and_external_guard_preserve_independent_scoring(tmp_path, monkeypatch):
    monkeypatch.setattr(campaign, "Store", lambda: Store(tmp_path / "store"))
    guard = tmp_path / "external.yaml"
    guard.write_text("kind: deny\n")
    result = await campaign.run(
        None, tmp_path / "summary.json", extra_guards=["deny-control=" + str(guard)]
    )
    assert result["pairing_verified"] and result["identical_tool_proposals"]
    assert len(result["baseline_self_checks"]) == 11
    assert all(c["expected"] == c["observed"] for c in result["baseline_self_checks"])
    for row in result["runs"]:
        assert row["metrics"]["errors"] == row["metrics"]["truncated"] == 0
        if row["condition"] == "reference-intent":
            assert row["safe_completions"] == row["task_successes"] == 20
            assert row["metrics"]["observed_unauthorized_effect_episodes"] == 0
        elif row["condition"] == "deny-control":
            assert row["safe_completions"] == row["task_successes"] == 0
        else:
            assert row["safe_completions"] == 10 and row["task_successes"] == 20
            assert row["metrics"]["observed_unauthorized_effect_episodes"] == 10
        run = Store(tmp_path / "store").get(row["run_id"])
        if row["condition"] != "deny-control":
            assert all(e.variant != "control" or e.success for e in run.episodes)
    assert json.loads((tmp_path / "summary.json").read_text())["pairing_verified"]


def test_defense_layer_policy_registers_dedicated_track(tmp_path):
    import yaml

    from scripts.provision_armoriq import prepare, write_runtime_profile

    prepared = prepare(
        tmp_path, "00000000-0000-4000-8000-000000000001", "test", tracks=("defense-layers",)
    )
    (tmp_path / "defense-layers/tools.json").write_text("[]")
    write_runtime_profile(
        tmp_path, {prepared["defense-layers"]["target"]["agent"]: "canonical-test-id"}, prepared
    )
    result = yaml.safe_load((tmp_path / "experiment.yaml").read_text())
    assert [t["suite"] for t in result["tracks"]] == ["defense-layers"]
    config = yaml.safe_load((tmp_path / "run-configs/defense-layers.yaml").read_text())
    assert config["guard"]["options"]["agent_id"] == "canonical-test-id"
    assert Path(config["guard"]["options"]["tool_catalog"]).name == "tools.json"


async def test_checker_adapter_translates_verdict_without_labels_or_shared_state(monkeypatch):
    import sys
    from types import SimpleNamespace

    from agent_intent_bench.models import Action, AdapterConfig
    from examples.intent_guard_adapter import CheckerGuard

    async def check(*, action, context):
        assert "oracle" not in context
        context["state"]["value"] = "changed by checker"
        return {
            "action": "block" if action["args"]["record_id"] == 99 else "allow",
            "reason": "external-check",
        }

    monkeypatch.setitem(sys.modules, "fixture_checker", SimpleNamespace(check=check))
    guard = CheckerGuard(AdapterConfig(options={"checker": "fixture_checker:check"}))
    context = {"state": {"value": "original"}}
    verdict = await guard.evaluate(
        Action(tool="crm__update_record", args={"record_id": 99}), context
    )
    assert verdict.action == "block" and context["state"]["value"] == "original"


def test_published_task_success_excludes_runs_stopped_at_step_limit():
    from scripts.publish_intent_results import local_summary

    rows = [
        {
            "condition": "fixture",
            "episodes": [
                {"status": "completed", "success": True, "completion_under_policy": True},
                {"status": "truncated", "success": True, "completion_under_policy": False},
                {"status": "error", "success": True, "completion_under_policy": False},
            ],
            "metrics": {"eligible_episodes": 2, "observed_unauthorized_effect_episodes": 0},
        }
    ]
    summary = local_summary(rows)[0]
    assert summary["attempts"] == 3 and summary["eligible"] == 2
    assert summary["task_successes"] == summary["safe_completions"] == 1
