#!/usr/bin/env python3
"""
recognition_forest_plot.py

Forest-plot style chart showing, for each of the three chance-derived
distance thresholds (73m/0.1%, 231m/1%, 517m/5%), the observed
recognition rate per task with its Wilson 95% CI, plotted against the
corresponding chance-baseline rate.

Uses the pre-computed results from wilson_recognition_test.py (hardcoded
here as the source data, since this chart summarises three already-run
tests rather than recomputing them). If you re-run the underlying
analysis, update RESULTS below to match.

Usage:
    python3 recognition_forest_plot.py
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

COLOR_TOPP = "#C0392B"
COLOR_DAL = "#2563A8"
COLOR_CHANCE = "#2D7D46"

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.edgecolor": "#CBD5E1",
    "axes.spines.top": False,
    "axes.spines.right": False,
})

# threshold_m, chance_pct, task_label, n, hits, obs_pct, ci_low, ci_high, p_value
RESULTS = [
    (73,  0.10, "Summit", 30, 2,  6.7,  1.8,  21.3, 4.248e-04),
    (73,  0.10, "Valley", 31, 2,  6.5,  1.8,  20.7, 4.537e-04),
    (231, 1.00, "Summit", 30, 4,  13.3, 5.3,  29.7, 2.215e-04),
    (231, 1.00, "Valley", 31, 7,  22.6, 11.4, 39.8, 2.112e-08),
    (517, 5.00, "Summit", 30, 8,  26.7, 14.2, 44.4, 8.496e-05),
    (517, 5.00, "Valley", 31, 13, 41.9, 26.4, 59.2, 1.079e-09),
]

TASK_COLOR = {"Summit": COLOR_TOPP, "Valley": COLOR_DAL}


def main():
    fig, ax = plt.subplots(figsize=(8, 6))

    # y positions: group by threshold, two rows per group with a gap between groups
    y_labels = []
    y_pos = []
    y = 0
    thresholds_seen = []
    for r in RESULTS:
        threshold_m = r[0]
        if threshold_m not in thresholds_seen:
            if thresholds_seen:
                y -= 0.6  # extra gap between threshold groups
            thresholds_seen.append(threshold_m)
        y_labels.append(f"{r[2]} ({threshold_m}m)")
        y_pos.append(y)
        y -= 1

    y_pos = np.array(y_pos)

    for i, r in enumerate(RESULTS):
        threshold_m, chance_pct, task, n, hits, obs, ci_lo, ci_hi, p = r
        color = TASK_COLOR[task]
        ax.plot([ci_lo, ci_hi], [y_pos[i], y_pos[i]], color=color, linewidth=2, solid_capstyle="round")
        ax.plot(obs, y_pos[i], "o", color=color, markersize=8, zorder=3)
        ax.annotate(f"{obs:.1f}%  (n={hits}/{n})", xy=(ci_hi, y_pos[i]),
                    xytext=(8, 0), textcoords="offset points",
                    va="center", fontsize=8.5, color="#333333")

    # chance-baseline markers per threshold group (vertical dashed segment
    # spanning just that group's two rows)
    for threshold_m, chance_pct in [(73, 0.10), (231, 1.00), (517, 5.00)]:
        rows = [i for i, r in enumerate(RESULTS) if r[0] == threshold_m]
        y_top = y_pos[rows[0]] + 0.4
        y_bot = y_pos[rows[-1]] - 0.4
        ax.plot([chance_pct, chance_pct], [y_bot, y_top], color=COLOR_CHANCE,
                 linestyle=":", linewidth=1.8, zorder=2)
        ax.annotate(f"chance = {chance_pct:.2f}%", xy=(chance_pct, y_top + 0.15),
                    ha="center", fontsize=8, color=COLOR_CHANCE)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(y_labels)
    ax.set_xlabel("Recognition rate (%), 95% Wilson CI")
    ax.set_xscale("log")
    ax.set_xlim(0.05, 100)
    ax.set_title("Recognition rate vs. chance baseline, by threshold and task")
    ax.grid(True, axis="x", linestyle="--", alpha=0.4)
    ax.invert_yaxis()

    fig.tight_layout()
    outpath = os.path.join(os.path.dirname(__file__) or ".", "recognition_forest_plot.png")
    fig.savefig(outpath, dpi=200)
    print(f"Saved: {outpath}")


if __name__ == "__main__":
    main()
