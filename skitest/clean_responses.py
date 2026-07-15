"""
clean_responses.py

Applies task_exclusions.json to a raw responses.json backup and writes a
cleaned copy for analysis. Original files are never modified.

Usage:
    py clean_responses.py raw_responses.json task_exclusions.json cleaned_responses.json
"""

import json
import sys

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def apply_exclusions(raw_data, exclusions):
    participant_excl = {e["pid"] for e in exclusions.get("participant_exclusions", [])}
    task_excl = {(e["pid"], e["task"]): e for e in exclusions.get("task_exclusions", [])}

    cleaned = []
    log = []

    for rec in raw_data:
        pid = rec.get("pid")

        if pid in participant_excl:
            log.append(f"REMOVED participant {pid} (fully excluded)")
            continue

        rec = json.loads(json.dumps(rec))  # deep copy, leave raw_data untouched

        for task_key, task in rec.get("tasks", {}).items():
            key = (pid, task_key)
            if key in task_excl:
                for field in ["time_seconds", "status", "distance_m",
                              "unity_position", "map_position"]:
                    if field in task:
                        task[field] = None
                log.append(f"NULLED {pid}/{task_key}: {task_excl[key]['reason']}")

        cleaned.append(rec)

    return cleaned, log

def main():
    if len(sys.argv) != 4:
        print("Usage: py clean_responses.py <raw_responses.json> <task_exclusions.json> <output.json>")
        sys.exit(1)

    raw_path, excl_path, out_path = sys.argv[1:4]
    raw_data = load_json(raw_path)
    exclusions = load_json(excl_path)

    cleaned, log = apply_exclusions(raw_data, exclusions)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    print(f"Input participants:  {len(raw_data)}")
    print(f"Output participants: {len(cleaned)}")
    print()
    print("Changes applied:")
    for line in log:
        print(" -", line)

if __name__ == "__main__":
    main()