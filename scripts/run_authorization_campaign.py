"""Run fixed authored probes plus transparent local baselines; optional real-model trials.

No native/fixture/model scores are pooled. Policies must be provisioned separately.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

import yaml

from agent_intent_bench.catalog import load_suite
from agent_intent_bench.experiments import pairing_identity
from agent_intent_bench.models import AdapterConfig, Intent, Rule, RunConfig
from agent_intent_bench.runner import run_suite
from agent_intent_bench.store import Store, verify_events


async def run(setup, model=False):
    suite = load_suite("authorization-boundaries")
    source = yaml.safe_load((setup / "run-configs/authorization-boundaries.yaml").read_text())
    base = RunConfig.model_validate(source)
    if model:
        live = yaml.safe_load(Path("examples/armoriq-inside/intent-gym.yaml").read_text())["agent"]
        base.agent = AdapterConfig.model_validate(live)
    conditions = (
        ("unguarded", "armoriq-monitor", "armoriq-enforce")
        if model
        else (
            "unguarded",
            "tool-scope-only",
            "plan-membership-only",
            "reference",
            "armoriq-monitor",
            "armoriq-enforce",
        )
    )
    store = Store()
    report = {
        "protocol": "authored-authorization-boundaries-1.0",
        "agent_kind": "real-model" if model else "scripted-executor-probe",
        "model_robustness_claim": False,
        "suite": "authorization-boundaries",
        "suite_cases": len(suite.scenarios),
        "stable_observation_ids": base.stable_observation_ids,
        "conditions": list(conditions),
        "runs": [],
        "scope": "Per-call authorization cases; not an official benchmark or representative population sample.",
    }
    target = setup / ("model-results.json" if model else "probe-results.json")
    expected = json.loads((setup / "provisioning.json").read_text())["policies"][
        "authorization-boundaries"
    ]
    for condition in conditions:
        cfg = base.model_copy(deep=True)
        cfg.mode = (
            "unguarded"
            if condition == "unguarded"
            else "monitor"
            if condition == "armoriq-monitor"
            else "enforce"
        )
        if condition in ("tool-scope-only", "reference", "plan-membership-only"):
            cfg.instrumentation = "external"
            cfg.guard = AdapterConfig(
                kind="plan" if condition == "plan-membership-only" else "reference"
            )
            if condition == "tool-scope-only":
                cfg.guard_policy = Intent(
                    id="tool-allowlist-baseline",
                    objective="Tool scope only, without argument constraints",
                    rules=[
                        Rule(
                            id="tools",
                            kind="allow_tools",
                            description="Tool allowlist",
                            allowed=sorted({t.name for s in suite.scenarios for t in s.tools}),
                        )
                    ],
                )
        print(condition, flush=True)
        result = await run_suite(suite, cfg, store)
        assert all(verify_events(e.events) for e in result.episodes)
        decisions = {}
        for episode in result.episodes:
            for event in episode.events:
                if not event.decision or condition not in ("armoriq-monitor", "armoriq-enforce"):
                    continue
                decision = event.decision
                if event.kind == "action":
                    assert expected["policy_id"] in decision.policy_ids
                    assert decision.evidence["policy_version"] == expected["policy_hash"]
                reason = decision.reason
                key = "matched-policy-" + decision.action if decision.policy_ids else reason
                decisions[key] = decisions.get(key, 0) + 1
        report["runs"].append(
            {
                "condition": condition,
                "run_id": result.id,
                "pairing_hash": pairing_identity(cfg),
                "metrics": result.metrics,
                "fixture": result.manifest["agent_is_fixture"],
                "trace_chains_verified": True,
                "decision_sources": decisions,
                "episodes": [
                    {
                        "scenario_id": e.scenario_id,
                        "variant": e.variant,
                        "status": e.status,
                        "success": e.success,
                        "completion_under_policy": e.completion_under_policy,
                        "unsafe_effects": e.effect_violations,
                        "error": e.error.splitlines()[0] if e.error else None,
                    }
                    for e in result.episodes
                ],
            }
        )
        target.write_text(json.dumps(report, indent=2) + "\n")
        print(
            result.id,
            result.metrics["completion_under_policy"],
            "unsafe",
            result.metrics["observed_unauthorized_effect_episodes"],
            "errors",
            result.metrics["errors"],
            flush=True,
        )
    # Fairness identity excludes condition/guard but includes the agent, task and budgets.
    assert len({r["pairing_hash"] for r in report["runs"]}) == 1
    report["pairing_verified"] = True
    target.write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("setup", type=Path)
    p.add_argument("--model", action="store_true")
    args = p.parse_args()
    report = asyncio.run(run(args.setup, args.model))
    raise SystemExit(
        2 if any(r["metrics"]["errors"] or r["metrics"]["cancelled"] for r in report["runs"]) else 0
    )
