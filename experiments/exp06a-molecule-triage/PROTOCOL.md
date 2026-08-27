# Experiment 06a: Molecule Triage v0

RDKit is the deterministic oracle. The implementation provides a bounded
SMILES-to-JSONL pipeline, including explicit invalid-input rows. Tests compare
known molecule descriptors to RDKit, check boundary rule logic using synthetic
descriptors, and verify graph-representation invariance with a tolerance of
`1e-9` for floating-point values.

The scientific scope is intentionally limited to descriptors and Lipinski
heuristics. It does not perform PAINS, ADMET, or biological-activity prediction.
