"""Replay scripted traces through the local plan-tools stand-in and through ArmorIQ IAP.

No model is called. Each case is replayed with the trace that follows the planted data, after
declaring the plan of the trace that ignores it, so the replay leaves its plan wherever the case
makes that possible. The two guards must decide every call the same way. A difference is a
setup error or a real gap between the stand-in and the product, and is printed.
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

from agent_intent_bench.catalog import load_config, load_suite
from agent_intent_bench.models import AdapterConfig
from agent_intent_bench.runner import run_suite
from agent_intent_bench.store import Store


def with_plans(actions, planned):
    """Put each turn's plan in front of that turn's actions; a finish ends a turn."""
    turns, plans = [[]], [[]]
    for source, target in ((actions, turns), (planned, plans)):
        for action in source:
            if action.get("kind") == "finish":
                target.append([])
            else:
                target[-1].append(action)
    out = []
    for index, turn in enumerate(turns):
        if not turn and index == len(turns) - 1:
            break
        plan = plans[index] if index < len(plans) else []
        out += [{"kind": "plan", "plan": plan}, *turn, {"kind": "finish"}]
    return out


def traces():
    """(suite, scenario, trace name, actions with plans) for every scripted trace."""
    from examples import build_coding_sessions_suite as coding
    from examples import build_runtime_intent_model_suite as single
    from examples import build_runtime_intent_turns_suite as turns

    for name, module in (("runtime-intent-model", single), ("runtime-intent-turns", turns)):
        suite = load_suite(name)
        for scenario in suite.scenarios:
            family, kind = scenario.id.split(".")[1:]
            both = module.calls(family, kind)
            for trace in ("ignore", "follow"):
                yield suite, scenario, trace, with_plans(both[trace], both["ignore"])
    suite = load_suite("coding-sessions")
    for scenario in suite.scenarios:
        kind = scenario.id.rsplit(".", 1)[1]
        for trace, actions in coding.TRACES[kind].items():
            yield suite, scenario, trace, with_plans(actions, coding.TRACES[kind]["reference"])


def decisions(episode):
    return [
        (e.action.tool, e.decision.action if e.decision else "allow")
        for e in episode.events
        if e.kind == "action"
    ]


def block_reasons(episode):
    return [
        e.decision.reason.split(":")[0]
        for e in episode.events
        if e.kind == "action" and e.decision and e.decision.action != "allow"
    ]


async def run(output, armoriq, only=None):
    from scripts.run_runtime_intent_models import ARMORIQ_IAP, guard_config

    base = load_config(Path("examples/intent-evaluation.yaml"))
    base.mode, base.max_steps, base.episode_timeout = "enforce", 16, 300
    report = {"compared": 0, "calls": 0, "blocked": 0, "errors": [], "differences": []}
    started = time.monotonic()
    for suite, scenario, trace, actions in traces():
        if only and only not in scenario.id:
            continue
        seen = {}
        for guard in ("plan-tools", ARMORIQ_IAP):
            config = base.model_copy(deep=True)
            config.guard = guard_config(guard, armoriq)
            config.agent = AdapterConfig(kind="script", options={"actions": actions})
            one = suite.model_copy(update={"scenarios": [scenario]})
            seen[guard] = (await run_suite(one, config, Store())).episodes[0]
        local, real = seen["plan-tools"], seen[ARMORIQ_IAP]
        label = f"{scenario.id} [{trace}]"
        if real.status == "error" or local.status == "error":
            report["errors"].append(
                {"case": label, "plan-tools": local.error, ARMORIQ_IAP: real.error}
            )
            print("error", label, real.error or local.error, flush=True)
            continue
        report["compared"] += 1
        report["calls"] += len(decisions(real))
        report["blocked"] += sum(d != "allow" for _, d in decisions(real))
        same_outcome = (local.effect_violations, local.success) == (
            real.effect_violations,
            real.success,
        )
        if decisions(local) != decisions(real) or not same_outcome:
            report["differences"].append(
                {
                    "case": label,
                    "plan-tools": decisions(local),
                    ARMORIQ_IAP: decisions(real),
                    "armoriq_block_reasons": block_reasons(real),
                    "unauthorized_effects": [local.effect_violations, real.effect_violations],
                    "task_success": [local.success, real.success],
                }
            )
            print("differs", label, block_reasons(real), flush=True)
    report["seconds"] = round(time.monotonic() - started)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=1) + "\n")
    print(
        f"{report['compared']} traces compared, {report['calls']} calls, "
        f"{report['blocked']} blocked by IAP, {len(report['differences'])} differences, "
        f"{len(report['errors'])} errors, {report['seconds']} s"
    )
    return report


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts.run_runtime_intent_models import armoriq_login

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--armoriq-credentials", type=Path, required=True)
    parser.add_argument("--armoriq-environment", choices=["staging", "production"], required=True)
    parser.add_argument("--armoriq-agent", required=True)
    parser.add_argument("--output", type=Path, default=Path(".benchmarks/armoriq-iap/parity.json"))
    parser.add_argument("--only", help="replay only scenarios whose id contains this text")
    args = parser.parse_args()
    login = armoriq_login(args.armoriq_credentials, args.armoriq_environment, args.armoriq_agent)
    report = asyncio.run(run(args.output, login, args.only))
    sys.exit(1 if report["differences"] or report["errors"] else 0)
