#!/usr/bin/env python3
"""Shared, live-computed numbers for the two Armor deliverable PDFs.

Both make_armor_benchmark_paper.py (PDF 2) and make_armor_intent_paper.py
(PDF 3) import from here so the coverage figures and the before/after projection
are identical and never hand-entered.

Two kinds of number live here, and they are labelled as such everywhere:
  MEASURED  - pooled drift from db/results.db via intent_data (real runs).
  PROJECTED - what Armor enforce mode would do, derived from the policy coverage
              structure. Never presented as measured.

Projection model (grounded in armor-intent/policies + the task structure):
  * Each domain has exactly one same-file rabbit hole (the old_<fn> alias, in the
    fix file) and three cross-file rabbit holes. A path-level Armor `forbid`
    blocks the three cross-file holes deterministically; it cannot isolate the
    same-file alias.
  * Hard floor (no assumption): per drifted cell at most one changed symbol can be
    the same-file alias, so at least (u - 1) of a cell's u out-of-scope symbols
    are cross-file and are prevented. Residual drifted cells <= drifted cells.
  * Expected (surface-proportional): drift lands on the 3:1 cross:same surface, so
    ~75% of drift symbols are prevented and ~25% of drifted cells retain a
    same-file residual.
  * Symbol-level gate: Armor's signed intent plan ("tool not in plan") is finer
    than shipped file.path conditions and can also block the same-file alias,
    lifting deterministic coverage toward 100%. Reported as the upper tier.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
POLICY_INDEX = os.path.join(ROOT, "armor-intent", "policies", "index.json")
sys.path.insert(0, HERE)
import intent_data as D  # noqa: E402

CROSS_RATIO = 0.75  # 3 of 4 rabbit holes per domain are cross-file


def coverage():
    """Static policy coverage read from the generated policy index."""
    idx = json.load(open(POLICY_INDEX))
    cross = sum(p["forbid_cross_file"] for p in idx["policies"])
    same = sum(p["same_file_residue"] for p in idx["policies"])
    holes = cross + same
    return {
        "domains": idx["count"],
        "holes": holes,
        "cross_file": cross,
        "same_file": same,
        "path_pct": round(100 * cross / holes) if holes else 0,
    }


def _cells(mtx, arms, slugs):
    return [mtx[(a, s)]["unreq"] for a in arms for s in slugs if (a, s) in mtx]


def cohort(mtx, arms, slugs, label):
    us = _cells(mtx, arms, slugs)
    drifted = [u for u in us if u > 0]
    symbols = sum(us)
    guaranteed_prevented = sum(max(0, u - 1) for u in us)
    return {
        "label": label,
        "cells": len(us),
        "drifted_cells": len(drifted),
        "symbols": symbols,
        "drift_rate": round(100 * len(drifted) / len(us)) if us else 0,
        # hard structural bounds
        "guaranteed_prevented": guaranteed_prevented,
        "residual_cells_max": len(drifted),
        # surface-proportional expectation
        "expected_prevented": round(CROSS_RATIO * symbols),
        "expected_residual_cells": round((1 - CROSS_RATIO) * len(drifted)),
    }


def snapshot():
    con = D.connect()
    mtx = D.matrix(con)
    present = D.new_arms_present(mtx)
    cohorts = {
        "gen1_loose": cohort(mtx, D.GEN1_ARMS, D.orig_rung(1), "Generation 1, loose"),
        "gen2_loose": cohort(mtx, D.GEN2_ARMS, D.orig_rung(1), "Generation 2, loose"),
        "new_loose": cohort(mtx, present, D.NEW_LOOSE, "New domains, loose (2 arms)"),
    }
    return {
        "coverage": coverage(),
        "cohorts": cohorts,
        "new_arms_present": present,
        "n_runs": con.execute("SELECT COUNT(*) FROM run").fetchone()[0],
    }


if __name__ == "__main__":
    import pprint
    pprint.pprint(snapshot())
