#!/usr/bin/env python3
"""Render the benchmark suite as a lab-style capability card list (PNG).

Mirrors how frontier labs publish an eval suite: one row per capability area,
the area name in bold with a named, versioned benchmark under it. The rows map
the existing intent-drift suite (17 bug domains across the scoped/loose/vague
ladder, two model generations) onto that presentation. Names and versions are a
proposal; swap SUITE / rows freely.

Output: paper/benchmark-suite.png
Usage:  python3 harness/make_suite_card.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "paper", "benchmark-suite.png")

SUITE = "IntentBench"
INK = "#1a1a1a"
SUB = "#6b7280"
ACCENT = "#8ab4f8"
BORDER = "#d7d9de"

# (capability area, benchmark name + version, one-line scope)
ROWS = [
    ("Agentic coding", f"{SUITE}-SWE 1.0",
     "config merge, CLI flags, semver, querystring"),
    ("Algorithmic reasoning", f"{SUITE}-Algo 1.0",
     "median, grade boundary, bisect, moving average, duration, nth-largest"),
    ("Bug fixing", f"{SUITE}-Core 1.0 (Main)",
     "percentile, pagination, money, backoff, slug, cache, histogram"),
    ("Instruction following", f"{SUITE}-Ladder 1.0",
     "same repo and bug, scoped / loose / vague prompt"),
    ("Scope discipline", f"{SUITE}-Guard 1.0",
     "resistance to four planted out-of-scope rabbit holes"),
    ("Cross-generation drift", f"{SUITE}-GenTrack 1.0",
     "gen-1 vs gen-2 agents on the identical task set"),
]


def build():
    n = len(ROWS)
    row_h = 1.0
    gap = 0.16
    top_pad = 1.15
    fig_h = top_pad + n * (row_h + gap) + 0.3
    fig_w = 6.2
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=200)
    ax.set_xlim(0, fig_w)
    ax.set_ylim(0, fig_h)
    ax.axis("off")

    ax.text(0.30, fig_h - 0.5, SUITE, fontsize=20, fontweight="bold", color=INK,
            va="center")
    ax.text(0.32, fig_h - 0.92,
            "An intent-fidelity suite: does the agent do the one thing asked, "
            "and nothing else.", fontsize=8.3, color=SUB, va="center")

    y = fig_h - top_pad - row_h
    for area, name, scope in ROWS:
        card = FancyBboxPatch(
            (0.30, y), fig_w - 0.60, row_h,
            boxstyle="round,pad=0.0,rounding_size=0.06",
            linewidth=1.0, edgecolor=BORDER, facecolor="white")
        ax.add_patch(card)
        ax.add_patch(Rectangle((0.30, y), 0.09, row_h, linewidth=0,
                               facecolor=ACCENT))
        ax.text(0.56, y + row_h - 0.34, area, fontsize=11.5, fontweight="bold",
                color=INK, va="center")
        ax.text(0.56, y + row_h - 0.62, name, fontsize=9.5, color=SUB,
                va="center")
        ax.text(0.56, y + 0.20, scope, fontsize=7.2, color=SUB, va="center",
                style="italic")
        y -= (row_h + gap)

    fig.savefig(OUT, bbox_inches="tight", facecolor="white", pad_inches=0.18)
    plt.close(fig)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
