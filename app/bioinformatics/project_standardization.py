from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app.bioinformatics.project_recognition import CURRENT_RECOGNITION_RUN, TYPE_LABELS
from app.bioinformatics.project_readiness import load_readiness_artifacts


STANDARDIZED_REGISTRY = Path("manifests") / "standardized_assets_registry.json"
ANALYSIS_READY_MANIFEST = Path("standardized_data") / "analysis_ready_assets" / "analysis_ready_manifest.json"
DATA_PROCESSING_TASK_PLAN = Path("manifests") / "data_processing_task_plan.json"
REPOSITORY_MANIFEST = Path("standardized_data") / "repositories" / "repository_manifest.json"
REPOSITORY_VALIDATION_REPORT = Path("standardized_data") / "repositories" / "validation_report.json"
REPOSITORY_ASSET_LINEAGE = Path("standardized_data") / "repositories" / "asset_lineage.jsonl"
ANALYSIS_INPUT_REPOSITORY = Path("standardized_data") / "repositories" / "analysis_input_repository"
EXCLUDED_STANDARDIZATION_TYPES = {
    "unknown",
    "unsupported",
    "archive",
    "archive_container",
    "geo_soft_container",
    "geo_series_matrix_container",
    "tabular_text_file",
    "differential_result_table",
    "platform_reference_hint",
}


