from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .models import ALLOWED_PERMUTATION_TYPES, ALLOWED_RANK_METRICS, ALLOWED_SCORING_SCHEMES, GSEA_PARAMETER_SCHEMA_VERSION


def build_gsea_parameter_manifest(
    gsea_input: dict[str, Any] | None,
    gene_set_resource: dict[str, Any] | None,
    *,
    min_gene_set_size: int = 10,
    max_gene_set_size: int = 500,
    permutation_type: str = "gene_set",
    permutation_count: int = 1000,
    random_seed: int | None = 1,
    scoring_scheme: str = "weighted",
    normalization_policy: str = "normalize_by_gene_set_size",
    p_value_threshold: float = 0.05,
    fdr_threshold: float = 0.25,
    multiple_testing_policy: str = "BH",
    gene_id_policy: str = "require_matching_gene_id_or_mapping",
    species_policy: str = "require_match_when_known",
    msigdb_license_acknowledged: bool = False,
) -> dict[str, Any]:
    gsea_input = gsea_input or {}
    gene_set_resource = gene_set_resource or {}
    manifest = {
        "schema_version": GSEA_PARAMETER_SCHEMA_VERSION,
        "created_at": _now(),
        "gsea_parameter_id": f"gsea_parameters_{uuid4().hex[:12]}",
        "gsea_input_id": str(gsea_input.get("gsea_input_id") or ""),
        "gene_set_resource_id": str(gene_set_resource.get("gene_set_resource_id") or ""),
        "source_result_id": str(gsea_input.get("source_result_id") or ""),
        "source_result_semantics": str(gsea_input.get("source_result_semantics") or ""),
        "rank_metric": str(gsea_input.get("rank_metric") or ""),
        "rank_metric_policy": str(gsea_input.get("rank_metric_policy") or "gsea_preranked_metric_gate_only_no_execution"),
        "min_gene_set_size": min_gene_set_size,
        "max_gene_set_size": max_gene_set_size,
        "permutation_type": permutation_type,
        "permutation_count": permutation_count,
        "random_seed": random_seed,
        "scoring_scheme": scoring_scheme,
        "normalization_policy": normalization_policy,
        "p_value_threshold": p_value_threshold,
        "fdr_threshold": fdr_threshold,
        "multiple_testing_policy": multiple_testing_policy,
        "gene_id_policy": gene_id_policy,
        "species_policy": species_policy,
        "msigdb_license_acknowledged": msigdb_license_acknowledged,
        "warnings": [],
        "blockers": [],
    }
    validation = validate_gsea_parameter_manifest(manifest, gsea_input=gsea_input, gene_set_resource=gene_set_resource)
    manifest["warnings"] = validation["warnings"]
    manifest["blockers"] = validation["blockers"]
    manifest["status"] = validation["status"]
    return manifest


def validate_gsea_parameter_manifest(
    manifest: dict[str, Any],
    *,
    gsea_input: dict[str, Any] | None = None,
    gene_set_resource: dict[str, Any] | None = None,
) -> dict[str, Any]:
    gsea_input = gsea_input or {}
    gene_set_resource = gene_set_resource or {}
    blockers: list[str] = []
    warnings: list[str] = []
    if not manifest.get("source_result_id"):
        blockers.append("gsea_parameter_missing_source_result")
    if str(gsea_input.get("source_task_type") or "") != "deg":
        blockers.append("gsea_parameter_source_result_not_deg")
    if str(gsea_input.get("source_result_semantics") or "") not in {"formal_computed_result", "imported_external_result"}:
        blockers.append("gsea_parameter_source_semantics_not_allowed")
    if gsea_input.get("status") != "passed":
        blockers.extend(str(item) for item in gsea_input.get("blockers", []) or ["gsea_input_gate_not_passed"])
    if str(manifest.get("rank_metric") or "") not in ALLOWED_RANK_METRICS:
        blockers.append("gsea_parameter_invalid_rank_metric")
    if int(gsea_input.get("ranked_gene_count") or 0) <= 0:
        blockers.append("gsea_parameter_ranked_gene_list_missing")
    if not manifest.get("gene_set_resource_id"):
        blockers.append("gsea_parameter_missing_gene_set_resource")
    if gene_set_resource.get("status") != "passed":
        blockers.extend(str(item) for item in gene_set_resource.get("blockers", []) or ["gsea_gene_set_gate_not_passed"])
    if int(manifest.get("min_gene_set_size") or 0) <= 0 or int(manifest.get("max_gene_set_size") or 0) <= 0 or int(manifest.get("min_gene_set_size") or 0) > int(manifest.get("max_gene_set_size") or 0):
        blockers.append("gsea_parameter_gene_set_size_bounds_invalid")
    if str(manifest.get("permutation_type") or "") not in ALLOWED_PERMUTATION_TYPES:
        blockers.append("gsea_parameter_permutation_type_not_allowed")
    if int(manifest.get("permutation_count") or 0) <= 0:
        blockers.append("gsea_parameter_permutation_count_invalid")
    if manifest.get("random_seed") is None or str(manifest.get("random_seed")) == "":
        blockers.append("gsea_parameter_random_seed_missing")
    if str(manifest.get("scoring_scheme") or "") not in ALLOWED_SCORING_SCHEMES:
        blockers.append("gsea_parameter_scoring_scheme_not_allowed")
    blockers.extend(_threshold_blockers("p_value_threshold", manifest.get("p_value_threshold")))
    blockers.extend(_threshold_blockers("fdr_threshold", manifest.get("fdr_threshold")))
    if not str(manifest.get("multiple_testing_policy") or "").strip():
        blockers.append("gsea_parameter_missing_multiple_testing_policy")
    if not str(manifest.get("normalization_policy") or "").strip():
        blockers.append("gsea_parameter_missing_normalization_policy")
    msigdb_warnings = [str(item) for item in gene_set_resource.get("warnings", []) or [] if "msigdb" in str(item).lower()]
    if msigdb_warnings:
        warnings.extend(msigdb_warnings)
        if not manifest.get("msigdb_license_acknowledged"):
            blockers.append("gsea_msigdb_license_or_source_unacknowledged")
    warnings.extend(str(item) for item in gsea_input.get("warnings", []) or [])
    warnings.extend(str(item) for item in gene_set_resource.get("warnings", []) or [])
    return {"status": "blocked" if blockers else "passed", "blockers": list(dict.fromkeys(blockers)), "warnings": list(dict.fromkeys(warnings))}


def _threshold_blockers(name: str, value: object) -> list[str]:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return [f"gsea_parameter_{name}_invalid"]
    if number < 0 or number > 1:
        return [f"gsea_parameter_{name}_invalid"]
    return []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
