from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .signature_models import ALLOWED_CATEGORIES, ImmuneSignature, normalize_gene, normalize_signature_id, signature_from_dict


BUILTIN_SIGNATURES_PATH = Path(__file__).with_name("builtin_signatures.json")


def load_builtin_signatures(path: str | Path | None = None) -> tuple[ImmuneSignature, ...]:
    source = Path(path).expanduser().resolve() if path else BUILTIN_SIGNATURES_PATH
    payload = json.loads(source.read_text(encoding="utf-8"))
    signatures = [signature_from_dict(item) for item in payload if isinstance(item, dict)]
    _validate_unique_ids(signatures)
    return tuple(signatures)


def load_signature_catalog(project_root: str | Path | None = None) -> dict[str, object]:
    signatures = list(load_builtin_signatures())
    warnings: list[str] = []
    if project_root is not None:
        custom_path = Path(project_root).expanduser().resolve() / "analysis" / "immune_infiltration" / "custom_signatures.json"
        if custom_path.exists():
            payload = json.loads(custom_path.read_text(encoding="utf-8"))
            for item in payload.get("signatures", []) if isinstance(payload, dict) else []:
                try:
                    signatures.append(signature_from_dict(item))
                except ValueError as exc:
                    warnings.append(str(exc))
    deduped = _dedupe_signatures(signatures)
    return {
        "schema_version": "biomedpilot.immune_signature_catalog.v1",
        "signatures": [signature.to_dict() for signature in deduped],
        "signature_count": len(deduped),
        "warnings": warnings,
        "limitations": [_limitations_text()],
    }


def import_gmt_signatures(path: str | Path, *, species: str = "unknown", category: str = "custom") -> dict[str, object]:
    if category not in ALLOWED_CATEGORIES:
        raise ValueError(f"unsupported signature category: {category}")
    source = Path(path).expanduser().resolve()
    signatures: list[ImmuneSignature] = []
    warnings: list[str] = []
    seen_ids: set[str] = set()
    for line_no, raw_line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            warnings.append(f"malformed_gmt_line:{line_no}")
            continue
        name, description, *genes = parts
        normalized_genes = tuple(dict.fromkeys(normalize_gene(gene) for gene in genes if normalize_gene(gene)))
        if not normalized_genes:
            warnings.append(f"empty_signature:{name or line_no}")
            continue
        base_id = normalize_signature_id(name)
        signature_id = base_id
        suffix = 2
        while signature_id in seen_ids:
            signature_id = f"{base_id}_{suffix}"
            suffix += 1
        seen_ids.add(signature_id)
        signatures.append(
            ImmuneSignature(
                signature_id=signature_id,
                display_name=name.strip() or signature_id,
                category=category,
                species=species,
                gene_id_type="symbol",
                genes=normalized_genes,
                source_label=f"custom GMT: {source.name}",
                notes=description.strip() or None,
            )
        )
    return {"signatures": [signature.to_dict() for signature in signatures], "warnings": warnings, "source_path": str(source)}


def save_custom_signatures(project_root: str | Path, signatures: list[ImmuneSignature]) -> Path:
    root = Path(project_root).expanduser().resolve()
    path = root / "analysis" / "immune_infiltration" / "custom_signatures.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"schema_version": "biomedpilot.custom_immune_signatures.v1", "signatures": [item.to_dict() for item in signatures]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def signatures_by_id(signatures: list[ImmuneSignature] | tuple[ImmuneSignature, ...]) -> dict[str, ImmuneSignature]:
    return {signature.signature_id: signature for signature in signatures}


def _validate_unique_ids(signatures: list[ImmuneSignature]) -> None:
    ids = [signature.signature_id for signature in signatures]
    duplicates = sorted({signature_id for signature_id in ids if ids.count(signature_id) > 1})
    if duplicates:
        raise ValueError("duplicate immune signature ids: " + ",".join(duplicates))


def _dedupe_signatures(signatures: list[ImmuneSignature]) -> tuple[ImmuneSignature, ...]:
    by_id: dict[str, ImmuneSignature] = {}
    for signature in signatures:
        by_id.setdefault(signature.signature_id, signature)
    return tuple(by_id[key] for key in sorted(by_id))


def _limitations_text() -> str:
    return "Exploratory built-in signatures for bulk expression scoring; not CIBERSORT/TIMER/xCell/EPIC/quanTIseq and not real immune cell proportions."


__all__ = [
    "BUILTIN_SIGNATURES_PATH",
    "import_gmt_signatures",
    "load_builtin_signatures",
    "load_signature_catalog",
    "save_custom_signatures",
    "signatures_by_id",
]
