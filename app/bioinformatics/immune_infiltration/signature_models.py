from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


ALLOWED_CATEGORIES = {"immune_cell", "checkpoint", "tme", "inflammation", "cytokine", "custom"}
ALLOWED_SPECIES = {"human", "mouse", "unknown"}


@dataclass(frozen=True)
class ImmuneSignature:
    signature_id: str
    display_name: str
    category: str
    species: str
    gene_id_type: str
    genes: tuple[str, ...]
    method_hint: str | None = None
    source_label: str = "exploratory built-in signature"
    license_note: str | None = None
    recommended_value_type: tuple[str, ...] = ("TPM", "FPKM", "FPKM-UQ", "normalized_expression", "log2_expression", "microarray_normalized")
    not_recommended_value_type: tuple[str, ...] = ("raw_counts", "unknown")
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["genes"] = list(self.genes)
        payload["recommended_value_type"] = list(self.recommended_value_type)
        payload["not_recommended_value_type"] = list(self.not_recommended_value_type)
        return payload


def normalize_gene(value: object) -> str:
    return str(value or "").strip().upper()


def normalize_signature_id(value: object) -> str:
    text = str(value or "").strip().lower()
    cleaned = "".join(char if char.isalnum() else "_" for char in text)
    return "_".join(part for part in cleaned.split("_") if part) or "signature"


def signature_from_dict(payload: dict[str, Any]) -> ImmuneSignature:
    category = str(payload.get("category") or "custom")
    species = str(payload.get("species") or "unknown")
    if category not in ALLOWED_CATEGORIES:
        raise ValueError(f"unsupported signature category: {category}")
    if species not in ALLOWED_SPECIES:
        raise ValueError(f"unsupported signature species: {species}")
    genes = tuple(dict.fromkeys(normalize_gene(gene) for gene in payload.get("genes", []) or [] if normalize_gene(gene)))
    if not genes:
        raise ValueError(f"signature has no genes: {payload.get('signature_id') or payload.get('display_name')}")
    return ImmuneSignature(
        signature_id=normalize_signature_id(payload.get("signature_id") or payload.get("display_name")),
        display_name=str(payload.get("display_name") or payload.get("signature_id") or "Immune signature"),
        category=category,
        species=species,
        gene_id_type=str(payload.get("gene_id_type") or "symbol"),
        genes=genes,
        method_hint=str(payload.get("method_hint") or "") or None,
        source_label=str(payload.get("source_label") or "exploratory built-in signature"),
        license_note=str(payload.get("license_note") or "") or None,
        recommended_value_type=tuple(str(item) for item in payload.get("recommended_value_type", []) or ImmuneSignature.__dataclass_fields__["recommended_value_type"].default),
        not_recommended_value_type=tuple(str(item) for item in payload.get("not_recommended_value_type", []) or ImmuneSignature.__dataclass_fields__["not_recommended_value_type"].default),
        notes=str(payload.get("notes") or "") or None,
    )


__all__ = [
    "ALLOWED_CATEGORIES",
    "ALLOWED_SPECIES",
    "ImmuneSignature",
    "normalize_gene",
    "normalize_signature_id",
    "signature_from_dict",
]
