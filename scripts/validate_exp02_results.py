from __future__ import annotations

import argparse
from pathlib import Path

from exp02_common import load_jsonl, read_json, validate_results


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate append-only Exp 02 observations.")
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    schedule = read_json(args.schedule)
    rows = load_jsonl(args.results)
    errors = validate_results(rows, schedule=schedule, smoke=args.smoke)
    if errors:
        raise SystemExit("invalid Exp 02 results:\n- " + "\n- ".join(errors))
    print(f"valid: {len(rows)} append-only observation(s)")


if __name__ == "__main__":
    main()