def generate_standardized_assets(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    current_recognition = _load_current_recognition_run(root)
    recognition = current_recognition.get("recognition_report") if isinstance(current_recognition.get("recognition_report"), dict) else {}
    recognized_files = current_recognition.get("recognized_files") if isinstance(current_recognition.get("recognized_files"), dict) else {}
    files = list(recognized_files.get("files", []) or recognition.get("files", []) or []) if isinstance(recognized_files, dict) else list(recognition.get("files", []) or [])
    assets = []
    warnings = ["当前为资产注册和轻量校验，不等于正式 biological normalization。"]
    warnings.extend(str(item) for item in current_recognition.get("warnings", []) or [])
    for item in files:
        if not isinstance(item, dict):
            continue
        block_assets = _content_block_standardized_assets(item)
        if block_assets:
            assets.extend(block_assets)
            continue
        for asset_type in _asset_types_for_standardization(item):
            assets.append(
                {
                    "asset_id": _asset_id(asset_type, len(assets) + 1),
                    "asset_type": asset_type,
                    "label_zh": TYPE_LABELS.get(asset_type, "未知文件"),
                    "file_path": item.get("route_path") or item.get("original_path"),
                    "source_file": item.get("original_path"),
                    "source_container_type": item.get("recognized_type"),
                    "materialize_strategy": "reference_registered_asset",
                    "validation_status": "warning" if item.get("warning") else "registered",
                    "warning": item.get("warning") or "",
                    "analysis_ready": asset_type
                    in {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix", "sample_metadata", "phenotype_metadata", "clinical_metadata", "survival_metadata", "gmt_gene_set"},
                }
            )
    assets.extend(_supplemental_manifest_assets(root, len(assets) + 1))
    assets = _assign_unique_asset_ids(_dedupe_standardized_assets(assets))
    assets = [_normalize_repository_asset(asset) for asset in assets]
    warnings.extend(_content_block_warnings(assets))
    readiness = load_readiness_artifacts(root).get("capability_matrix") or {}
    usable = [
        str(row.get("label"))
        for row in readiness.get("rows", []) or []  # type: ignore[union-attr]
        if isinstance(row, dict) and row.get("can_run")
    ]
    missing = sorted({missing for row in readiness.get("rows", []) or [] if isinstance(row, dict) for missing in row.get("missing_inputs", []) or []})  # type: ignore[union-attr]
    default_asset_selection = _default_asset_selection(assets)
    repository_manifest = {
        "schema_version": "biomedpilot.repository_manifest.v1",
        "generated_at": _now(),
        "project_root": str(root),
        "assets": assets,
        "default_asset_selection": default_asset_selection,
        "source_state": {
            "recognition_current": current_recognition.get("current") or {},
            "source_state_hash": str((current_recognition.get("current") or {}).get("run_id") or ""),
        },
        "warnings": warnings,
    }
    analysis_input_packages = _analysis_input_packages(assets)
    registry = {
        "schema_version": "biomedpilot.standardized_assets_registry.v2",
        "generated_at": _now(),
        "project_root": str(root),
        "assets": assets,
        "standardized_assets": assets,
        "default_asset_selection": default_asset_selection,
        "current_recognition_run": current_recognition.get("current") or {},
        "warnings": warnings,
    }
    processing_plan = {
        "schema_version": "biomedpilot.data_processing_task_plan.v1",
        "generated_at": registry["generated_at"],
        "project_root": str(root),
        "tasks": _processing_tasks_from_assets(assets),
        "note": "当前生成数据处理任务清单，不等于已经执行正式 normalization 或统计分析。",
    }
    manifest = {
        "schema_version": "biomedpilot.analysis_ready_manifest.v1",
        "generated_at": registry["generated_at"],
        "exists": bool(assets),
        "standardized_assets": assets,
        "assets": assets,
        "analysis_input_packages": analysis_input_packages,
        "repository_manifest_path": str(root / REPOSITORY_MANIFEST),
        "usable_analyses": usable,
        "missing_assets": missing,
        "warnings": warnings,
    }
    _write_json(root / STANDARDIZED_REGISTRY, registry)
    _write_json(root / ANALYSIS_READY_MANIFEST, manifest)
    _write_json(root / DATA_PROCESSING_TASK_PLAN, processing_plan)
    _write_repository_state(root, repository_manifest, analysis_input_packages)
    return {
        "registry": registry,
        "analysis_ready_manifest": manifest,
        "data_processing_task_plan": processing_plan,
        "repository_manifest": repository_manifest,
    }


def _load_current_recognition_run(root: Path) -> dict[str, object]:
    current_path = root / CURRENT_RECOGNITION_RUN
    if not current_path.exists():
        legacy_report_path = root / "logs" / "recognition" / "recognition_report.json"
        if legacy_report_path.exists():
            report = _read_json(legacy_report_path)
            return {
                "current": {"recognition_report_path": str(legacy_report_path), "source": "legacy_recognition_report"},
                "recognition_report": report,
                "recognized_files": report,
                "warnings": [],
            }
        return {
            "current": None,
            "recognition_report": {},
            "recognized_files": {},
            "warnings": ["未找到当前识别批次 recognized_data/current.json。请先完成数据识别，或在历史识别记录中选择当前结果。"],
        }
    current = _read_json(current_path)
    run_dir = Path(str(current.get("run_dir") or ""))
    if not run_dir.is_absolute():
        run_dir = root / run_dir
    report_path = Path(str(current.get("recognition_report_path") or ""))
    if not report_path.is_absolute():
        report_path = root / report_path
    recognized_files_path = run_dir / "recognized_files.json"
    warnings = []
    report = _read_json(report_path) if report_path.exists() else {}
    recognized_files = _read_json(recognized_files_path) if recognized_files_path.exists() else {}
    if not report:
        warnings.append(f"当前识别批次缺少 recognition_report.json：{report_path}")
    if not recognized_files:
        warnings.append(f"当前识别批次缺少 recognized_files.json：{recognized_files_path}")
    return {
        "current": current,
        "recognition_report": report,
        "recognized_files": recognized_files,
        "warnings": warnings,
    }


def _content_block_standardized_assets(item: dict[str, object]) -> list[dict[str, object]]:
    blocks = _content_blocks(item)
    if not blocks:
        return []
    material_block_types = {"count_expression_matrix", "fpkm_expression_matrix", "tpm_expression_matrix", "deg_comparisons", "gene_annotation"}
    if not any(str(block.get("block_type") or "") in material_block_types for block in blocks):
        return []
    assets: list[dict[str, object]] = []
    has_deg_block = any(str(block.get("block_type") or "") == "deg_comparisons" for block in blocks)
    has_expression_block = any(str(block.get("block_type") or "").endswith("_expression_matrix") for block in blocks)
    source_file = str(item.get("original_path") or item.get("file_name") or "")
    file_path = str(item.get("route_path") or item.get("original_path") or "")
    species = str(item.get("species") or _profile_value(item, "species") or "")
    species_group = str(item.get("species_group") or _profile_value(item, "species_group") or "")
    gene_id_type = str(item.get("gene_id_type") or _profile_value(item, "gene_id_type") or "")
    for block in blocks:
        block_type = str(block.get("block_type") or "")
        if block_type == "count_expression_matrix":
            assets.append(
                _block_asset(
                    "count_matrix",
                    item,
                    block,
                    source_file=source_file,
                    file_path=file_path,
                    species=species,
                    species_group=species_group,
                    gene_id_type=gene_id_type,
                    recommended_for=["differential_expression", "normalization", "quality_control"],
                    label_zh="Count 表达矩阵",
                    value_type="count",
                    analysis_ready=True,
                    limitations=["重新差异分析建议优先使用 count matrix。"],
                )
            )
        elif block_type == "fpkm_expression_matrix":
            assets.append(
                _block_asset(
                    "normalized_expression_matrix",
                    item,
                    block,
                    source_file=source_file,
                    file_path=file_path,
                    species=species,
                    species_group=species_group,
                    gene_id_type=gene_id_type,
                    recommended_for=["expression_visualization", "heatmap", "correlation", "gene_expression_browse"],
                    label_zh="FPKM 表达矩阵",
                    value_type="fpkm",
                    analysis_ready=True,
                    limitations=["不建议用 FPKM 直接做 DESeq2/edgeR 式重新差异分析。"],
                )
            )
        elif block_type == "tpm_expression_matrix":
            assets.append(
                _block_asset(
                    "normalized_expression_matrix",
                    item,
                    block,
                    source_file=source_file,
                    file_path=file_path,
                    species=species,
                    species_group=species_group,
                    gene_id_type=gene_id_type,
                    recommended_for=["expression_visualization", "heatmap", "correlation", "gene_expression_browse"],
                    label_zh="TPM 表达矩阵",
                    value_type="tpm",
                    analysis_ready=True,
                    limitations=["不建议用 TPM 直接做 DESeq2/edgeR 式重新差异分析。"],
                )
            )
        elif block_type == "deg_comparisons":
            assets.append(
                _block_asset(
                    "deg_result_table",
                    item,
                    block,
                    source_file=source_file,
                    file_path=file_path,
                    species=species,
                    species_group=species_group,
                    gene_id_type=gene_id_type,
                    recommended_for=["volcano_plot", "deg_filtering", "enrichment_input", "result_browse"],
                    label_zh="已有差异分析结果",
                    analysis_ready=True,
                    source_origin="imported_deg_result",
                    limitations=["差异结果来源为导入表格；如需重新计算差异分析，请确认分组配置。"],
                )
            )
        elif block_type == "gene_annotation":
            if has_deg_block and not has_expression_block:
                continue
            assets.append(
                _block_asset(
                    "gene_annotation",
                    item,
                    block,
                    source_file=source_file,
                    file_path=file_path,
                    species=species,
                    species_group=species_group,
                    gene_id_type=gene_id_type,
                    recommended_for=["gene_symbol_mapping", "gene_description_display", "protein_coding_filter", "report_annotation"],
                    label_zh="基因注释",
                    analysis_ready=True,
                )
            )
        elif block_type == "gene_identifier":
            if has_deg_block and not has_expression_block:
                continue
            assets.append(
                _block_asset(
                    "gene_identifier_metadata",
                    item,
                    block,
                    source_file=source_file,
                    file_path=file_path,
                    species=species or str(block.get("species") or ""),
                    species_group=species_group or str(block.get("species_group") or ""),
                    gene_id_type=gene_id_type or str(block.get("gene_id_type") or ""),
                    recommended_for=["species_inference", "gene_id_tracking", "id_conversion_planning"],
                    label_zh="基因标识元数据",
                    analysis_ready=True,
                )
            )
    return assets


def _block_asset(
    asset_type: str,
    item: dict[str, object],
    block: dict[str, object],
    *,
    source_file: str,
    file_path: str,
    species: str,
    species_group: str,
    gene_id_type: str,
    recommended_for: list[str],
    label_zh: str,
    value_type: str = "",
    analysis_ready: bool = True,
    source_origin: str = "",
    limitations: list[str] | None = None,
) -> dict[str, object]:
    asset = {
        "asset_type": asset_type,
        "label_zh": label_zh,
        "file_path": file_path,
        "source_file": source_file,
        "source_container_type": item.get("recognized_type"),
        "source_file_name": item.get("file_name") or Path(source_file).name,
        "source_block_type": block.get("block_type"),
        "semantic_type": item.get("semantic_type") or _profile_value(item, "semantic_type"),
        "materialize_strategy": "content_block_reference",
        "validation_status": "registered",
        "warning": item.get("warning") or "",
        "analysis_ready": analysis_ready,
        "recommended_for": recommended_for,
        "species": species,
        "species_group": species_group,
        "gene_id_type": gene_id_type,
        "limitations": limitations or [],
    }
    if value_type:
        asset["value_type"] = value_type
    for key in (
        "sample_count",
        "sample_columns",
        "inferred_sample_ids",
        "inferred_groups",
        "replicate_count_by_group",
        "matches_count_sample_ids",
        "comparison_count",
        "complete_comparison_count",
        "comparisons",
        "annotation_fields",
        "gene_id_columns",
        "gene_name_columns",
        "example_values",
    ):
        value = block.get(key)
        if value not in (None, "", []):
            asset[key] = value
    if source_origin:
        asset["source_origin"] = source_origin
    return asset


def _normalize_repository_asset(asset: dict[str, object]) -> dict[str, object]:
    normalized = dict(asset)
    asset_type = str(normalized.get("asset_type") or "")
    source_origin = str(normalized.get("source_origin") or "")
    if source_origin == "imported_deg_result" or asset_type in {"deg_result_table", "differential_result_table"}:
        normalized.setdefault("asset_type", "differential_result_table")
        normalized["asset_role"] = "imported_result"
        normalized["repository"] = "imported_result_repository"
        normalized.setdefault("result_semantics", "imported_external_result")
    elif asset_type in {"count_matrix", "raw_count_matrix", "expression_matrix", "normalized_expression_matrix", "tcga_expression_matrix", "gtex_expression_matrix"}:
        normalized["asset_role"] = "expression_matrix"
        normalized["repository"] = "expression_repository"
    elif asset_type in {"sample_metadata", "tcga_sample_metadata", "gtex_sample_metadata", "phenotype_metadata"}:
        normalized["asset_role"] = "sample_metadata"
        normalized["repository"] = "sample_metadata_repository"
    elif asset_type in {"clinical_metadata", "survival_metadata", "tcga_clinical_metadata"}:
        normalized["asset_role"] = "clinical_metadata"
        normalized["repository"] = "clinical_repository"
    elif asset_type in {"gene_annotation", "platform_annotation", "gene_identifier_metadata"}:
        normalized["asset_role"] = "feature_annotation"
        normalized["repository"] = "feature_annotation_repository"
        if str(normalized.get("gene_id_type") or "") in {"probe_id", "ID_REF"}:
            normalized["validation_status"] = "blocked"
            normalized.setdefault("blockers", ["probe_mapping_missing"])
    elif asset_type in {"group_design", "comparison_config"}:
        normalized["asset_type"] = "group_design"
        normalized["asset_role"] = "group_design"
        normalized["repository"] = "group_design_repository"
    else:
        normalized["asset_role"] = normalized.get("asset_role") or asset_type
        normalized["repository"] = normalized.get("repository") or f"{asset_type}_repository"
    if asset_type == "count_matrix":
        normalized.setdefault("expression_value_type", "count")
    elif asset_type == "raw_count_matrix":
        normalized.setdefault("expression_value_type", "count")
    elif asset_type == "normalized_expression_matrix":
        value_type = str(normalized.get("value_type") or "")
        normalized.setdefault("expression_value_type", value_type.upper() if value_type else "normalized_expression")
    elif asset_type == "gtex_expression_matrix":
        normalized.setdefault("expression_value_type", "TPM")
    normalized.setdefault("path", normalized.get("file_path") or normalized.get("source_file") or "")
    normalized.setdefault("file_path", normalized.get("path") or normalized.get("source_file") or "")
    normalized.setdefault("validation_status", "passed" if normalized.get("analysis_ready") else "registered")
    return normalized


def _supplemental_manifest_assets(root: Path, start_index: int) -> list[dict[str, object]]:
    assets: list[dict[str, object]] = []
    group_design_path = root / "manifests" / "group_comparison_design.json"
    confirmation_path = root / "manifests" / "standardization_confirmation.json"
    confirmation = _read_json(confirmation_path) if confirmation_path.exists() else {}
    confirmed_group = confirmation.get("confirmed_group_design") if isinstance(confirmation.get("confirmed_group_design"), dict) else {}
    if group_design_path.exists() or confirmed_group.get("group_confirmed"):
        assets.append(
            {
                "asset_id": _asset_id("group_design", start_index),
                "asset_type": "group_design",
                "label_zh": "分组与比较设计",
                "file_path": str(group_design_path if group_design_path.exists() else confirmation_path),
                "source_file": str(group_design_path if group_design_path.exists() else confirmation_path),
                "materialize_strategy": "manifest_reference",
                "validation_status": "passed",
                "analysis_ready": True,
                "recommended_for": ["differential_expression"],
            }
        )
    gene = confirmation.get("gene_id_type_confirmed") if isinstance(confirmation.get("gene_id_type_confirmed"), dict) else {}
    gene_id_type = str(gene.get("gene_id_type") or "")
    if gene.get("confirmed") and gene_id_type:
        assets.append(
            {
                "asset_id": _asset_id("gene_identifier_metadata", start_index + len(assets)),
                "asset_type": "gene_identifier_metadata",
                "label_zh": "基因标识元数据",
                "file_path": str(confirmation_path),
                "source_file": str(confirmation_path),
                "materialize_strategy": "manifest_reference",
                "validation_status": "blocked" if gene.get("requires_platform_mapping") else "passed",
                "analysis_ready": True,
                "gene_id_type": gene_id_type,
                "recommended_for": ["gene_id_tracking", "id_conversion_planning"],
            }
        )
    return assets


def _default_asset_selection(assets: list[dict[str, object]]) -> dict[str, object]:
    expression_assets = [
        asset
        for asset in assets
        if str(asset.get("repository") or "") == "expression_repository"
        and str(asset.get("asset_type") or "") in {"count_matrix", "raw_count_matrix", "expression_matrix", "normalized_expression_matrix", "tcga_expression_matrix", "gtex_expression_matrix"}
    ]
    count_assets = [asset for asset in expression_assets if str(asset.get("expression_value_type") or asset.get("value_type") or "").lower() == "count"]
    selected = count_assets[0] if len(count_assets) == 1 else expression_assets[0] if len(expression_assets) == 1 else None
    if not isinstance(selected, dict):
        return {}
    selected["default_selected"] = True
    return {"expression": {"asset_id": str(selected.get("asset_id") or ""), "selection_state": "recommended_default"}}


def _analysis_input_packages(assets: list[dict[str, object]]) -> list[dict[str, object]]:
    expression_assets = [asset for asset in assets if str(asset.get("repository") or "") == "expression_repository"]
    sample_assets = [asset for asset in assets if str(asset.get("repository") or "") == "sample_metadata_repository"]
    group_assets = [asset for asset in assets if str(asset.get("repository") or "") == "group_design_repository"]
    feature_assets = [asset for asset in assets if str(asset.get("repository") or "") == "feature_annotation_repository"]
    imported_assets = [asset for asset in assets if str(asset.get("repository") or "") == "imported_result_repository"]
    packages: list[dict[str, object]] = []
    if imported_assets and not expression_assets:
        packages.append(
            {
                "package_type": "enrichment_from_imported_result",
                "status": "available",
                "task_semantics": "exploratory",
                "source_asset_id": imported_assets[0].get("asset_id", ""),
                "warnings": ["imported_deg_is_external_result_not_biomedpilot_recomputed"],
                "blockers": [],
            }
        )
        return packages
    if expression_assets:
        blockers: list[str] = []
        expression = expression_assets[0]
        gene_id_type = str(expression.get("gene_id_type") or "")
        if not sample_assets:
            blockers.append("missing_sample_metadata")
        if not group_assets:
            blockers.append("missing_group_design")
        if (gene_id_type in {"probe_id", "ID_REF"} and not feature_assets) or any(str(asset.get("validation_status") or "") == "blocked" for asset in feature_assets):
            blockers.append("probe_mapping_missing")
        packages.append(
            {
                "package_type": "deg_recompute",
                "status": "blocked" if blockers else "available",
                "task_semantics": "formal_candidate" if not blockers else "preflight_only",
                "source_asset_id": expression.get("asset_id", ""),
                "blockers": blockers,
                "warnings": [],
            }
        )
    if imported_assets:
        packages.append(
            {
                "package_type": "deg_imported_result",
                "status": "available",
                "task_semantics": "exploratory",
                "source_asset_id": imported_assets[0].get("asset_id", ""),
                "warnings": ["imported_deg_is_external_result_not_biomedpilot_recomputed"],
                "blockers": [],
            }
        )
    return packages


def _write_repository_state(root: Path, repository_manifest: dict[str, object], analysis_input_packages: list[dict[str, object]]) -> None:
    _write_repository_json(root / REPOSITORY_MANIFEST, repository_manifest)
    _write_repository_json(
        root / REPOSITORY_VALIDATION_REPORT,
        {
            "schema_version": "biomedpilot.repository_validation_report.v1",
            "generated_at": repository_manifest.get("generated_at", ""),
            "status": "passed",
            "warnings": repository_manifest.get("warnings", []),
        },
    )
    lineage_path = root / REPOSITORY_ASSET_LINEAGE
    lineage_path.parent.mkdir(parents=True, exist_ok=True)
    with lineage_path.open("w", encoding="utf-8") as handle:
        for asset in repository_manifest.get("assets", []) or []:
            if isinstance(asset, dict):
                handle.write(json.dumps({"asset_id": asset.get("asset_id", ""), "source_file": asset.get("source_file", "")}, ensure_ascii=False) + "\n")
    package_dir = root / ANALYSIS_INPUT_REPOSITORY
    package_dir.mkdir(parents=True, exist_ok=True)
    for index, package in enumerate(analysis_input_packages, start=1):
        package_id = str(package.get("package_type") or f"package_{index}")
        _write_repository_json(package_dir / f"{package_id}.json", package)


def _write_repository_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _content_blocks(item: dict[str, object]) -> list[dict[str, object]]:
    blocks = item.get("content_blocks")
    if not isinstance(blocks, list):
        profile = item.get("content_profile")
        blocks = profile.get("content_blocks") if isinstance(profile, dict) else []
    return [block for block in blocks or [] if isinstance(block, dict)]


def _profile_value(item: dict[str, object], key: str) -> object:
    profile = item.get("content_profile")
    return profile.get(key) if isinstance(profile, dict) else ""


def _asset_id(asset_type: str, index: int) -> str:
    prefix = {
        "count_matrix": "count_matrix",
        "normalized_expression_matrix": "fpkm_matrix",
        "deg_result_table": "deg_results",
        "gene_annotation": "gene_annotation",
        "gene_identifier_metadata": "gene_identifier",
    }.get(asset_type, asset_type or "asset")
    return f"{prefix}_{index:03d}"


def _assign_unique_asset_ids(assets: list[dict[str, object]]) -> list[dict[str, object]]:
    counters: dict[str, int] = {}
    assigned: set[str] = set()
    for asset in assets:
        asset_type = str(asset.get("asset_type") or "asset")
        while True:
            counters[asset_type] = counters.get(asset_type, 0) + 1
            asset_id = _asset_id(asset_type, counters[asset_type])
            if asset_id not in assigned:
                break
        asset["asset_id"] = asset_id
        assigned.add(asset_id)
    return assets


def _content_block_warnings(assets: list[dict[str, object]]) -> list[str]:
    asset_types = {str(asset.get("asset_type") or "") for asset in assets}
    warnings: list[str] = []
    if {"count_matrix", "normalized_expression_matrix"} <= asset_types:
        value_types = {str(asset.get("value_type") or "") for asset in assets}
        normalized_label = "FPKM/TPM" if {"fpkm", "tpm"} & value_types else "标准化表达矩阵"
        warnings.append(f"检测到 count 与 {normalized_label}。差异分析建议使用 count；表达展示可使用 {normalized_label}。")
    if "deg_result_table" in asset_types:
        warnings.append("文件已包含差异分析结果，可用于结果浏览、火山图和富集分析输入；如需重新计算差异分析，请确认分组配置。")
    if any(str(asset.get("species") or "") == "Mus musculus" for asset in assets):
        warnings.append("小鼠数据：适合动物模型分析、方法验证和机制探索，不应直接按人类临床队列解释。")
    return warnings


def _asset_types_for_standardization(item: dict[str, object]) -> list[str]:
    detected_assets = [asset for asset in item.get("detected_assets", []) or [] if isinstance(asset, dict)]
    if detected_assets:
        roles = []
        for asset in detected_assets:
            if asset.get("input_eligible") is False:
                continue
            role = str(asset.get("role") or asset.get("asset_type") or "")
            if role and role not in EXCLUDED_STANDARDIZATION_TYPES:
                roles.append(role)
        return list(dict.fromkeys(roles))
    roles = [str(role) for role in item.get("recognized_roles", []) or [] if str(role) and str(role) != "unknown"]
    roles.extend(str(role) for role in item.get("secondary_roles", []) or [] if str(role) and str(role) != "unknown")
    primary = str(item.get("recognized_type") or "unknown")
    if roles:
        return [role for role in dict.fromkeys(roles) if role not in EXCLUDED_STANDARDIZATION_TYPES]
    if primary in EXCLUDED_STANDARDIZATION_TYPES:
        return []
    return [primary]


def _dedupe_standardized_assets(assets: list[dict[str, object]]) -> list[dict[str, object]]:
    deduped: dict[tuple[str, str], dict[str, object]] = {}
    for asset in assets:
        asset_type = str(asset.get("asset_type") or "")
        source_file = str(asset.get("source_file") or asset.get("file_path") or "")
        path = Path(source_file).expanduser()
        key_path = str(path.resolve()) if path.exists() else source_file
        key = (asset_type, key_path, str(asset.get("source_block_type") or ""), str(asset.get("value_type") or ""))
        deduped.setdefault(key, asset)
    return list(deduped.values())


def _processing_tasks_from_assets(assets: list[dict[str, object]]) -> list[dict[str, object]]:
    tasks: list[dict[str, object]] = []
    for asset in assets:
        asset_type = str(asset.get("asset_type") or "")
        file_path = str(asset.get("file_path") or "")
        if asset_type in {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix", "count_matrix"}:
            tasks.append(_processing_task("expression_matrix_cleaning", "表达矩阵清洗", file_path, asset_type, "pending_confirmation"))
            tasks.append(_processing_task("gene_annotation_mapping", "基因注释映射", file_path, asset_type, "pending_annotation_source"))
        elif asset_type in {"platform_annotation", "gene_annotation", "platform_reference_hint"}:
            tasks.append(_processing_task("gene_annotation_mapping", "基因注释映射", file_path, asset_type, "pending_confirmation"))
        elif asset_type in {"sample_metadata", "phenotype_metadata"}:
            tasks.append(_processing_task("sample_annotation_review", "样本注释整理", file_path, asset_type, "pending_group_confirmation"))
        elif asset_type in {"clinical_metadata", "survival_metadata"}:
            tasks.append(_processing_task("clinical_metadata_standardization", "临床/生存信息整理", file_path, asset_type, "pending_field_mapping"))
    deduped: dict[tuple[str, str, str], dict[str, object]] = {}
    for task in tasks:
        key = (str(task["task_type"]), str(task["source_file"]), str(task["asset_type"]))
        deduped.setdefault(key, task)
    return list(deduped.values())


def _processing_task(task_type: str, label: str, file_path: str, asset_type: str, status: str) -> dict[str, object]:
    return {
        "task_type": task_type,
        "label": label,
        "source_file": file_path,
        "asset_type": asset_type,
        "status": status,
        "execution": "not_run",
    }


def load_standardization_artifacts(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    registry_path = root / STANDARDIZED_REGISTRY
    manifest_path = root / ANALYSIS_READY_MANIFEST
    return {
        "registry": _read_json(registry_path) if registry_path.exists() else None,
        "analysis_ready_manifest": _read_json(manifest_path) if manifest_path.exists() else None,
        "data_processing_task_plan": _read_json(root / DATA_PROCESSING_TASK_PLAN) if (root / DATA_PROCESSING_TASK_PLAN).exists() else None,
        "registry_path": str(registry_path),
        "manifest_path": str(manifest_path),
        "data_processing_task_plan_path": str(root / DATA_PROCESSING_TASK_PLAN),
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    _atomic_write_json(path, payload)


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, indent=2)
    temp_path = path.with_name(f".{path.name}.tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp_path, path)
