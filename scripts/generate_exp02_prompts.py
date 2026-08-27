from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from transformers import AutoTokenizer

TARGETS = {
    "2k": 2048,
    "16k": 16384,
    "32k": 32768,
}


def synthetic_module(index: int) -> str:
    return f"""
# file: src/service_{index:04d}.py

from dataclasses import dataclass


@dataclass(frozen=True)
class SampleRecord{index:04d}:
    sample_id: str
    batch_id: str
    measurement: float
    qc_passed: bool


def normalize_measurement_{index:04d}(value: float, baseline: float) -> float:
    \"\"\"Normalize one deterministic synthetic measurement.

    The function is intentionally simple. These modules exist only to create
    repeatable repository-like context for local inference benchmarking.
    \"\"\"
    if baseline == 0:
        raise ValueError("baseline must be non-zero")
    return value / baseline


def summarize_record_{index:04d}(record: SampleRecord{index:04d}) -> str:
    status = "PASS" if record.qc_passed else "FAIL"
    return (
        f"sample={{record.sample_id}} "
        f"batch={{record.batch_id}} "
        f"measurement={{record.measurement:.4f}} "
        f"qc={{status}}"
    )
"""


FINAL_TASK = """
# Benchmark task

You are reviewing the synthetic repository context above.

Answer concisely:

1. What exception is raised when a normalization baseline is zero?
2. What two string values represent QC status?
3. Why should these synthetic modules not be interpreted as scientific software?

Limit the response to at most 150 words.
"""


def build_prompt(tokenizer, target_tokens: int) -> tuple[str, int]:
    header = """# Synthetic repository benchmark

The following files are deterministic synthetic Python modules.
They exist only to provide repository-like context for an inference benchmark.
Do not infer scientific meaning from the data model.

"""

    chunks = [header]
    index = 1

    # Leave room for the final task.
    final_task_tokens = len(tokenizer.encode(FINAL_TASK, add_special_tokens=False))

    while True:
        candidate = "".join(chunks) + synthetic_module(index)
        token_count = len(tokenizer.encode(candidate, add_special_tokens=False))

        if token_count + final_task_tokens >= target_tokens:
            break

        chunks.append(synthetic_module(index))
        index += 1

    base_text = "".join(chunks)
    base_tokens = tokenizer.encode(base_text, add_special_tokens=False)

    desired_base_tokens = target_tokens - final_task_tokens

    if len(base_tokens) > desired_base_tokens:
        base_tokens = base_tokens[:desired_base_tokens]

    prompt = tokenizer.decode(base_tokens, skip_special_tokens=True) + FINAL_TASK
    actual_tokens = len(tokenizer.encode(prompt, add_special_tokens=False))

    return prompt, actual_tokens


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-dir",
        type=Path,
        required=True,
        help="Local Qwen MLX checkpoint directory.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("prompts/exp02"),
    )
    args = parser.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(
        args.model_dir,
        local_files_only=True,
        trust_remote_code=True,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating deterministic Exp 02 prompts")

    for label, target in TARGETS.items():
        prompt, actual_tokens = build_prompt(tokenizer, target)
        output_path = args.output_dir / f"{label}.txt"
        output_path.write_text(prompt, encoding="utf-8")

        digest = sha256_text(prompt)

        print(f"{label:>3}: target={target:,} actual={actual_tokens:,} sha256={digest}")


if __name__ == "__main__":
    main()
