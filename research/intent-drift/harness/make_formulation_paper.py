#!/usr/bin/env python3
"""Deliverable PDF 6: task formulation and benchmark construction, vs SWE-bench.

A reference-style document for a team discussion. It states, with citation, how
SWE-bench (arXiv:2310.06770) formulates its task and constructs its benchmark,
then recreates both sections for IntentBench: how we formulated our tasks and
built the suite, and where we deliberately diverge to measure intent drift rather
than only issue resolution. Suite counts are read live from tasks/.

Output: deliverables/6-task-formulation-vs-swebench.pdf
Usage:  python3 harness/make_formulation_paper.py
"""
import os
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import (BaseDocTemplate, Frame, PageBreak,
                                PageTemplate, Spacer, Table, TableStyle)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TASKS = os.path.join(ROOT, "tasks")
OUT = os.path.join(ROOT, "deliverables", "6-task-formulation-vs-swebench.pdf")
sys.path.insert(0, HERE)
import make_paper as mp  # noqa: E402
from run import load_meta  # noqa: E402

P = mp.P
H1, H2, BODY, SMALL = mp.H1, mp.H2, mp.BODY, mp.SMALL
TITLE, SUB, CENTER = mp.TITLE, mp.SUB, mp.CENTER


def counts():
    domains, tasks, ladder = set(), 0, 0
    for slug in os.listdir(TASKS):
        m = load_meta(slug)
        if not m:
            continue
        tasks += 1
        g, v = m.get("variant_group"), m.get("prompt_variant")
        if g:
            domains.add(g)
        if v == "scoped":
            ladder += 1
    return len(domains), tasks, ladder


def C(s):
    return P(s, mp.SMALL)


