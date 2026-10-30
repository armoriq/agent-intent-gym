#!/usr/bin/env python3
"""Generate paper figures from the results DB. Every figure is regenerated from a
SQL query, so it always reflects the committed data. Output: paper/figures/*.png

Covers the prompt-realism ladder across all swept domains (percentile, pagination,
money, backoff, slug), 8 arms per task, latest run per (arm, task).

Usage: python harness/charts.py
"""
import os
import sqlite3
import sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DB = os.path.join(ROOT, "db", "results.db")
FIG = os.path.join(ROOT, "paper", "figures")
sys.path.insert(0, HERE)
from run import load_meta  # noqa: E402

ARM_LABEL = {
    "claude-code-opus-4-8": "Claude Opus 4.8",
    "cursor-codex-5.3": "Codex 5.3",
    "cursor-composer-2.5": "Composer 2.5",
    "cursor-glm-5.2": "GLM 5.2",
    "cursor-gpt-5.6-sol": "GPT-5.6 Sol",
    "cursor-grok-4.6": "Grok 4.6",
    "cursor-gemini-3.x": "Gemini flash",
    "cursor-kimi-k2.7-code": "Kimi K2.7",
}
ARM_ORDER = list(ARM_LABEL.keys())

VARIANTS = [("scoped", "#4c78a8"), ("loose", "#e45756"), ("realistic_vague", "#54a24b")]
VLABEL = {"scoped": "scoped", "loose": "loose", "realistic_vague": "vague"}
VSHORT = {"scoped": "sc", "loose": "lo", "realistic_vague": "vg"}
DOMAIN_ORDER = ["percentile", "pagination", "money", "backoff", "slug",
                "cache", "histogram"]
DOMAIN_SHORT = {"percentile": "perc", "pagination": "page", "money": "money",
                "backoff": "bkof", "slug": "slug", "cache": "cache",
                "histogram": "hist"}


def latest_rows(con):
    """[(arm, slug, metric, intent, unreq, turns)] latest run per (arm, task)."""
    return con.execute(
        """
        SELECT m.name, t.slug, r.metric_pass, r.intent_pass,
               r.unrequested_changes, run.turns
        FROM run
        JOIN model m ON m.id = run.model_id
        JOIN task t ON t.id = run.task_id
        JOIN result r ON r.run_id = run.id
        WHERE run.id = (
            SELECT MAX(r2.id) FROM run r2
            WHERE r2.model_id = run.model_id AND r2.task_id = run.task_id
        )
        """
    ).fetchall()


def ladder_index():
    """Map (domain, variant) -> slug, for every task carrying both meta fields."""
    idx = {}
    tasks_dir = os.path.join(ROOT, "tasks")
    for slug in os.listdir(tasks_dir):
        m = load_meta(slug) or {}
        g, v = m.get("variant_group"), m.get("prompt_variant")
        if g and v:
            idx[(g, v)] = slug
    return idx


def build_cells(con):
    """cells[slug][arm] = dict(metric,intent,unreq,turns)."""
    cells = defaultdict(dict)
    for arm, slug, mp, ip, u, tn in latest_rows(con):
        cells[slug][arm] = {"metric": mp, "intent": ip,
                            "unreq": u or 0, "turns": tn}
    return cells


def fig_drift_rate(con):
    """Headline: drift rate per prompt variant, pooled over all ladder tasks."""
    cells = build_cells(con)
    idx = ladder_index()
    tally = {v: [0, 0, 0] for v, _ in VARIANTS}  # variant -> [drift, intentfail, total]
    for (g, v), slug in idx.items():
        for arm, d in cells.get(slug, {}).items():
            tally[v][2] += 1
            if d["unreq"] > 0:
                tally[v][0] += 1
            if d["metric"] == 1 and d["intent"] == 0:
                tally[v][1] += 1
    labels, rates, cols, notes = [], [], [], []
    for v, color in VARIANTS:
        drift, ifail, total = tally[v]
        if not total:
            continue
        labels.append(VLABEL[v])
        rates.append(100 * drift / total)
        cols.append(color)
        notes.append("%d/%d" % (drift, total))
    fig, ax = plt.subplots(figsize=(6.8, 5))
    bars = ax.bar(labels, rates, color=cols, width=0.6)
    for b, note in zip(bars, notes):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.5, note,
                ha="center", va="bottom", fontsize=12, fontweight="bold")
    ax.set_ylabel("runs that touched out-of-scope code (%)")
    ax.set_ylim(0, 105)
    ax.set_title("Drift rate by prompt style\n"
                 "pooled over 7 domains x 8 agents (same repo/bug, only prompt varies)")
    fig.tight_layout()
    _save(fig, "fig3_drift_rate.png")


def fig_domain_generalization(con):
    """Per-domain drift rate, grouped bars scoped/loose/vague. The generalization view."""
    cells = build_cells(con)
    idx = ladder_index()
    domains = [d for d in DOMAIN_ORDER if any((d, v) in idx for v, _ in VARIANTS)]
    x = np.arange(len(domains))
    w = 0.26
    fig, ax = plt.subplots(figsize=(10, 5.4))
    for k, (v, color) in enumerate(VARIANTS):
        rates = []
        for d in domains:
            slug = idx.get((d, v))
            cc = cells.get(slug, {}) if slug else {}
            n = len(cc)
            drift = sum(1 for x2 in cc.values() if x2["unreq"] > 0)
            rates.append(100 * drift / n if n else 0)
        ax.bar(x + (k - 1) * w, rates, w, label=VLABEL[v], color=color)
    ax.set_xticks(x)
    ax.set_xticklabels([d for d in domains])
    ax.set_ylabel("agents that drifted (%)")
    ax.set_ylim(0, 105)
    ax.set_title("Loose prompts drive drift in every domain; scoped and vague never do")
    ax.legend(title="prompt")
    fig.tight_layout()
    _save(fig, "fig5_domain_generalization.png")


