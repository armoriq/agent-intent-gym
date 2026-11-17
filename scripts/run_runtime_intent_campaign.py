"""Run the runtime-intent suite under local plan-check proxies.

plan-tools stands in for a tool-name plan check, plan-exact for a check that also binds
arguments, and argument-rules for argument predicates taken from the request. These are local
mechanism proxies, not measurements of ArmorIQ or any other product. The agent is scripted.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from agent_intent_bench.catalog import load_config, load_suite
from agent_intent_bench.experiments import pairing_identity
from agent_intent_bench.models import AdapterConfig
from agent_intent_bench.runner import run_suite
from agent_intent_bench.store import Store, verify_events

AGENT = AdapterConfig(kind="python", factory="examples.benchmarks.runtime_intent:create_agent")
STACKS = {
    "plan-tools": ["plan-tools"],
    "argument-rules": ["argument-rules"],
    "plan-tools+argument-rules": ["plan-tools", "argument-rules"],
    "plan-exact": ["plan-exact"],
    "plan-exact+argument-rules": ["plan-exact", "argument-rules"],
}
CONDITIONS = [
    ("unguarded", None),
    *[
        (
            name,
            AdapterConfig(
                kind="python",
                factory="examples.benchmarks.runtime_intent:create_guard_stack",
                options={"layers": layers},
            ),
        )
        for name, layers in STACKS.items()
    ],
    ("reference-intent", AdapterConfig(kind="reference")),
]


def outcome(episode):
    blocked = [
        e
        for e in episode.events
        if e.kind == "action" and e.decision and e.decision.action != "allow"
    ]
    return {
        "safe": episode.completion_under_policy,
        "unsafe_effects": episode.effect_violations,
        "blocked_authorized": sum(bool(e.verdict and e.verdict.allowed) for e in blocked),
    }


async def run(output, store=None):
    base = load_config(Path("examples/intent-evaluation.yaml"))
    base.agent = AGENT
    suite = load_suite("runtime-intent")
    report = {
        "schema_version": "runtime-intent-study-1.0",
        "suite": suite.id,
        "scope": "Authored simulated tools, scripted executor and local plan-check proxies. Not an LLM attack-resistance or product result.",
        "runs": [],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    for name, guard in CONDITIONS:
        config = base.model_copy(deep=True)
        config.mode = "unguarded" if guard is None else "enforce"
        config.instrumentation = "external"
        if guard:
            config.guard = guard
        result = await run_suite(suite, config, store or Store())
        assert all(verify_events(e.events) for e in result.episodes)
        cases = {e.scenario_id: outcome(e) for e in result.episodes}
        report["runs"].append(
            {
                "condition": name,
                "run_id": result.id,
                "pairing_hash": pairing_identity(config),
                "suite_hash": result.manifest["suite_hash"],
                "safe_completions": sum(c["safe"] for c in cases.values()),
                "unsafe_episodes": sum(c["unsafe_effects"] > 0 for c in cases.values()),
                "blocked_authorized": sum(c["blocked_authorized"] for c in cases.values()),
                "errors": result.metrics["errors"],
                "cases": cases,
            }
        )
        row = report["runs"][-1]
        print(
            f"{name}: {row['safe_completions']}/{len(cases)} safe, "
            f"{row['unsafe_episodes']} unsafe, {row['blocked_authorized']} authorized calls blocked",
            flush=True,
        )
    assert len({r["pairing_hash"] for r in report["runs"]}) == 1
    output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path(".benchmarks/runtime-intent/results.json")
    )
    args = parser.parse_args()
    result = asyncio.run(run(args.output))
    raise SystemExit(2 if any(r["errors"] for r in result["runs"]) else 0)
