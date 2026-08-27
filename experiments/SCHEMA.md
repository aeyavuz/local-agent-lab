# Experiment Result Schema

Every measured benchmark run should record the following fields where applicable.

Raw observations are JSONL and append-only. Derived statistics belong under
`results/summary/` and must not modify a raw record.

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

## Agent task extensions

- baseline_identity_hash
- commands_executed
- files_modified
- diagnosis
- focused_gate_status
- full_gate_status
- repair_attempts
- lines_added
- lines_removed
- unexpected_untracked_files
- configuration_changes
- frontier_escalation
- failure_category
- failure_subcategory
- failure_category_uncertain
- context_consumption: input/output tokens, model turns, completion context size
- context_failure_signals: invented path, constraint violation, repeated failure,
  or forgotten gate

Failure categories are `TOOL_FORMAT`, `CONTEXT_INSTRUCTION_LOSS`,
`KNOWLEDGE_HALLUCINATION`, `ALGORITHMIC_REASONING`,
`ENVIRONMENT_INFRASTRUCTURE`, and `SCOPE_POLICY`. Use uncertainty rather than
forcing an ambiguous classification.

`TOOL_FORMAT` may use a more specific subtype such as `INVALID_COMMAND`,
`INVALID_PATCH`, `TOOL_INVOCATION`, or `REPOSITORY_INTERFACE_DISCOVERY`.

Fields that cannot be measured by a runtime should be stored as null rather than estimated.
