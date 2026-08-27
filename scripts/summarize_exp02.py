from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from exp02_common import load_jsonl, read_json, validate_results

COMPARABLE_METRICS = ("wall_time_seconds", "ttft_seconds", "output_tokens")


def descriptive(values: list[float]) -> dict[str, float | None]:
    return {
        "mean": statistics.mean(values) if values else None,
        "standard_deviation": statistics.stdev(values) if len(values) > 1 else None,
        "median": statistics.median(values) if values else None,
        "min": min(values) if values else None,
        "max": max(values) if values else None,
    }


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    successful = [row for row in rows if row.get("success")]
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    paired: dict[tuple[str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in successful:
        grouped[(row["condition"], row["runtime"])].append(row)
        paired[(row["condition"], row["repetition"])][row["runtime"]] = row

    runtime_summaries: dict[str, Any] = {}
    for (condition, runtime), group in sorted(grouped.items()):
        runtime_summaries[f"{condition}:{runtime}"] = {
            metric: descriptive(
                [float(row[metric]) for row in group if row.get(metric) is not None]
            )
            for metric in COMPARABLE_METRICS
        }

    paired_summaries: dict[str, Any] = {}
    for condition in sorted({row["condition"] for row in successful}):
        paired_summaries[condition] = {}
        pairs = [
            pair for (item_condition, _), pair in paired.items() if item_condition == condition
        ]
        for metric in COMPARABLE_METRICS:
            differences: list[float] = []
            percentages: list[float] = []
            for pair in pairs:
                lmstudio, mlx = pair.get("lmstudio"), pair.get("mlx")
                if (
                    not lmstudio
                    or not mlx
                    or lmstudio.get(metric) is None
                    or mlx.get(metric) is None
                ):
                    continue
                difference = float(mlx[metric]) - float(lmstudio[metric])
                differences.append(difference)
                if float(lmstudio[metric]) != 0:
                    percentages.append(difference / float(lmstudio[metric]) * 100)
            paired_summaries[condition][metric] = {
                "mlx_minus_lmstudio": descriptive(differences),
                "percent_difference_vs_lmstudio": descriptive(percentages),
            }
    return {
        "successful_observations": len(successful),
        "runtime": runtime_summaries,
        "paired": paired_summaries,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a derived Exp 02 summary from immutable raw JSONL."
    )
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite derived summary: {args.output}")
    schedule = read_json(args.schedule)
    rows = load_jsonl(args.results)
    errors = validate_results(rows, schedule=schedule, smoke=args.smoke)
    if errors:
        raise SystemExit("cannot summarize invalid raw results:\n- " + "\n- ".join(errors))
    summary = build_summary(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote derived summary to {args.output}")


if __name__ == "__main__":
    main()
