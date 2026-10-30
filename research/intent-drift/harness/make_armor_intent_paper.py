#!/usr/bin/env python3
"""Deliverable PDF 3: intent evals before and after ArmorIQ.

Projects what the measured drift baseline becomes once each task's intent
contract is enforced as an Armor policy. The before numbers are measured live;
the after numbers are PROJECTED from the policy coverage structure and are
labelled as projections throughout, because the current Cursor quota does not
allow live Armor runs.

Output: deliverables/3-intent-evals-before-after-armor.pdf
Usage:  python3 harness/make_armor_intent_paper.py
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
OUT = os.path.join(ROOT, "deliverables", "3-intent-evals-before-after-armor.pdf")
sys.path.insert(0, HERE)
import make_paper as mp  # noqa: E402
import armor_data as A  # noqa: E402

P = mp.P
H1, H2, BODY, SMALL = mp.H1, mp.H2, mp.BODY, mp.SMALL
TITLE, SUB, CENTER = mp.TITLE, mp.SUB, mp.CENTER


def C(s):
    return P(s, mp.SMALL)


def tbl(data, widths, shade="#eef1f6", spans=None):
    t = Table(data, colWidths=widths, repeatRows=1)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(shade)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for s in spans or []:
        style.append(("SPAN",) + s)
    t.setStyle(TableStyle(style))
    return t


def pct(n, d):
    return round(100 * n / d) if d else 0


def build():
    snap = A.snapshot()
    cov = snap["coverage"]
    co = snap["cohorts"]
    story = []

    story.append(Spacer(1, 3.0 * cm))
    story.append(P("Intent Evals Before and After ArmorIQ", TITLE))
    story.append(P("The measured drift baseline, and the projected drift once each "
                   "task's intent contract is enforced as an Armor policy that "
                   "prevents an agent from touching anything it was not asked to.",
                   SUB))
    story.append(Spacer(1, 0.8 * cm))
    story.append(P("Deliverable 3 of 3.", CENTER))
    story.append(Spacer(1, 0.5 * cm))
    story.append(P(
        "The before columns are measured live from db/results.db (%d runs). The "
        "after columns are PROJECTIONS, derived from the policy coverage in "
        "armor-intent/policies, not from Armor runs. The current Cursor quota caps "
        "five of seven arms until 30 September 2026, so the enforced re-run that "
        "would replace these projections with measurements is deferred, not "
        "assumed. No projected number is presented as measured." % snap["n_runs"],
        SMALL))
    story.append(PageBreak())

    # 1. what enforcement changes
    story.append(P("1. What Armor enforces, and why the rungs should flatten", H1))
    story.append(P(
        "The benchmark finding is a prompt-rung effect: with a scoped prompt agents "
        "hold, with a loose prompt they drift, with a vague prompt they hold again. "
        "That variance lives entirely on the agent side, in how prompt phrasing "
        "invites scope expansion. Armor removes the agent's ability to act on that "
        "invitation. Its PreToolUse gate refuses any edit to a forbidden file "
        "before it lands, regardless of how the prompt was worded, so the drift a "
        "loose prompt would have produced never reaches the repository. The scoped "
        "and vague rungs are already at zero drift and stay there; the loose rung is "
        "where enforcement does its work, and the projection is that it collapses "
        "toward the same floor."))

    # 2. before/after per cohort (loose rung)
    story.append(P("2. Loose-rung drift, measured before vs projected after", H1))
    story.append(P(
        "Each cohort is the loose rung, where all drift lives. Before is the "
        "measured drift rate. After (expected) applies the 3-to-1 cross-to-same "
        "coverage; after (worst case) is the structural ceiling in which every "
        "drifted cell happened to hit the one same-file alias a path policy cannot "
        "block. The true measured value will fall between them and is pinned by "
        "persisting per-symbol identity."))
    hr = [C("<b>Cohort (loose)</b>"), C("<b>Before: drift</b>"),
          C("<b>After: expected</b>"), C("<b>After: worst case</b>")]
    rows = [hr]
    for k in ("gen1_loose", "gen2_loose", "new_loose"):
        c = co[k]
        exp_cells = c["expected_residual_cells"]
        rows.append([
            C(c["label"]),
            C("%d / %d (%d%%)" % (c["drifted_cells"], c["cells"], c["drift_rate"])),
            C("~ %d / %d (%d%%)" % (exp_cells, c["cells"], pct(exp_cells, c["cells"]))),
            C("&le; %d / %d (%d%%)" % (c["residual_cells_max"], c["cells"],
                                       pct(c["residual_cells_max"], c["cells"]))),
        ])
    story.append(tbl(rows, [4.7 * cm, 4.0 * cm, 4.0 * cm, 4.0 * cm]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(P(
        "Scoped and vague rungs, both cohorts: 0 before, 0 after (nothing to "
        "prevent). The expected after-rate is a projection, not a measurement.",
        SMALL))

    # 3. the two enforcement tiers
    story.append(P("3. Two enforcement tiers, and where each lands", H1))
    story.append(P(
        "Path-level policy (shipped Armor conditions) blocks the %d cross-file "
        "rabbit holes of %d deterministically, %d%% of the surface. Its residual is "
        "the same-file old_&lt;fn&gt; alias, at most one per cell. Symbol-level "
        "enforcement adds Armor's signed intent plan: an edit to the fix file that "
        "targets the alias rather than the declared symbol is a tool-not-in-plan "
        "denial, which closes the residual and drives covered drift to zero. Armor "
        "has both mechanisms; the path tier is a configuration, the symbol tier "
        "uses the plan granularity Armor already supports."
        % (cov["cross_file"], cov["holes"], cov["path_pct"])))
    tr = [[C("<b>Tier</b>"), C("<b>Mechanism</b>"), C("<b>Covered surface</b>"), C("<b>Determinism</b>")],
          [C("Path policy"), C("file.path forbid on rabbit-hole files"),
           C("%d of %d holes (%d%%)" % (cov["cross_file"], cov["holes"], cov["path_pct"])),
           C("deterministic on covered surface")],
          [C("+ Symbol plan"), C("signed intent plan, tool-not-in-plan"),
           C("adds the same-file alias residue"), C("deterministic toward 100%")]]
    story.append(tbl(tr, [3.0 * cm, 5.5 * cm, 4.5 * cm, 3.7 * cm]))

    # 4. task success under enforcement
    story.append(PageBreak())
    story.append(P("4. Does the fix still get made under enforcement", H1))
    story.append(P(
        "Preventing drift is only useful if the requested fix still lands. The "
        "policy permits edits to the fix file, so the in-scope change is never "
        "blocked; enforcement only denies the out-of-scope edits. In enforce mode "
        "the projected outcome on a covered cell is the target state the benchmark "
        "defines as fidelity: visible and hidden tests pass and unrequested_changes "
        "is zero. The honest risk is an agent that, denied a rabbit-hole edit, "
        "fails to complete the real fix or loops retrying the blocked call. That is "
        "a behavioural question a projection cannot answer; it is the first thing "
        "the enforced re-run measures, per arm, as a task-success rate under "
        "policy."))

    # 5. precision achievable now
    story.append(P("5. Data precision achievable now, without live Armor runs", H1))
    story.append(P(
        "Two things are already exact today. The policy coverage is exact: %d of "
        "%d holes are cross-file across all %d domains, a static fact of the "
        "fixtures, not a sample. And the structural floor is exact: at least "
        "(drift symbols minus drifted cells) edits are provably cross-file and "
        "would be denied. What is not yet exact is the split of measured drift "
        "between cross-file and same-file, because the scorer stored only the count "
        "of changed symbols, not their identity. Recovering that identity is the "
        "one missing measurement, and the AST diff already computes it at scoring "
        "time, so a single stored column turns every projected band in this "
        "document into a measured number, before any Armor run and before the quota "
        "resets." % (cov["cross_file"], cov["holes"], cov["domains"])))
    story.append(P(
        "Until then the claims stated as measured are: the before drift rates, the "
        "%d%% path coverage, and the per-cohort guaranteed floor. Everything about "
        "the after state is a projection carrying an explicit band, and the "
        "enforced re-run after the 30 September 2026 quota reset is what converts "
        "it." % cov["path_pct"], SMALL))

    doc = BaseDocTemplate(OUT, pagesize=A4,
                          leftMargin=2 * cm, rightMargin=2 * cm,
                          topMargin=2 * cm, bottomMargin=1.8 * cm,
                          title="Intent Evals Before and After ArmorIQ")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=mp.footer)])
    doc.build(story)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
