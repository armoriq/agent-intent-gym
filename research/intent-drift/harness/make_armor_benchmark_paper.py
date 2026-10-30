#!/usr/bin/env python3
"""Deliverable PDF 2: improving IntentBench with ArmorIQ evals.

How Armor's intent contracts raise the benchmark from a stochastic behavioural
estimate to a deterministic, scored eval, and exactly how much of the drift
surface that determinism covers. Every measured number is live from
db/results.db via armor_data; every projected number is labelled projected and
derived from the policy coverage structure.

Output: deliverables/2-improving-benchmark-with-armor.pdf
Usage:  python3 harness/make_armor_benchmark_paper.py
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
OUT = os.path.join(ROOT, "deliverables", "2-improving-benchmark-with-armor.pdf")
sys.path.insert(0, HERE)
import make_paper as mp  # noqa: E402
import armor_data as A  # noqa: E402

P = mp.P
H1, H2, BODY, SMALL = mp.H1, mp.H2, mp.BODY, mp.SMALL
TITLE, SUB, CENTER = mp.TITLE, mp.SUB, mp.CENTER


def tbl(data, widths, shade="#eef1f6"):
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(shade)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def C(s):
    return P(s, mp.SMALL)


def build():
    snap = A.snapshot()
    cov = snap["coverage"]
    co = snap["cohorts"]
    story = []

    story.append(Spacer(1, 3.0 * cm))
    story.append(P("Improving IntentBench with ArmorIQ Evals", TITLE))
    story.append(P("From a stochastic drift estimate to a deterministic, scored "
                   "intent eval: what Armor's policy layer adds to the benchmark, "
                   "and exactly how much of the drift surface it makes precise.",
                   SUB))
    story.append(Spacer(1, 0.8 * cm))
    story.append(P("Deliverable 2 of 3. Companion to the full intent-drift report "
                   "(deliverable 1) and the before/after projection (deliverable "
                   "3).", CENTER))
    story.append(Spacer(1, 0.5 * cm))
    story.append(P(
        "Measured figures are queried live from db/results.db (%d runs). Projected "
        "figures are labelled as such and are derived from the intent-contract "
        "policy coverage in armor-intent/policies, not from Armor runs, which the "
        "current quota does not allow." % snap["n_runs"], SMALL))
    story.append(PageBreak())

    # 1. the gap Armor fills
    story.append(P("1. The measurement gap this closes", H1))
    story.append(P(
        "The benchmark's core result is that on an identical repository and bug, "
        "prompt wording alone drives drift: scoped and vague prompts hold, loose "
        "prompts drift in a majority of cells. Measured pooled loose drift is %d of "
        "%d cells on generation 1 (%d%%), %d of %d on generation 2 (%d%%), and %d of "
        "%d on the new software domains (%d%%). That result is behavioural: each "
        "cell is a single sampled run, and whether an agent wanders into a rabbit "
        "hole is a probabilistic event. Turning a drift rate into a confident "
        "number needs repeated runs and error bars, which is the benchmark's "
        "standing future work."
        % (co["gen1_loose"]["drifted_cells"], co["gen1_loose"]["cells"],
           co["gen1_loose"]["drift_rate"], co["gen2_loose"]["drifted_cells"],
           co["gen2_loose"]["cells"], co["gen2_loose"]["drift_rate"],
           co["new_loose"]["drifted_cells"], co["new_loose"]["cells"],
           co["new_loose"]["drift_rate"])))
    story.append(P(
        "Armor changes what is being measured. Instead of sampling whether an agent "
        "chooses to stay in scope, it enforces the scope at the tool-call boundary "
        "and records the decision. Armor already detects this exact phenomenon and "
        "calls it intent drift: a runtime tool call that diverges from the signed "
        "plan is refused. What Armor lacks is a scored benchmark of it: its own "
        "evals surface is an empty stub. IntentBench supplies that eval; Armor "
        "supplies the determinism. The rest of this document quantifies the trade."))

    # 2. the mapping
    story.append(P("2. Every task is already an Armor policy", H1))
    story.append(P(
        "Each task states one permitted change (the fix) and four planted rabbit "
        "holes it must not touch. That is an intent contract, and it compiles "
        "directly into a real armor.policy.v1 PolicyProfile: default deny, "
        "deny_overrides, one permit statement on the fix file, and forbid "
        "statements on the rabbit-hole files. All %d domains were compiled this way "
        "(armor-intent/policies/), with no per-result tuning." % cov["domains"]))
    rows = [[C("<b>Benchmark concept</b>"), C("<b>Armor concept (real IR)</b>")],
            [C("the requested fix (in_scope)"), C("permit, action tool in Edit/Write, file.path = fix file")],
            [C("planted rabbit holes (out_of_scope)"), C("forbid on each cross-file rabbit-hole path")],
            [C("unrequested_changes &gt; 0 (our drift)"), C("Drift / \"intent drift: tool not in plan\"")],
            [C("a benchmark cell (arm x task)"), C("one enforced session, decision logged")]]
    story.append(tbl(rows, [7.5 * cm, 9.0 * cm]))

    # 3. coverage
    story.append(P("3. How much of the drift surface is deterministic", H1))
    story.append(P(
        "Armor's shipped policy conditions match on file.path. In every domain, "
        "three of the four rabbit holes live in a different file from the fix, so a "
        "path forbid blocks them deterministically. The fourth is the old_&lt;fn&gt; "
        "legacy alias, which sits in the same file as the fix and cannot be "
        "separated by a path condition. Across the suite that is a hard structural "
        "split, identical in all %d domains:" % cov["domains"]))
    cr = [[C("<b>Rabbit-hole surface</b>"), C("<b>Count</b>"), C("<b>Armor path policy</b>")],
          [C("Cross-file holes (different module from fix)"), C(str(cov["cross_file"])), C("blocked deterministically")],
          [C("Same-file hole (old_&lt;fn&gt; alias)"), C(str(cov["same_file"])), C("not separable by file.path")],
          [C("<b>Total planted holes</b>"), C("<b>%d</b>" % cov["holes"]), C("<b>%d%% path-covered</b>" % cov["path_pct"])]]
    story.append(tbl(cr, [9.0 * cm, 2.5 * cm, 5.0 * cm]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(P(
        "So a purely path-level policy makes %d%% of the drift surface a "
        "deterministic verdict rather than a sampled rate. The remaining %d%% (the "
        "same-file alias) needs Armor's finer gate: the signed intent plan that "
        "names the target symbol, or a matches condition on edit content, the same "
        "parameter inspection Armor already runs for PCI and payment detection. "
        "With that gate the covered fraction rises toward 100%%, still "
        "deterministic." % (cov["path_pct"], 100 - cov["path_pct"]), SMALL))

    # 4. precision gain, quantified
    story.append(PageBreak())
    story.append(P("4. The precision gain, per cohort", H1))
    story.append(P(
        "Precision here means: how much of the measured drift stops being a "
        "sampled quantity. The table gives, per measured cohort, the drift observed "
        "today and two enforce-mode bounds. The guaranteed floor assumes nothing: "
        "since each domain has exactly one same-file hole, at most one changed "
        "symbol per cell can survive a path policy, so at least (symbols minus "
        "drifted cells) are prevented. The expected column assumes drift lands on "
        "the 3-to-1 cross-to-same surface in proportion."))
    hr = [C("<b>Cohort</b>"), C("<b>Drifted cells</b>"), C("<b>Drift symbols</b>"),
          C("<b>Prevented (floor)</b>"), C("<b>Prevented (expected)</b>"),
          C("<b>Residual cells</b>")]
    rows = [hr]
    for k in ("gen1_loose", "gen2_loose", "new_loose"):
        c = co[k]
        rows.append([C(c["label"]), C(str(c["drifted_cells"])), C(str(c["symbols"])),
                     C("&ge; %d" % c["guaranteed_prevented"]),
                     C("~ %d" % c["expected_prevented"]),
                     C("&le; %d" % c["residual_cells_max"])])
    story.append(tbl(rows, [4.7 * cm, 2.3 * cm, 2.3 * cm, 2.5 * cm, 2.8 * cm, 2.2 * cm]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(P(
        "The floor is weak exactly where drift is single-symbol: on the new "
        "domains both runnable arms changed one rabbit hole per drifted cell, so "
        "the floor cannot rule out that each was the same-file alias, and the "
        "guaranteed prevention there is %d. This is not a defect of Armor but of a "
        "path-only policy, and it is the precise place the symbol-level intent gate "
        "earns its keep: naming the fix symbol in the plan makes even a same-file "
        "second edit a tool-not-in-plan denial." % co["new_loose"]["guaranteed_prevented"], SMALL))

    # 5. what to build
    story.append(P("5. What this adds to the benchmark, concretely", H1))
    story.append(P(
        "Three changes turn the drift study into an Armor-scored eval suite. First, "
        "run each cell twice, once unenforced (the current baseline) and once under "
        "the task's PolicyProfile in enforce mode; the delta is the measured "
        "prevention, which replaces the projection in this document. Second, "
        "persist the identity of each changed symbol, not just the count: the AST "
        "diff in the scorer already computes it, so this is a one-column schema "
        "add, and it collapses the floor-to-expected band above into a point "
        "number. Third, score monitor mode alongside enforce mode: monitor leaves "
        "behaviour unchanged but labels every drift event with the statement it "
        "violated, which measures attribution precision without touching the "
        "agent."))
    story.append(P(
        "The payoff is that the benchmark's headline stops depending on prompt "
        "phrasing. Today the same model reads as faithful or unfaithful depending "
        "on whether the prompt was scoped or loose. Under enforced policy the "
        "covered surface is faithful by construction, and the residual is a small, "
        "named, same-file set rather than an open-ended behavioural tail. That is "
        "the difference between reporting a drift rate and certifying a drift "
        "bound."))

    doc = BaseDocTemplate(OUT, pagesize=A4,
                          leftMargin=2 * cm, rightMargin=2 * cm,
                          topMargin=2 * cm, bottomMargin=1.8 * cm,
                          title="Improving IntentBench with ArmorIQ Evals")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=mp.footer)])
    doc.build(story)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
