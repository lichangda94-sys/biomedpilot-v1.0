from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from .models import AnalysisAssetRef, AnalysisInputPackage, AnalysisInputResolverResult, package_status


REPOSITORY_MANIFEST = Path("standardized_data") / "repositories" / "repository_manifest.json"
STANDARDIZED_REGISTRY = Path("manifests") / "standardized_assets_registry.json"
ANALYSIS_INPUT_REPOSITORY = Path("standardized_data") / "repositories" / "analysis_input_repository"
VALIDATION_REPORT = Path("standardized_data") / "repositories" / "validation_report.json"
ASSET_LINEAGE = Path("standardized_data") / "repositories" / "asset_lineage.jsonl"
DATA_PROCESSING_TASK_PLAN = Path("manifests") / "data_processing_task_plan.json"

EXPRESSION_ASSET_TYPES = {"raw_count_matrix", "expression_matrix", "normalized_expression_matrix", "tcga_expression_matrix", "gtex_expression_matrix"}
SAMPLE_METADATA_ASSET_TYPES = {"sample_metadata", "phenotype_metadata", "tcga_sample_metadata", "gtex_sample_metadata"}
FEATURE_ASSET_TYPES = {"feature_annotation", "platform_annotation", "gene_annotation", "platform_reference_hint"}
CLINICAL_ASSET_TYPES = {"clinical_metadata", "survival_metadata", "tcga_clinical_metadata"}
IMPORTED_RESULT_ASSET_TYPES = {"differential_result_table"}
COUNT_VALUE_TYPES = {"count", "raw_count", "raw_counts", "count_like_candidate"}
DISPLAY_VALUE_TYPES = {"TPM", "FPKM", "FPKM-UQ", "CPM", "normalized", "normalized_expression", "normalized_or_log_expression", "log_expression", "log2_transformed"}
PROBE_GENE_ID_TYPES = {"probe", "probe_id", "ID_REF", "id_ref", "unknown"}
GENE_LEVEL_TYPES = {"symbol", "gene_symbol", "ensembl", "ensembl_gene_id"}


def resolve_analysis_inputs(project_root: str | Path) -> AnalysisInputResolverResult:
    root = Path(project_root).expanduser().resolve()
    repository_manifest = _read_json(root / REPOSITORY_MANIFEST)
    registry = _read_json(root / STANDARDIZED_REGISTRY)
    repository_packages = _load_repository_packages(root)
    assets = _collect_assets(repository_manifest, registry)
    default_expression = _default_expression_asset(assets, repository_manifest, registry)
    expression_assets = [asset for asset in assets if str(asset.get("asset_type") or "") in EXPRESSION_ASSET_TYPES]
    sample_asset = _first_asset(assets, SAMPLE_METADATA_ASSET_TYPES)
    group_asset = _first_asset(assets, {"group_design"})
    feature_asset = _first_asset(assets, FEATURE_ASSET_TYPES)
    clinical_asset = _first_asset(assets, CLINICAL_ASSET_TYPES)
    imported_asset = _first_asset(assets, IMPORTED_RESULT_ASSET_TYPES)
    global_blockers: list[str] = []
    global_warnings: list[str] = []
    if not repository_manifest:
        global_blockers.append("missing_repository_manifest")
    if not registry:
        global_warnings.append("missing_standardized_assets_registry")
    if len(expression_assets) > 1 and default_expression is None:
        global_blockers.append("multiple_candidate_matrices_without_default_selection")

    packages = [
        _deg_recompute_package(root, repository_manifest, repository_packages, default_expression, sample_asset, group_asset, feature_asset, global_blockers),
        _deg_imported_package(root, repository_manifest, imported_asset),
        _enrichment_from_deg_package(root, repository_manifest, imported_asset),
        _gsea_preranked_package(root, repository_manifest, imported_asset),
        _correlation_expression_package(root, repository_manifest, default_expression, feature_asset, global_blockers),
        _immune_score_linkage_package(root, repository_manifest, default_expression, feature_asset, global_blockers),
        _survival_preflight_package(root, repository_manifest, default_expression, sample_asset, clinical_asset, global_blockers),
    ]
    return AnalysisInputResolverResult(
        project_root=str(root),
        packages=tuple(packages),
        blockers=tuple(global_blockers),
        warnings=tuple(global_warnings),
        repository_manifest_path=str(root / REPOSITORY_MANIFEST),
        registry_path=str(root / STANDARDIZED_REGISTRY),
    )


