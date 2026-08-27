from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from exp02_common import read_json, validate_results, validate_schedule  # noqa: E402
from generate_exp02_report import report_data  # noqa: E402
from generate_exp02_schedule import build_schedule  # noqa: E402
from sanitize_exp02 import MODEL_CHECKPOINT, MODEL_DIR_SUFFIX, sanitize_row  # noqa: E402
from summarize_exp02 import build_summary  # noqa: E402


def test_official_schedule_is_complete_and_frozen() -> None:
    schedule = read_json(Path("experiments/exp02-inference/schedule.json"))
    assert validate_schedule(schedule) == []
    assert len(schedule["runs"]) == 30


def test_schedule_generation_is_deterministic() -> None:
    assert build_schedule(smoke=False, seed=20260823) == build_schedule(smoke=False, seed=20260823)


def test_result_validator_rejects_duplicate_observations() -> None:
    schedule = build_schedule(smoke=True, seed=20260823)
    run = schedule["runs"][0]
    row = {
        **run,
        "experiment_id": "exp02-inference",
        "benchmark_kind": "smoke",
        "timestamp": "2026-08-26T00:00:00+00:00",
        "success": True,
    }
    errors = validate_results([row, row], schedule=schedule, smoke=True)
    assert any("duplicate measured result" in error for error in errors)


def test_schedule_json_is_valid_json() -> None:
    with Path("experiments/exp02-inference/smoke-schedule.json").open(encoding="utf-8") as handle:
        assert json.load(handle)["kind"] == "smoke"


def test_prompt_manifest_covers_all_frozen_conditions() -> None:
    with Path("experiments/exp02-inference/prompt-manifest.json").open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    assert set(manifest["prompts"]) == {"2k", "16k", "32k"}


def test_summary_reports_paired_runtime_difference() -> None:
    rows = [
        {
            "success": True,
            "condition": "2k",
            "repetition": 1,
            "runtime": "lmstudio",
            "wall_time_seconds": 2.0,
            "ttft_seconds": 1.0,
            "output_tokens": 10,
        },
        {
            "success": True,
            "condition": "2k",
            "repetition": 1,
            "runtime": "mlx",
            "wall_time_seconds": 1.0,
            "ttft_seconds": 0.5,
            "output_tokens": 10,
        },
    ]
    paired = build_summary(rows)["paired"]["2k"]["wall_time_seconds"]
    assert paired["mlx_minus_lmstudio"]["mean"] == -1.0
    assert paired["percent_difference_vs_lmstudio"]["mean"] == -50.0


def test_sanitizer_replaces_only_the_expected_machine_path() -> None:
    row = {
        "configuration": {"model_dir": f"/Users/testuser{MODEL_DIR_SUFFIX}"},
        "prompt_id": "exp02-2k",
    }
    assert sanitize_row(row)["configuration"] == {"model_checkpoint": MODEL_CHECKPOINT}


def test_sanitizer_rejects_an_unrecognized_machine_path() -> None:
    row = {"configuration": {"model_dir": "/Users/someone-else/model"}}
    try:
        sanitize_row(row)
    except ValueError as error:
        assert "unexpected model_dir" in str(error)
    else:
        raise AssertionError("sanitizer accepted an unrecognized local path")


def test_report_includes_sample_standard_deviation() -> None:
    rows = [
        {
            "success": True,
            "condition": "2k",
            "runtime": "mlx",
            "ttft_seconds": ttft,
            "wall_time_seconds": ttft + 1.0,
            "generation_tps": 10.0,
            "output_tokens": 5,
        }
        for ttft in (1.0, 3.0)
    ]
    report = report_data(rows)["2k"]["mlx"]
    assert report["mean_ttft_seconds"] == 2.0
    assert report["ttft_standard_deviation_seconds"] == 2**0.5
