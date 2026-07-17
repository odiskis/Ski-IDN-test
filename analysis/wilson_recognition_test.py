"""
wilson_recognition_test.py

Computes, for each task found in a Ski-IDN-test responses JSON file:
  - the chance-level probability of landing within a given radius of the
    target by pure random placement on the terrain,
  - an exact one-sided binomial test of the observed hit rate against
    that chance rate,
  - a Wilson score confidence interval for the true recognition rate.

Works on ANY version of the responses JSON that follows the structure
    [ { "pid": ..., "tasks": { "<task_key>": { "status": ...,
                                                 "distance_m": ... }, ... } }, ... ]
Task-level records with status/distance_m == null (i.e. excluded records)
are automatically skipped, so this can be pointed at either a raw export
or a cleaned/exclusion-applied file without any changes.

No third-party dependencies (standard library only) so it runs with a
plain `py` / `python3` install.

Usage:
    py wilson_recognition_test.py responses_cleaned_2026-07-13.json
    py wilson_recognition_test.py responses.json --radius 231
    py wilson_recognition_test.py responses.json --radius 517 --terrain-size 4097 --confidence 0.95
"""

import argparse
import json
import math


def chance_probability(radius_m: float, terrain_size_m: float) -> float:
    """Probability that a uniformly random point on a square terrain of
    side `terrain_size_m` falls within `radius_m` of a fixed target point.

    Computed as circle area / terrain area. This ignores edge-clipping
    for targets near the terrain boundary (a simplification worth noting
    in the methods text if a target sits close to an edge).
    """
    terrain_area = terrain_size_m ** 2
    circle_area = math.pi * radius_m ** 2
    return circle_area / terrain_area


def binomial_test_greater(x: int, n: int, p0: float) -> float:
    """Exact one-sided binomial test p-value for:
        H0: true hit rate == p0
        H1: true hit rate  > p0

    p = P(X >= x), where X ~ Binomial(n, p0).
    Computed as an exact sum of binomial probabilities (no normal
    approximation), using math.comb (Python 3.8+).
    """
    if n == 0:
        return float("nan")
    return sum(
        math.comb(n, k) * (p0 ** k) * ((1 - p0) ** (n - k))
        for k in range(x, n + 1)
    )


def wilson_score_interval(x: int, n: int, confidence: float = 0.95):
    """Wilson score confidence interval for a binomial proportion.

    Preferred over the Wald (textbook) interval, which under-covers at
    small n / extreme proportions, and over the Clopper-Pearson "exact"
    interval, which over-covers (is needlessly wide) in most cases.

    Source: Wilson, E.B. (1927). Probable Inference, the Law of
    Succession, and Statistical Inference. Journal of the American
    Statistical Association, 22(158), 209-212.
    Recommended as the practical default by: Brown, L.D., Cai, T.T., &
    DasGupta, A. (2001). Interval Estimation for a Binomial Proportion.
    Statistical Science, 16(2), 101-133.
    """
    if n == 0:
        return (float("nan"), float("nan"))

    z_table = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
    z = z_table.get(round(confidence, 2))
    if z is None:
        raise ValueError("confidence must be one of 0.90, 0.95, 0.99")

    phat = x / n
    denom = 1 + z**2 / n
    center = (phat + z**2 / (2 * n)) / denom
    margin = (z * math.sqrt(phat * (1 - phat) / n + z**2 / (4 * n**2))) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def load_valid_distances(json_path: str) -> dict:
    """Load a responses JSON (raw or cleaned) and return, for each task
    key found in the data, the list of valid (non-null) distance_m
    values. A task record counts as valid only if BOTH status and
    distance_m are non-null, which automatically skips excluded /
    nulled task-level records without needing a separate exclusion file.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    task_distances = {}
    for rec in data:
        tasks = rec.get("tasks", {})
        for task_key, task in tasks.items():
            if not task:
                continue
            status = task.get("status")
            distance = task.get("distance_m")
            if status is not None and distance is not None:
                task_distances.setdefault(task_key, []).append(distance)
    return task_distances


def main():
    parser = argparse.ArgumentParser(
        description="Exact binomial test + Wilson score CI for recognition "
                    "rate vs. chance, computed from a responses JSON file."
    )
    parser.add_argument("json_path", help="Path to a responses JSON file (raw or cleaned).")
    parser.add_argument("--radius", type=float, default=517.0,
                         help="Recognition threshold radius in metres (default: 517).")
    parser.add_argument("--terrain-size", type=float, default=4097.0,
                         help="Terrain side length in metres, square terrain assumed "
                              "(default: 4097).")
    parser.add_argument("--confidence", type=float, default=0.95,
                         help="Confidence level for the Wilson interval: "
                              "0.90, 0.95, or 0.99 (default: 0.95).")
    args = parser.parse_args()

    p0 = chance_probability(args.radius, args.terrain_size)
    task_distances = load_valid_distances(args.json_path)

    print(f"Chance probability of landing within {args.radius:.0f}m "
          f"on a {args.terrain_size:.0f}x{args.terrain_size:.0f}m terrain: "
          f"{p0*100:.2f}%\n")

    if not task_distances:
        print("No valid task records found in this file.")
        return

    for task_key, distances in task_distances.items():
        n = len(distances)
        hits = sum(1 for d in distances if d < args.radius)
        phat = hits / n if n else float("nan")

        p_value = binomial_test_greater(hits, n, p0)
        ci_low, ci_high = wilson_score_interval(hits, n, args.confidence)

        print(f"--- Task: {task_key} ---")
        print(f"  n = {n}, hits = {hits} ({phat*100:.1f}%)")
        print(f"  One-sided exact binomial p (H1: rate > chance): {p_value:.3e}")
        print(f"  Wilson {int(args.confidence*100)}% CI: "
              f"[{ci_low*100:.1f}%, {ci_high*100:.1f}%]")
        exceeds = "yes" if ci_low > p0 else "no"
        print(f"  Lower CI bound exceeds chance rate: {exceeds}\n")


if __name__ == "__main__":
    main()