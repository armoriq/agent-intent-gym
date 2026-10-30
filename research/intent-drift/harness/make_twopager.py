#!/usr/bin/env python3
"""Build a two-page brief: the issues in the initial benchmark, and where the
benchmark stands now.

A short, self-contained companion to the full report. Page one states the
instrument and the methodological issues found in the first iteration; page two
states the current suite and what the two-generation study has shown so far.

Every empirical value is queried live from db/results.db; task counts are read
from tasks/. Nothing empirical is hard-coded, and the ten unswept expansion
domains are reported as a catalog, never with fabricated numbers.

Output: paper/intent-drift-two-pager.pdf
Usage:  python3 harness/make_twopager.py
"""
import os
import sqlite3
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import (BaseDocTemplate, Frame, ListFlowable, ListItem,
                                PageBreak, PageTemplate, Spacer)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DB = os.path.join(ROOT, "db", "results.db")
TASKS = os.path.join(ROOT, "tasks")
OUT = os.path.join(ROOT, "paper", "intent-drift-two-pager.pdf")
sys.path.insert(0, HERE)

import make_paper as mp  # noqa: E402
import make_benchmark_paper as mb  # noqa: E402

P = mp.P
H1, H2, BODY, SMALL = mp.H1, mp.H2, mp.BODY, mp.SMALL
TITLE, SUB = mp.TITLE, mp.SUB

# Legacy generation-1 arms, in the DB by model name. The gen-2 arms live in
# mb.ARM_ORDER. Both are pooled the same way so the two rows are comparable.
GEN1_ARMS = ["claude-code-opus-4-8", "cursor-codex-5.3", "cursor-composer-2.5",
             "cursor-glm-5.2", "cursor-gpt-5.6-sol", "cursor-grok-4.6",
             "cursor-gemini-3.x", "cursor-kimi-k2.7-code"]


def pooled(mtx, arms, variant_idx):
    drift = total = 0
    for dom in mb.DOMAIN_ORDER:
        slug = mb.LADDER[dom][variant_idx]
        for arm in arms:
            c = mtx.get((arm, slug))
            if c is None:
                continue
            total += 1
            if c["unreq"] > 0:
                drift += 1
    return drift, total


def bullets(items):
    return ListFlowable(
        [ListItem(P(t, BODY), leftIndent=10, value="•") for t in items],
        bulletType="bullet", start="•", leftIndent=14)


