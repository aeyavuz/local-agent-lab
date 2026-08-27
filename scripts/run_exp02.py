from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from exp02_common import CONDITIONS, RUNTIMES, sha256_text


@dataclass
class RunResult:
    experiment_id: str
    benchmark_kind: str
    timestamp: str
    runtime: str
    condition: str
    repetition: int
    run_order: int
    prompt_id: str
    prompt_hash: str
    prompt_tokens: int | None
    output_tokens: int | None
    ttft_seconds: float | None
    wall_time_seconds: float
    prompt_tps: float | None
    generation_tps: float | None
    peak_memory_gb: float | None
    configuration: dict[str, Any]
    success: bool
    error: str | None


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def append_jsonl(path: Path, result: RunResult) -> None:
    """Append one immutable observation; never rewrite existing rows."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(result), sort_keys=True))
        handle.write("\n")


def make_result(
    *,
    benchmark_kind: str,
    runtime: str,
    condition: str,
    repetition: int,
    run_order: int,
    prompt: str,
    max_tokens: int,
    started: float,
    success: bool,
    runtime_configuration: dict[str, Any] | None = None,
    **metrics: Any,
) -> RunResult:
    return RunResult(
        experiment_id="exp02-inference",
        benchmark_kind=benchmark_kind,
        timestamp=utc_now(),
        runtime=runtime,
        condition=condition,
        repetition=repetition,
        run_order=run_order,
        prompt_id=f"exp02-{condition}",
        prompt_hash=sha256_text(prompt),
        prompt_tokens=metrics.get("prompt_tokens"),
        output_tokens=metrics.get("output_tokens"),
        ttft_seconds=metrics.get("ttft_seconds"),
        wall_time_seconds=time.perf_counter() - started,
        prompt_tps=metrics.get("prompt_tps"),
        generation_tps=metrics.get("generation_tps"),
        peak_memory_gb=metrics.get("peak_memory_gb"),
        configuration={
            "max_tokens": max_tokens,
            "temperature": 0,
            "batch_size": 1,
            **(runtime_configuration or {}),
        },
        success=success,
        error=metrics.get("error"),
    )


def run_raw_mlx(
    *,
    model_dir: Path,
    prompt: str,
    condition: str,
    repetition: int,
    run_order: int,
    max_tokens: int,
    benchmark_kind: str,
    warmup: bool,
) -> RunResult:
    """Load, optionally warm, measure, and release MLX in this one process."""
    started = time.perf_counter()
    try:
        import mlx.core as mx
        from mlx_lm import load, stream_generate

        model, tokenizer = load(str(model_dir))
        if warmup:
            for _ in stream_generate(model, tokenizer, prompt="Reply with OK.", max_tokens=8):
                pass
        mx.reset_peak_memory()
        measured_started = time.perf_counter()
        first_token_at: float | None = None
        final_response: Any | None = None
        for response in stream_generate(model, tokenizer, prompt=prompt, max_tokens=max_tokens):
            if first_token_at is None:
                first_token_at = time.perf_counter()
            final_response = response
        if final_response is None:
            raise RuntimeError("mlx-lm returned no generation response")
        return make_result(
            benchmark_kind=benchmark_kind,
            runtime="mlx",
            condition=condition,
            repetition=repetition,
            run_order=run_order,
            prompt=prompt,
            max_tokens=max_tokens,
            started=measured_started,
            success=True,
            runtime_configuration={"model_dir": str(model_dir)},
            prompt_tokens=getattr(final_response, "prompt_tokens", len(tokenizer.encode(prompt))),
            output_tokens=getattr(final_response, "generation_tokens", None),
            ttft_seconds=(first_token_at - measured_started if first_token_at else None),
            prompt_tps=getattr(final_response, "prompt_tps", None),
            generation_tps=getattr(final_response, "generation_tps", None),
            peak_memory_gb=getattr(final_response, "peak_memory", None),
        )
    except Exception as exc:
        return make_result(
            benchmark_kind=benchmark_kind,
            runtime="mlx",
            condition=condition,
            repetition=repetition,
            run_order=run_order,
            prompt=prompt,
            max_tokens=max_tokens,
            started=started,
            success=False,
            runtime_configuration={"model_dir": str(model_dir)},
            error=repr(exc),
        )


def run_lmstudio(
    *,
    base_url: str,
    model_name: str,
    prompt: str,
    condition: str,
    repetition: int,
    run_order: int,
    max_tokens: int,
    benchmark_kind: str,
    warmup: bool,
) -> RunResult:
    started = time.perf_counter()
    try:
        request_body = {
            "model": model_name,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": 0,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        with httpx.Client(timeout=None) as client:
            if warmup:
                warmup_body = {**request_body, "prompt": "Reply with OK.", "max_tokens": 8}
                with client.stream(
                    "POST", f"{base_url}/v1/completions", json=warmup_body
                ) as response:
                    response.raise_for_status()
                    for _ in response.iter_lines():
                        pass
            measured_started = time.perf_counter()
            first_token_at: float | None = None
            prompt_tokens: int | None = None
            output_tokens: int | None = None
            with client.stream("POST", f"{base_url}/v1/completions", json=request_body) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line.removeprefix("data: ").strip()
                    if payload == "[DONE]":
                        continue
                    data = json.loads(payload)
                    choices = data.get("choices", [])
                    if choices and choices[0].get("text") and first_token_at is None:
                        first_token_at = time.perf_counter()
                    usage = data.get("usage")
                    if usage:
                        prompt_tokens = usage.get("prompt_tokens")
                        output_tokens = usage.get("completion_tokens")
        return make_result(
            benchmark_kind=benchmark_kind,
            runtime="lmstudio",
            condition=condition,
            repetition=repetition,
            run_order=run_order,
            prompt=prompt,
            max_tokens=max_tokens,
            started=measured_started,
            success=True,
            runtime_configuration={"base_url": base_url, "model_name": model_name},
            prompt_tokens=prompt_tokens,
            output_tokens=output_tokens,
            ttft_seconds=(first_token_at - measured_started if first_token_at else None),
        )
    except Exception as exc:
        return make_result(
            benchmark_kind=benchmark_kind,
            runtime="lmstudio",
            condition=condition,
            repetition=repetition,
            run_order=run_order,
            prompt=prompt,
            max_tokens=max_tokens,
            started=started,
            success=False,
            runtime_configuration={"base_url": base_url, "model_name": model_name},
            error=repr(exc),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run exactly one scheduled Exp 02 observation.")
    parser.add_argument("--runtime", choices=RUNTIMES, required=True)
    parser.add_argument("--condition", choices=CONDITIONS, required=True)
    parser.add_argument("--repetition", type=int, required=True)
    parser.add_argument("--run-order", type=int, choices=(1, 2), required=True)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--warmup", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prompts-dir", type=Path, default=Path("prompts/exp02"))
    parser.add_argument("--model-dir", type=Path)
    parser.add_argument("--lmstudio-base-url", default="http://localhost:1234")
    parser.add_argument("--lmstudio-model", default="local-coder")
    parser.add_argument("--benchmark-kind", choices=("official", "smoke"), required=True)
    args = parser.parse_args()
    if args.repetition < 1 or args.max_tokens < 1:
        raise SystemExit("repetition and max-tokens must be positive")
    prompt = (args.prompts_dir / f"{args.condition}.txt").read_text(encoding="utf-8")
    if args.runtime == "mlx":
        if args.model_dir is None:
            raise SystemExit("--model-dir is required for runtime=mlx")
        observation = run_raw_mlx(
            model_dir=args.model_dir,
            prompt=prompt,
            condition=args.condition,
            repetition=args.repetition,
            run_order=args.run_order,
            max_tokens=args.max_tokens,
            benchmark_kind=args.benchmark_kind,
            warmup=args.warmup,
        )
    else:
        observation = run_lmstudio(
            base_url=args.lmstudio_base_url,
            model_name=args.lmstudio_model,
            prompt=prompt,
            condition=args.condition,
            repetition=args.repetition,
            run_order=args.run_order,
            max_tokens=args.max_tokens,
            benchmark_kind=args.benchmark_kind,
            warmup=args.warmup,
        )
    append_jsonl(args.output, observation)
    print(json.dumps(asdict(observation), indent=2, sort_keys=True))
    if not observation.success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
