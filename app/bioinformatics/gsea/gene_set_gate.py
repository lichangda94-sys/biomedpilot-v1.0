from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.enrichment.gene_set_gate import build_ora_gene_set_resource_gate

from .models import GSEA_GENE_SET_SCHEMA_VERSION


def build_gsea_gene_set_resource_gate(
    project_root: str | Path,
    *,
    gsea_input: dict[str, Any] | None = None,
    resource_id: str = "",
    resource_path: str | Path | None = None,
    min_gene_set_size: int = 10,
    max_gene_set_size: int = 500,
    minimum_overlap_count: int = 1,
    msigdb_license_acknowledged: bool = False,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    gsea_input = gsea_input or {}
    blockers: list[str] = []
    warnings: list[str] = []
    if min_gene_set_size <= 0 or max_gene_set_size <= 0 or min_gene_set_size > max_gene_set_size:
        blockers.append("gsea_gene_set_size_bounds_invalid")
    expected_gene_id_type = str(gsea_input.get("source_gene_id_type") or "unknown")
    base = build_ora_gene_set_resource_gate(root, resource_id=resource_id, resource_path=resource_path, expected_gene_id_type=expected_gene_id_type)
    blockers.extend(str(item).replace("ora_", "gsea_", 1) for item in base.get("blockers", []) or [])
    warnings.extend(str(item).replace("ora_", "gsea_", 1) for item in base.get("warnings", []) or [])
    path = Path(str(base.get("resource_path") or ""))
    ranked_genes = _read_ranked_genes(root, str(gsea_input.get("ranked_gene_list_path") or ""))
    gene_sets = _read_gmt(path)
    tested_terms = 0
    overlapping_terms = 0
    max_overlap = 0
    for _term_id, _term_name, genes in gene_sets:
        filtered = set(genes)
        if len(filtered) < min_gene_set_size or len(filtered) > max_gene_set_size:
            continue
        tested_terms += 1
        overlap = len(filtered & ranked_genes)
        max_overlap = max(max_overlap, overlap)
        if overlap >= minimum_overlap_count:
            overlapping_terms += 1
    if gsea_input.get("status") != "passed":
        blockers.extend(str(item) for item in gsea_input.get("blockers", []) or ["gsea_input_gate_not_passed"])
    if not ranked_genes:
        blockers.append("gsea_ranked_gene_list_missing_or_empty")
    if not gene_sets:
        blockers.append("gsea_gene_set_no_terms")
    if tested_terms <= 0:
        blockers.append("gsea_gene_set_no_terms_after_size_filter")
    if ranked_genes and gene_sets and overlapping_terms <= 0:
        blockers.append("gsea_gene_set_no_overlap_with_ranked_genes")
    if _looks_like_msigdb(base):
        warnings.append("gsea_msigdb_resource_requires_manual_license_acknowledgement")
        if not msigdb_license_acknowledged:
            blockers.append("gsea_msigdb_license_or_source_unacknowledged")
    return {
        "schema_version": GSEA_GENE_SET_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "blocked" if blockers else "passed",
        "gene_set_resource_id": str(base.get("gene_set_resource_id") or ""),
        "resource_name": str(base.get("resource_name") or ""),
        "resource_path": str(base.get("resource_path") or ""),
        "resource_format": "GMT",
        "species": str(base.get("species") or "unknown"),
        "gene_id_type": str(base.get("gene_id_type") or "unknown"),
        "term_count": int(base.get("term_count") or len(gene_sets)),
        "ranked_gene_count": len(ranked_genes),
        "tested_term_count": tested_terms,
        "overlapping_term_count": overlapping_terms,
        "max_overlap_count": max_overlap,
        "min_gene_set_size": min_gene_set_size,
        "max_gene_set_size": max_gene_set_size,
        "minimum_overlap_count": minimum_overlap_count,
        "license_warning": str(base.get("license_warning") or ""),
        "msigdb_license_acknowledged": msigdb_license_acknowledged,
        "warnings": list(dict.fromkeys(warnings)),
        "blockers": list(dict.fromkeys(blockers)),
    }


def _read_ranked_genes(root: Path, ranked_path: str) -> set[str]:
    path = Path(ranked_path).expanduser()
    path = path if path.is_absolute() else root / path
    if not path.is_file():
        return set()
    genes: set[str] = set()
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        parts = line.split("\t")
        if parts and parts[0].strip():
            genes.add(parts[0].strip())
    return genes


def _read_gmt(path: Path) -> list[tuple[str, str, list[str]]]:
    if not path.is_file():
        return []
    rows: list[tuple[str, str, list[str]]] = []
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        parts = [part.strip() for part in line.split("\t")]
        if len(parts) >= 3:
            genes = [gene for gene in parts[2:] if gene]
            if genes:
                rows.append((parts[0], parts[1], genes))
    return rows


def _looks_like_msigdb(resource: dict[str, Any]) -> bool:
    text = " ".join(str(resource.get(key) or "") for key in ("gene_set_resource_id", "resource_name", "resource_type", "collection_name", "source", "license_warning"))
    return "msigdb" in text.lower()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
