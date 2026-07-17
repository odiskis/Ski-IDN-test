#!/usr/bin/env python3
"""
experience_yuen_test.py

Compares final distance-to-target between two map-reading-experience
groups, per task, using Yuen's independent-samples trimmed-means
bootstrap test (the paired version, ydbt, was used earlier for the
summit-vs-valley comparison; this is the independent-samples analogue,
since low- and high-experience participants are different people).

Group definition (low = 0, high = 1):
    low  = "aldri" (never) + "under5" (<5 times/year)
    high = "5til15" (5-15 times/year) + "over15" (15+ times/year)

Requires: hypothesize, pandas  (pip install hypothesize pandas --break-system-packages)

Usage:
    python3 experience_yuen_test.py responses_cleaned_2026-07-13.json
"""

import argparse
import json

import pandas as pd
from scipy.stats import trim_mean
from hypothesize.compare_groups_with_single_factor import yuenbt

LOW_CATEGORIES = {"aldri", "under5"}
HIGH_CATEGORIES = {"5til15", "over15"}


def load_group_distances(data, task_key):
    low, high = [], []
    for rec in data:
        t = rec.get("tasks", {}).get(task_key, {})
        status = t.get("status")
        distance = t.get("distance_m")
        exp = rec.get("map_experience")
        if status is None or not isinstance(distance, (int, float)):
            continue
        if exp in LOW_CATEGORIES:
            low.append(distance)
        elif exp in HIGH_CATEGORIES:
            high.append(distance)
    return low, high


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("json_path")
    parser.add_argument("--trim", type=float, default=0.2)
    parser.add_argument("--nboot", type=int, default=2000)
    args = parser.parse_args()

    with open(args.json_path, encoding="utf-8") as f:
        data = json.load(f)

    task_labels = {"topp": "Summit", "dal": "Valley"}
    results = []

    for task_key, label in task_labels.items():
        low, high = load_group_distances(data, task_key)
        low_s, high_s = pd.Series(low), pd.Series(high)

        result = yuenbt(low_s, high_s, tr=args.trim, nboot=args.nboot, seed=True)

        row = {
            "task": label,
            "n_low": len(low),
            "n_high": len(high),
            "trimmed_mean_low": trim_mean(low, args.trim),
            "trimmed_mean_high": trim_mean(high, args.trim),
            "diff": result["est_dif"],
            "ci_low": result["ci"][0],
            "ci_high": result["ci"][1],
            "p_value": result["p_value"],
        }
        results.append(row)

        print(f"--- {label} ---")
        print(f"  n (low)  = {len(low)}")
        print(f"  n (high) = {len(high)}")
        print(f"  Difference in {int(args.trim*100)}%-trimmed means (low - high): {result['est_dif']:.1f} m")
        print(f"  {int((1-0.05)*100)}% CI: [{result['ci'][0]:.1f}, {result['ci'][1]:.1f}] m")
        print(f"  p-value: {result['p_value']:.4f}\n")

    return results


if __name__ == "__main__":
    main()