def _deg_recompute_package(
    root: Path,
    repository_manifest: dict[str, Any],
    repository_packages: list[dict[str, Any]],
    expression_asset: dict[str, Any] | None,
    sample_asset: dict[str, Any] | None,
    group_asset: dict[str, Any] | None,
    feature_asset: dict[str, Any] | None,
    global_blockers: list[str],
) -> AnalysisInputPackage:
    blockers = list(global_blockers)
    warnings: list[str] = []
    if expression_asset is None:
        blockers.append("missing_expression_asset")
    if sample_asset is None:
        blockers.append("missing_sample_metadata_asset")
    if group_asset is None:
        blockers.append("missing_group_design_asset")
    value_type = _value_type(expression_asset)
    gene_id_type = _gene_id_type(expression_asset, feature_asset)
    if gene_id_type in PROBE_GENE_ID_TYPES and not _mapping_confirmed(feature_asset):
        blockers.append("geo_probe_or_id_ref_requires_platform_mapping")
    if value_type in DISPLAY_VALUE_TYPES:
        warnings.append("display_value_type_requires_controlled_two_group_method_not_count_model")
    elif value_type in COUNT_VALUE_TYPES:
        warnings.append("raw_counts_allowed_for_controlled_two_group_mvp_not_count_model")
    else:
        blockers.append("unknown_or_unsupported_value_type_for_deg")
    if _is_gtex_asset(expression_asset):
        blockers.append("gtex_must_not_auto_fill_tcga_normal_control")
    status, semantics = package_status(blockers, warnings)
    return AnalysisInputPackage(
        input_package_id=_package_id("deg_recompute", expression_asset, sample_asset, group_asset),
        package_type="deg_recompute",
        source_dataset_id=_source_dataset_id(repository_manifest, expression_asset),
        source_repository_manifest=str(root / REPOSITORY_MANIFEST),
        expression_asset=AnalysisAssetRef.from_asset(expression_asset, "expression_matrix"),
        sample_metadata_asset=AnalysisAssetRef.from_asset(sample_asset, "sample_metadata"),
        group_design_asset=AnalysisAssetRef.from_asset(group_asset, "group_design"),
        feature_annotation_asset=AnalysisAssetRef.from_asset(feature_asset, "feature_annotation"),
        value_type=value_type,
        gene_id_type=gene_id_type,
        allowed_downstream_tasks=tuple(() if blockers else ("deg_preflight",)),
        blockers=tuple(_dedupe(blockers)),
        warnings=tuple(_dedupe(warnings)),
        provenance=_provenance(repository_packages, "deg_recompute"),
        status=status,
        task_semantics=semantics,
    )


def _deg_imported_package(root: Path, repository_manifest: dict[str, Any], imported_asset: dict[str, Any] | None) -> AnalysisInputPackage:
    blockers: list[str] = []
    warnings = ["imported_deg_is_external_result_not_biomedpilot_recomputed"]
    if imported_asset is None:
        blockers.append("missing_imported_deg_result_asset")
    status, semantics = package_status(blockers, warnings, exploratory=True)
    return AnalysisInputPackage(
        input_package_id=_package_id("deg_imported_result", imported_asset),
        package_type="deg_imported_result",
        source_dataset_id=_source_dataset_id(repository_manifest, imported_asset),
        source_repository_manifest=str(root / REPOSITORY_MANIFEST),
        imported_result_asset=AnalysisAssetRef.from_asset(imported_asset, "imported_result"),
        allowed_downstream_tasks=tuple(() if blockers else ("result_browse", "enrichment_from_deg", "plot_spec_candidate")),
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        provenance={"source": "standardized imported_result_repository", "semantics": "imported_external_result"},
        status=status,
        task_semantics=semantics,
    )


