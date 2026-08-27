# Local Agent Lab

A reproducible study of local LLM inference and agentic software engineering on Apple Silicon.

## Research Question

How much useful software-engineering work can a high-memory Apple Silicon laptop execute locally before frontier-model intervention becomes necessary?

## Experiments

| Experiment | Question | Status |
| --- | --- | --- |
| Exp 01 | Can the model run locally at useful interactive speeds? | Complete |
| Exp 02 | How do LM Studio MLX and raw mlx-lm behave under controlled context workloads? | Complete; public export available |
| Exp 03 | Can a local agent inspect a repository read-only and diagnose a bounded defect? | Complete; 0/3 strict successes |
| Exp 04 | Can a local agent make a bounded repair to that controlled defect? | Complete; 0/3 strict successes |
| Exp 06a | Can a small RDKit pipeline produce verified molecule-triage output? | Complete harness/oracle |
| Exp 06b | Can a local agent implement Molecule Triage from a clean specification? | Preliminary; 0/1 strict successes |

## Principles

- Raw results are preserved before analysis.
- Observational measurements are distinguished from controlled benchmarks.
- Deterministic tests and scientific oracles define correctness where possible.
- Missing measurements are reported as missing rather than estimated.
- Agent autonomy is evaluated separately from model fluency.

## Reproduction

Exp 01 is an observational setup smoke test. Its preserved results are not a
controlled comparison. Exp 02 is the controlled runtime benchmark: it uses the
frozen prompts and schedules in `experiments/exp02-inference/`, with a six-run
smoke before the official 30 observations. See its
[protocol](experiments/exp02-inference/PROTOCOL.md).

```sh
export LMSTUDIO_LOAD_CMD='your local LM Studio model-load/start command'
export LMSTUDIO_UNLOAD_CMD='your local LM Studio model-unload/stop command'
uv run bash scripts/run_exp02.sh --smoke --model-dir /absolute/path/to/model
uv run bash scripts/run_exp02.sh --model-dir /absolute/path/to/model
```

Exp 03 and Exp 04 both begin by creating a disposable copy of the immutable
calculator fixture; their protocols define the read-only and bounded-repair
constraints respectively.

```sh
uv run python scripts/prepare_agent_benchmark.py \
  --experiment exp03 --output-dir /tmp/local-agent-lab-exp03-run-001
uv run python scripts/prepare_agent_benchmark.py \
  --experiment exp04 --output-dir /tmp/local-agent-lab-exp04-run-001
```

Exp 06a is a small RDKit-backed scientific benchmark, not an ADMET or activity
prediction system. See [Molecule Triage v0](projects/molecule_triage/README.md).

```sh
uv run python scripts/run_molecule_triage.py \
  --input molecules.smi --output results/raw/exp06a-run-001.jsonl
```

Run all deterministic project checks with `make gates`.

The collected Exp 02 raw JSONL is private evidence. Use the documented
sanitization export before sharing or deriving public report artifacts.

## Baseline 1 findings

The public Exp 02 export and its derived [summary](results/summary/exp02-inference.json)
show that raw MLX reduced mean time-to-first-token by 13–20% across the three
tested prompt contexts. Context growth had a much larger effect than that
runtime gap.

The agent results use a strict definition of success: a correct diagnosis or
edit without executing the required verification gate is a failure. See the
[agent-results table](results/summary/agent-results-baseline-v1.md) and the
[Baseline 1 publication draft](posts/baseline-v1.md).

## Deferred by design

Ollama, gpt-oss, Aider, OpenHands, Zed Agent, 64K context benchmarking, prefix
caching, dose-response analysis, and advanced thermal telemetry are future work.
