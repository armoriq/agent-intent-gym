"""Verify and publish targeted capability results without copying private platform IDs."""

import argparse
import json
from collections import Counter
from pathlib import Path

from agent_intent_bench.benchmarks.store import BenchmarkStore
from agent_intent_bench.catalog import load_suite
from agent_intent_bench.expressions import canonical_hash
from agent_intent_bench.metrics import aggregate
from agent_intent_bench.store import Store, verify_events


def verify_local(report):
    for row in report["runs"]:
        result = Store().get(row["run_id"])
        assert all(verify_events(e.events) for e in result.episodes)
        metrics = aggregate(result.episodes, guarded=row["condition"] != "unguarded")
        metrics["input_tokens"] = sum(e.usage.get("input_tokens", 0) for e in result.episodes)
        metrics["output_tokens"] = sum(e.usage.get("output_tokens", 0) for e in result.episodes)
        assert metrics == result.metrics == row["metrics"]
        row["stable_observation_ids"] = result.config.stable_observation_ids
        row["source_hash"] = result.manifest["source_hash"]
        row["budgets"] = {
            k: getattr(result.config, k)
            for k in ("seed", "repeats", "max_steps", "step_timeout", "episode_timeout")
        }
        if row["condition"].startswith("armoriq-"):
            expected = expected_policy(result.config, "authorization-boundaries")
            for episode in result.episodes:
                for event in episode.events:
                    if event.kind == "action" and event.decision:
                        verify_decision(event.decision.model_dump(), expected)
            row["matched_policy_version_verified"] = True
    assert len({r["pairing_hash"] for r in report["runs"]}) == 1
    report["metrics_recomputed_verified"] = True
    return report


def expected_policy(config, track):
    folder = Path(config.guard.options["tool_catalog"]).parent.parent
    return json.loads((folder / "provisioning.json").read_text())["policies"][track]


def verify_decision(decision, expected):
    assert expected["policy_id"] in decision["policy_ids"]
    assert decision["evidence"]["policy_version"] == expected["policy_hash"]


