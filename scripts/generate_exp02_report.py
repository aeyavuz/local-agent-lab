# ruff: noqa: E501
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from exp02_common import load_jsonl, read_json, validate_results

CONDITIONS = ("2k", "16k", "32k")
RUNTIME_LABELS = {"lmstudio": "LM Studio", "mlx": "raw MLX"}


def mean(values: list[float]) -> float | None:
    return statistics.mean(values) if values else None


def sample_standard_deviation(values: list[float]) -> float | None:
    return statistics.stdev(values) if len(values) > 1 else None


def report_data(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("success"):
            groups[(row["condition"], row["runtime"])].append(row)
    results: dict[str, Any] = {}
    for condition in CONDITIONS:
        results[condition] = {}
        for runtime in ("lmstudio", "mlx"):
            group = groups[(condition, runtime)]
            ttft_values = [float(row["ttft_seconds"]) for row in group]
            wall_time_values = [float(row["wall_time_seconds"]) for row in group]
            generation_tps_values = [
                float(row["generation_tps"]) for row in group if row["generation_tps"] is not None
            ]
            results[condition][runtime] = {
                "observations": len(group),
                "mean_ttft_seconds": mean(ttft_values),
                "ttft_standard_deviation_seconds": sample_standard_deviation(ttft_values),
                "mean_wall_time_seconds": mean(wall_time_values),
                "wall_time_standard_deviation_seconds": sample_standard_deviation(wall_time_values),
                "mean_generation_tps": mean(generation_tps_values),
                "generation_tps_standard_deviation": sample_standard_deviation(
                    generation_tps_values
                ),
                "output_tokens": sorted({int(row["output_tokens"]) for row in group}),
            }
    return results


def svg_line_chart(
    title: str,
    y_label: str,
    series: dict[str, list[float]],
    uncertainty: dict[str, list[float | None]],
    destination: Path,
) -> None:
    width, height = 760, 430
    left, right, top, bottom = 92, 30, 56, 80
    values = [
        value + (uncertainty[label][index] or 0.0)
        for label, points in series.items()
        for index, value in enumerate(points)
    ]
    y_min, y_max = 0.0, max(values)
    padding = (y_max - y_min) * 0.12 or 1.0
    y_max += padding
    plot_width, plot_height = width - left - right, height - top - bottom

    def x(index: int) -> float:
        return left + index * plot_width / (len(CONDITIONS) - 1)

    def y(value: float) -> float:
        return top + (y_max - value) / (y_max - y_min) * plot_height

    colors = {"LM Studio": "#1565c0", "raw MLX": "#d65f00"}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width / 2}" y="30" text-anchor="middle" font-family="system-ui" font-size="20">{escape(title)}</text>',
        f'<text x="18" y="{height / 2}" transform="rotate(-90 18 {height / 2})" text-anchor="middle" font-family="system-ui" font-size="14">{escape(y_label)}</text>',
    ]
    for tick in range(5):
        value = y_min + (y_max - y_min) * tick / 4
        y_position = y(value)
        parts.append(
            f'<line x1="{left}" y1="{y_position:.1f}" x2="{width - right}" y2="{y_position:.1f}" stroke="#d0d0d0"/>'
        )
        parts.append(
            f'<text x="{left - 10}" y="{y_position + 5:.1f}" text-anchor="end" font-family="system-ui" font-size="12">{value:.1f}</text>'
        )
    for index, condition in enumerate(CONDITIONS):
        x_position = x(index)
        parts.append(
            f'<text x="{x_position:.1f}" y="{height - 42}" text-anchor="middle" font-family="system-ui" font-size="14">{condition}</text>'
        )
    for label, points in series.items():
        coordinates = " ".join(
            f"{x(index):.1f},{y(value):.1f}" for index, value in enumerate(points)
        )
        color = colors[label]
        parts.append(
            f'<polyline points="{coordinates}" fill="none" stroke="{color}" stroke-width="3"/>'
        )
        for index, value in enumerate(points):
            standard_deviation = uncertainty[label][index]
            if standard_deviation is not None:
                x_position = x(index)
                upper, lower = y(value + standard_deviation), y(value - standard_deviation)
                parts.append(
                    f'<line x1="{x_position:.1f}" y1="{upper:.1f}" x2="{x_position:.1f}" y2="{lower:.1f}" stroke="{color}" stroke-width="2"/>'
                )
                parts.append(
                    f'<line x1="{x_position - 5:.1f}" y1="{upper:.1f}" x2="{x_position + 5:.1f}" y2="{upper:.1f}" stroke="{color}" stroke-width="2"/>'
                )
                parts.append(
                    f'<line x1="{x_position - 5:.1f}" y1="{lower:.1f}" x2="{x_position + 5:.1f}" y2="{lower:.1f}" stroke="{color}" stroke-width="2"/>'
                )
            parts.append(f'<circle cx="{x(index):.1f}" cy="{y(value):.1f}" r="5" fill="{color}"/>')
    for index, label in enumerate(series):
        parts.append(
            f'<rect x="{left + index * 145}" y="{height - 24}" width="14" height="14" fill="{colors[label]}"/>'
        )
        parts.append(
            f'<text x="{left + 20 + index * 145}" y="{height - 12}" font-family="system-ui" font-size="13">{label}</text>'
        )
    parts.append(
        f'<text x="{width - right}" y="{height - 12}" text-anchor="end" font-family="system-ui" font-size="12" fill="#555">mean ± 1 SD (n=5)</text>'
    )
    parts.append("</svg>")
    destination.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create Exp 02 summaries and SVG charts from a public export."
    )
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--charts-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.summary.exists() or args.charts_dir.exists():
        raise SystemExit("refusing to overwrite an existing derived report destination")
    rows = load_jsonl(args.results)
    errors = validate_results(rows, schedule=read_json(args.schedule), smoke=False)
    if errors:
        raise SystemExit("cannot report invalid observations:\n- " + "\n- ".join(errors))
    summary = {
        "source_sha256": hashlib.sha256(args.results.read_bytes()).hexdigest(),
        "source": args.results.as_posix(),
        "results": report_data(rows),
        "limitations": [
            "LM Studio did not expose native generation throughput.",
            "Output-token counts differ between runtimes for the 16k and 32k prompts.",
        ],
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.charts_dir.mkdir(parents=True)
    report = summary["results"]
    svg_line_chart(
        "Exp 02: TTFT by input context",
        "Mean TTFT (seconds)",
        {
            "LM Studio": [
                report[condition]["lmstudio"]["mean_ttft_seconds"] for condition in CONDITIONS
            ],
            "raw MLX": [report[condition]["mlx"]["mean_ttft_seconds"] for condition in CONDITIONS],
        },
        {
            "LM Studio": [
                report[condition]["lmstudio"]["ttft_standard_deviation_seconds"]
                for condition in CONDITIONS
            ],
            "raw MLX": [
                report[condition]["mlx"]["ttft_standard_deviation_seconds"]
                for condition in CONDITIONS
            ],
        },
        args.charts_dir / "exp02-ttft-by-context.svg",
    )
    svg_line_chart(
        "Exp 02: raw MLX generation throughput by input context",
        "Mean generation throughput (tokens/second)",
        {"raw MLX": [report[condition]["mlx"]["mean_generation_tps"] for condition in CONDITIONS]},
        {
            "raw MLX": [
                report[condition]["mlx"]["generation_tps_standard_deviation"]
                for condition in CONDITIONS
            ]
        },
        args.charts_dir / "exp02-mlx-generation-throughput.svg",
    )
    print(f"wrote summary and two charts from {args.results}")


if __name__ == "__main__":
    main()
