# Experiment 01: Local Inference Smoke Test

## Question

Can the local Apple Silicon setup successfully run Qwen3-Coder-30B through LM Studio's MLX runtime at interactive speeds?

## Status

Completed.

## Classification

Observational smoke test.

This experiment was conducted during initial setup and was not designed as a controlled performance benchmark.

## Setup

- Runtime: LM Studio using MLX
- Model: Qwen3-Coder-30B
- Local identifier: `local-coder`
- Context allocation: 32,768 tokens
- Model disk footprint: approximately 17.19 GB
- Loaded memory reported by LM Studio: approximately 16.01 GiB

Exact system information is preserved in `system-info.txt`.

## Observations

Two repeated engineering-reasoning generations produced:

| Run | TTFT | Decode throughput | Prompt tokens | Output tokens |
| --- | ---: | ---: | ---: | ---: |
| A | 0.510 s | 90.60 tok/s | 68 | 221 |
| B | 2.969 s | 79.14 tok/s | 68 | 258 |

## Interpretation

The setup demonstrated sufficient local generation speed for interactive software-engineering experiments.

These values should not be interpreted as comparative benchmark results because thermal state, cache state, machine load, and run ordering were not controlled.

## Notable observation

During an earlier identity prompt, the model incorrectly claimed to be Claude.

This was treated as generated-content hallucination rather than evidence about the executing infrastructure. Runtime identity was instead verified through the locally loaded LM Studio model and localhost inference stack.

## Next Experiment

Experiment 02 will use controlled repeated measurements to compare local inference configurations under standardized prompts and context sizes.