def _enrichment_from_deg_package(root: Path, repository_manifest: dict[str, Any], imported_asset: dict[str, Any] | None) -> AnalysisInputPackage:
    blockers: list[str] = []
    warnings = ["enrichment_from_imported_deg_remains_external_until_result_schema_validated"]
    if imported_asset is None:
        blockers.append("missing_deg_result_for_enrichment")
    status, semantics = package_status(blockers, warnings, exploratory=True)
    return AnalysisInputPackage(
        input_package_id=_package_id("enrichment_from_deg", imported_asset),
        package_type="enrichment_from_deg",
        source_dataset_id=_source_dataset_id(repository_manifest, imported_asset),
        source_repository_manifest=str(root / REPOSITORY_MANIFEST),
        imported_result_asset=AnalysisAssetRef.from_asset(imported_asset, "imported_result"),
        allowed_downstream_tasks=tuple(() if blockers else ("ora_preflight", "gsea_prerank_candidate")),
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        provenance={"source": "deg result asset", "semantics": "inherits source DEG semantics"},
        status=status,
        task_semantics=semantics,
    )


def _gsea_preranked_package(root: Path, repository_manifest: dict[str, Any], imported_asset: dict[str, Any] | None) -> AnalysisInputPackage:
    blockers: list[str] = []
    warnings = ["gsea_preranked_requires_rank_metric_validation_in_later_stage"]
    if imported_asset is None:
        blockers.append("missing_deg_result_for_preranked_gsea")
    status, semantics = package_status(blockers, warnings, exploratory=True)
    return AnalysisInputPackage(
        input_package_id=_package_id("gsea_preranked", imported_asset),
        package_type="gsea_preranked",
        source_dataset_id=_source_dataset_id(repository_manifest, imported_asset),
        source_repository_manifest=str(root / REPOSITORY_MANIFEST),
        imported_result_asset=AnalysisAssetRef.from_asset(imported_asset, "imported_result"),
        allowed_downstream_tasks=tuple(() if blockers else ("gsea_preflight",)),
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        provenance={"source": "deg result asset", "semantics": "preflight_only"},
        status=status,
        task_semantics=semantics,
    )


def _correlation_expression_package(
    root: Path,
    repository_manifest: dict[str, Any],
    expression_asset: dict[str, Any] | None,
    feature_asset: dict[str, Any] | None,
    global_blockers: list[str],
) -> AnalysisInputPackage:
    blockers = [item for item in global_blockers if item == "multiple_candidate_matrices_without_default_selection"]
    warnings: list[str] = []
    if expression_asset is None:
        blockers.append("missing_expression_asset")
    value_type = _value_type(expression_asset)
    gene_id_type = _gene_id_type(expression_asset, feature_asset)
    if value_type in COUNT_VALUE_TYPES:
        warnings.append("raw_counts_not_recommended_for_correlation_display_without_normalization")
    elif value_type not in DISPLAY_VALUE_TYPES:
        blockers.append("unsupported_value_type_for_correlation_expression")
    status, semantics = package_status(blockers, warnings, exploratory=True)
    return AnalysisInputPackage(
        input_package_id=_package_id("correlation_expression", expression_asset),
        package_type="correlation_expression",
        source_dataset_id=_source_dataset_id(repository_manifest, expression_asset),
        source_repository_manifest=str(root / REPOSITORY_MANIFEST),
        expression_asset=AnalysisAssetRef.from_asset(expression_asset, "expression_matrix"),
        feature_annotation_asset=AnalysisAssetRef.from_asset(feature_asset, "feature_annotation"),
        value_type=value_type,
        gene_id_type=gene_id_type,
        allowed_downstream_tasks=tuple(() if blockers else ("correlation_preflight", "display")),
        blockers=tuple(_dedupe(blockers)),
        warnings=tuple(_dedupe(warnings)),
        provenance={"source": "standardized expression_repository", "semantics": "exploratory"},
        status=status,
        task_semantics=semantics,
    )


