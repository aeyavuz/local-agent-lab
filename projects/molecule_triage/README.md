# Molecule Triage v0

This is a deliberately small controlled scientific benchmark:

`SMILES → RDKit parsing → descriptors → Lipinski evaluation → JSONL`

For every valid input it records molecular weight, cLogP, HBD, HBA, TPSA,
individual Rule-of-Five failures, and a summary pass/fail value. Invalid or
chemically invalid SMILES produce a structured failure row and do not stop a
batch.

Run it without overwriting prior raw data:

```sh
uv run python scripts/run_molecule_triage.py --input molecules.smi --output results/raw/exp06a-run-001.jsonl
```

Lipinski criteria are heuristics, not a decision rule: a failure does not make a
molecule non-viable. This project does not predict ADMET properties or infer
biological activity. PAINS screening is intentionally deferred.
