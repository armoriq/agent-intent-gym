"""Classify AgentDojo attack cases by which ArmorIQ layer can stop them.

Offline: reads AgentDojo's own task definitions and ground-truth tool calls.
No model, no API key, no network.

For every (user task, injection task) pair:
  plan_breaking  -> the injection needs at least one tool the user task's
                    ground truth never calls. A plan check on tool names can
                    stop it, assuming the agent's plan matches the ground truth.
  same_tools     -> every tool the injection needs is already used by the user
                    task. Only an argument check can stop it.
  text_only      -> the injection asks only for words in the final answer, no
                    tool call. Neither tool-level layer can stop it.

AgentDojo leaves ground_truth empty for a few injection tasks. Their tools are
taken from MANUAL_TOOLS below, read from each task's GOAL text, and every such
pair is marked "manual": true in the JSON output.

Run with the AgentDojo runtime:
  .benchmarks/runtimes/agentdojo/bin/python scripts/count_agentdojo_attack_types.py
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict

from agentdojo.task_suite.load_suites import get_suites

MANUAL_TOOLS = {
    ("workspace", "injection_task_6"): ["get_unread_emails", "send_email", "delete_email"],
    ("workspace", "injection_task_7"): [
        "get_received_emails",
        "get_sent_emails",
        "send_email",
        "delete_email",
    ],
    ("workspace", "injection_task_8"): ["get_unread_emails", "send_email", "delete_email"],
    ("workspace", "injection_task_9"): ["get_unread_emails", "send_email", "delete_email"],
    ("workspace", "injection_task_10"): ["list_files", "send_email", "delete_email"],
    ("workspace", "injection_task_11"): ["list_files", "send_email", "delete_email", "delete_file"],
    ("workspace", "injection_task_12"): ["list_files", "send_email", "delete_email", "delete_file"],
    ("workspace", "injection_task_13"): ["get_day_calendar_events", "send_email"],
}
TEXT_ONLY = {("travel", "injection_task_6")}
# The original AgentDojo paper's 629 cases used only workspace injection tasks 0 to 5.
V1_WORKSPACE_INJECTIONS = {f"injection_task_{i}" for i in range(6)}


READ_PREFIXES = ("get_", "search_", "list_", "read_", "check_")
# Reads that still send data out or reach an attacker-chosen host count as effects.
EFFECTFUL_READS = {"get_webpage"}


def effectful(tool):
    return tool in EFFECTFUL_READS or not tool.startswith(READ_PREFIXES)


def tools(calls):
    return [call.function for call in calls]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1.2.2")
    parser.add_argument("--json", help="write per-pair results to this file")
    args = parser.parse_args()

    rows = []
    summary = defaultdict(Counter)
    for suite_name, suite in sorted(get_suites(args.version).items()):
        env = suite.load_and_inject_default_environment(suite.get_injection_vector_defaults())
        user = {}
        for uid, task in suite.user_tasks.items():
            user[uid] = tools(task.ground_truth(env.model_copy(deep=True)))
        inj, manual = {}, set()
        for iid, task in suite.injection_tasks.items():
            found = tools(task.ground_truth(env.model_copy(deep=True)))
            if not found and (suite_name, iid) in MANUAL_TOOLS:
                found, _ = MANUAL_TOOLS[(suite_name, iid)], manual.add(iid)
            inj[iid] = found
        for uid, utools in user.items():
            for iid, itools in inj.items():
                new = sorted(set(itools) - set(utools))
                effects = sorted(t for t in set(itools) if effectful(t))
                effects_blocked = bool(effects) and all(t not in utools for t in effects)
                if (suite_name, iid) in TEXT_ONLY:
                    kind = "text_only"
                elif not itools:
                    raise ValueError(f"{suite_name}/{iid} has no tools and no manual entry")
                else:
                    kind = "plan_breaking" if new else "same_tools"
                summary[suite_name][kind] += 1
                summary[suite_name]["effects_blocked"] += effects_blocked
                if suite_name != "workspace" or iid in V1_WORKSPACE_INJECTIONS:
                    summary["_paper629"][kind] += 1
                    summary["_paper629"]["effects_blocked"] += effects_blocked
                rows.append(
                    {
                        "suite": suite_name,
                        "user_task": uid,
                        "injection_task": iid,
                        "user_tools": sorted(set(utools)),
                        "injection_tools": sorted(set(itools)),
                        "tools_outside_user_task": new,
                        "kind": kind,
                        "effect_tools": effects,
                        "every_effect_unplanned": effects_blocked,
                        "manual": iid in manual,
                    }
                )
        summary[suite_name]["user_tasks"] = len(user)
        summary[suite_name]["injection_tasks"] = len(inj)
        for iid, itools in inj.items():
            flag = " (manual)" if iid in manual else ""
            print(f"  {suite_name}/{iid}: {sorted(set(itools))}{flag}")

    def line(name, c):
        pairs = c["plan_breaking"] + c["same_tools"] + c["text_only"]
        print(
            f"{name:<13}{c['user_tasks'] or '':>6}{c['injection_tasks'] or '':>5}{pairs:>7}"
            f"{c['plan_breaking']:>15}{c['same_tools']:>12}{c['text_only']:>11}"
            f"{c['effects_blocked']:>18}"
        )

    total = Counter()
    print(f"\nAgentDojo {args.version}")
    print(
        f"{'suite':<13}{'user':>6}{'inj':>5}{'pairs':>7}{'plan-breaking':>15}{'same-tools':>12}{'text-only':>11}"
        f"{'effects-unplanned':>18}"
    )
    for name, c in summary.items():
        if name.startswith("_"):
            continue
        total.update(c)
        line(name, c)
    line("total", total)
    line("paper's 629", summary["_paper629"])
    if args.json:
        with open(args.json, "w") as f:
            json.dump({"version": args.version, "pairs": rows}, f, indent=1)


if __name__ == "__main__":
    main()
