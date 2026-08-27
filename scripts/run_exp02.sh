#!/usr/bin/env bash
# Shell owns runtime residency; run_exp02.py owns measurement and JSONL serialization.
set -euo pipefail

usage() {
  echo "usage: $0 --model-dir PATH [--smoke] [--schedule PATH] [--output PATH] [--lmstudio-model NAME]"
}

MODEL_DIR=""
SCHEDULE="experiments/exp02-inference/schedule.json"
OUTPUT="results/raw/exp02-inference.jsonl"
MAX_TOKENS=256
KIND="official"
LMSTUDIO_MODEL="local-coder"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model-dir) MODEL_DIR="$2"; shift 2 ;;
    --schedule) SCHEDULE="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    --lmstudio-model) LMSTUDIO_MODEL="$2"; shift 2 ;;
    --smoke)
      KIND="smoke"
      SCHEDULE="experiments/exp02-inference/smoke-schedule.json"
      OUTPUT="results/raw/exp02-inference-smoke.jsonl"
      MAX_TOKENS=32
      shift
      ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$MODEL_DIR" ]]; then
  echo "--model-dir is required" >&2
  exit 2
fi
if [[ -e "$OUTPUT" ]]; then
  echo "refusing to add to existing output; raw observations are immutable: $OUTPUT" >&2
  exit 2
fi
if [[ "$KIND" == "official" ]]; then
  if [[ ! -f results/raw/exp02-inference-smoke.jsonl ]]; then
    echo "official benchmark requires a completed validated smoke output first" >&2
    exit 2
  fi
  uv run python scripts/validate_exp02_results.py \
    --schedule experiments/exp02-inference/smoke-schedule.json \
    --results results/raw/exp02-inference-smoke.jsonl --smoke
fi
if [[ "$KIND" == "smoke" && "$OUTPUT" == *"exp02-inference.jsonl" ]]; then
  echo "smoke output must not use the official output filename" >&2
  exit 2
fi

uv run python - "$SCHEDULE" "$KIND" <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, "scripts")
from exp02_common import read_json, validate_schedule

errors = validate_schedule(read_json(Path(sys.argv[1])), smoke=sys.argv[2] == "smoke")
if errors:
    raise SystemExit("invalid schedule:\n- " + "\n- ".join(errors))
PY

wait_for_lmstudio() {
  local attempts=0
  until curl --fail --silent --show-error "${LMSTUDIO_BASE_URL:-http://localhost:1234}/v1/models" >/dev/null; do
    attempts=$((attempts + 1))
    if [[ $attempts -ge 30 ]]; then
      echo "LM Studio API did not become ready" >&2
      return 1
    fi
    sleep 1
  done
}

run_lmstudio() {
  if [[ -z "${LMSTUDIO_LOAD_CMD:-}" || -z "${LMSTUDIO_UNLOAD_CMD:-}" ]]; then
    echo "LMSTUDIO_LOAD_CMD and LMSTUDIO_UNLOAD_CMD must load/unload the model" >&2
    return 2
  fi
  bash -lc "$LMSTUDIO_LOAD_CMD"
  wait_for_lmstudio
  set +e
  uv run python scripts/run_exp02.py --runtime lmstudio --condition "$1" --repetition "$2" \
    --run-order "$3" --max-tokens "$MAX_TOKENS" --output "$OUTPUT" \
    --benchmark-kind "$KIND" --lmstudio-model "$LMSTUDIO_MODEL" \
    --lmstudio-base-url "${LMSTUDIO_BASE_URL:-http://localhost:1234}"
  local status=$?
  bash -lc "$LMSTUDIO_UNLOAD_CMD"
  set -e
  return "$status"
}

while IFS=$'\t' read -r runtime condition repetition run_order; do
  echo "running $KIND: $runtime $condition repetition=$repetition order=$run_order"
  if [[ "$runtime" == "lmstudio" ]]; then
    run_lmstudio "$condition" "$repetition" "$run_order"
  else
    uv run python scripts/run_exp02.py --runtime mlx --condition "$condition" --repetition "$repetition" \
      --run-order "$run_order" --max-tokens "$MAX_TOKENS" --output "$OUTPUT" \
      --benchmark-kind "$KIND" --model-dir "$MODEL_DIR"
  fi
done < <(uv run python - "$SCHEDULE" <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, "scripts")
from exp02_common import read_json

for run in read_json(Path(sys.argv[1]))["runs"]:
    print("{runtime}\t{condition}\t{repetition}\t{run_order}".format(**run))
PY
)

if [[ "$KIND" == "smoke" ]]; then
  uv run python scripts/validate_exp02_results.py --schedule "$SCHEDULE" --results "$OUTPUT" --smoke
else
  uv run python scripts/validate_exp02_results.py --schedule "$SCHEDULE" --results "$OUTPUT"
fi
