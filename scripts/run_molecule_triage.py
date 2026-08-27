from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from projects.molecule_triage.triage import analyze_smiles  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run controlled RDKit molecule triage on one SMILES per line."
    )
    parser.add_argument(
        "--input", type=Path, required=True, help="Text file containing one SMILES per line."
    )
    parser.add_argument("--output", type=Path, required=True, help="New JSONL output path.")
    parser.add_argument(
        "--append", action="store_true", help="Explicitly append to an existing raw JSONL file."
    )
    args = parser.parse_args()
    if args.output.exists() and not args.append:
        raise SystemExit(f"refusing to overwrite raw output: {args.output}; use --append to append")
    if not args.input.is_file():
        raise SystemExit(f"input file does not exist: {args.input}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with (
        args.input.open(encoding="utf-8") as input_file,
        args.output.open("a", encoding="utf-8") as output_file,
    ):
        for raw_smiles in input_file:
            smiles = raw_smiles.strip()
            if smiles:
                output_file.write(
                    json.dumps(analyze_smiles(smiles).to_dict(), sort_keys=True) + "\n"
                )


if __name__ == "__main__":
    main()
