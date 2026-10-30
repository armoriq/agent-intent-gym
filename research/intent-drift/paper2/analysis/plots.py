"""Publication figures rendered from the analysis tables, without database access."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
import numpy as np


GENERATIONS = ("gen-1", "gen-2")
RUNGS = ("scoped", "loose", "realistic_vague")
RUNG_LABELS = {"scoped": "Scoped", "loose": "Loose", "realistic_vague": "Vague"}
COLORS = {"gen-1": "#465b6b", "gen-2": "#997252"}
MARKERS = {"gen-1": "o", "gen-2": "s"}
GEN_LABELS = {"gen-1": "Generation 1", "gen-2": "Generation 2"}


def _style():
    available = {f.name for f in font_manager.fontManager.ttflist}
    family = next((f for f in ("Times New Roman", "Nimbus Roman", "STIXGeneral") if f in available), "DejaVu Serif")
    plt.rcParams.update({
        "font.family": "serif", "font.serif": [family], "font.size": 8.5,
        "axes.labelsize": 8.5, "xtick.labelsize": 8, "ytick.labelsize": 8,
        "legend.fontsize": 8, "axes.linewidth": 0.5,
        "xtick.major.width": 0.5, "ytick.major.width": 0.5,
        "xtick.major.size": 3, "ytick.major.size": 3,
        "lines.linewidth": 0.8, "lines.markersize": 4,
        "pdf.fonttype": 42, "ps.fonttype": 42, "mathtext.fontset": "stix",
        "savefig.facecolor": "white", "figure.facecolor": "white",
    })


def _finish(fig, out, stem):
    fig.savefig(out / f"{stem}.pdf", metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(out / f"{stem}.png", dpi=180)
    plt.close(fig)


def _axis(ax, percent="y"):
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_axisbelow(True)
    if percent == "y":
        ax.set_ylim(-3, 103)
        ax.set_yticks(np.arange(0, 101, 25))
        ax.yaxis.grid(True, color="0.9", linewidth=0.35)
    else:
        ax.set_xlim(-3, 103)
        ax.set_xticks(np.arange(0, 101, 25))
        ax.xaxis.grid(True, color="0.9", linewidth=0.35)


def _value(row, key):
    value = row.get(key)
    return float(value) if value is not None and np.isfinite(value) else None


def _errors(row, key, scale=1.0):
    center = _value(row, key)
    low = _value(row, key + "_ci_low")
    high = _value(row, key + "_ci_high")
    if center is None or low is None or high is None:
        return None
    return np.array([[max(0, center - low)], [max(0, high - center)]]) * scale


def _empty(ax):
    ax.text(0.5, 0.5, "No valid observations", transform=ax.transAxes, ha="center", va="center", color="0.4")


def _ladder(rows, out):
    fig, ax = plt.subplots(figsize=(3.3, 2.6))
    any_data = False
    for gen in GENERATIONS:
        selected = {r["rung"]: r for r in rows if r["generation"] == gen}
        xs, ys = [], []
        for pos, rung in enumerate(RUNGS):
            row = selected.get(rung)
            if row is None or _value(row, "drift_rate") is None:
                continue
            x = pos + (-0.045 if gen == GENERATIONS[0] else 0.045)
            y = row["drift_rate"] * 100
            ax.errorbar(x, y, yerr=_errors(row, "drift_rate", 100), color=COLORS[gen], marker=MARKERS[gen], capsize=2, elinewidth=0.7)
            xs.append(x)
            ys.append(y)
            any_data = True
        if xs:
            ax.plot(xs, ys, color=COLORS[gen], label=GEN_LABELS[gen], linestyle="-" if gen == GENERATIONS[0] else "--", marker=MARKERS[gen])
    _axis(ax)
    ax.set_ylabel("Planted-function drift (%)")
    ax.set_xticks(range(len(RUNGS)), [RUNG_LABELS[r] for r in RUNGS])
    ax.set_xlim(-0.25, len(RUNGS) - 0.75)
    if any_data:
        ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.18), ncol=2, handlelength=1.5, columnspacing=0.9)
    else:
        _empty(ax)
    fig.subplots_adjust(left=0.16, right=0.98, bottom=0.15, top=0.83)
    _finish(fig, out, "fig_ladder")


def _arms(rows, out):
    selected = {gen: sorted((r for r in rows if r["generation"] == gen and r["rung"] == "loose" and _value(r, "drift_rate") is not None), key=lambda r: (r["drift_rate"], r.get("label", r["arm"]))) for gen in GENERATIONS}
    count = max((len(v) for v in selected.values()), default=0)
    height = max(3.0, 1.0 + count * 0.30)
    fig, axes = plt.subplots(1, 2, figsize=(6.9, height))
    for ax, gen in zip(axes, GENERATIONS):
        subset = selected[gen]
        for y, row in enumerate(subset):
            flagged = row["n"] < 5 or (row.get("escape_rate") or 0) > 0.5
            color = "0.6" if flagged else COLORS[gen]
            for metric, offset, marker, filled in (("drift_rate", -0.12, "o", True), ("intent_pass_rate", 0.12, "s", False)):
                val = _value(row, metric)
                if val is None:
                    continue
                ax.errorbar(val * 100, y + offset, xerr=_errors(row, metric, 100), fmt=marker, color=color, markerfacecolor=color if filled and not flagged else "white", markersize=4, capsize=1.8, elinewidth=0.6)
        labels = [f'{r.get("label", r["arm"])} (n={r["n"]})' + ("$^\\dagger$" if r["arm"] == "g2-gemini-3.8" else "") for r in subset]
        ax.set_yticks(range(len(subset)), labels, fontsize=8)
        for tick, row in zip(ax.get_yticklabels(), subset):
            if row["n"] < 5 or (row.get("escape_rate") or 0) > 0.5:
                tick.set_color("0.6")
        ax.set_ylim(-0.6, max(len(subset) - 0.4, 0.6))
        ax.invert_yaxis()
        ax.set_xlabel("Runs (%)")
        _axis(ax, percent="x")
        ax.text(0.5, 1.045, GEN_LABELS[gen], transform=ax.transAxes, ha="center")
        if not subset:
            _empty(ax)
    handles = [Line2D([], [], marker="o", color="0.35", linestyle="none", label="Planted drift"), Line2D([], [], marker="s", markerfacecolor="white", color="0.35", linestyle="none", label="Hidden-test pass")]
    fig.legend(handles=handles, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.0))
    fig.subplots_adjust(left=0.28, right=0.985, bottom=0.14, top=0.84, wspace=1.65)
    _finish(fig, out, "fig_arms")


def _exposure(rows, out):
    primary = [r for r in rows if r.get("population") == "NoEsc"]
    panels = [(gen, "Cursor") for gen in GENERATIONS]
    panels.extend((gen, "Claude Code") for gen in GENERATIONS if any(r.get("harness_group") == "Claude Code" and r["generation"] == gen for r in primary))
    fig, axes = plt.subplots(1, len(panels), figsize=(6.9, 2.95), squeeze=False)
    markers = {"scoped": "o", "loose": "s", "realistic_vague": "^"}
    for ax, (gen, harness) in zip(axes.flat, panels):
        selected = {r["rung"]: r for r in primary if r["generation"] == gen and r.get("harness_group") == harness}
        valid = [(rung, selected[rung]) for rung in RUNGS if rung in selected and _value(selected[rung], "mean_tool_calls") is not None and _value(selected[rung], "drift_rate") is not None]
        for rung, row in valid:
            x, y = row["mean_tool_calls"], row["drift_rate"] * 100
            ax.errorbar(x, y, xerr=_errors(row, "mean_tool_calls"), yerr=_errors(row, "drift_rate", 100), fmt=markers[rung], color=COLORS[gen], capsize=2, elinewidth=0.65)
        _axis(ax)
        ax.set_xlabel("Mean unique tool calls")
        panel_label = "Opus 4.8, Claude Code" if harness == "Claude Code" else f"{GEN_LABELS[gen]}, {harness}"
        ax.text(0.5, 1.045, panel_label, transform=ax.transAxes, ha="center", fontsize=8.5)
        if valid:
            ax.margins(x=0.30)
            ax.set_xlim(left=max(0, ax.get_xlim()[0]))
            ordered = sorted(valid, key=lambda item: item[1]["mean_tool_calls"])
            xmin, xmax = ax.get_xlim()
            for rank, (rung, row) in enumerate(ordered):
                x, y = row["mean_tool_calls"], row["drift_rate"] * 100
                nearby = [other for other_rung, other in ordered if other_rung != rung and abs(other["mean_tool_calls"] - x) < (xmax - xmin) * 0.18 and abs(other["drift_rate"] * 100 - y) < 12]
                label_x = max([x] + [other["mean_tool_calls"] for other in nearby])
                dy = (9 + 12 * rank) if nearby else 9
                if y > 70:
                    dy = -dy
                ax.annotate(RUNG_LABELS[rung], (label_x, y), xytext=(6, dy), textcoords="offset points", ha="left", va="bottom" if dy > 0 else "top", fontsize=8)
        else:
            _empty(ax)
    axes.flat[0].set_ylabel("Planted-function drift (%)")
    fig.subplots_adjust(left=0.075, right=0.985, bottom=0.17, top=0.87, wspace=0.32)
    _finish(fig, out, "fig_exposure")


def _domains(rows, out):
    domains = sorted({r["domain"] for r in rows})
    fig, ax = plt.subplots(figsize=(6.9, max(3.0, 0.7 + len(domains) * 0.24)))
    lookup = {(r["generation"], r["domain"]): r for r in rows}
    for gen, offset in zip(GENERATIONS, (-0.13, 0.13)):
        any_gen = False
        for y, domain in enumerate(domains):
            row = lookup.get((gen, domain))
            if row is None or _value(row, "drift_rate") is None:
                continue
            ax.errorbar(row["drift_rate"] * 100, y + offset, xerr=_errors(row, "drift_rate", 100), fmt=MARKERS[gen], color=COLORS[gen], capsize=1.8, elinewidth=0.65)
            any_gen = True
        if any_gen:
            ax.plot([], [], color=COLORS[gen], marker=MARKERS[gen], linestyle="none", label=GEN_LABELS[gen])
    ax.set_yticks(range(len(domains)), [str(d).replace("_", " ") for d in domains])
    ax.set_ylim(-0.6, max(len(domains) - 0.4, 0.6))
    ax.invert_yaxis()
    _axis(ax, percent="x")
    ax.set_xlabel("Loose planted-function drift (%)")
    if ax.get_legend_handles_labels()[0]:
        ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.12), ncol=2)
    else:
        _empty(ax)
    fig.subplots_adjust(left=0.28, right=0.98, bottom=0.13, top=0.88)
    _finish(fig, out, "fig_domains")


def make_figures(tables: dict[str, list[dict]], out: Path) -> None:
    """Write vector PDFs and PNG inspection copies from summary table rows."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    _style()
    _ladder(tables.get("ladder_generation", []), out)
    _arms(tables.get("ladder_arm", []), out)
    _exposure(tables.get("ladder_harness", []), out)
    _domains(tables.get("domain_loose", []), out)
