#!/usr/bin/env python3
"""
paired_task_comparison.py

Two complementary views of the same paired data: each participant's
final distance-to-target on the summit task vs. the valley task.

  (A) Paired scatter: summit distance (x) vs valley distance (y), one
      point per participant, with a y=x reference line. Points below
      the line = closer on valley; above = closer on summit.
  (B) Slope chart: two columns (Summit, Valley), one line per
      participant connecting their two distances.

Only participants with a VALID distance on BOTH tasks are included
(paired data only -- same n=28 subset used for the Yuen paired test).

Usage:
    python3 paired_task_comparison.py responses_cleaned_2026-07-13.json
"""

import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

COLOR_TOPP = "#C0392B"
COLOR_DAL = "#2563A8"
COLOR_LINE = "#94A3B8"
COLOR_REF = "#2D7D46"

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.edgecolor": "#CBD5E1",
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def load_paired_distances(data):
    pairs = []
    for rec in data:
        t = rec.get("tasks", {}).get("topp", {})
        d = rec.get("tasks", {}).get("dal", {})
        if (t.get("status") is not None and isinstance(t.get("distance_m"), (int, float))
                and d.get("status") is not None and isinstance(d.get("distance_m"), (int, float))):
            pairs.append((rec.get("pid", "?"), t["distance_m"], d["distance_m"]))
    return pairs


def plot_scatter(ax, pairs):
    summit = [p[1] for p in pairs]
    valley = [p[2] for p in pairs]
    ax.scatter(summit, valley, color="#334155", s=40, alpha=0.75, zorder=3)

    lims = [min(min(summit), min(valley)) * 0.7, max(max(summit), max(valley)) * 1.15]
    ax.plot(lims, lims, color=COLOR_REF, linestyle="--", linewidth=1.3, zorder=1, label="Equal distance (y=x)")
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Summit distance to target (m)")
    ax.set_ylabel("Valley distance to target (m)")
    ax.set_title(f"(A) Paired scatter: summit vs. valley distance (n={len(pairs)})")
    ax.legend(fontsize=8, loc="upper left")
    ax.set_aspect("equal", adjustable="box")


def plot_slope(ax, pairs):
    x_positions = [0, 1]
    for pid, summit_d, valley_d in pairs:
        color = COLOR_TOPP if summit_d > valley_d else COLOR_DAL
        ax.plot(x_positions, [summit_d, valley_d], color=color, alpha=0.5, linewidth=1.3, marker="o", markersize=4)

    ax.set_xticks(x_positions)
    ax.set_xticklabels(["Summit", "Valley"])
    ax.set_xlim(-0.3, 1.3)
    ax.set_yscale("log")
    ax.set_ylabel("Distance to target (m)")
    ax.set_title(f"(B) Slope chart: each participant, summit -> valley (n={len(pairs)})")

    from matplotlib.lines import Line2D
    legend_elems = [
        Line2D([0], [0], color=COLOR_DAL, lw=2, label="Closer on valley"),
        Line2D([0], [0], color=COLOR_TOPP, lw=2, label="Closer on summit"),
    ]
    ax.legend(handles=legend_elems, fontsize=8, loc="upper right")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("json_path")
    parser.add_argument("--outdir", default=".")
    args = parser.parse_args()

    with open(args.json_path, encoding="utf-8") as f:
        data = json.load(f)

    pairs = load_paired_distances(data)

    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    plot_scatter(axes[0], pairs)
    plot_slope(axes[1], pairs)

    fig.tight_layout()
    outpath = os.path.join(args.outdir, "paired_task_comparison.png")
    fig.savefig(outpath, dpi=200)
    print(f"Saved: {outpath}")
    print(f"n paired participants: {len(pairs)}")


if __name__ == "__main__":
    main()
