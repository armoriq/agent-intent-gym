"""Pick a fixed, stratified subset of AgentDojo (user task, injection task) pairs.

Input is the per-pair file written by `count_agentdojo_attack_types.py --json`. Per suite the
subset takes up to `--same-tools` pairs where the injection reuses the user task's tools, up
to `--text-only` pairs where it only asks for text, and fills the rest with pairs that need
a tool outside the user task. The draw is seeded, so the same inputs give the same subset.
"""

import argparse
import json
import random
from collections import Counter


def select(pairs, per_suite, same_tools, text_only, seed):
    chosen = []
    for suite in sorted({p["suite"] for p in pairs}):
        rng = random.Random(f"{seed}:{suite}")
        pools = {
            kind: sorted(
                (p["user_task"], p["injection_task"])
                for p in pairs
                if p["suite"] == suite and p["kind"] == kind
            )
            for kind in ("same_tools", "text_only", "plan_breaking")
        }
        quota = {
            "same_tools": min(same_tools, len(pools["same_tools"])),
            "text_only": min(text_only, len(pools["text_only"])),
        }
        quota["plan_breaking"] = per_suite - sum(quota.values())
        for kind, count in quota.items():
            for user_task, injection_task in sorted(rng.sample(pools[kind], count)):
                chosen.append(
                    {
                        "suite": suite,
                        "user_task": user_task,
                        "injection_task": injection_task,
                        "kind": kind,
                    }
                )
    return chosen


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pairs")
    parser.add_argument("output")
    parser.add_argument("--per-suite", type=int, default=40)
    parser.add_argument("--same-tools", type=int, default=10)
    parser.add_argument("--text-only", type=int, default=4)
    parser.add_argument("--seed", default="20261117")
    args = parser.parse_args()
    source = json.load(open(args.pairs))
    subset = select(source["pairs"], args.per_suite, args.same_tools, args.text_only, args.seed)
    document = {
        "version": source["version"],
        "seed": args.seed,
        "per_suite": args.per_suite,
        "pairs": subset,
    }
    with open(args.output, "w") as handle:
        json.dump(document, handle, indent=1)
        handle.write("\n")
    print(len(subset), "pairs", dict(Counter(p["kind"] for p in subset)))
