#!/usr/bin/env python3
"""
slope_chart_paired_distance.py

Standalone slope chart: each participant's final distance to target on
the summit task connected by a line to their distance on the valley
task. Red = closer on summit, blue = closer on valley.

Only participants with a valid distance on BOTH tasks are included
(n=28, same subset as the paired Yuen's test).

Usage:
    python3 slope_chart_paired_distance.py responses_cleaned_2026-07-13.json
"""

import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

COLOR_TOPP = "#C0392B"
COLOR_DAL = "#2563A8"

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 12,
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("json_path")
    parser.add_argument("--outdir", default=".")
    args = parser.parse_args()

    with open(args.json_path, encoding="utf-8") as f:
        data = json.load(f)

    pairs = load_paired_distances(data)
    n = len(pairs)
    closer_valley = sum(1 for p in pairs if p[2] < p[1])
    closer_summit = sum(1 for p in pairs if p[1] < p[2])

    fig, ax = plt.subplots(figsize=(7, 9))
    x_positions = [0, 1]

    for pid, summit_d, valley_d in pairs:
        color = COLOR_TOPP if summit_d > valley_d else COLOR_DAL
        ax.plot(x_positions, [summit_d, valley_d], color=color, alpha=0.55,
                 linewidth=1.6, marker="o", markersize=5, zorder=3)

    ax.set_xticks(x_positions)
    ax.set_xticklabels(["Summit", "Valley"], fontsize=13)
    ax.set_xlim(-0.35, 1.35)
    ax.set_yscale("log")
    ax.set_ylabel("Distance to target (m)")
    ax.set_title(f"Distance to target per participant: summit vs. valley (n={n})", pad=14)

    legend_elems = [
        Line2D([0], [0], color=COLOR_DAL, lw=2.5, label=f"Closer on valley ({closer_valley}/{n})"),
        Line2D([0], [0], color=COLOR_TOPP, lw=2.5, label=f"Closer on summit ({closer_summit}/{n})"),
    ]
    ax.legend(handles=legend_elems, fontsize=10, loc="upper center",
              bbox_to_anchor=(0.5, -0.06), ncol=2, frameon=False)

    fig.tight_layout()
    outpath = os.path.join(args.outdir, "slope_chart_paired_distance.png")
    fig.savefig(outpath, dpi=200, bbox_inches="tight")
    print(f"Saved: {outpath}")
    print(f"n={n}, closer on valley={closer_valley}, closer on summit={closer_summit}")


if __name__ == "__main__":
    main()