def fig_which_models_drift(con):
    """Per-arm: on how many of the 7 loose tasks did the arm touch out-of-scope code."""
    cells = build_cells(con)
    idx = ladder_index()
    loose_slugs = [idx[(d, "loose")] for d in DOMAIN_ORDER if (d, "loose") in idx]
    arms = [a for a in ARM_ORDER
            if any(a in cells.get(s, {}) for s in loose_slugs)]
    counts, totals, tot_unreq = [], [], []
    for a in arms:
        c = t = u = 0
        for s in loose_slugs:
            d = cells.get(s, {}).get(a)
            if d:
                t += 1
                if d["unreq"] > 0:
                    c += 1
                u += d["unreq"]
        counts.append(c)
        totals.append(t)
        tot_unreq.append(u)
    fig, ax = plt.subplots(figsize=(11, 5.2))
    bars = ax.bar([ARM_LABEL[a] for a in arms], counts, color="#e45756", width=0.6)
    for b, c, t, u in zip(bars, counts, totals, tot_unreq):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.05,
                "%d/%d\n(%d symbols)" % (c, t, u), ha="center", va="bottom",
                fontsize=9)
    ax.set_ylabel("loose-prompt domains with drift (of 7)")
    ax.set_ylim(0, 7.8)
    ax.set_xticklabels([ARM_LABEL[a] for a in arms], rotation=30, ha="right")
    ax.set_title("Which agents drift under a loose prompt\n"
                 "(count of the 7 domains where the agent edited out-of-scope code)")
    fig.tight_layout()
    _save(fig, "fig1_which_models_drift.png")


def fig_turns_by_variant(con):
    """Mean turns per arm by prompt variant: does vagueness inflate exploration?"""
    cells = build_cells(con)
    idx = ladder_index()
    by_arm_variant = defaultdict(lambda: defaultdict(list))
    for (g, v), slug in idx.items():
        for arm, d in cells.get(slug, {}).items():
            if d["turns"] is not None:
                by_arm_variant[arm][v].append(d["turns"])
    arms = [a for a in ARM_ORDER if a in by_arm_variant]
    x = np.arange(len(arms))
    w = 0.26
    fig, ax = plt.subplots(figsize=(11, 5.2))
    for k, (v, color) in enumerate(VARIANTS):
        means = []
        for a in arms:
            vals = by_arm_variant[a].get(v, [])
            means.append(sum(vals) / len(vals) if vals else 0)
        ax.bar(x + (k - 1) * w, means, w, label=VLABEL[v], color=color)
    ax.set_xticks(x)
    ax.set_xticklabels([ARM_LABEL[a] for a in arms], rotation=30, ha="right")
    ax.set_ylabel("mean turns (tool calls) to solve")
    ax.set_title("Effort per agent by prompt style (mean over 7 domains)\n"
                 "vague raises exploration above scoped, yet never drifts")
    ax.legend(title="prompt")
    fig.tight_layout()
    _save(fig, "fig2_turns_by_variant.png")


def fig_matrix(con):
    """Heatmap: 8 arms x 21 ladder tasks (7 domains x 3 variants) of unrequested
    changes. Blue box marks a run that broke guarded behavior (intent fail)."""
    cells = build_cells(con)
    idx = ladder_index()
    cols = []  # (slug, label)
    for d in DOMAIN_ORDER:
        for v, _ in VARIANTS:
            slug = idx.get((d, v))
            if slug:
                cols.append((slug, "%s\n%s" % (DOMAIN_SHORT[d], VSHORT[v])))
    arms = [a for a in ARM_ORDER if any(a in cells.get(s, {}) for s, _ in cols)]
    M = np.full((len(arms), len(cols)), np.nan)
    for i, a in enumerate(arms):
        for j, (slug, _) in enumerate(cols):
            d = cells.get(slug, {}).get(a)
            if d:
                M[i, j] = d["unreq"]
    fig, ax = plt.subplots(figsize=(16, 6))
    im = ax.imshow(M, cmap="Reds", vmin=0, vmax=4, aspect="auto")
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels([c for _, c in cols], fontsize=7)
    ax.set_yticks(range(len(arms)))
    ax.set_yticklabels([ARM_LABEL[a] for a in arms])
    for i, a in enumerate(arms):
        for j, (slug, _) in enumerate(cols):
            d = cells.get(slug, {}).get(a)
            if not d:
                continue
            v = d["unreq"]
            ax.text(j, i, str(int(v)), ha="center", va="center",
                    color="white" if v >= 2 else "black", fontsize=8)
            if d["metric"] == 1 and d["intent"] == 0:
                ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                                           edgecolor="#1f77b4", lw=3))
    # domain separators every 3 columns
    for j in range(3, len(cols), 3):
        ax.axvline(j - 0.5, color="#444", lw=1.2)
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("out-of-scope symbols touched (of 4)")
    ax.set_title("Drift by agent and task (7 domains x scoped/loose/vague)\n"
                 "loose columns light up; blue box = passed visible test but broke guarded behavior")
    fig.tight_layout()
    _save(fig, "fig4_model_problem_matrix.png")


def _save(fig, name):
    out = os.path.join(FIG, name)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print("wrote", out)


def main():
    os.makedirs(FIG, exist_ok=True)
    con = sqlite3.connect(DB)
    fig_which_models_drift(con)
    fig_turns_by_variant(con)
    fig_drift_rate(con)
    fig_matrix(con)
    fig_domain_generalization(con)
    con.close()


if __name__ == "__main__":
    main()
