#!/usr/bin/env python3
"""Read-only characterization of how the user actually prompts.

Walks ~/.claude/projects/**/*.jsonl, extracts genuine human prompts (skipping
tool results, meta/sidechain, and harness-injected text), and reports the traits
that plausibly drive intent drift in real use: prompt length, multi-goal density,
scope-expanding language, and specificity (does the prompt name a file/symbol).

Purpose: replace guesses about "how I prompt" with an empirical profile that the
benchmark's task prompts should match, so drift is measured under realistic input.
"""
import glob
import json
import os
import re
import statistics

PROJECTS = os.path.expanduser("~/.claude/projects")

# Text that is clearly not a human-typed prompt.
NON_HUMAN_PREFIXES = ("<system-reminder", "<command-", "Caveat:", "[SYSTEM",
                      "<local-command", "<task-", "Called the", "This session is being continued")

MULTI_GOAL = re.compile(r"\b(also|then|additionally|as well|after that|and also|plus)\b", re.I)
BULLETS = re.compile(r"(^|\n)\s*(\d+[.)]|[-*])\s", re.M)
SCOPE_CREEP = re.compile(r"\b(clean up|cleanup|refactor|while you(?:'re| are)?|make it better|improve|tidy|optimi[sz]e|everything|anything else|any other|as well|and fix|also fix)\b", re.I)
# specificity signals: a filename, a backticked token, or a path
SPECIFIC = re.compile(r"`[^`]+`|\b[\w/]+\.(py|ts|tsx|js|jsx|go|rs|java|rb|c|cpp|sql|yaml|yml|json|md)\b|/\w+/")


def human_prompts():
    for path in glob.glob(os.path.join(PROJECTS, "**", "*.jsonl"), recursive=True):
        try:
            fh = open(path)
        except OSError:
            continue
        with fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") != "user":
                    continue
                if obj.get("isMeta") or obj.get("isSidechain"):
                    continue
                msg = obj.get("message", {})
                content = msg.get("content")
                text = None
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    # skip if it carries a tool_result; else join text blocks
                    if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
                        continue
                    parts = [b.get("text", "") for b in content
                             if isinstance(b, dict) and b.get("type") == "text"]
                    text = "\n".join(p for p in parts if p)
                if not text:
                    continue
                t = text.strip()
                if not t or t.startswith(NON_HUMAN_PREFIXES) or t.startswith("/"):
                    continue
                yield t


def main():
    prompts = list(human_prompts())
    n = len(prompts)
    if not n:
        print("no prompts found")
        return
    words = [len(p.split()) for p in prompts]
    multi = sum(1 for p in prompts if MULTI_GOAL.search(p) or len(BULLETS.findall(p)) >= 2)
    creep = sum(1 for p in prompts if SCOPE_CREEP.search(p))
    specific = sum(1 for p in prompts if SPECIFIC.search(p))
    short = sum(1 for w in words if w <= 15)

    def pct(x):
        return f"{100 * x / n:.0f}%"

    q = statistics.quantiles(words, n=100)
    print(f"prompts analyzed: {n}")
    print(f"word count: median={statistics.median(words):.0f} "
          f"p75={q[74]:.0f} p90={q[89]:.0f} max={max(words)}")
    print(f"short (<=15 words): {pct(short)}")
    print(f"multi-goal (also/then/bullets): {pct(multi)}")
    print(f"scope-expanding language: {pct(creep)}")
    print(f"names a specific file/symbol/path: {pct(specific)}")
    print(f"vague (no specific target): {pct(n - specific)}")


if __name__ == "__main__":
    main()
