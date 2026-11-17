"""How many AgentDojo user tasks can have their write arguments pinned from the prompt alone.

Offline. For each user task, takes the side-effecting calls in AgentDojo's ground
truth and checks whether every argument value appears in the user prompt text.
A value that only comes from a tool result (a recipient read from a file, an IBAN
from a bill) cannot be pinned by rules generated from the request alone.

  .benchmarks/runtimes/agentdojo/bin/python scripts/agentdojo_rule_coverage.py
"""

from __future__ import annotations

import argparse
import json
from collections import Counter

from agentdojo.task_suite.load_suites import get_suites
from count_agentdojo_attack_types import effectful

# Free text the agent writes itself; a security rule doesn't pin these.
FREE_TEXT = {"subject", "body", "content", "description", "title", "message", "text", "attachments"}


def norm(value):
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def values(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from values(v)
    elif isinstance(value, (list, tuple, set)):
        for v in value:
            yield from values(v)
    elif value is not None and not isinstance(value, bool):
        yield norm(value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1.2.2")
    parser.add_argument("--pairs", help="pairs JSON from count_agentdojo_attack_types.py")
    parser.add_argument("--json")
    args = parser.parse_args()
    rows, counts = [], Counter()
    for suite_name, suite in sorted(get_suites(args.version).items()):
        env = suite.load_and_inject_default_environment(suite.get_injection_vector_defaults())
        for uid, task in suite.user_tasks.items():
            prompt = task.PROMPT.lower()
            writes = [
                c for c in task.ground_truth(env.model_copy(deep=True)) if effectful(c.function)
            ]
            missing = sorted(
                {
                    f"{c.function}.{k}"
                    for c in writes
                    for k, v in c.args.items()
                    if k not in FREE_TEXT and any(x.lower() not in prompt for x in values(v))
                }
            )
            kind = "read_only" if not writes else ("pinnable" if not missing else "needs_tool_data")
            counts[kind] += 1
            rows.append(
                {
                    "suite": suite_name,
                    "user_task": uid,
                    "kind": kind,
                    "write_tools": sorted({c.function for c in writes}),
                    "args_not_in_prompt": missing,
                }
            )
    print(f"AgentDojo {args.version}: {sum(counts.values())} user tasks")
    for k in ("read_only", "pinnable", "needs_tool_data"):
        print(f"  {k:<16}{counts[k]:>4}")
    if args.pairs:
        kinds = {(r["suite"], r["user_task"]): r["kind"] for r in rows}
        same = [p for p in json.load(open(args.pairs))["pairs"] if p["kind"] == "same_tools"]
        c = Counter(kinds[(p["suite"], p["user_task"])] for p in same)
        print(f"same-tool attack pairs by user-task kind ({len(same)}): {dict(c)}")
    if args.json:
        with open(args.json, "w") as f:
            json.dump(rows, f, indent=1)


if __name__ == "__main__":
    main()
