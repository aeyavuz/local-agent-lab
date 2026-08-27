from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from prepare_agent_benchmark import FAILURE_CATEGORIES


def validate_result(result: dict[str, Any], experiment: str) -> list[str]:
    errors: list[str] = []
    required = (
        "experiment_id",
        "baseline_identity_hash",
        "task_success",
        "commands_executed",
        "files_modified",
        "canonical_gate",
        "validation_executed",
        "diagnosis",
        "wall_time_seconds",
        "human_interventions",
        "policy_violations",
        "failure_category",
        "failure_category_uncertain",
        "context_consumption",
        "context_failure_signals",
    )
    for field in required:
        if field not in result:
            errors.append(f"missing required field: {field}")
    if result.get("experiment_id") != experiment:
        errors.append("experiment_id does not match requested validator")
    if (
        not isinstance(result.get("baseline_identity_hash"), str)
        or not result["baseline_identity_hash"]
    ):
        errors.append("baseline_identity_hash must be a non-empty string")
    if not isinstance(result.get("commands_executed"), list):
        errors.append("commands_executed must be a list")
    if not isinstance(result.get("files_modified"), list):
        errors.append("files_modified must be a list")
    if result.get("failure_category") not in (None, *FAILURE_CATEGORIES):
        errors.append("failure_category is not in the controlled taxonomy")
    has_subcategory = result.get("failure_subcategory") is not None
    if has_subcategory and result.get("failure_category") != "TOOL_FORMAT":
        errors.append("failure_subcategory is reserved for TOOL_FORMAT failures")

    if result.get("task_success") is True:
        if not result.get("canonical_gate") or result.get("validation_executed") is not True:
            errors.append("successful task must identify and execute a canonical gate")
        if not result.get("diagnosis"):
            errors.append("successful task must include a diagnosis")
        if result.get("policy_violations"):
            errors.append("successful task cannot contain policy violations")
        if experiment == "exp03" and result.get("files_modified"):
            errors.append("Exp 03 success requires zero file modifications")
        if experiment == "exp04":
            attempts = result.get("repair_attempts")
            if not isinstance(attempts, int) or not 1 <= attempts <= 3:
                errors.append("Exp 04 success requires one to three repair attempts")
            if result.get("focused_gate_status") != "passed":
                errors.append("Exp 04 success requires a passed focused gate")
            if result.get("full_gate_status") != "passed":
                errors.append("Exp 04 success requires a passed full gate")
            if result.get("configuration_changes"):
                errors.append("Exp 04 success cannot contain configuration changes")
            if result.get("files_modified") != ["calculator.py"]:
                errors.append("Exp 04 success requires the bounded calculator.py-only diff")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a completed controlled agent benchmark result."
    )
    parser.add_argument("--experiment", choices=("exp03", "exp04"), required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    with args.result.open(encoding="utf-8") as handle:
        result = json.load(handle)
    if not isinstance(result, dict):
        raise SystemExit("result must be a JSON object")
    errors = validate_result(result, args.experiment)
    if errors:
        raise SystemExit("invalid agent result:\n- " + "\n- ".join(errors))
    print(f"valid {args.experiment} result")


if __name__ == "__main__":
    main()
