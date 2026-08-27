# Experiment 02 Protocol

## Question

How do LM Studio MLX and raw mlx-lm compare when executing the same local Qwen3-Coder-30B-A3B-Instruct MLX 4-bit checkpoint?

## Controlled variables

- Same physical model checkpoint
- Same machine
- Same prompt payload
- Same context target
- Same output-token budget
- Same deterministic sampling configuration (`temperature = 0`; raw MLX uses
  its argmax default, which is the corresponding deterministic sampler)
- Batch size = 1

## Runtime variable

- LM Studio MLX
- raw mlx-lm

## Conditions

Three prompt sizes:

- `2k`: frozen prompt (currently 2,039 actual tokens)
- `16k`: frozen prompt (currently 16,229 actual tokens)
- `32k`: frozen prompt (currently 32,569 actual tokens)

Five paired repetitions per condition.

The frozen `schedule.json` defines the 30 measured observations. Repetitions
one through four alternate LM Studio then MLX / MLX then LM Studio; repetition
five is a seeded deterministic choice. `smoke-schedule.json` contains the six
smoke observations and is intentionally distinct from the official schedule.
`prompt-manifest.json` records the frozen prompt hashes and actual token counts.

## Warm-up

After loading a runtime/model, perform one unmeasured warm-up generation.

## Recorded metrics

- actual prompt tokens
- output tokens
- TTFT when measurable
- prompt/prefill tokens per second
- generation tokens per second
- total wall time
- peak memory when exposed
- runtime order
- run number

## Interpretation rule

Runtime-native metrics are preserved separately.

Only metrics with equivalent definitions across runtimes are used for direct comparison.

## Exclusions

- Ollama
- 64K context
- deep thermal characterization
- prefix-cache benchmarking

These are deferred experiments.

## Execution

`run_exp02.py` measures exactly one schedule row and appends exactly one JSONL
observation. `run_exp02.sh` owns residency: it requires `LMSTUDIO_LOAD_CMD` and
`LMSTUDIO_UNLOAD_CMD` so the local LM Studio setup can supply its own reliable
model load/unload actions. It waits for the local API, warms the runtime,
measures one row, and unloads it before the next runtime.

Run the six-row smoke first, then validate it. The shell runner will refuse the
official 30-run benchmark until a complete smoke JSONL has validated.

```sh
export LMSTUDIO_LOAD_CMD='your command that loads the benchmark model and starts its API'
export LMSTUDIO_UNLOAD_CMD='your command that unloads the model or stops its server'
uv run bash scripts/run_exp02.sh --smoke --model-dir /absolute/path/to/model
uv run bash scripts/run_exp02.sh --model-dir /absolute/path/to/model
```

Raw output paths are refused if they already exist. This prevents a rerun from
silently mixing or overwriting observations. Validate a completed output with:

```sh
uv run python scripts/validate_exp02_results.py \
  --schedule experiments/exp02-inference/schedule.json \
  --results results/raw/exp02-inference.jsonl
```

Create a separate report-ready summary (mean, standard deviation, median, min,
max, paired runtime differences, and percent differences; no hypothesis tests)
only after validation:

```sh
uv run python scripts/summarize_exp02.py \
  --schedule experiments/exp02-inference/schedule.json \
  --results results/raw/exp02-inference.jsonl \
  --output results/summary/exp02-inference.json
```

For publication, preserve `results/raw/` as the private collected evidence.
Create `results/public/exp02-inference.jsonl` with
`scripts/sanitize_exp02.py`; it replaces only the known machine-local model path
and refuses unrecognized local paths. Run `scripts/generate_exp02_report.py`
against that public export to create the summary and SVG charts.

ShellCheck was unavailable in the implementation environment. `bash -n` is run
as the deterministic shell syntax check instead; install nothing solely for this
project.
