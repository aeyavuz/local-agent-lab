from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, Lipinski

from projects.molecule_triage.triage import DescriptorsResult, analyze_smiles, evaluate_lipinski


def test_known_molecule_descriptors_match_rdkit_oracle() -> None:
    molecule = Chem.MolFromSmiles("CCO")
    assert molecule is not None
    actual = analyze_smiles("CCO")
    assert actual.valid and actual.descriptors is not None
    assert actual.descriptors.molecular_weight == Descriptors.MolWt(molecule)
    assert actual.descriptors.clogp == Crippen.MolLogP(molecule)
    assert actual.descriptors.hbd == Lipinski.NumHDonors(molecule)
    assert actual.descriptors.hba == Lipinski.NumHAcceptors(molecule)
    assert actual.descriptors.tpsa == Descriptors.TPSA(molecule)


def test_invalid_smiles_returns_structured_failure() -> None:
    result = analyze_smiles("C1CC")
    assert not result.valid
    assert result.error is not None
    assert result.descriptors is None


def test_lipinski_threshold_boundaries() -> None:
    at_limits = DescriptorsResult(500.0, 5.0, 5, 10, 0.0)
    assert evaluate_lipinski(at_limits).passes
    assert evaluate_lipinski(DescriptorsResult(500.01, 5.0, 5, 10, 0.0)).failures == [
        "molecular_weight"
    ]
    assert evaluate_lipinski(DescriptorsResult(500.0, 5.001, 5, 10, 0.0)).failures == ["clogp"]
    assert evaluate_lipinski(DescriptorsResult(500.0, 5.0, 6, 10, 0.0)).failures == ["hbd"]
    assert evaluate_lipinski(DescriptorsResult(500.0, 5.0, 5, 11, 0.0)).failures == ["hba"]


def test_smiles_representations_are_descriptor_invariant() -> None:
    first = analyze_smiles("CCO")
    second = analyze_smiles("C(C)O")
    assert first.descriptors is not None and second.descriptors is not None
    assert first.descriptors.hbd == second.descriptors.hbd
    assert first.descriptors.hba == second.descriptors.hba
    for field in ("molecular_weight", "clogp", "tpsa"):
        assert math.isclose(
            getattr(first.descriptors, field), getattr(second.descriptors, field), abs_tol=1e-9
        )


def test_cli_writes_invalid_rows_without_overwriting(tmp_path: Path) -> None:
    input_path = tmp_path / "molecules.smi"
    output_path = tmp_path / "result.jsonl"
    input_path.write_text("CCO\nC1CC\n", encoding="utf-8")
    command = [
        sys.executable,
        "scripts/run_molecule_triage.py",
        "--input",
        str(input_path),
        "--output",
        str(output_path),
    ]
    subprocess.run(command, check=True)
    rows = output_path.read_text(encoding="utf-8").splitlines()
    assert len(rows) == 2
    assert subprocess.run(command, check=False).returncode != 0
