"""Verify defense-layer evidence and update the public result index.

Preserves the complete earlier campaign and its adverse findings. Local, native,
model and mechanism-proxy measurements remain separately labeled.
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from agent_intent_bench.catalog import load_suite
from agent_intent_bench.expressions import canonical_hash
from agent_intent_bench.metrics import aggregate
from agent_intent_bench.store import Store, verify_events


def local_summary(rows):
    return [
        {
            "condition": r["condition"],
            "attempts": len(r["episodes"]),
            "eligible": r["metrics"]["eligible_episodes"],
            "task_successes": sum(
                e["success"] for e in r["episodes"] if e["status"] in ("completed", "truncated")
            ),
            "safe_completions": sum(e["completion_under_policy"] for e in r["episodes"]),
            "unsafe_effect_episodes": r["metrics"]["observed_unauthorized_effect_episodes"],
        }
        for r in rows
    ]


def publish(source, docs, recorded_date):
    report = json.loads(source.read_text())
    assert all(r["agent_is_fixture"] for r in report["runs"])
    assert {"armoriq-monitor", "armoriq-enforce"} <= {r["condition"] for r in report["runs"]}
    statuses = Counter()
    proposals = []
    sdk_versions = set()
    for row in report["runs"]:
        stored = Store().get(row["run_id"])
        assert all(verify_events(e.events) for e in stored.episodes)
        metrics = aggregate(stored.episodes, guarded=row["condition"] != "unguarded")
        metrics.update(
            {
                key: sum(e.usage.get(key, 0) for e in stored.episodes)
                for key in ("input_tokens", "output_tokens")
            }
        )
        assert metrics == stored.metrics == row["metrics"]
        assert row["safe_completions"] == sum(e.completion_under_policy for e in stored.episodes)
        assert row["task_successes"] == sum(
            e.success for e in stored.episodes if e.status in ("completed", "truncated")
        )
        assert row["suite_hash"] == canonical_hash(load_suite("defense-layers").model_dump())
        row["budgets"] = {
            key: getattr(stored.config, key)
            for key in ("seed", "repeats", "max_steps", "episode_timeout", "step_timeout")
        }
        if not row["condition"].startswith("armoriq-"):
            row["guard_adapter"] = stored.config.guard.model_dump()
        if row["condition"].startswith("armoriq-"):
            sdk_versions.add(stored.manifest["packages"]["armoriq-sdk"])
            folder = Path(stored.config.guard.options["tool_catalog"]).parent.parent
            expected = json.loads((folder / "provisioning.json").read_text())["policies"][
                "defense-layers"
            ]
            for e in stored.episodes:
                for event in e.events:
                    if event.kind == "action" and event.decision:
                        assert expected["policy_id"] in event.decision.policy_ids
                        assert expected["policy_hash"] == event.decision.evidence["policy_version"]
            row["matched_policy_version_verified"] = True
        statuses.update(e.status for e in stored.episodes)
        proposals.append(
            {
                e.scenario_id: [v.action.model_dump() for v in e.events if v.kind == "action"]
                for e in stored.episodes
            }
        )
    assert len({r["pairing_hash"] for r in report["runs"]}) == 1
    assert all(p == proposals[0] for p in proposals)
    report.update(
        recorded_date=recorded_date,
        sdk_versions=sorted(sdk_versions),
        agent_is_fixture=True,
        identical_tool_proposals=True,
        verification={
            "local_trace_chains": True,
            "local_metrics_recomputed": True,
            "sdk_policy_versions_matched": True,
            "status_counts": dict(statuses),
            "attempts": sum(statuses.values()),
        },
    )
    (docs / "defense-layer-results.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    targeted = json.loads((docs / "authorization-boundary-results.json").read_text())
    native = {}
    for condition in ("unguarded", "armoriq-monitor", "armoriq-enforce"):
        rows = [
            r
            for group in targeted["native_extensions"]
            if group["benchmark"].startswith("agentdojo")
            for r in group["runs"]
            if r["condition"] == condition
        ]
        audits = [e["derived_scores"]["authorization_audit"] for r in rows for e in r["episodes"]]
        native[condition] = {
            "scripted_cases": len(audits),
            "native_utility_successes": sum(bool(a["native_task_success"]) for a in audits),
            "completions_under_authored_authorization": sum(
                a["completion_under_authorization"] for a in audits
            ),
            "unauthorized_native_calls": sum(a["unauthorized_native_executions"] for a in audits),
        }
    index_path = docs / "results.json"
    index = json.loads(index_path.read_text())
    index.update(
        last_updated=recorded_date,
        scope="Separate broad model, targeted authorization, and local defense-layer studies. Original native grades retained; no pooled performance score or official leaderboard claim.",
    )
    index["authorization_extensions_2026_10_22"] = {
        "recorded_date": targeted["recorded_date"],
        "report": "authorization-boundaries.md",
        "data": "authorization-boundary-results.json",
        "scripted_local": local_summary(targeted["scripted_executor_probes"]["runs"]),
        "real_model": local_summary(targeted["real_model"]["runs"]),
        "scripted_agentdojo": native,
        "attempts": targeted["verification"]["final_episode_attempts"],
        "limits": "Selected authored cases. Local reference matches ArmorIQ; real model loses one task success; indirect browser navigation bypasses enforcement. Native probes are not LLM attack-success rates.",
    }
    index["defense_layers_2026_10_23"] = {
        "recorded_date": recorded_date,
        "report": "intent-evaluation.md",
        "data": "defense-layer-results.json",
        "scope": report["scope"],
        "attempts": sum(statuses.values()),
        "summary": [
            {
                "condition": r["condition"],
                "eligible": r["eligible"],
                "task_successes": r["task_successes"],
                "safe_completions": r["safe_completions"],
                "unsafe_effect_episodes": r["metrics"]["observed_unauthorized_effect_episodes"],
                "denied_authorized_proposals": r["metrics"]["guard_confusion"]["blocked_authorized"]
                if r["condition"] != "unguarded"
                else None,
            }
            for r in report["runs"]
        ],
        "limits": "Fixed benign-content scripted proposals and simulated tools. Pattern-content, pre-authenticated-principal/tool grants, and workspace/host boundary proxies are not named product tests, authentication tests or OS isolation tests. A full intent-aware rule engine also passes.",
    }
    index_path.write_text(json.dumps(index, indent=2, allow_nan=False) + "\n")
    print(
        "Verified and published", sum(statuses.values()), "defense-layer attempts:", dict(statuses)
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--source", type=Path, default=Path(".benchmarks/defense-layers/20261023-results.json")
    )
    p.add_argument("--docs", type=Path, default=Path("docs"))
    p.add_argument("--recorded-date", default="2026-10-23")
    a = p.parse_args()
    publish(a.source, a.docs, a.recorded_date)
