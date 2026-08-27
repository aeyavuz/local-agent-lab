# How Much Software Engineering Can I Offload to a Local 30B Model? Baseline 1

> Local inference was fast enough. Trustworthy agent completion was the harder problem.

## Question

How much useful software-engineering work can a high-memory Apple Silicon laptop
complete locally before premium frontier-model intervention becomes necessary?

Tests used Qwen3-Coder-30B-A3B-Instruct MLX 4-bit on an Apple M5 Pro MacBook Pro
with 48 GB unified memory. LM Studio MLX and raw `mlx-lm` used the same physical
checkpoint.

## Finding

Local inference was viable in this setup. Raw MLX reduced mean time-to-first-token
relative to LM Studio at every tested context size, but the more consequential
result was the latency cost of growing context. The local coding agent could
diagnose and repair a simple deterministic defect, yet did not reliably produce
evidence-backed completion.

## Runtime baseline

| Input context | LM Studio mean TTFT | raw MLX mean TTFT | raw MLX difference |
| --- | ---: | ---: | ---: |
| ~2K | 1.208 s | 0.969 s | -19.7% |
| ~16K | 12.055 s | 10.412 s | -13.4% |
| ~32K | 37.621 s | 31.184 s | -17.1% |

Five paired measurements were collected per context condition using a frozen,
balanced run order. Each runtime received a warm-up before measurement, and the
competing runtime was unloaded to avoid simultaneous model residency. Input
prompts were fixed and hashed. The public [protocol](../experiments/exp02-inference/PROTOCOL.md),
[frozen schedule](../experiments/exp02-inference/schedule.json),
[sanitized JSONL](../results/public/exp02-inference.jsonl), and
[summary JSON](../results/summary/exp02-inference.json) provide the
reproducibility trail.

Each mean uses five paired measurements. The public [TTFT figure](../results/summary/exp02-charts/exp02-ttft-by-context.svg)
and [raw-MLX throughput figure](../results/summary/exp02-charts/exp02-mlx-generation-throughput.svg)
show mean ±1 sample standard deviation.

Raw MLX native generation throughput declined from 74.7 tokens/second at ~2K,
to 55.0 at ~16K, and 37.1 at ~32K. The runtime gap was modest next to the
context-scaling effect. Keeping an agent's context compact may therefore matter
more than choosing between these two inference paths.

## Agent baseline

| Experiment | Task | Correct reasoning/edit | Verification | Overall |
| --- | --- | --- | --- | --- |
| Exp 03 | Read-only repository operator | 3/3 correct diagnoses | 0/3 canonical gate | 0/3 |
| Exp 04 | Bounded calculator repair | 3/3 correct repairs | 0/3 verified | 0/3 |
| Exp 06b | Molecule Triage implementation | incomplete | no gate | 0/1 |

A strict definition of success was used: a correct code edit without execution
of the required verification gate counted as a failure. In Exp 04, two of three
attempts incorrectly claimed that tests had passed.

The initial interpretation is not that the local model cannot code. It could
identify the defect and generate the small repair. In these baseline tasks, the
dominant failures were repository-interface discovery and verification
discipline rather than defect diagnosis or code generation: correct code is not
the same as trustworthy completion.

## Limitations

The 16K and 32K runtime observations have different output lengths between the
runtimes, so total wall time is not a clean apples-to-apples runtime metric.
LM Studio did not expose native generation throughput. Exp 06b is only one
controlled attempt so far. These are baseline measurements, not claims of
statistical significance.

## Next controlled comparison

Hold the model, runtime, and Exp03/04 fixtures constant, and vary only the
agent harness. That directly tests whether the verification failures originate
primarily in the model or in the orchestration layer.