def _immune_score_linkage_package(
    root: Path,
    repository_manifest: dict[str, Any],
    expression_asset: dict[str, Any] | None,
    feature_asset: dict[str, Any] | None,
    global_blockers: list[str],
) -> AnalysisInputPackage:
    blockers = [item for item in global_blockers if item == "multiple_candidate_matrices_without_default_selection"]
    warnings = ["immune_tme_score_is_exploratory_not_deconvolution_or_clinical_conclusion"]
    if expression_asset is None:
        blockers.append("missing_expression_asset")
    value_type = _value_type(expression_asset)
    gene_id_type = _gene_id_type(expression_asset, feature_asset)
    if value_type in COUNT_VALUE_TYPES:
        blockers.append("raw_counts_not_allowed_for_immune_score_linkage")
    elif value_type not in DISPLAY_VALUE_TYPES:
        blockers.append("unsupported_value_type_for_immune_score_linkage")
    status, semantics = package_status(blockers, warnings, exploratory=True)
    return AnalysisInputPackage(
        input_package_id=_package_id("immune_score_linkage", expression_asset),
        package_type="immune_score_linkage",
        source_dataset_id=_source_dataset_id(repository_manifest, expression_asset),
        source_repository_manifest=str(root / REPOSITORY_MANIFEST),
        expression_asset=AnalysisAssetRef.from_asset(expression_asset, "expression_matrix"),
        feature_annotation_asset=AnalysisAssetRef.from_asset(feature_asset, "feature_annotation"),
        value_type=value_type,
        gene_id_type=gene_id_type,
        allowed_downstream_tasks=tuple(() if blockers else ("immune_score_preflight", "exploratory_linkage")),
        blockers=tuple(_dedupe(blockers)),
        warnings=tuple(_dedupe(warnings)),
        provenance={"source": "standardized expression_repository", "semantics": "exploratory"},
        status=status,
        task_semantics=semantics,
    )


def _survival_preflight_package(
    root: Path,
    repository_manifest: dict[str, Any],
    expression_asset: dict[str, Any] | None,
    sample_asset: dict[str, Any] | None,
    clinical_asset: dict[str, Any] | None,
    global_blockers: list[str],
) -> AnalysisInputPackage:
    blockers = [item for item in global_blockers if item == "multiple_candidate_matrices_without_default_selection"]
    warnings = ["survival_is_preflight_only_until_censoring_grouping_backend_are_validated"]
    if expression_asset is None:
        blockers.append("missing_expression_asset")
    if clinical_asset is None:
        blockers.append("missing_clinical_asset")
    if _is_gtex_asset(expression_asset):
        blockers.append("gtex_expression_cannot_be_auto_used_as_tcga_survival_normal_control")
    status, semantics = package_status(blockers, warnings)
    return AnalysisInputPackage(
        input_package_id=_package_id("tcga_clinical_survival_preflight", expression_asset, clinical_asset),
        package_type="tcga_clinical_survival_preflight",
        source_dataset_id=_source_dataset_id(repository_manifest, expression_asset),
        source_repository_manifest=str(root / REPOSITORY_MANIFEST),
        expression_asset=AnalysisAssetRef.from_asset(expression_asset, "expression_matrix"),
        sample_metadata_asset=AnalysisAssetRef.from_asset(sample_asset, "sample_metadata"),
        clinical_asset=AnalysisAssetRef.from_asset(clinical_asset, "clinical_metadata"),
        value_type=_value_type(expression_asset),
        gene_id_type=_gene_id_type(expression_asset, None),
        allowed_downstream_tasks=tuple(() if blockers else ("survival_preflight", "clinical_association_preflight")),
        blockers=tuple(_dedupe(blockers)),
        warnings=tuple(_dedupe(warnings)),
        provenance={"source": "standardized clinical_repository", "semantics": "preflight_only"},
        status=status,
        task_semantics=semantics,
    )


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_repository_packages(root: Path) -> list[dict[str, Any]]:
    packages: list[dict[str, Any]] = []
    for path in sorted((root / ANALYSIS_INPUT_REPOSITORY).glob("*.json")):
        payload = _read_json(path)
        if payload:
            payload.setdefault("path", str(path))
            packages.append(payload)
    return packages


def _collect_assets(repository_manifest: dict[str, Any], registry: dict[str, Any]) -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    for source in (repository_manifest, registry):
        for asset in source.get("assets", []) or []:
            if isinstance(asset, dict) and asset.get("asset_id"):
                assets.append(asset)
    deduped: dict[str, dict[str, Any]] = {}
    for asset in assets:
        deduped[str(asset.get("asset_id") or "")] = asset
    return list(deduped.values())