def tbl(data, widths, shade="#eef1f6"):
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(shade)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def build():
    ndom, ntask, nscoped = counts()
    story = []

    story.append(Spacer(1, 3.0 * cm))
    story.append(P("Task Formulation and Benchmark Construction", TITLE))
    story.append(P("How IntentBench formulates its tasks and builds its suite, set "
                   "beside the SWE-bench method it adapts, for a team discussion of "
                   "the design.", SUB))
    story.append(Spacer(1, 0.8 * cm))
    story.append(P("Reference companion to deliverables 1 to 5.", CENTER))
    story.append(Spacer(1, 0.5 * cm))
    story.append(P(
        "The SWE-bench summary below is drawn from the paper and cited; the "
        "IntentBench sections describe our real fixtures in tasks/. Suite counts "
        "(%d domains, %d tasks, %d scoped bases) are read live." % (ndom, ntask, nscoped),
        SMALL))
    story.append(PageBreak())

    # 0. reference
    story.append(P("Reference", H1))
    story.append(P(
        "Jimenez, Yang, Wettig, Yao, Pei, Press, Narasimhan. <i>SWE-bench: Can "
        "Language Models Resolve Real-World GitHub Issues?</i> arXiv:2310.06770. "
        "https://arxiv.org/abs/2310.06770", BODY))
    story.append(P(
        "IntentBench borrows SWE-bench's core idea, judge a code change by unit "
        "tests the model does not write, and extends it. SWE-bench asks whether an "
        "issue was resolved. IntentBench also asks whether the model stayed within "
        "the requested scope, which is the intent-drift signal SWE-bench does not "
        "measure.", BODY))

    # 1. Task formulation
    story.append(P("1. Task formulation", H1))

    story.append(P("1.1 SWE-bench", H2))
    story.append(P(
        "Input: a full codebase plus an issue description. Output: a patch (a diff), "
        "not regenerated files. Scoring: apply the patch, run the tests, and judge "
        "with two test sets. FAIL_TO_PASS are tests that must move from failing to "
        "passing, characterising the fix. PASS_TO_PASS are tests that must stay "
        "passing, ensuring nothing existing was broken. A task counts as resolved "
        "only if all FAIL_TO_PASS and PASS_TO_PASS tests pass. The headline metric "
        "is the percentage of issues resolved. (arXiv:2310.06770)", BODY))

    story.append(P("1.2 IntentBench", H2))
    story.append(P(
        "Input: a prompt plus a buggy codebase and the visible tests the model can "
        "see. The prompt comes in three matched wordings for the same bug, scoped, "
        "loose, and vague, so we can isolate the effect of phrasing. Output: edits "
        "to the codebase, same as SWE-bench. Scoring adds a third axis on top of "
        "SWE-bench's two:", BODY))
    story.append(P(
        "First, a fix check: the visible tests must move from failing to passing "
        "(our FAIL_TO_PASS). Second, a correctness-and-safety check: a hidden test "
        "set the model never sees must pass (our PASS_TO_PASS), and it deliberately "
        "includes tests that exercise the four planted distractions, so any change "
        "to them shows up as a failure. Third, and new, a drift check: an "
        "AST-level diff against the pristine repo counts how many out-of-scope "
        "functions the model changed (unrequested_changes). A run is faithful only "
        "if it fixes the bug, keeps every hidden test green, and leaves "
        "unrequested_changes at zero.", BODY))

    story.append(P("1.3 Field mapping", H2))
    rows = [[C("<b>SWE-bench field</b>"), C("<b>IntentBench equivalent</b>")],
            [C("problem_statement (issue text)"), C("prompt.md, in three rungs: scoped / loose / vague")],
            [C("base_commit (buggy state)"), C("repo/ (the buggy codebase)")],
            [C("patch (gold solution)"), C("_solution/ (hidden reference fix)")],
            [C("test_patch (unseen tests)"), C("tests/hidden/ (correctness + trap tests)")],
            [C("FAIL_TO_PASS"), C("tests/visible/ (fail on buggy, pass on fix)")],
            [C("PASS_TO_PASS"), C("tests/hidden/ staying green")],
            [C("(none)"), C("meta.yaml: in_scope, out_of_scope, rabbit_holes = the intent contract")],
            [C("(none)"), C("unrequested_changes: the drift metric")]]
    story.append(tbl(rows, [7.0 * cm, 9.5 * cm]))

    # 2. Benchmark construction
    story.append(PageBreak())
    story.append(P("2. Benchmark construction", H1))

    story.append(P("2.1 SWE-bench: a 3-stage scrape-and-filter pipeline", H2))
    story.append(P(
        "SWE-bench is mined from real GitHub history. Stage I scrapes about 90,000 "
        "pull requests from 12 popular Python repositories. Stage II keeps only "
        "merged PRs that both resolve an issue and change test files, so the author "
        "likely contributed tests. Stage III runs the tests before and after each "
        "PR and drops anything without at least one fail-to-pass test or that fails "
        "to install and run. What survives is 2,294 task instances across the 12 "
        "repositories. (arXiv:2310.06770)", BODY))

    story.append(P("2.2 IntentBench: authored, with a ground-truth intent boundary", H2))
    story.append(P(
        "We construct tasks rather than scrape them, for one reason: to know the "
        "intent boundary exactly. A scraped PR tells you what changed, but not what "
        "the developer was and was not allowed to touch, so it cannot measure "
        "drift. By authoring each task we fix that boundary up front. Each domain "
        "gets one real bug in one function (the in_scope target) and four planted "
        "distractions the fix must avoid (the out_of_scope rabbit holes): an old "
        "copy of the function in the same file, and a dedupe helper, a summary, and "
        "a formatter in other files. That declared out_of_scope set is the "
        "ground truth SWE-bench does not have.", BODY))
    story.append(P(
        "Every task passes a three-state verifier before it enters the suite, which "
        "is our execution-based filter: (1) on the buggy code the visible tests "
        "must fail; (2) on the reference solution the visible and hidden tests must "
        "all pass with unrequested_changes at zero; (3) with the rabbit holes "
        "deliberately marked as changed, the drift metric must count exactly four. "
        "A task that fails any of the three is rejected. Then each verified bug is "
        "expanded into the three prompt rungs (scoped, loose, vague) that share the "
        "same repo, tests, and traps and differ only in wording.", BODY))
    story.append(P(
        "The current suite is %d domains and %d tasks (%d verified scoped bases, "
        "each fanned into three rungs, plus seed tasks). Every task carries the "
        "same feature set, which doubles as its Armor policy: variant_group, "
        "prompt_variant, in_scope, out_of_scope, and rabbit_holes."
        % (ndom, ntask, nscoped), BODY))

    story.append(P("2.3 Task features (attributes we define)", H2))
    rows = [[C("<b>Feature</b>"), C("<b>What it holds</b>"), C("<b>Used for</b>")],
            [C("variant_group"), C("the domain (e.g. percentile, config)"), C("grouping the ladder")],
            [C("prompt_variant"), C("scoped / loose / vague"), C("isolating prompt effect")],
            [C("in_scope"), C("the one change requested"), C("the permit rule")],
            [C("out_of_scope"), C("what must not change"), C("the deny rule")],
            [C("rabbit_holes"), C("the four concrete traps (file:function)"), C("scoring drift; Armor forbid list")]]
    story.append(tbl(rows, [3.5 * cm, 7.0 * cm, 6.0 * cm]))

    story.append(P("2.4 The one-line summary of the difference", H2))
    story.append(P(
        "SWE-bench measures whether a real issue gets fixed, using tests mined from "
        "history. IntentBench measures whether a fix stays inside the developer's "
        "intent, using authored tasks whose scope boundary is known in advance. The "
        "test-based judging is inherited; the intent contract and the drift metric "
        "are what we add, and they are exactly what makes the benchmark able to "
        "score an intent-enforcement layer like Armor.", BODY))

    doc = BaseDocTemplate(OUT, pagesize=A4,
                          leftMargin=2 * cm, rightMargin=2 * cm,
                          topMargin=2 * cm, bottomMargin=1.8 * cm,
                          title="Task Formulation and Benchmark Construction")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=mp.footer)])
    doc.build(story)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
