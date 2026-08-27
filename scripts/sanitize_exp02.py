from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

USER_HOME_PREFIX = "/Users/"
MODEL_DIR_SUFFIX = "/.lmstudio/models/lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-MLX-4bit"
MODEL_CHECKPOINT = "Qwen3-Coder-30B-A3B-Instruct-MLX-4bit"


def sanitize_row(row: dict[str, Any]) -> dict[str, Any]:
    """Replace only the known local model directory with a checkpoint identifier."""
    result = json.loads(json.dumps(row))
    configuration = result.get("configuration")
    if not isinstance(configuration, dict):
        raise ValueError("result row has no object configuration")
    model_dir = configuration.get("model_dir")
    if model_dir is not None:
        if not _is_recognized_model_dir(model_dir):
            raise ValueError(f"unexpected model_dir; refusing to sanitize: {model_dir!r}")
        configuration.pop("model_dir")
        configuration["model_checkpoint"] = MODEL_CHECKPOINT
    _reject_unexpected_user_paths(result)
    return result


def _is_recognized_model_dir(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if not value.startswith(USER_HOME_PREFIX) or not value.endswith(MODEL_DIR_SUFFIX):
        return False
    username = value[len(USER_HOME_PREFIX) : -len(MODEL_DIR_SUFFIX)]
    return bool(username) and "/" not in username


def _reject_unexpected_user_paths(value: Any) -> None:
    if isinstance(value, str):
        if "/Users/" in value:
            raise ValueError(f"unexpected machine-local path; refusing to sanitize: {value!r}")
    elif isinstance(value, dict):
        for nested in value.values():
            _reject_unexpected_user_paths(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_unexpected_user_paths(nested)


def sanitize_jsonl(source: Path, destination: Path) -> int:
    if destination.exists():
        raise ValueError(f"refusing to overwrite public export: {destination}")
    rows: list[dict[str, Any]] = []
    with source.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"source row {line_number} is not an object")
            rows.append(sanitize_row(value))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a strict public-safe Exp 02 JSONL export.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(
        "wrote "
        f"{sanitize_jsonl(args.source, args.output)} sanitized observation(s) to {args.output}"
    )


if __name__ == "__main__":
    main()
