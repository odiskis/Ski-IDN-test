#!/usr/bin/env python3
"""
confidence_by_distance_rank.py

For each task (summit/valley), sorts participants by their actual final
distance to target (closest -> farthest) and plots their self-reported
confidence rating (task_topp_sure / task_dal_sure, Likert 1-5) as bars in
that order. A secondary line shows the actual distance value per position,
so rank compression (many people sharing similar ranks despite different
real distances) stays visible alongside the confidence pattern.

This is a diagnostic/exploratory complement to the Spearman correlation
between confidence and distance -- it lets you see the raw pattern rather
than only a single summary statistic, which matters when one variable
(confidence) is a heavily-tied 5-point Likert scale.

Usage:
    python3 confidence_by_distance_rank.py responses_cleaned_2026-07-13.json
"""

import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

COLOR_TOPP = "#C0392B"
COLOR_DAL = "#2563A8"

TASK_CONFIG = {
    "topp": {"label": "Summit", "confidence_key": "task_topp_sure", "color": COLOR_TOPP},
    "dal":  {"label": "Valley", "confidence_key": "task_dal_sure", "color": COLOR_DAL},
}

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.edgecolor": "#CBD5E1",
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def load_task_points(data, task_key, confidence_key):
    """Returns list of (pid, distance_m, confidence) for participants with
    BOTH a valid distance and a valid confidence rating for this task."""
    points = []
    for rec in data:
        t = rec.get("tasks", {}).get(task_key, {})
        status = t.get("status")
        distance = t.get("distance_m")
        conf_raw = rec.get("survey", {}).get(confidence_key)
        if status is None or not isinstance(distance, (int, float)):
            continue
        try:
            conf = int(conf_raw)
        except (TypeError, ValueError):
            continue
        points.append((rec.get("pid", "?"), distance, conf))
    return points


def plot_task(ax, points, task_label, bar_color):
    # sort by distance ascending -> rank 1 = closest
    points_sorted = sorted(points, key=lambda p: p[1])
    n = len(points_sorted)
    ranks = np.arange(1, n + 1)
    distances = [p[1] for p in points_sorted]
    confidences = [p[2] for p in points_sorted]

    ax.bar(ranks, confidences, color=bar_color, alpha=0.85, width=0.7,
           edgecolor="white", linewidth=0.5, label="Confidence (Likert 1-5)")
    ax.set_ylim(0, 5.5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_ylabel("Confidence rating (1-5)")
    ax.set_xlabel("Participant rank, sorted by final distance (1 = closest)")
    ax.set_title(f"{task_label}: confidence rating vs. distance-to-target rank (n={n})")

    # secondary axis: actual distance value at each rank, so rank
    # compression doesn't hide how close/far apart real distances were
    ax2 = ax.twinx()
    ax2.plot(ranks, distances, color="#1E293B", marker="o", markersize=3,
              linewidth=1.2, alpha=0.8, label="Actual distance (m)")
    ax2.set_ylabel("Actual distance to target (m)")
    ax2.set_yscale("log")

    # combined legend
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
        points = load_task_points(data, task_key, cfg["confidence_key"])
        plot_task(ax, points, cfg["label"], cfg["color"])

    fig.tight_layout()
    outpath = os.path.join(args.outdir, "confidence_by_distance_rank.png")
    fig.savefig(outpath, dpi=200)
    print(f"Saved: {outpath}")


if __name__ == "__main__":
    main()
