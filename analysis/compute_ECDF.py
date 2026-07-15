import json
import os

import matplotlib.pyplot as plt
from scipy.stats import ecdf

DATA_FILE = os.path.join(
    os.path.dirname(__file__), "..", "skitest", "data", "responses_cleaned_2026-07-13.json"
)

COLOR_TOPP = "#C0392B"
COLOR_DAL = "#2563A8"
COLOR_COMBINED = "#000000"
COLOR_REFERENCE = "#2D7D46"

REFERENCE_DISTANCES = [73, 231, 517]
REFERENCE_LABELS = ["0.1%", "1%", "5%"]


def distance_values(data, task):
    out = []
    for d in data:
        t = d.get("tasks", {}).get(task, {})
        if t.get("status") is not None and isinstance(t.get("distance_m"), (int, float)):
           out.append(t["distance_m"])
    return out


def main():
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    topp_vals = distance_values(data, "topp")
    dal_vals = distance_values(data, "dal")
    combined_vals = topp_vals + dal_vals

    fig, ax = plt.subplots(figsize=(8, 5))

    def plot_ecdf_pct(vals, **kwargs):
        line, = ecdf(vals).cdf.plot(ax, **kwargs)
        line.set_ydata(line.get_ydata() * 100)

    if topp_vals:
        plot_ecdf_pct(topp_vals, color=COLOR_TOPP, label="Summit")
    if dal_vals:
        plot_ecdf_pct(dal_vals, color=COLOR_DAL, label="Valley")
    if combined_vals:
        plot_ecdf_pct(combined_vals, color=COLOR_COMBINED, linestyle="--", label="Combined")

    all_vals = combined_vals
    xlim_lo = max(1, min(all_vals) * 0.5) if all_vals else 1
    xlim_hi = max(all_vals) * 1.1 if all_vals else 1000
    ax.set_xscale("log")
    ax.set_xlim(xlim_lo, xlim_hi)
    ax.set_ylim(0, 100)

    for dist, pct_label in zip(REFERENCE_DISTANCES, REFERENCE_LABELS):
        ax.axvline(dist, color=COLOR_REFERENCE, linestyle=":", linewidth=1.5)
        ax.annotate(f"{dist}m\n({pct_label})", xy=(dist, 0), xycoords=("data", "axes fraction"),
                    xytext=(0, -32), textcoords="offset points",
                    color=COLOR_REFERENCE, fontsize=8, ha="center", va="top", clip_on=False)

    fig.subplots_adjust(bottom=0.24)

    ax.set_title("Empirical Cumulative Distribution Function of Final Distance")
    ax.set_xlabel("Distance to goal (meters)")
    ax.set_ylabel("%")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend()

    outpath = os.path.join(os.path.dirname(__file__), "ecdf_distance.png")
    fig.savefig(outpath, dpi=200)
    print(f"Saved: {outpath}")

    plt.show()


if __name__ == "__main__":
    main()
