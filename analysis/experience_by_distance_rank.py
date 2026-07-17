#!/usr/bin/env python3
"""
experience_by_distance_rank.py

For each task (summit/valley), sorts participants by their actual final
distance to target (closest -> farthest) and plots their map-reading
experience level (map_experience, ordinal 0-3) as bars in that order.
A secondary line shows the actual distance value per position, so rank
compression stays visible alongside the experience pattern.

Experience coding (0 = no experience):
    aldri   (never)        -> 0
    under5  (<5 times/yr)  -> 1
    5til15  (5-15 times/yr)-> 2
    over15  (15+ times/yr) -> 3

This is a diagnostic/exploratory complement to a formal group comparison
(e.g. a low/high experience split tested with a paired-independent
bootstrap comparison) -- it lets you see the raw pattern across all four
levels before collapsing anything into two groups.

Usage:
    python3 experience_by_distance_rank.py responses_cleaned_2026-07-13.json
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

TASK_CONFIG = {
    "topp": {"label": "Summit", "color": COLOR_TOPP},
    "dal":  {"label": "Valley", "color": COLOR_DAL},
}

EXPERIENCE_CODE = {
    "aldri": 0,
    "under5": 1,
    "5til15": 2,
    "over15": 3,
}
EXPERIENCE_TICK_LABELS = ["0\n(Never)", "1\n(<5/yr)", "2\n(5-15/yr)", "3\n(15+/yr)"]

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.edgecolor": "#CBD5E1",
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def load_task_points(data, task_key):
    """Returns list of (pid, distance_m, experience_code) for participants
    with BOTH a valid distance for this task AND a recognised
    map_experience value."""
    points = []
    for rec in data:
        t = rec.get("tasks", {}).get(task_key, {})
        status = t.get("status")
        distance = t.get("distance_m")
        exp_raw = rec.get("map_experience")
        exp_code = EXPERIENCE_CODE.get(exp_raw)
        if status is None or not isinstance(distance, (int, float)) or exp_code is None:
            continue
        points.append((rec.get("pid", "?"), distance, exp_code))
    return points


def plot_task(ax, points, task_label, bar_color):
    points_sorted = sorted(points, key=lambda p: p[1])
    n = len(points_sorted)
    ranks = np.arange(1, n + 1)
    distances = [p[1] for p in points_sorted]
    experience = [p[2] for p in points_sorted]

    ax.bar(ranks, experience, color=bar_color, alpha=0.85, width=0.7,
           edgecolor="white", linewidth=0.5, label="Map experience (0-3)")
    ax.set_ylim(0, 3.5)
    ax.set_yticks([0, 1, 2, 3])
    ax.set_yticklabels(EXPERIENCE_TICK_LABELS, fontsize=8)
    ax.set_ylabel("Map-reading experience")
    ax.set_xlabel("Participant rank, sorted by final distance (1 = closest)")
    ax.set_title(f"{task_label}: map experience vs. distance-to-target rank (n={n})")

    ax2 = ax.twinx()
    ax2.plot(ranks, distances, color="#1E293B", marker="o", markersize=3,
              linewidth=1.2, alpha=0.8, label="Actual distance (m)")
    ax2.set_ylabel("Actual distance to target (m)")
    ax2.set_yscale("log")

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=8)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("json_path")
    parser.add_argument("--outdir", default=".")
    args = parser.parse_args()

    with open(args.json_path, encoding="utf-8") as f:
        data = json.load(f)

    fig, axes = plt.subplots(2, 1, figsize=(9, 9))
    for ax, (task_key, cfg) in zip(axes, TASK_CONFIG.items()):
        points = load_task_points(data, task_key)
        plot_task(ax, points, cfg["label"], cfg["color"])

    fig.tight_layout()
    outpath = os.path.join(args.outdir, "experience_by_distance_rank.png")
    fig.savefig(outpath, dpi=200)
    print(f"Saved: {outpath}")


if __name__ == "__main__":
    main()