def _default_expression_asset(assets: list[dict[str, Any]], repository_manifest: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any] | None:
    expression_assets = [asset for asset in assets if str(asset.get("asset_type") or "") in EXPRESSION_ASSET_TYPES]
    selected_id = _selected_expression_id(repository_manifest) or _selected_expression_id(registry)
    if selected_id:
        for asset in expression_assets:
            if str(asset.get("asset_id") or "") == selected_id:
                return asset
    selected = [asset for asset in expression_assets if asset.get("default_selected")]
    if len(selected) == 1:
        return selected[0]
    if len(expression_assets) == 1:
        return expression_assets[0]
    return None


def _selected_expression_id(payload: dict[str, Any]) -> str:
    selection = payload.get("default_asset_selection") if isinstance(payload.get("default_asset_selection"), dict) else {}
    expression = selection.get("expression") if isinstance(selection.get("expression"), dict) else {}
    return str(expression.get("asset_id") or "")


def _first_asset(assets: list[dict[str, Any]], asset_types: set[str]) -> dict[str, Any] | None:
    for asset in assets:
        if str(asset.get("asset_type") or "") in asset_types or str(asset.get("repository") or "") in asset_types:
            return asset
    return None


def _value_type(asset: dict[str, Any] | None) -> str:
    if not isinstance(asset, dict):
        return "unknown"
    value = str(asset.get("expression_value_type") or asset.get("value_type") or "")
    if not value:
        asset_type = str(asset.get("asset_type") or "")
        if asset_type == "raw_count_matrix":
            return "count"
        if asset_type in {"normalized_expression_matrix", "gtex_expression_matrix"}:
            return "normalized_expression"
    mapping = {"raw_counts": "count", "count_like_candidate": "count", "tpm": "TPM", "fpkm": "FPKM", "fpkm-uq": "FPKM-UQ"}
    return mapping.get(value.strip().lower(), value or "unknown")


def _gene_id_type(asset: dict[str, Any] | None, feature_asset: dict[str, Any] | None) -> str:
    for source in (asset, feature_asset):
        if isinstance(source, dict):
            value = str(source.get("gene_id_type") or "")
            if value:
                return value
    return "unknown"


def _mapping_confirmed(feature_asset: dict[str, Any] | None) -> bool:
    if not isinstance(feature_asset, dict):
        return False
    if str(feature_asset.get("validation_status") or "") == "blocked":
        return False
    path = Path(str(feature_asset.get("path") or feature_asset.get("file_path") or "")).expanduser()
    if path.is_file() and path.suffix.lower() == ".json":
        payload = _read_json(path)
        if payload:
            return str(payload.get("mapping_quality") or "") == "confirmed_or_not_required" or bool(payload.get("confirmed"))
    return bool(feature_asset.get("analysis_ready"))


def _is_gtex_asset(asset: dict[str, Any] | None) -> bool:
    if not isinstance(asset, dict):
        return False
    text = " ".join(str(asset.get(key) or "") for key in ("asset_type", "source_file", "path", "label_zh", "source_acquisition_id")).lower()
    return "gtex" in text


def _source_dataset_id(repository_manifest: dict[str, Any], asset: dict[str, Any] | None) -> str:
    if isinstance(asset, dict):
        for key in ("source_acquisition_id", "asset_id"):
            value = str(asset.get(key) or "")
            if value:
                return value
    state = repository_manifest.get("source_state") if isinstance(repository_manifest.get("source_state"), dict) else {}
    return str(state.get("source_state_hash") or "")


def _package_id(package_type: str, *assets: dict[str, Any] | None) -> str:
    raw = "|".join([package_type, *[str(asset.get("asset_id") or "") for asset in assets if isinstance(asset, dict)]])
    return f"{package_type}-{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:12]}"


def _provenance(repository_packages: Iterable[dict[str, Any]], package_type: str) -> dict[str, Any]:
    for package in repository_packages:
        if str(package.get("package_type") or "") == package_type:
            return {
                "source": "analysis_input_repository",
                "legacy_package_id": package.get("package_id") or package.get("input_package_id") or "",
                "legacy_package_path": package.get("path") or "",
                "legacy_status": package.get("status") or "",
            }
    return {"source": "resolver_from_standardized_repositories"}


def _dedupe(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value)))
