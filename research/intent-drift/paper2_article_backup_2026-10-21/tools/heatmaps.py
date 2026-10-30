#!/usr/bin/env python3
"""Heatmap figures from analysis/out/run_evidence.csv (escaped runs excluded)."""
import csv
import os
import sys
from pathlib import Path

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = os.path.dirname(HERE)
ROOT = os.path.dirname(PAPER)
OUT = Path(PAPER, "analysis", "out")
sys.path.insert(0, os.path.join(PAPER, "analysis"))

from plots import _finish, _style  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

RUNGS = ("scoped", "loose", "realistic_vague")
RUNG_LABELS = ("Scoped", "Loose", "Vague")
GENS = ("gen-1", "gen-2")
INCOMPLETE = {"Gemini 3.8 Flash"}
CMAP = LinearSegmentedColormap.from_list("ink", ["#ffffff", "#c9d3dc", "#6f8597", "#22313d"])
MISSING = "#eeeeee"

runs = [r for r in csv.DictReader(open(os.path.join(OUT, "run_evidence.csv"))) if r["escaped"] == "False"]
reg = yaml.safe_load(open(os.path.join(ROOT, "suites", "registry.yaml")))
suite_order = {"core": 0, "algo": 1, "swe": 2}
DOMAINS = [d for b in sorted(reg["domain_benchmarks"], key=lambda b: suite_order[b["id"]])
           for d in sorted(b["members"])]


def arms_of(gen):
    labels = sorted({r["label"] for r in runs if r["generation"] == gen})
    planted = {a: np.mean([int(r["unrequested_changes"]) for r in runs
                           if r["label"] == a and r["generation"] == gen and r["rung"] == "loose"] or [0])
               for a in labels}
    return sorted(labels, key=lambda a: (a in INCOMPLETE, planted[a], a))


def ink(value, vmax):
    return "white" if value / vmax > 0.55 else "black"


def draw(ax, grid, vmax, fmt):
    shown = np.ma.masked_invalid(grid)
    ax.imshow(shown, cmap=CMAP, vmin=0, vmax=vmax, aspect="auto")
    for (i, j), v in np.ndenumerate(grid):
        if np.isnan(v):
            ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, color=MISSING, lw=0))
            ax.text(j, i, "--", ha="center", va="center", fontsize=6.5, color="0.55")
        else:
            ax.text(j, i, fmt(v), ha="center", va="center", fontsize=6.5, color=ink(v, vmax))
    ax.set_xticks(np.arange(grid.shape[1] + 1) - .5, minor=True)
    ax.set_yticks(np.arange(grid.shape[0] + 1) - .5, minor=True)
    ax.grid(which="minor", color="white", linewidth=0.8)
    ax.tick_params(which="both", length=0)
    for s in ax.spines.values():
        s.set_visible(False)


def arm_label(arm, gen):
    return arm + ("$^\\dagger$" if arm in INCOMPLETE else "")


def fig_tasks():
    """Arm x domain on the loose rung: mean planted functions edited (0 to 4)."""
    fig = plt.figure(figsize=(6.9, 5.4))
    cell = 0.78 / len(DOMAINS)
    for k, gen in enumerate(GENS):
        arms = arms_of(gen)
        doms = [d for d in DOMAINS if any(r["domain"] == d and r["generation"] == gen for r in runs)]
        grid = np.full((len(arms), len(doms)), np.nan)
        for i, a in enumerate(arms):
            for j, d in enumerate(doms):
                vals = [int(r["unrequested_changes"]) for r in runs if r["generation"] == gen and r["label"] == a
                        and r["domain"] == d and r["rung"] == "loose"]
                if vals:
                    grid[i, j] = np.mean(vals)
        bottom = 0.60 if k == 0 else 0.12
        ax = fig.add_axes([0.17, bottom, cell * len(doms), 0.32])
        draw(ax, grid, 4, lambda v: f"{v:g}" if v == int(v) else f"{v:.1f}")
        ax.set_yticks(range(len(arms)), [arm_label(a, gen) for a in arms])
        ax.set_xticks(range(len(doms)), doms, rotation=45, ha="right", rotation_mode="anchor")
        ax.set_title(f"Generation {k + 1}, loose prompt", fontsize=8.5, loc="left")
    cax = fig.add_axes([0.17 + cell * 7 + 0.10, 0.64, 0.015, 0.24])
    bar = fig.colorbar(plt.cm.ScalarMappable(cmap=CMAP, norm=plt.Normalize(0, 4)), cax=cax, ticks=range(5))
    bar.set_label("Planted functions edited (of 4)")
    bar.outline.set_linewidth(0.4)
    _finish(fig, OUT, "fig_heat_tasks")


