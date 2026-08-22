# Experiment Result Schema

Every measured benchmark run should record the following fields where applicable.

## Experiment

- experiment_id
- timestamp
- run_id
- notes

## Hardware

- machine
- chip
- memory_gb
- macos_version

## Runtime

- runtime
- runtime_version
- model
- model_checkpoint
- model_format
- quantization
- context_length

## Prompt

- prompt_id
- prompt_hash
- prompt_tokens

## Generation

- output_tokens
- ttft_seconds
- prefill_tokens_per_second
- decode_tokens_per_second
- wall_time_seconds

## System State

- memory_pressure_before
- memory_pressure_after
- swap_before
- swap_after
- run_order

## Evaluation

- success
- verification_method
- human_interventions
- policy_violations

Fields that cannot be measured by a runtime should be stored as null rather than estimated.
