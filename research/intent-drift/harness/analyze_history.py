#!/usr/bin/env python3
"""Retrospective session-duration analysis over local Claude Code transcripts.

Read-only. Measures, per user prompt, the run duration = time from the prompt
to the last assistant message before the next prompt (idle time after the
response finished is not counted). Aggregates by month (p95 + bootstrap CI) and
compares an early vs recent window. Outputs metadata/aggregates only, never
prompt text.
"""
import glob
import json
import os
import random
from datetime import datetime, timezone

ROOT = os.path.expanduser("~/.claude/projects")
META_PREFIXES = ("<command-", "<local-command", "<user-prompt-submit",
                 "[Request interrupted", "Caveat:", "<system-reminder")


def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def is_real_prompt(o):
    """True if this entry is a human-sent prompt (not a tool result / sidechain)."""
    if o.get("type") != "user" or o.get("isSidechain"):
        return False
    m = o.get("message", {})
    c = m.get("content") if isinstance(m, dict) else None
    text = None
    if isinstance(c, str):
        text = c
    elif isinstance(c, list):
        types = {b.get("type") for b in c if isinstance(b, dict)}
        if "tool_result" in types:        # a tool result, not a prompt
            return False
        if "text" not in types:
            return False
        text = next((b.get("text", "") for b in c
                     if isinstance(b, dict) and b.get("type") == "text"), "")
    else:
        return False
    if not text or not text.strip():
        return False
    return not text.lstrip().startswith(META_PREFIXES)


def session_events(path):
    """Ordered (timestamp, kind) events for one transcript. kind: prompt|assistant."""
    ev = []
    for line in open(path, errors="ignore"):
        try:
            o = json.loads(line)
        except Exception:
            continue
        ts = parse_ts(o.get("timestamp"))
        if ts is None:
            continue
        if is_real_prompt(o):
            ev.append((ts, "prompt"))
        elif o.get("type") == "assistant":
            ev.append((ts, "assistant"))
    ev.sort(key=lambda x: x[0])
    return ev


def durations():
    """List of (prompt_datetime, duration_seconds) across all transcripts."""
    out = []
    for path in glob.glob(os.path.join(ROOT, "**", "*.jsonl"), recursive=True):
        ev = session_events(path)
        # index of next prompt for each position
        for i, (ts, kind) in enumerate(ev):
            if kind != "prompt":
                continue
            last_asst = None
            for ts2, kind2 in ev[i + 1:]:
                if kind2 == "prompt":
                    break
                if kind2 == "assistant":
                    last_asst = ts2
            if last_asst is None:
                continue
            dur = (last_asst - ts).total_seconds()
            if dur > 0:
                out.append((ts, dur))
    return out


def pct(sorted_vals, p):
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def boot_ci_p95(vals, iters=2000, seed=7):
    if len(vals) < 5:
        return (0.0, 0.0)
    rnd = random.Random(seed)
    est = []
    n = len(vals)
    for _ in range(iters):
        s = sorted(vals[rnd.randrange(n)] for _ in range(n))
        est.append(pct(s, 0.95))
    est.sort()
    return (pct(est, 0.025), pct(est, 0.975))


def fmt(sec):
    sec = int(round(sec))
    return f"{sec // 60}m{sec % 60:02d}s"


def main():
    data = durations()
    if not data:
        print("no durations found")
        return
    data.sort()
    print(f"total prompts measured: {len(data)}")
    print(f"date range: {data[0][0].date()} to {data[-1][0].date()}\n")

    # Table A: p95 by month
    by_month = {}
    for ts, d in data:
        by_month.setdefault(ts.strftime("%Y-%m"), []).append(d)
    print("=== Table A: p95 by month (all harnesses) ===")
    print(f"{'Month':<10}{'n':>6}   {'p95':>8}   {'95% CI (bootstrap)'}")
    for month in sorted(by_month):
        vals = sorted(by_month[month])
        lo, hi = boot_ci_p95(vals)
        print(f"{month:<10}{len(vals):>6}   {fmt(pct(vals, 0.95)):>8}   "
              f"{fmt(lo)} to {fmt(hi)}")

    # Table B: early vs recent window
    months = sorted(by_month)
    early, recent = months[0], months[-1]

    def window(month):
        return sorted(by_month[month])
    print("\n=== Table B: early vs recent window ===")
    print(f"{'Window':<12}{'Turns':>7}   {'Median':>8}{'Mean':>8}{'p75':>8}{'p90':>8}")
    for label, month in ((early, early), (recent, recent)):
        v = window(month)
        print(f"{label:<12}{len(v):>7}   {fmt(pct(v,0.5)):>8}{fmt(sum(v)/len(v)):>8}"
              f"{fmt(pct(v,0.75)):>8}{fmt(pct(v,0.90)):>8}")


if __name__ == "__main__":
    main()