def rate(rows, key):
    return 100 * np.mean([int(r[key]) for r in rows]) if rows else np.nan


def fig_rungs():
    """Arm x rung: share of runs that opened planted files, edited them, or made any out-of-scope edit."""
    metrics = (("exposed_non_target_any", "Opened a planted file"),
               ("planted_drifted", "Edited a planted function"),
               ("any_out_of_scope", "Any out-of-scope edit"))
    rows = [(gen, a) for gen in GENS for a in arms_of(gen)]
    fig, axes = plt.subplots(1, 3, figsize=(6.9, 4.6), sharey=True)
    for ax, (key, title) in zip(axes, metrics):
        grid = np.array([[rate([r for r in runs if r["generation"] == g and r["label"] == a and r["rung"] == rung], key)
                          for rung in RUNGS] for g, a in rows])
        draw(ax, grid, 100, lambda v: f"{v:.0f}")
        ax.axhline(len(arms_of("gen-1")) - .5, color="black", linewidth=0.8)
        ax.set_xticks(range(3), RUNG_LABELS)
        ax.xaxis.tick_top()
        ax.set_title(title, fontsize=8.5, pad=16)
    axes[0].set_yticks(range(len(rows)), [f"G{g[-1]}  {arm_label(a, g)}" for g, a in rows])
    cax = fig.add_axes([0.3, 0.07, 0.5, 0.018])
    bar = fig.colorbar(plt.cm.ScalarMappable(cmap=CMAP, norm=plt.Normalize(0, 100)), cax=cax,
                       orientation="horizontal", ticks=range(0, 101, 25))
    bar.set_label("Runs (%)")
    bar.outline.set_linewidth(0.4)
    fig.subplots_adjust(left=0.24, right=0.99, top=0.88, bottom=0.16, wspace=0.08)
    _finish(fig, OUT, "fig_heat_rungs")


def fig_domains():
    """Domain x rung, pooled over arms and generations: planted edits and test-file edits."""
    metrics = (("planted_drifted", "Edited a planted function"), ("test_edited", "Edited a test file"))
    fig, axes = plt.subplots(1, 2, figsize=(5.2, 4.4), sharey=True)
    for ax, (key, title) in zip(axes, metrics):
        grid = np.array([[rate([r for r in runs if r["domain"] == d and r["rung"] == rung], key)
                          for rung in RUNGS] for d in DOMAINS])
        draw(ax, grid, 100, lambda v: f"{v:.0f}")
        for edge in (7, 13):
            ax.axhline(edge - .5, color="black", linewidth=0.8)
        ax.set_xticks(range(3), RUNG_LABELS)
        ax.xaxis.tick_top()
        ax.set_title(title, fontsize=8.5, pad=16)
    axes[0].set_yticks(range(len(DOMAINS)), DOMAINS)
    cax = fig.add_axes([0.3, 0.09, 0.55, 0.02])
    bar = fig.colorbar(plt.cm.ScalarMappable(cmap=CMAP, norm=plt.Normalize(0, 100)), cax=cax,
                       orientation="horizontal", ticks=range(0, 101, 25))
    bar.set_label("Runs (%)")
    bar.outline.set_linewidth(0.4)
    fig.subplots_adjust(left=0.17, right=0.98, top=0.88, bottom=0.19, wspace=0.08)
    _finish(fig, OUT, "fig_heat_domains")


_style()
fig_tasks()
fig_rungs()
fig_domains()
print("wrote fig_heat_tasks, fig_heat_rungs, fig_heat_domains")
