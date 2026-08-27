from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, Lipinski


@dataclass(frozen=True)
class DescriptorsResult:
    molecular_weight: float
    clogp: float
    hbd: int
    hba: int
    tpsa: float


@dataclass(frozen=True)
class LipinskiResult:
    failures: list[str]

    @property
    def passes(self) -> bool:
        return not self.failures


@dataclass(frozen=True)
class MoleculeResult:
    smiles: str
    valid: bool
    descriptors: DescriptorsResult | None
    lipinski: LipinskiResult | None
    error: str | None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.lipinski is not None:
            data["lipinski"]["passes"] = self.lipinski.passes
        return data


def calculate_descriptors(molecule: Chem.Mol) -> DescriptorsResult:
    """Calculate the five deterministic RDKit descriptors used by v0."""
    return DescriptorsResult(
        molecular_weight=Descriptors.MolWt(molecule),
        clogp=Crippen.MolLogP(molecule),
        hbd=Lipinski.NumHDonors(molecule),
        hba=Lipinski.NumHAcceptors(molecule),
        tpsa=Descriptors.TPSA(molecule),
    )


def evaluate_lipinski(descriptors: DescriptorsResult) -> LipinskiResult:
    """Evaluate Rule-of-Five thresholds; equal-to-threshold values pass."""
    failures: list[str] = []
    if descriptors.molecular_weight > 500.0:
        failures.append("molecular_weight")
    if descriptors.clogp > 5.0:
        failures.append("clogp")
    if descriptors.hbd > 5:
        failures.append("hbd")
    if descriptors.hba > 10:
        failures.append("hba")
    return LipinskiResult(failures=failures)


def analyze_smiles(smiles: str) -> MoleculeResult:
    """Parse one SMILES and return a structured failure instead of raising."""
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        return MoleculeResult(
            smiles=smiles,
            valid=False,
            descriptors=None,
            lipinski=None,
            error="RDKit could not parse a valid molecule from the supplied SMILES",
        )
    descriptors = calculate_descriptors(molecule)
    return MoleculeResult(
        smiles=smiles,
        valid=True,
        descriptors=descriptors,
        lipinski=evaluate_lipinski(descriptors),
        error=None,
    )
