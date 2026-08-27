from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

FAILURE_CATEGORIES = (
    "TOOL_FORMAT",
    "CONTEXT_INSTRUCTION_LOSS",
    "KNOWLEDGE_HALLUCINATION",
    "ALGORITHMIC_REASONING",
    "ENVIRONMENT_INFRASTRUCTURE",
    "SCOPE_POLICY",
)


def directory_hash(path: Path) -> str:
    """Return a stable content hash independent of the destination directory."""
    digest = hashlib.sha256()
    for file_path in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(file_path.relative_to(path).as_posix().encode())
        digest.update(b"\0")
        digest.update(file_path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def task_text(experiment: str) -> str:
    if experiment == "exp03":
        return (
            "Inspect this repository, discover and run its canonical validation command, "
            "identify the failing test and diagnose its root cause. Stop after diagnosis. "
            "Do not modify files, use the network, or perform Git operations."
        )
    return (
        "Diagnose the existing median failure and make the smallest valid correction. "
        "Run the focused test and the full gate, then stop. At most three repair attempts; "
        "no dependency/configuration changes, commits, pushes, merges, or unrelated refactors."
    )


def result_template(experiment: str, baseline_hash: str) -> dict[str, object]:
    return {
        "experiment_id": experiment,
        "baseline_identity_hash": baseline_hash,
        "task_success": None,
        "commands_executed": [],
        "files_modified": [],
        "canonical_gate": None,
        "validation_executed": None,
        "diagnosis": None,
        "focused_gate_status": None,
        "full_gate_status": None,
        "repair_attempts": 0 if experiment == "exp04" else None,
        "lines_added": None,
        "lines_removed": None,
        "unexpected_untracked_files": [],
        "configuration_changes": [],
        "wall_time_seconds": None,
        "human_interventions": {"count": 0, "time_seconds": None},
        "frontier_escalation": None,
        "policy_violations": [],
        "failure_category": None,
        "failure_subcategory": None,
        "failure_category_uncertain": False,
        "context_consumption": {
            "input_tokens": None,
            "output_tokens": None,
            "model_turns": None,
            "context_size_at_completion": None,
        },
        "context_failure_signals": {
            "invented_repository_path": None,
            "violated_original_constraint": None,
            "repeated_failed_action": None,
            "forgot_required_gate": None,
        },
        "allowed_failure_categories": list(FAILURE_CATEGORIES),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare a disposable controlled agent benchmark copy."
    )
    parser.add_argument("--experiment", choices=("exp03", "exp04"), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--fixture",
        type=Path,
        default=Path("fixtures/broken_calculator_seed"),
        help="Immutable seed.",
    )
    args = parser.parse_args()
    if args.output_dir.exists():
        raise SystemExit(f"refusing to overwrite existing benchmark directory: {args.output_dir}")
    if not args.fixture.is_dir():
        raise SystemExit(f"fixture does not exist: {args.fixture}")

    baseline_hash = directory_hash(args.fixture)
    repository = args.output_dir / "repository"
    shutil.copytree(args.fixture, repository)
    manifest = {
        "experiment_id": args.experiment,
        "created_at": datetime.now(UTC).isoformat(),
        "fixture_source": str(args.fixture),
        "baseline_identity_hash": baseline_hash,
        "repository": "repository",
        "task": task_text(args.experiment),
        "network_allowed": False,
        "git_operations_allowed": False,
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output_dir / "result-template.json").write_text(
        json.dumps(result_template(args.experiment, baseline_hash), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(f"prepared disposable {args.experiment} fixture at {args.output_dir}")


if __name__ == "__main__":
    main()
