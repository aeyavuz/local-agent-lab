# Experiment 04: Bounded Repair

This experiment uses a new disposable copy of the same calculator fixture as
Exp 03. It is a repair task, not a general refactoring task.

## Task

Diagnose the median failure, make the smallest valid correction, run the
focused test and `make gates`, then stop. No more than three repair attempts are
permitted. Dependency/configuration changes, unrelated edits, commits, pushes,
and merges are forbidden.

Prepare a run with:

```sh
uv run python scripts/prepare_agent_benchmark.py \
  --experiment exp04 --output-dir /tmp/local-agent-lab-exp04-run-001
```

Use the resulting `result-template.json` to record the bounded diff,
verification, attempts, intervention and escalation data, context measurements
when available, and any failure-category uncertainty.

Validate a completed result with `uv run python scripts/validate_agent_result.py
--experiment exp04 --result path/to/result.json`.
