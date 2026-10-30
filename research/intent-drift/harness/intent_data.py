#!/usr/bin/env python3
"""Single source of truth for every measured number in the intent-drift study.

All three deliverable PDFs import from here so no figure is hand-entered or
duplicated. Everything is queried live from db/results.db via the latest-clean-run
matrix in make_benchmark_paper (which already excludes vendor-cap / empty-session
rows). Cohorts:

  gen1  - 8 legacy bundles, original 7 domains
  gen2  - 7 current-generation arms, original 7 domains
  new   - the 10 new software/algorithmic domains; only the arms that have run
          appear (Cursor third-party quota capped the other 5 until 30 Sep 2026)

Usage: import intent_data as D; D.snapshot(D.connect())
"""
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DB = os.path.join(ROOT, "db", "results.db")
sys.path.insert(0, HERE)
import make_benchmark_paper as mb  # noqa: E402

GEN1_ARMS = ["claude-code-opus-4-8", "cursor-codex-5.3", "cursor-composer-2.5",
             "cursor-glm-5.2", "cursor-gpt-5.6-sol", "cursor-grok-4.6",
             "cursor-gemini-3.x", "cursor-kimi-k2.7-code"]
GEN2_ARMS = list(mb.ARM_ORDER)

# The 10 new domains, scoped/loose/vague slugs in a fixed order.
NEW_LADDER = [
    ("median", "T025-stats-median", "T035-stats-loose-prompt", "T036-stats-vague-prompt", "algorithmic"),
    ("grade boundary", "T026-grade-boundary", "T037-grade-loose-prompt", "T038-grade-vague-prompt", "algorithmic"),
    ("bisect insert", "T027-bisect-insert", "T039-bisect-loose-prompt", "T040-bisect-vague-prompt", "algorithmic"),
    ("moving average", "T028-moving-average", "T041-moving-loose-prompt", "T042-moving-vague-prompt", "algorithmic"),
    ("duration format", "T029-duration-hms", "T043-duration-loose-prompt", "T044-duration-vague-prompt", "algorithmic"),
    ("nth largest", "T030-nth-largest", "T045-nth-loose-prompt", "T046-nth-vague-prompt", "algorithmic"),
    ("config merge", "T031-config-merge", "T047-config-loose-prompt", "T048-config-vague-prompt", "broader software"),
    ("CLI flags", "T032-cli-flags", "T049-cli-loose-prompt", "T050-cli-vague-prompt", "broader software"),
    ("semver compare", "T033-semver-compare", "T051-semver-loose-prompt", "T052-semver-vague-prompt", "broader software"),
    ("querystring", "T034-querystring-build", "T053-querystring-loose-prompt", "T054-querystring-vague-prompt", "broader software"),
]
NEW_SCOPED = [r[1] for r in NEW_LADDER]
NEW_LOOSE = [r[2] for r in NEW_LADDER]
NEW_VAGUE = [r[3] for r in NEW_LADDER]


def connect():
    return sqlite3.connect(DB)


def matrix(con):
    return mb.latest_matrix(con)


def orig_rung(idx):
    return [mb.LADDER[d][idx] for d in mb.DOMAIN_ORDER]


def pooled(mtx, arms, slugs):
    """Return dict(drift, total, symbols, broken) over arms x slugs (present cells only)."""
    drift = total = symbols = broken = 0
    for a in arms:
        for s in slugs:
            c = mtx.get((a, s))
            if c is None:
                continue
            total += 1
            if c["unreq"] > 0:
                drift += 1
                symbols += c["unreq"]
            if c["intent"] == 0:
                broken += 1
    return dict(drift=drift, total=total, symbols=symbols, broken=broken)


def new_arms_present(mtx):
    """Which gen-2 arms actually have data on the new loose rung (quota-aware)."""
    return [a for a in GEN2_ARMS
            if any((a, s) in mtx for s in NEW_LOOSE)]


def snapshot(con):
    mtx = matrix(con)
    present = new_arms_present(mtx)
    return {
        "gen1": {r: pooled(mtx, GEN1_ARMS, orig_rung(i))
                 for i, r in enumerate(("scoped", "loose", "vague"))},
        "gen2": {r: pooled(mtx, GEN2_ARMS, orig_rung(i))
                 for i, r in enumerate(("scoped", "loose", "vague"))},
        "new": {r: pooled(mtx, present, s)
                for r, s in (("scoped", NEW_SCOPED), ("loose", NEW_LOOSE),
                             ("vague", NEW_VAGUE))},
        "new_arms_present": present,
        "new_arms_all": GEN2_ARMS,
        "n_runs": con.execute("SELECT COUNT(*) FROM run").fetchone()[0],
        "n_error_rows": con.execute(
            "SELECT COUNT(*) FROM run WHERE error IS NOT NULL").fetchone()[0],
    }


if __name__ == "__main__":
    import json
    con = connect()
    snap = snapshot(con)
    print(json.dumps(snap, indent=2))