def summarize(setup, initial, native, destination):
    fixture = verify_local(json.loads((setup / "probe-results.json").read_text()))
    model = verify_local(json.loads((setup / "model-results.json").read_text()))
    initial_fixture = verify_local(json.loads((initial / "probe-results.json").read_text()))
    initial_model = verify_local(json.loads((initial / "model-results.json").read_text()))
    variable_id_path = setup / "model-variable-id-development.json"
    variable_id_exploration = (
        verify_local(json.loads(variable_id_path.read_text()))
        if variable_id_path.exists()
        else None
    )
    native_reports = []
    for path in (
        native / "agentdojo-results.json",
        native / "agentdojo-bcc-results.json",
        native / "final/doomarena-results.json",
    ):
        report = json.loads(path.read_text())
        report.pop("official_upstream_task", None)
        report.update(
            official_upstream_submission=False,
            uses_original_upstream_tasks=True,
            native_benchmark="doomarena" if report["benchmark"] == "doomarena" else "agentdojo",
        )
        for row in report["runs"]:
            assert BenchmarkStore().verify(row["run_id"])
            assert (
                row["artifact_sha256"]
                == (BenchmarkStore().path(row["run_id"]) / "results.sha256").read_text()
            )
            stored = BenchmarkStore().get(row["run_id"])
            episode = stored.episodes[0]
            if row["condition"].startswith("armoriq-"):
                expected = expected_policy(stored.config, report["benchmark"])
                for transition in episode.transitions:
                    if transition.get("decision") and transition.get("kind") != "guard_plan":
                        verify_decision(transition["decision"], expected)
                row["matched_policy_version_verified"] = True
                row["policy_hash"] = expected["policy_hash"]
            row["native_tool_errors"] = sum(
                bool((t.get("info") or {}).get("tool_error")) for t in episode.transitions
            )
            row["decision_sources"] = dict(
                Counter(
                    t["decision"]["reason"]
                    for t in episode.transitions
                    if t.get("decision") and t.get("kind") != "guard_plan"
                )
            )
        native_reports.append(report)
    conditions = {r["condition"]: Store().get(r["run_id"]) for r in model["runs"]}
    base = {e.scenario_id: e for e in conditions["unguarded"].episodes}
    monitor = {e.scenario_id: e for e in conditions["armoriq-monitor"].episodes}
    same = [
        name
        for name in base
        if [v.action.model_dump() for v in base[name].events if v.action]
        == [v.action.model_dump() for v in monitor[name].events if v.action]
    ]
    assert all(r["stable_observation_ids"] for r in model["runs"])
    fixed_sequences = []
    for row in fixture["runs"]:
        run = Store().get(row["run_id"])
        fixed_sequences.append(
            {
                e.scenario_id: [v.action.model_dump() for v in e.events if v.action]
                for e in run.episodes
            }
        )
    assert all(s == fixed_sequences[0] for s in fixed_sequences)
    status = Counter()
    for row in fixture["runs"] + model["runs"]:
        status.update(e.status for e in Store().get(row["run_id"]).episodes)
    for report in native_reports:
        for row in report["runs"]:
            status.update(e["status"] for e in row["episodes"])
    suite = load_suite("authorization-boundaries")
    policies = {}
    for label, folder in [("v1_array_equality", initial), ("v2_indexed_fields", setup)]:
        record = json.loads((folder / "provisioning.json").read_text())["policies"][
            "authorization-boundaries"
        ]
        policies[label] = {k: record[k] for k in ("policy_hash", "source_sha256", "status")}
    result = {
        "schema_version": "authorization-extension-results-1.0",
        "recorded_date": "2026-10-22",
        "scope": "Targeted authored extensions. Fixture, real-model, and native results are separate, not pooled population scores. No official leaderboard claim.",
        "suite": {
            "id": suite.id,
            "version": suite.version,
            "sha256": canonical_hash(suite.model_dump()),
            "cases": 17,
            "families": sorted({s.family for s in suite.scenarios}),
            "variants": dict(Counter(s.variant for s in suite.scenarios)),
        },
        "sdk": "0.8.17",
        "model": {"name": "qwen2.5:3b", "id": "357c53fb659c", "ollama": "0.34.0"},
        "policies": policies,
        "scripted_executor_probes": fixture,
        "real_model": model,
        "native_extensions": native_reports,
        "policy_authoring_diagnostics": {
            "same_scenarios_and_labels": True,
            "v1_scripted": initial_fixture,
            "v1_exploratory_model": initial_model,
            "v2_variable_id_exploration": variable_id_exploration,
            "finding": "Array-equality variants fell through to block even for valid BCCs. A separately versioned indexed-field policy passed the unchanged cases. This is observed deployed behavior, not a claim about all vendor implementations. Exploratory model inputs used variable run IDs and are not the final paired comparison.",
        },
        "verification": {
            "baseline_monitor_identical_proposal_cases": len(same),
            "scripted_identical_proposals_across_six_conditions": True,
            "local_trace_chains_verified": True,
            "local_metrics_recomputed_verified": True,
            "native_artifacts_verified": True,
            "matched_policy_versions_verified": True,
            "status_counts": dict(status),
            "final_episode_attempts": sum(status.values()),
        },
        "limitations": [
            "17 selected per-call cases; not representative of all tasks, models, attacks, or constraints.",
            "One model, seed and repeat; scripted native probes are not LLM attack success rates.",
            "The local reference guard matches the scripted outcome, so this does not demonstrate a unique algorithmic advantage over a correct rule engine.",
            "All attack candidates are in the fixture plans: plan declaration is not an authorization label.",
            "Eight-step local model budget produced truncations; they retain zero completion-under-policy credit.",
            "Array-policy v1 and all development traces are retained; no labels/cases were removed after seeing results.",
            "Indirect navigation remains an ArmorIQ policy/event-representation limitation; DoomArena detects it correctly.",
            "Native authored overlays support per-call args/intent rules only; execution counts are not automatically verified effect counts.",
        ],
    }
    assert result["verification"]["final_episode_attempts"] == 180
    destination.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print("Verified and archived", sum(status.values()), "final attempts:", dict(status))
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--setup", type=Path, default=Path(".benchmarks/policy-setup/20261022-boundaries-v2")
    )
    p.add_argument(
        "--initial", type=Path, default=Path(".benchmarks/policy-setup/20261022-boundaries-v1")
    )
    p.add_argument("--native", type=Path, default=Path(".benchmarks/authorization-probes"))
    p.add_argument("--output", type=Path, default=Path("docs/authorization-boundary-results.json"))
    a = p.parse_args()
    summarize(a.setup, a.initial, a.native, a.output)
