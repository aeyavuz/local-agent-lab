from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

CONDITIONS = ("2k", "16k", "32k")
RUNTIMES = ("lmstudio", "mlx")
SCHEDULE_VERSION = 1


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"schedule must be a JSON object: {path}")
    return data


def validate_schedule(schedule: dict[str, Any], *, smoke: bool = False) -> list[str]:
    errors: list[str] = []
    expected_rows = 6 if smoke else 30
    expected_repetitions = 1 if smoke else 5
    expected_kind = "smoke" if smoke else "official"

    if schedule.get("schema_version") != SCHEDULE_VERSION:
        errors.append("unexpected schedule schema_version")
    if schedule.get("kind") != expected_kind:
        errors.append(f"schedule kind must be {expected_kind!r}")

    runs = schedule.get("runs")
    if not isinstance(runs, list):
        return [*errors, "schedule runs must be a list"]
    if len(runs) != expected_rows:
        errors.append(f"schedule must contain exactly {expected_rows} rows")

    seen: set[tuple[str, str, int]] = set()
    counts: Counter[tuple[str, int]] = Counter()
    for run in runs:
        if not isinstance(run, dict):
            errors.append("schedule contains a non-object row")
            continue
        runtime = run.get("runtime")
        condition = run.get("condition")
        repetition = run.get("repetition")
        run_order = run.get("run_order")
        if runtime not in RUNTIMES:
            errors.append(f"invalid runtime: {runtime!r}")
            continue
        if condition not in CONDITIONS:
            errors.append(f"invalid condition: {condition!r}")
            continue
        if not isinstance(repetition, int) or not 1 <= repetition <= expected_repetitions:
            errors.append(f"invalid repetition: {repetition!r}")
            continue
        if run_order not in (1, 2):
            errors.append(f"invalid run_order: {run_order!r}")
        key = (runtime, condition, repetition)
        if key in seen:
            errors.append(f"duplicate runtime/condition/repetition: {key}")
        seen.add(key)
        counts[(condition, repetition)] += 1

    for condition in CONDITIONS:
        for repetition in range(1, expected_repetitions + 1):
            if counts[(condition, repetition)] != 2:
                errors.append(f"{condition} repetition {repetition} must contain two runtime rows")
    return errors


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"JSONL row {line_number} is not an object")
            rows.append(value)
    return rows


def validate_results(
    rows: list[dict[str, Any]], *, schedule: dict[str, Any], smoke: bool
) -> list[str]:
    errors = validate_schedule(schedule, smoke=smoke)
    expected_kind = "smoke" if smoke else "official"
    scheduled = {
        (row["runtime"], row["condition"], row["repetition"]): row for row in schedule["runs"]
    }
    seen: set[tuple[str, str, int]] = set()
    for row in rows:
        key = (row.get("runtime"), row.get("condition"), row.get("repetition"))
        if key not in scheduled:
            errors.append(f"result not present in frozen schedule: {key}")
            continue
        if key in seen:
            errors.append(f"duplicate measured result: {key}")
        seen.add(key)
        if row.get("benchmark_kind") != expected_kind:
            errors.append(f"result has wrong benchmark_kind for {key}")
        if row.get("run_order") != scheduled[key]["run_order"]:
            errors.append(f"result run_order disagrees with schedule for {key}")
        if row.get("success"):
            identifiers = (
                "experiment_id",
                "timestamp",
                "runtime",
                "condition",
                "repetition",
                "run_order",
            )
            for field in identifiers:
                if row.get(field) is None:
                    errors.append(f"successful result missing {field}: {key}")
    if len(rows) > len(scheduled):
        errors.append("result file contains more rows than its frozen schedule")
    return errors
