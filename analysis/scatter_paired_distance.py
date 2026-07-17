#!/usr/bin/env python3
"""
scatter_paired_distance.py

Standalone paired scatter plot: each participant's summit distance (x)
vs. valley distance (y), with a y=x reference line. Points near the
diagonal indicate consistent performance across tasks; points far from
it indicate a large gap between summit and valley performance for that
person. Colored the same way as the slope chart (red = closer on
summit, blue = closer on valley) for visual continuity.

Only participants with a valid distance on BOTH tasks are included
(n=28, same subset as the paired Yuen's test and the slope chart).

Usage:
    python3 scatter_paired_distance.py responses_cleaned_2026-07-13.json
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
COLOR_REF = "#2D7D46"

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

    fig, ax = plt.subplots(figsize=(8, 8))

    for pid, summit_d, valley_d in pairs:
        color = COLOR_TOPP if summit_d > valley_d else COLOR_DAL
        ax.scatter(summit_d, valley_d, color=color, s=70, alpha=0.75,
                    edgecolor="white", linewidth=0.6, zorder=3)

    summit_vals = [p[1] for p in pairs]
    valley_vals = [p[2] for p in pairs]
    lo = min(min(summit_vals), min(valley_vals)) * 0.7
    hi = max(max(summit_vals), max(valley_vals)) * 1.15
    ax.plot([lo, hi], [lo, hi], color=COLOR_REF, linestyle="--", linewidth=1.4, zorder=1)
    ax.annotate("equal distance (y = x)", xy=(hi * 0.55, hi * 0.62), color=COLOR_REF,
                fontsize=9, rotation=38, rotation_mode="anchor")

    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Summit distance to target (m)")
    ax.set_ylabel("Valley distance to target (m)")
    ax.set_title(f"Summit vs. valley distance to target, per participant (n={n})", pad=14)

    closer_valley = sum(1 for p in pairs if p[2] < p[1])
    closer_summit = sum(1 for p in pairs if p[1] < p[2])
    legend_elems = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=COLOR_DAL, markersize=9,
               label=f"Below diagonal: closer on valley ({closer_valley}/{n})"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=COLOR_TOPP, markersize=9,
               label=f"Above diagonal: closer on summit ({closer_summit}/{n})"),
    ]
    ax.legend(handles=legend_elems, fontsize=9.5, loc="upper center",
              bbox_to_anchor=(0.5, -0.1), frameon=False)

    fig.tight_layout()
    outpath = os.path.join(args.outdir, "scatter_paired_distance.png")
    fig.savefig(outpath, dpi=200, bbox_inches="tight")
    print(f"Saved: {outpath}")


if __name__ == "__main__":
    main()
