from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from prepare_agent_benchmark import directory_hash, result_template  # noqa: E402
from validate_agent_result import validate_result  # noqa: E402


def test_fixture_hash_is_stable() -> None:
    fixture = Path("fixtures/broken_calculator_seed")
    assert directory_hash(fixture) == directory_hash(fixture)


def test_exp03_preparation_copies_without_modifying_seed(tmp_path: Path) -> None:
    fixture = Path("fixtures/broken_calculator_seed")
    before = directory_hash(fixture)
    output = tmp_path / "run"
    subprocess.run(
        [
            sys.executable,
            "scripts/prepare_agent_benchmark.py",
            "--experiment",
            "exp03",
            "--output-dir",
            str(output),
        ],
        check=True,
    )
    assert directory_hash(fixture) == before
    assert (output / "repository" / "calculator.py").is_file()
    assert '"repair_attempts": null' in (output / "result-template.json").read_text()
    gate = subprocess.run(
        ["make", "gates"], cwd=output / "repository", capture_output=True, text=True, check=False
    )
    assert gate.returncode != 0
    assert "test_median_even_length" in gate.stdout


def test_exp04_result_template_has_repair_bound() -> None:
    template = result_template("exp04", "baseline")
    assert template["repair_attempts"] == 0
    assert "SCOPE_POLICY" in template["allowed_failure_categories"]


def test_agent_result_validator_enforces_read_only_success() -> None:
    result = result_template("exp03", "baseline")
    result.update(
        {
            "task_success": True,
            "canonical_gate": "make gates",
            "validation_executed": True,
            "diagnosis": "The even-length median chooses the upper middle value.",
            "wall_time_seconds": 1.0,
        }
    )
    assert validate_result(result, "exp03") == []
    result["files_modified"] = ["calculator.py"]
    assert any("zero file modifications" in error for error in validate_result(result, "exp03"))


def test_agent_result_validator_allows_tool_format_subcategory() -> None:
    result = result_template("exp03", "baseline")
    result["failure_category"] = "TOOL_FORMAT"
    result["failure_subcategory"] = "REPOSITORY_INTERFACE_DISCOVERY"
    assert validate_result(result, "exp03") == []
