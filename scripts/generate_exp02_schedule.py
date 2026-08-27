from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from exp02_common import CONDITIONS, RUNTIMES, SCHEDULE_VERSION, validate_schedule


def build_schedule(*, smoke: bool, seed: int) -> dict[str, object]:
    repetitions = 1 if smoke else 5
    orders = {
        1: ["lmstudio", "mlx"],
        2: ["mlx", "lmstudio"],
        3: ["lmstudio", "mlx"],
        4: ["mlx", "lmstudio"],
    }
    rng = random.Random(seed)
    runs: list[dict[str, object]] = []
    for condition in CONDITIONS:
        for repetition in range(1, repetitions + 1):
            order = orders[repetition] if repetition in orders else rng.sample(list(RUNTIMES), k=2)
            for run_order, runtime in enumerate(order, start=1):
                runs.append(
                    {
                        "runtime": runtime,
                        "condition": condition,
                        "repetition": repetition,
                        "run_order": run_order,
                    }
                )
    return {
        "schema_version": SCHEDULE_VERSION,
        "kind": "smoke" if smoke else "official",
        "seed": seed,
        "runs": runs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze an Exp 02 runtime order schedule.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--seed", type=int, default=20260823)
    args = parser.parse_args()

    if args.output.exists():
        raise SystemExit(f"refusing to overwrite frozen schedule: {args.output}")
    schedule = build_schedule(smoke=args.smoke, seed=args.seed)
    errors = validate_schedule(schedule, smoke=args.smoke)
    if errors:
        raise RuntimeError("generated invalid schedule: " + "; ".join(errors))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(schedule, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(schedule['runs'])} frozen rows to {args.output}")


if __name__ == "__main__":
    main()