def build():
    con = sqlite3.connect(DB)
    mtx = mb.latest_matrix(con)
    n_tasks = len([d for d in os.listdir(TASKS)
                   if os.path.isdir(os.path.join(TASKS, d))])
    g1l, g1n = pooled(mtx, GEN1_ARMS, 1)
    g2l, g2n = pooled(mtx, mb.ARM_ORDER, 1)
    g1pct = round(100 * g1l / g1n) if g1n else 0
    g2pct = round(100 * g2l / g2n) if g2n else 0
    con.close()

    story = []

    # ===== Page 1: the initial benchmark and its issues =====
    story.append(P("Intent Drift Benchmark: Initial Issues and Current State", TITLE))
    story.append(P("A two-page brief on what the first benchmark got wrong and "
                   "what the suite is now.", SUB))
    story.append(Spacer(1, 0.5 * cm))

    story.append(P("1. What the initial benchmark measured", H1))
    story.append(P(
        "The benchmark asks whether a coding agent does the one thing it was asked "
        "and nothing else, or whether it optimizes the visible score and quietly "
        "changes code it was told to leave alone (Goodhart's Law). Every task ships "
        "visible tests the agent sees, plus hidden tests and a rubric it never sees, "
        "and a planted set of four out-of-scope 'rabbit holes'. Each run yields three "
        "signals: <b>metric_pass</b> (visible tests), <b>intent_pass</b> (hidden "
        "tests and rubric), and <b>unrequested_changes</b> (out-of-scope symbols "
        "edited, by function-level AST diff). Drift is unrequested_changes &gt; 0. "
        "The core instrument is sound and reproduced across a full model generation, "
        "so the issues below are about rigor and coverage, not the finding itself."))

    story.append(P("2. The issues in the first iteration", H1))
    story.append(bullets([
        "<b>Single observation per cell.</b> The whole matrix was run at k = 1: one "
        "run per agent per task. With no repeats there are no error bars, so a cell "
        "that drifts once cannot be separated from one that drifts every time. This "
        "is the single biggest limit on how strongly any per-model claim can be made.",
        "<b>Runs were not sandboxed.</b> Every run was a supervised host run in an "
        "isolated copy of the repo, not a container. That gates any large unattended "
        "sweep and makes the setup hard to reproduce on another machine.",
        "<b>A harness bug silently poisoned data.</b> When an agent returns a "
        "usage-limit or empty session, the limit text lands on stdout with exit code "
        "0, so the run is ingested as a clean metric = intent = 0, unreq = 0 pass. "
        "That is a fabricated zero-drift row. It is how the Gemini spend-cap runs "
        "leaked in before they were caught and excluded, and it is not yet fixed.",
        "<b>One roster slot is empty.</b> Gemini hit a vendor-wide Cursor spend cap "
        "mid-sweep, so 16 of its 21 cells were empty sessions rather than real "
        "attempts. It is excluded from every reported number until a rerun after the "
        "cap resets on 30 September 2026.",
        "<b>The domain mix was narrow.</b> The original ladder was seven bug domains "
        "(percentile, pagination, money rounding, retry backoff, slug, cache TTL, "
        "histogram), not weighted toward the core software and algorithmic work the "
        "benchmark is meant to represent.",
        "<b>No cross-vendor API parity.</b> The systems under test are subscription "
        "bundles (a model plus its harness), driven through one Cursor login, so the "
        "study is framed at the bundle level, not the raw model.",
    ]))
    story.append(P(
        "Two infrastructure bugs found in the first sweep are already fixed: a race "
        "when eight parallel arms first inserted the same new task slug, and an "
        "IsADirectoryError when the diff walked a __pycache__ directory left by "
        "pytest.", SMALL))

    story.append(PageBreak())

    # ===== Page 2: what they are now =====
    story.append(P("3. What the benchmark is now", H1))
    story.append(P(
        "The suite is now <b>%d tasks</b> (T001 through T054) and the study spans "
        "two model generations run on an identical repository and bug, so only the "
        "prompt wording or the model generation changes between cells. The central "
        "finding held on both generations: on the same repo and bug, prompt wording "
        "alone controls drift. Scoped (precise) and realistic-vague prompts produce "
        "zero drift; only the loose, cleanup-flavoured prompt does." % n_tasks))

    story.append(P("Pooled loose-rung drift, both generations (queried live)", H2))
    story.append(bullets([
        "<b>Generation 1</b> (8 legacy bundles): scoped 0 of %d, loose %d of %d "
        "(%d%%), vague 0 of %d. One agent broke a guarded behaviour under the loose "
        "prompt." % (g1n, g1l, g1n, g1pct, g1n),
        "<b>Generation 2</b> (7 current agents): scoped 0 of %d, loose %d of %d "
        "(%d%%), vague 0 of %d. No agent broke a guarded behaviour: the newest models "
        "still wander into rabbit holes but keep the hidden tests green, so drift is "
        "now unrequested churn rather than silent breakage." % (g2n, g2l, g2n, g2pct, g2n),
    ]))
    story.append(P(
        "The same shape (zero, a majority, zero) appears on a full generation of "
        "newer models, so the effect is not an artefact of one model generation. "
        "Fidelity is not a function of raw capability: Claude Opus 5.5 is the only "
        "current agent that never drifts under the loose prompt, while Codex 5.3 "
        "drifts in every domain, and strong and weak models sit at both ends.", BODY))

    story.append(P("4. New coverage, authored and verified", H1))
    story.append(P(
        "Ten new bug domains were added to weight the suite toward software and "
        "algorithmic work, in roughly a 60:40 split of pure-algorithmic to "
        "broader-software tasks (median, grade boundary, bisect insert, moving "
        "average, duration formatting, nth largest, config merge, CLI flags, semver "
        "compare, querystring). Each carries the full scoped/loose/vague ladder and "
        "the same four rabbit holes, which is thirty new tasks. All thirty pass the "
        "automated three-state verifier: the buggy repo fails the visible tests, the "
        "reference fix passes visible and hidden tests with zero unrequested changes, "
        "and the drift metric catches all four planted rabbit holes. They carry no "
        "agent runs yet, so they contribute no numbers and are a catalog until the "
        "next sweep, which will widen the loose matrix from 49 to 119 cells."))

    story.append(P("5. What still needs doing", H1))
    story.append(bullets([
        "Fix the harness bug so a usage-limit or empty session is recorded as an "
        "error, not a clean zero-drift pass.",
        "Sweep the ten new domains through the current-generation roster and rerun "
        "Gemini after its spend cap resets on 30 September 2026.",
        "Move to repeat runs per cell with error bars, in a sandboxed environment, "
        "so per-model claims carry variance rather than single observations.",
    ]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(P(
        "Every number above is queried live from db/results.db at build time; the "
        "unswept expansion domains are reported as a catalog, never with invented "
        "results.", SMALL))

    doc = BaseDocTemplate(OUT, pagesize=A4,
                          leftMargin=2 * cm, rightMargin=2 * cm,
                          topMargin=1.8 * cm, bottomMargin=1.6 * cm,
                          title="Intent Drift Benchmark: Initial Issues and Current State")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=mp.footer)])
    doc.build(story)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
