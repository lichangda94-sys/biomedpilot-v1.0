from __future__ import annotations

import csv
import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.project_recognition import TYPE_LABELS, load_recognition_report
from app.bioinformatics.project_readiness import load_readiness_artifacts
from app.bioinformatics.standardization_confirmation import load_standardization_confirmation_artifacts


STANDARDIZED_REGISTRY = Path("manifests") / "standardized_assets_registry.json"
ANALYSIS_READY_MANIFEST = Path("standardized_data") / "analysis_ready_assets" / "analysis_ready_manifest.json"
DATA_PROCESSING_TASK_PLAN = Path("manifests") / "data_processing_task_plan.json"
REPOSITORY_ROOT = Path("standardized_data") / "repositories"
REPOSITORY_MANIFEST = REPOSITORY_ROOT / "repository_manifest.json"
REPOSITORY_VALIDATION_REPORT = REPOSITORY_ROOT / "validation_report.json"
ASSET_LINEAGE = REPOSITORY_ROOT / "asset_lineage.jsonl"
REPOSITORY_DIRS = {
    "expression_repository": REPOSITORY_ROOT / "expression_repository",
    "sample_metadata_repository": REPOSITORY_ROOT / "sample_metadata_repository",
    "group_design_repository": REPOSITORY_ROOT / "group_design_repository",
    "feature_annotation_repository": REPOSITORY_ROOT / "feature_annotation_repository",
    "clinical_repository": REPOSITORY_ROOT / "clinical_repository",
    "imported_result_repository": REPOSITORY_ROOT / "imported_result_repository",
    "analysis_input_repository": REPOSITORY_ROOT / "analysis_input_repository",
}
EXPRESSION_ASSET_TYPES = {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix", "tcga_expression_matrix", "gtex_expression_matrix"}
SAMPLE_METADATA_ASSET_TYPES = {"sample_metadata", "phenotype_metadata", "tcga_sample_metadata", "gtex_sample_metadata"}
CLINICAL_ASSET_TYPES = {"clinical_metadata", "survival_metadata", "tcga_clinical_metadata"}
FEATURE_ASSET_TYPES = {"platform_annotation", "gene_annotation", "platform_reference_hint"}
IMPORTED_RESULT_ASSET_TYPES = {"differential_result_table"}
EXCLUDED_STANDARDIZATION_TYPES = {
    "unknown",
    "unsupported",
    "archive",
    "archive_container",
    "geo_soft_container",
    "geo_series_matrix_container",
    "tabular_text_file",
    "platform_reference_hint",
    "raw_heavy_file",
    "gdc_manifest",
}


def generate_standardized_assets(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    recognition = load_recognition_report(root) or {}
    files = list(recognition.get("files", []) or [])
    confirmation_artifacts = load_standardization_confirmation_artifacts(root)
    confirmation = confirmation_artifacts.get("confirmation") if isinstance(confirmation_artifacts.get("confirmation"), dict) else {}
    repository_bundle = _build_repository_bundle(root, recognition if isinstance(recognition, dict) else {}, files, confirmation)
    assets = repository_bundle["assets"]
    warnings = ["当前为资产注册和轻量校验，不等于正式 biological normalization。"]
    warnings.extend(str(item) for item in repository_bundle.get("warnings", []) or [])
    readiness = load_readiness_artifacts(root).get("capability_matrix") or {}
    usable = [
        str(row.get("label"))
        for row in readiness.get("rows", []) or []  # type: ignore[union-attr]
        if isinstance(row, dict) and row.get("can_run")
    ]
    missing = sorted({missing for row in readiness.get("rows", []) or [] if isinstance(row, dict) for missing in row.get("missing_inputs", []) or []})  # type: ignore[union-attr]
    registry = {
        "schema_version": "biomedpilot.standardized_assets_registry.v2",
        "generated_at": repository_bundle["generated_at"],
        "project_root": str(root),
        "assets": assets,
        "repositories": repository_bundle["repository_summary"],
        "default_asset_selection": repository_bundle["default_asset_selection"],
        "source_state": repository_bundle["source_state"],
        "repository_manifest_path": str(root / REPOSITORY_MANIFEST),
        "validation_report_path": str(root / REPOSITORY_VALIDATION_REPORT),
        "asset_lineage_path": str(root / ASSET_LINEAGE),
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
        "schema_version": "biomedpilot.analysis_ready_manifest.v2",
        "generated_at": registry["generated_at"],
        "exists": bool(assets),
        "usable_analyses": usable,
        "missing_assets": missing,
        "analysis_input_packages": repository_bundle["analysis_input_packages"],
        "analysis_input_repository": str(root / REPOSITORY_DIRS["analysis_input_repository"]),
        "default_asset_selection": repository_bundle["default_asset_selection"],
        "warnings": warnings,
    }
    repository_manifest = {
        "schema_version": "biomedpilot.repository_manifest.v1",
        "generated_at": registry["generated_at"],
        "project_root": str(root),
        "source_state": repository_bundle["source_state"],
        "repositories": repository_bundle["repository_summary"],
        "assets": assets,
        "analysis_input_packages": repository_bundle["analysis_input_packages"],
        "biological_normalization_performed": False,
        "normalization_boundary": "standardized repositories organize files into internal format; they do not perform biological normalization.",
    }
    validation_report = {
        "schema_version": "biomedpilot.repository_validation_report.v1",
        "generated_at": registry["generated_at"],
        "overall_status": repository_bundle["validation_status"],
        "issues": repository_bundle["validation_issues"],
        "asset_validation": repository_bundle["asset_validation"],
    }
    _write_repository_outputs(root, repository_manifest, validation_report, repository_bundle["lineage"])
    _write_json(root / STANDARDIZED_REGISTRY, registry)
    _write_json(root / ANALYSIS_READY_MANIFEST, manifest)
    _write_json(root / DATA_PROCESSING_TASK_PLAN, processing_plan)
    return {
        "registry": registry,
        "analysis_ready_manifest": manifest,
        "data_processing_task_plan": processing_plan,
        "repository_manifest": repository_manifest,
        "validation_report": validation_report,
    }


def _asset_types_for_standardization(item: dict[str, object]) -> list[str]:
    detected_assets = [asset for asset in item.get("detected_assets", []) or [] if isinstance(asset, dict)]
    if detected_assets:
        roles = []
        for asset in detected_assets:
            role = str(asset.get("role") or asset.get("asset_type") or "")
            if asset.get("input_eligible") is False and role not in IMPORTED_RESULT_ASSET_TYPES:
                continue
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


def _build_repository_bundle(root: Path, recognition: dict[str, object], files: list[object], confirmation: dict[str, object]) -> dict[str, Any]:
    generated_at = _now()
    for directory in REPOSITORY_DIRS.values():
        (root / directory).mkdir(parents=True, exist_ok=True)
    assets: list[dict[str, object]] = []
    validation_issues: list[dict[str, object]] = []
    asset_validation: dict[str, object] = {}
    lineage: list[dict[str, object]] = []
    for record in files:
        if not isinstance(record, dict):
            continue
        for asset_type in _asset_types_for_standardization(record):
            repository = _repository_for_asset_type(asset_type)
            if not repository:
                continue
            asset_id = _asset_id(record, asset_type)
            source_path = Path(str(record.get("original_path") or "")).expanduser()
            output_path = _materialize_repository_asset(root, repository, asset_id, asset_type, source_path, record)
            validation = _validate_repository_asset(asset_type, source_path, record, confirmation)
            asset_validation[asset_id] = validation
            validation_issues.extend(dict(issue, asset_id=asset_id, asset_type=asset_type) for issue in validation.get("issues", []) or [] if isinstance(issue, dict))
            asset = _repository_asset_record(
                root,
                asset_id=asset_id,
                repository=repository,
                asset_type=asset_type,
                source_path=source_path,
                output_path=output_path,
                record=record,
                confirmation=confirmation,
                validation=validation,
            )
            assets.append(asset)
            lineage.append(_lineage_record(asset, record, confirmation))
    assets.extend(_derived_assets_from_confirmation(root, confirmation, recognition, validation_issues, asset_validation, lineage))
    assets = _dedupe_standardized_assets(assets)
    default_selection = _default_asset_selection(assets, confirmation)
    analysis_input_packages = _analysis_input_packages(root, assets, confirmation, default_selection, validation_issues)
    repository_summary = _repository_summary(assets)
    warnings = [str(issue.get("message") or issue.get("code") or "") for issue in validation_issues if issue.get("severity") in {"warning", "error", "blocker"}]
    validation_status = "passed"
    if any(issue.get("severity") in {"blocker", "error"} for issue in validation_issues):
        validation_status = "blocked"
    elif validation_issues:
        validation_status = "warning"
    return {
        "generated_at": generated_at,
        "assets": assets,
        "repository_summary": repository_summary,
        "default_asset_selection": default_selection,
        "analysis_input_packages": analysis_input_packages,
        "validation_status": validation_status,
        "validation_issues": validation_issues,
        "asset_validation": asset_validation,
        "lineage": lineage,
        "warnings": list(dict.fromkeys(warnings)),
        "source_state": _source_state(recognition, confirmation),
    }


def _repository_for_asset_type(asset_type: str) -> str:
    if asset_type in EXPRESSION_ASSET_TYPES:
        return "expression_repository"
    if asset_type in SAMPLE_METADATA_ASSET_TYPES:
        return "sample_metadata_repository"
    if asset_type in CLINICAL_ASSET_TYPES:
        return "clinical_repository"
    if asset_type in FEATURE_ASSET_TYPES:
        return "feature_annotation_repository"
    if asset_type in IMPORTED_RESULT_ASSET_TYPES:
        return "imported_result_repository"
    if asset_type == "gmt_gene_set":
        return "feature_annotation_repository"
    return ""


def _asset_id(record: dict[str, object], asset_type: str) -> str:
    raw = "|".join(
        [
            asset_type,
            str(record.get("original_path") or record.get("file_name") or ""),
            str(record.get("recognition_run_id") or ""),
        ]
    )
    return f"{asset_type}-{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:12]}"


def _materialize_repository_asset(root: Path, repository: str, asset_id: str, asset_type: str, source_path: Path, record: dict[str, object]) -> Path:
    target_dir = root / REPOSITORY_DIRS[repository]
    if asset_type in EXPRESSION_ASSET_TYPES and source_path.exists() and _is_tabular_text_path(source_path):
        target = target_dir / f"{asset_id}.matrix.tsv"
        _write_canonical_matrix(source_path, target)
        _write_json(target_dir / f"{asset_id}.metadata.json", _asset_sidecar(record, asset_type, source_path, target))
        return target
    if source_path.exists() and _is_tabular_text_path(source_path) and repository in {"sample_metadata_repository", "clinical_repository", "imported_result_repository", "feature_annotation_repository"}:
        suffix = "tsv" if repository != "imported_result_repository" else "imported.tsv"
        target = target_dir / f"{asset_id}.{suffix}"
        _write_tsv_copy(source_path, target)
        _write_json(target_dir / f"{asset_id}.metadata.json", _asset_sidecar(record, asset_type, source_path, target))
        return target
    target = target_dir / f"{asset_id}.asset.json"
    _write_json(target, _asset_sidecar(record, asset_type, source_path, source_path if source_path.exists() else target))
    return target


def _asset_sidecar(record: dict[str, object], asset_type: str, source_path: Path, materialized_path: Path) -> dict[str, object]:
    return {
        "schema_version": "biomedpilot.repository_asset_sidecar.v1",
        "asset_type": asset_type,
        "source_file": str(source_path),
        "materialized_path": str(materialized_path),
        "recognition_run_id": record.get("recognition_run_id") or "",
        "matrix_profile": record.get("matrix_profile") if isinstance(record.get("matrix_profile"), dict) else {},
        "metadata_profile": record.get("metadata_profile") if isinstance(record.get("metadata_profile"), dict) else {},
        "biological_normalization_performed": False,
    }


def _repository_asset_record(
    root: Path,
    *,
    asset_id: str,
    repository: str,
    asset_type: str,
    source_path: Path,
    output_path: Path,
    record: dict[str, object],
    confirmation: dict[str, object],
    validation: dict[str, object],
) -> dict[str, object]:
    stats = _path_stats(output_path)
    role = _asset_role(asset_type)
    warnings = [str(issue.get("message") or issue.get("code") or "") for issue in validation.get("issues", []) or [] if isinstance(issue, dict)]
    return {
        "asset_id": asset_id,
        "repository": repository,
        "asset_role": role,
        "asset_type": asset_type,
        "label_zh": TYPE_LABELS.get(asset_type, asset_type),
        "source_file": str(source_path),
        "source_acquisition_id": _source_acquisition_id(record),
        "source_recognition_run_id": str(record.get("recognition_run_id") or ""),
        "confirmation_id": _confirmation_id(confirmation),
        "path": str(output_path),
        "file_path": str(output_path),
        "format": _asset_format(output_path, asset_type),
        "checksum": stats.get("sha256", ""),
        "size": stats.get("size_bytes", 0),
        "size_bytes": stats.get("size_bytes", 0),
        "row_count": validation.get("row_count", 0),
        "column_count": validation.get("column_count", 0),
        "validation_status": validation.get("status", "registered"),
        "warnings": warnings,
        "warning": "；".join(warnings),
        "consumable_by": _consumable_by(asset_type, validation),
        "analysis_ready": asset_type in {
            *EXPRESSION_ASSET_TYPES,
            *SAMPLE_METADATA_ASSET_TYPES,
            *CLINICAL_ASSET_TYPES,
            "gmt_gene_set",
            *IMPORTED_RESULT_ASSET_TYPES,
        },
        "materialize_strategy": "standard_repository_asset",
        "biological_normalization_performed": False,
        "normalization_boundary": "整理成 BioMedPilot 内部标准格式；未执行生物学 normalization。",
        "source_container_type": record.get("recognized_type"),
        "expression_value_type": _confirmed_value_type(asset_type, record, confirmation),
        "gene_id_type": _confirmed_gene_id_type(record, confirmation),
        "default_selected": False,
    }


def _derived_assets_from_confirmation(
    root: Path,
    confirmation: dict[str, object],
    recognition: dict[str, object],
    validation_issues: list[dict[str, object]],
    asset_validation: dict[str, object],
    lineage: list[dict[str, object]],
) -> list[dict[str, object]]:
    assets: list[dict[str, object]] = []
    group = confirmation.get("confirmed_group_design") if isinstance(confirmation.get("confirmed_group_design"), dict) else {}
    if group.get("group_confirmed"):
        asset_id = f"group_design-{_confirmation_id(confirmation)}"
        target = root / REPOSITORY_DIRS["group_design_repository"] / f"{asset_id}.json"
        payload = {
            "schema_version": "biomedpilot.group_design_asset.v1",
            "group_design": group,
            "source": group.get("source") or "standardization_confirmation",
            "recognition_run_id": recognition.get("recognition_run_id") or "",
        }
        _write_json(target, payload)
        validation = {"status": "passed", "issues": [], "row_count": len(group.get("sample_group_assignments", {}) or {}), "column_count": 2}
        asset_validation[asset_id] = validation
        asset = {
            "asset_id": asset_id,
            "repository": "group_design_repository",
            "asset_role": "group_design",
            "asset_type": "group_design",
            "label_zh": "分组比较设计",
            "source_file": "standardization_confirmation.json",
            "source_acquisition_id": "",
            "source_recognition_run_id": str(recognition.get("recognition_run_id") or ""),
            "confirmation_id": _confirmation_id(confirmation),
            "path": str(target),
            "file_path": str(target),
            "format": "json",
            "checksum": _path_stats(target).get("sha256", ""),
            "size_bytes": _path_stats(target).get("size_bytes", 0),
            "row_count": validation["row_count"],
            "column_count": validation["column_count"],
            "validation_status": "passed",
            "warnings": [],
            "warning": "",
            "consumable_by": ["differential_expression"],
            "analysis_ready": True,
            "materialize_strategy": "derived_from_user_confirmation",
            "biological_normalization_performed": False,
            "default_selected": True,
        }
        assets.append(asset)
        lineage.append(_lineage_record(asset, {}, confirmation))
        assignments = group.get("sample_group_assignments") if isinstance(group.get("sample_group_assignments"), dict) else {}
        if assignments:
            sample_id = f"sample_metadata-{_confirmation_id(confirmation)}"
            sample_target = root / REPOSITORY_DIRS["sample_metadata_repository"] / f"{sample_id}.tsv"
            with sample_target.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle, delimiter="\t")
                writer.writerow(["sample_id", "group"])
                for sample, group_name in assignments.items():
                    writer.writerow([sample, group_name])
            sample_validation = {"status": "passed", "issues": [], "row_count": len(assignments), "column_count": 2}
            asset_validation[sample_id] = sample_validation
            sample_asset = {
                "asset_id": sample_id,
                "repository": "sample_metadata_repository",
                "asset_role": "sample_metadata",
                "asset_type": "sample_metadata",
                "label_zh": "样本注释",
                "source_file": "confirmed_group_design",
                "source_acquisition_id": "",
                "source_recognition_run_id": str(recognition.get("recognition_run_id") or ""),
                "confirmation_id": _confirmation_id(confirmation),
                "path": str(sample_target),
                "file_path": str(sample_target),
                "format": "tsv",
                "checksum": _path_stats(sample_target).get("sha256", ""),
                "size_bytes": _path_stats(sample_target).get("size_bytes", 0),
                "row_count": sample_validation["row_count"],
                "column_count": sample_validation["column_count"],
                "validation_status": "passed",
                "warnings": [],
                "warning": "",
                "consumable_by": ["differential_expression"],
                "analysis_ready": True,
                "materialize_strategy": "derived_from_group_design",
                "biological_normalization_performed": False,
                "default_selected": True,
            }
            assets.append(sample_asset)
            lineage.append(_lineage_record(sample_asset, {}, confirmation))
    gene = confirmation.get("gene_id_type_confirmed") if isinstance(confirmation.get("gene_id_type_confirmed"), dict) else {}
    platform = confirmation.get("platform_annotation_confirmed") if isinstance(confirmation.get("platform_annotation_confirmed"), dict) else {}
    if gene:
        asset_id = f"feature_annotation-{_confirmation_id(confirmation)}"
        target = root / REPOSITORY_DIRS["feature_annotation_repository"] / f"{asset_id}.json"
        requires_mapping = bool(gene.get("requires_platform_mapping"))
        issue = None
        if requires_mapping and not platform.get("confirmed"):
            issue = {
                "severity": "blocker",
                "code": "probe_mapping_missing",
                "message": "probe/ID_REF 需要平台注释确认，当前缺少 mapping。",
                "repository": "feature_annotation_repository",
            }
            validation_issues.append(issue)
        _write_json(
            target,
            {
                "schema_version": "biomedpilot.feature_annotation_asset.v1",
                "gene_id_type": gene.get("gene_id_type") or "",
                "confirmed": bool(gene.get("confirmed")),
                "requires_platform_mapping": requires_mapping,
                "platform_annotation_confirmed": platform,
                "mapping_quality": "missing" if issue else "confirmed_or_not_required",
            },
        )
        validation = {"status": "blocked" if issue else "passed", "issues": [issue] if issue else [], "row_count": 0, "column_count": 0}
        asset_validation[asset_id] = validation
        asset = {
            "asset_id": asset_id,
            "repository": "feature_annotation_repository",
            "asset_role": "feature_annotation",
            "asset_type": "feature_annotation",
            "label_zh": "基因/探针注释状态",
            "source_file": "standardization_confirmation.json",
            "source_acquisition_id": "",
            "source_recognition_run_id": str(recognition.get("recognition_run_id") or ""),
            "confirmation_id": _confirmation_id(confirmation),
            "path": str(target),
            "file_path": str(target),
            "format": "json",
            "checksum": _path_stats(target).get("sha256", ""),
            "size_bytes": _path_stats(target).get("size_bytes", 0),
            "row_count": 0,
            "column_count": 0,
            "validation_status": validation["status"],
            "warnings": [issue["message"]] if issue else [],
            "warning": issue["message"] if issue else "",
            "consumable_by": [] if issue else ["differential_expression", "enrichment", "correlation"],
            "analysis_ready": not bool(issue),
            "materialize_strategy": "derived_from_user_confirmation",
            "biological_normalization_performed": False,
            "default_selected": True,
        }
        assets.append(asset)
        lineage.append(_lineage_record(asset, {}, confirmation))
    return assets


def _validate_repository_asset(asset_type: str, source_path: Path, record: dict[str, object], confirmation: dict[str, object]) -> dict[str, object]:
    issues: list[dict[str, object]] = []
    row_count = 0
    column_count = 0
    if asset_type in EXPRESSION_ASSET_TYPES and source_path.exists() and _is_tabular_text_path(source_path):
        profile = _scan_expression_table(source_path, asset_type)
        row_count = int(profile.get("row_count") or 0)
        column_count = int(profile.get("column_count") or 0)
        issues.extend(profile.get("issues", []) or [])
        sample_columns = [str(item) for item in profile.get("sample_columns", []) or []]
        _validate_sample_alignment(sample_columns, confirmation, issues)
    if asset_type in EXPRESSION_ASSET_TYPES:
        value_type = _confirmed_value_type(asset_type, record, confirmation)
        if value_type in {"", "unknown", "unknown_expression_value"}:
            issues.append({"severity": "blocker", "code": "unknown_value_type", "message": "表达值类型未确认，不能生成 analysis input package。"})
        gene_type = _confirmed_gene_id_type(record, confirmation)
        platform = confirmation.get("platform_annotation_confirmed") if isinstance(confirmation.get("platform_annotation_confirmed"), dict) else {}
        if gene_type in {"probe_id", "unknown"} and not platform.get("confirmed"):
            issues.append({"severity": "blocker", "code": "probe_mapping_missing", "message": "probe/ID_REF 缺少平台注释 mapping，阻断重新计算 DEG input。"})
    status = "passed"
    if any(issue.get("severity") in {"blocker", "error"} for issue in issues if isinstance(issue, dict)):
        status = "blocked"
    elif issues:
        status = "warning"
    return {"status": status, "issues": issues, "row_count": row_count, "column_count": column_count}


def _validate_sample_alignment(sample_columns: list[str], confirmation: dict[str, object], issues: list[dict[str, object]]) -> None:
    group = confirmation.get("confirmed_group_design") if isinstance(confirmation.get("confirmed_group_design"), dict) else {}
    assignments = group.get("sample_group_assignments") if isinstance(group.get("sample_group_assignments"), dict) else {}
    if not assignments:
        return
    expression_samples = set(sample_columns)
    assignment_samples = {str(sample) for sample in assignments}
    matched = expression_samples & assignment_samples
    if not matched:
        issues.append({"severity": "blocker", "code": "sample_mismatch", "message": "表达矩阵样本列与用户确认分组完全不匹配。"})
    elif matched != expression_samples:
        issues.append({"severity": "warning", "code": "sample_partial_match", "message": "表达矩阵样本列与用户确认分组部分匹配；未匹配样本只能作为参考。"})


def _scan_expression_table(source_path: Path, asset_type: str) -> dict[str, object]:
    issues: list[dict[str, object]] = []
    row_count = 0
    column_count = 0
    seen: set[str] = set()
    duplicates: set[str] = set()
    sample_columns: list[str] = []
    try:
        rows_iter = _iter_matrix_rows(source_path)
        header = next(rows_iter, [])
        if header:
            column_count = len(header)
            sample_columns = [str(item) for item in header[1:]]
        for row in rows_iter:
            if not row:
                continue
            row_count += 1
            feature_id = str(row[0]).strip() if row else ""
            if feature_id in seen:
                duplicates.add(feature_id)
            seen.add(feature_id)
            for raw in row[1:]:
                value = str(raw).strip()
                if value == "":
                    issues.append({"severity": "warning", "code": "missing_expression_value", "message": "表达矩阵包含缺失值。"})
                    continue
                try:
                    numeric = float(value)
                except ValueError:
                    issues.append({"severity": "blocker", "code": "non_numeric_expression", "message": "表达矩阵包含非数值表达值。"})
                    continue
                if asset_type == "raw_count_matrix" and numeric < 0:
                    issues.append({"severity": "blocker", "code": "negative_counts", "message": "count matrix 包含负数。"})
            if row_count >= 2000:
                break
    except (OSError, StopIteration):
        issues.append({"severity": "warning", "code": "matrix_scan_failed", "message": "表达矩阵无法完成内容校验，仅登记 lineage。"})
    if duplicates:
        issues.append({"severity": "warning", "code": "duplicated_gene_ids", "message": "表达矩阵包含重复 gene/probe ID。"})
    return {"row_count": row_count, "column_count": column_count, "sample_columns": sample_columns, "issues": _dedupe_issues(issues)}


def _default_asset_selection(assets: list[dict[str, object]], confirmation: dict[str, object]) -> dict[str, object]:
    selected_expression = confirmation.get("selected_expression_candidate") if isinstance(confirmation.get("selected_expression_candidate"), dict) else {}
    expression_assets = [asset for asset in assets if str(asset.get("asset_type") or "") in EXPRESSION_ASSET_TYPES]
    imported_assets = [asset for asset in assets if str(asset.get("asset_type") or "") in IMPORTED_RESULT_ASSET_TYPES]
    selection = {
        "schema_version": "biomedpilot.default_asset_selection.v1",
        "expression": _selected_asset_state(expression_assets, selected_expression),
        "imported_result": _selected_asset_state(imported_assets, {}),
    }
    selected_ids = {
        str(value.get("asset_id") or "")
        for value in selection.values()
        if isinstance(value, dict) and value.get("selection_state") in {"user_confirmed", "auto_recommended"}
    }
    for asset in assets:
        asset["default_selected"] = str(asset.get("asset_id") or "") in selected_ids or bool(asset.get("default_selected"))
    return selection


def _selected_asset_state(assets: list[dict[str, object]], selected_candidate: dict[str, object]) -> dict[str, object]:
    if not assets:
        return {"selection_state": "missing", "asset_id": "", "reason": "no candidate assets"}
    selected_source = Path(str(selected_candidate.get("source_path") or selected_candidate.get("source_file") or "")).name
    if selected_source:
        for asset in assets:
            if Path(str(asset.get("source_file") or "")).name == selected_source:
                return {"selection_state": "user_confirmed", "asset_id": asset.get("asset_id"), "reason": "selected in standardization confirmation"}
    if len(assets) == 1:
        return {"selection_state": "auto_recommended", "asset_id": assets[0].get("asset_id"), "reason": "single candidate auto recommended and recorded"}
    return {"selection_state": "blocked_multiple_candidates", "asset_id": "", "reason": "multiple candidates require explicit default selection"}


def _analysis_input_packages(
    root: Path,
    assets: list[dict[str, object]],
    confirmation: dict[str, object],
    default_selection: dict[str, object],
    validation_issues: list[dict[str, object]],
) -> list[dict[str, object]]:
    packages: list[dict[str, object]] = []
    expression_asset = _asset_by_id(assets, str((default_selection.get("expression") or {}).get("asset_id") if isinstance(default_selection.get("expression"), dict) else ""))
    group_asset = next((asset for asset in assets if str(asset.get("asset_type") or "") == "group_design"), None)
    sample_asset = next((asset for asset in assets if str(asset.get("repository") or "") == "sample_metadata_repository"), None)
    clinical_asset = next((asset for asset in assets if str(asset.get("repository") or "") == "clinical_repository"), None)
    imported_asset = _asset_by_id(assets, str((default_selection.get("imported_result") or {}).get("asset_id") if isinstance(default_selection.get("imported_result"), dict) else ""))
    blockers = {str(issue.get("code") or "") for issue in validation_issues if issue.get("severity") in {"blocker", "error"}}
    if expression_asset and sample_asset and group_asset:
        value_type = str(expression_asset.get("expression_value_type") or "")
        status = "ready" if value_type in {"count", "count_like_candidate"} and not blockers.intersection({"sample_mismatch", "negative_counts", "non_numeric_expression", "unknown_value_type", "probe_mapping_missing"}) else "blocked"
        packages.append(_write_analysis_input_package(root, "deg_recompute", status, [expression_asset, sample_asset, group_asset], ["differential_expression"], blockers))
    if imported_asset:
        packages.append(_write_analysis_input_package(root, "enrichment_from_imported_result", "ready", [imported_asset], ["enrichment", "result_browse", "volcano_plot"], blockers))
    if expression_asset:
        value_type = str(expression_asset.get("expression_value_type") or "")
        status = "ready" if value_type in {"TPM", "FPKM", "CPM", "normalized", "normalized_expression", "log2_transformed", "log_expression", "normalized_or_log_expression"} else "blocked"
        packages.append(_write_analysis_input_package(root, "correlation_heatmap", status, [expression_asset], ["correlation", "heatmap"], blockers))
    if expression_asset and clinical_asset:
        packages.append(_write_analysis_input_package(root, "survival", "ready", [expression_asset, clinical_asset], ["survival"], blockers))
    return packages


def _write_analysis_input_package(root: Path, package_type: str, status: str, assets: list[dict[str, object]], consumable_by: list[str], blockers: set[str]) -> dict[str, object]:
    package_id = f"{package_type}-{hashlib.sha1('|'.join(str(asset.get('asset_id') or '') for asset in assets).encode('utf-8')).hexdigest()[:12]}"
    target = root / REPOSITORY_DIRS["analysis_input_repository"] / f"{package_id}.json"
    payload = {
        "schema_version": "biomedpilot.analysis_input_package.v1",
        "package_id": package_id,
        "package_type": package_type,
        "status": status,
        "asset_refs": [{"asset_id": asset.get("asset_id"), "repository": asset.get("repository"), "path": asset.get("path"), "asset_role": asset.get("asset_role")} for asset in assets],
        "consumable_by": consumable_by if status == "ready" else [],
        "blockers": sorted(blockers) if status != "ready" else [],
        "biological_normalization_performed": False,
    }
    _write_json(target, payload)
    return {**payload, "path": str(target)}


def _write_repository_outputs(root: Path, repository_manifest: dict[str, object], validation_report: dict[str, object], lineage: list[dict[str, object]]) -> None:
    _write_json(root / REPOSITORY_MANIFEST, repository_manifest)
    _write_json(root / REPOSITORY_VALIDATION_REPORT, validation_report)
    lineage_path = root / ASSET_LINEAGE
    lineage_path.parent.mkdir(parents=True, exist_ok=True)
    lineage_path.write_text("\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in lineage) + ("\n" if lineage else ""), encoding="utf-8")


def _dedupe_standardized_assets(assets: list[dict[str, object]]) -> list[dict[str, object]]:
    deduped: dict[tuple[str, str], dict[str, object]] = {}
    for asset in assets:
        asset_type = str(asset.get("asset_type") or "")
        source_file = str(asset.get("source_file") or asset.get("file_path") or asset.get("path") or "")
        path = Path(source_file).expanduser()
        key_path = str(path.resolve()) if path.exists() else source_file
        key = (asset_type, key_path)
        deduped.setdefault(key, asset)
    return list(deduped.values())


def _asset_role(asset_type: str) -> str:
    if asset_type in EXPRESSION_ASSET_TYPES:
        return "expression_matrix"
    if asset_type in SAMPLE_METADATA_ASSET_TYPES:
        return "sample_metadata"
    if asset_type in CLINICAL_ASSET_TYPES:
        return "clinical_metadata"
    if asset_type in FEATURE_ASSET_TYPES:
        return "feature_annotation"
    if asset_type in IMPORTED_RESULT_ASSET_TYPES:
        return "imported_result"
    return asset_type


def _consumable_by(asset_type: str, validation: dict[str, object]) -> list[str]:
    if validation.get("status") == "blocked":
        return []
    if asset_type == "raw_count_matrix":
        return ["differential_expression", "correlation", "heatmap"]
    if asset_type in {"expression_matrix", "normalized_expression_matrix", "tcga_expression_matrix", "gtex_expression_matrix"}:
        return ["correlation", "heatmap", "survival"]
    if asset_type in SAMPLE_METADATA_ASSET_TYPES:
        return ["differential_expression", "correlation", "heatmap"]
    if asset_type in CLINICAL_ASSET_TYPES:
        return ["survival", "clinical_association"]
    if asset_type in FEATURE_ASSET_TYPES:
        return ["differential_expression", "enrichment", "correlation"]
    if asset_type in IMPORTED_RESULT_ASSET_TYPES:
        return ["enrichment", "result_browse", "volcano_plot"]
    return []


def _repository_summary(assets: list[dict[str, object]]) -> dict[str, object]:
    summary: dict[str, object] = {}
    for repository in REPOSITORY_DIRS:
        repo_assets = [asset for asset in assets if str(asset.get("repository") or "") == repository]
        blocked = sum(1 for asset in repo_assets if str(asset.get("validation_status") or "") == "blocked")
        warnings = sum(1 for asset in repo_assets if str(asset.get("validation_status") or "") == "warning")
        summary[repository] = {
            "asset_count": len(repo_assets),
            "ready_count": sum(1 for asset in repo_assets if asset.get("analysis_ready") and str(asset.get("validation_status") or "") != "blocked"),
            "blocked_count": blocked,
            "warning_count": warnings,
            "path": str(REPOSITORY_DIRS[repository]),
        }
    return summary


def _source_state(recognition: dict[str, object], confirmation: dict[str, object]) -> dict[str, object]:
    payload = {
        "recognition_run_id": recognition.get("recognition_run_id") or "",
        "recognition_engine_version": recognition.get("recognition_engine_version") or "",
        "recognition_fingerprint": (recognition.get("input_fingerprint") or {}).get("fingerprint_hash") if isinstance(recognition.get("input_fingerprint"), dict) else "",
        "confirmation_updated_at": confirmation.get("updated_at") or "",
        "confirmation_id": _confirmation_id(confirmation),
    }
    payload["source_state_hash"] = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return payload


def _confirmation_id(confirmation: dict[str, object]) -> str:
    updated = str(confirmation.get("updated_at") or confirmation.get("created_at") or "unconfirmed")
    return hashlib.sha1(updated.encode("utf-8")).hexdigest()[:12]


def _source_acquisition_id(record: dict[str, object]) -> str:
    evidence = record.get("evidence") if isinstance(record.get("evidence"), dict) else {}
    source_manifest = evidence.get("source_manifest") if isinstance(evidence.get("source_manifest"), dict) else {}
    return str(source_manifest.get("acquisition_id") or source_manifest.get("manifest_path") or "")


def _confirmed_value_type(asset_type: str, record: dict[str, object], confirmation: dict[str, object]) -> str:
    value = confirmation.get("expression_value_type_confirmed") if isinstance(confirmation.get("expression_value_type_confirmed"), dict) else {}
    confirmed_value = str(value.get("value_type") or "")
    if confirmed_value:
        return _normalize_value_type(confirmed_value)
    if asset_type == "raw_count_matrix":
        return "count"
    profile = record.get("matrix_profile") if isinstance(record.get("matrix_profile"), dict) else {}
    candidate = str(record.get("expression_value_type_candidate") or profile.get("value_type_candidate") or "")
    return _normalize_value_type(candidate)


def _normalize_value_type(value: str) -> str:
    normalized = value.strip()
    mapping = {
        "count_like_candidate": "count_like_candidate",
        "count": "count",
        "TPM": "TPM",
        "tpm": "TPM",
        "FPKM": "FPKM",
        "fpkm": "FPKM",
        "CPM": "CPM",
        "cpm": "CPM",
        "normalized_expression": "normalized_expression",
        "normalized_or_log_expression": "normalized_or_log_expression",
        "log_expression": "log_expression",
        "log2_transformed": "log2_transformed",
    }
    return mapping.get(normalized, normalized or "unknown")


def _confirmed_gene_id_type(record: dict[str, object], confirmation: dict[str, object]) -> str:
    gene = confirmation.get("gene_id_type_confirmed") if isinstance(confirmation.get("gene_id_type_confirmed"), dict) else {}
    if gene.get("gene_id_type"):
        return str(gene.get("gene_id_type"))
    profile = record.get("matrix_profile") if isinstance(record.get("matrix_profile"), dict) else {}
    return str(record.get("gene_id_type_candidate") or profile.get("gene_id_type_candidate") or "unknown")


def _asset_format(path: Path, asset_type: str) -> str:
    if path.name.endswith(".matrix.tsv"):
        return "tsv"
    if path.suffix.lower() == ".json":
        return "json"
    if path.suffix.lower() in {".tsv", ".csv"}:
        return path.suffix.lower().lstrip(".")
    if asset_type in EXPRESSION_ASSET_TYPES:
        return "tsv"
    return "reference"


def _path_stats(path: Path) -> dict[str, object]:
    if not path.exists() or not path.is_file():
        return {"size_bytes": 0, "sha256": ""}
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"size_bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def _lineage_record(asset: dict[str, object], record: dict[str, object], confirmation: dict[str, object]) -> dict[str, object]:
    return {
        "asset_id": asset.get("asset_id"),
        "repository": asset.get("repository"),
        "asset_type": asset.get("asset_type"),
        "source_file": asset.get("source_file"),
        "source_recognition_run_id": asset.get("source_recognition_run_id") or record.get("recognition_run_id") or "",
        "confirmation_id": asset.get("confirmation_id") or _confirmation_id(confirmation),
        "path": asset.get("path"),
        "materialize_strategy": asset.get("materialize_strategy"),
        "biological_normalization_performed": False,
    }


def _asset_by_id(assets: list[dict[str, object]], asset_id: str) -> dict[str, object] | None:
    if not asset_id:
        return None
    return next((asset for asset in assets if str(asset.get("asset_id") or "") == asset_id), None)


def _is_tabular_text_path(path: Path) -> bool:
    suffixes = [suffix.lower() for suffix in path.suffixes]
    if suffixes and suffixes[-1] == ".gz":
        suffixes = suffixes[:-1]
    return bool(suffixes and suffixes[-1] in {".csv", ".tsv", ".txt", ".matrix"})


def _open_text(path: Path):
    return gzip.open(path, "rt", encoding="utf-8", errors="ignore") if path.name.lower().endswith(".gz") else path.open("r", encoding="utf-8", errors="ignore")


def _detect_delimiter(path: Path) -> str:
    suffixes = [suffix.lower() for suffix in path.suffixes]
    if suffixes and suffixes[-1] == ".gz":
        suffixes = suffixes[:-1]
    if suffixes and suffixes[-1] == ".csv":
        return ","
    try:
        with _open_text(path) as handle:
            sample = "".join(handle.readline() for _ in range(5))
    except OSError:
        sample = ""
    return "\t" if sample.count("\t") >= sample.count(",") else ","


def _write_tsv_copy(source_path: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    delimiter = _detect_delimiter(source_path)
    with _open_text(source_path) as source, target.open("w", encoding="utf-8", newline="") as output:
        reader = csv.reader(source, delimiter=delimiter)
        writer = csv.writer(output, delimiter="\t")
        for row in reader:
            writer.writerow(row)


def _write_canonical_matrix(source_path: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output, delimiter="\t")
        rows_iter = _iter_matrix_rows(source_path)
        header = next(rows_iter, [])
        if header:
            writer.writerow(["feature_id", *header[1:]])
        for row in rows_iter:
            if row:
                writer.writerow(row)


def _iter_matrix_rows(source_path: Path):
    delimiter = _detect_delimiter(source_path)
    with _open_text(source_path) as source:
        in_geo_matrix = False
        saw_geo_marker = False
        for raw_line in source:
            line = raw_line.rstrip("\n\r")
            stripped = line.strip()
            lower = stripped.lower()
            if lower.startswith("!series_matrix_table_begin"):
                in_geo_matrix = True
                saw_geo_marker = True
                continue
            if lower.startswith("!series_matrix_table_end"):
                break
            if saw_geo_marker and not in_geo_matrix:
                continue
            if saw_geo_marker and in_geo_matrix:
                if stripped:
                    yield next(csv.reader([stripped], delimiter="\t"))
                continue
            if not stripped or stripped.startswith("!") or stripped.startswith("^"):
                continue
            yield next(csv.reader([stripped], delimiter=delimiter))


def _dedupe_issues(issues: list[dict[str, object]]) -> list[dict[str, object]]:
    deduped: dict[tuple[str, str], dict[str, object]] = {}
    for issue in issues:
        key = (str(issue.get("severity") or ""), str(issue.get("code") or ""))
        deduped.setdefault(key, issue)
    return list(deduped.values())


def _processing_tasks_from_assets(assets: list[dict[str, object]]) -> list[dict[str, object]]:
    tasks: list[dict[str, object]] = []
    for asset in assets:
        asset_type = str(asset.get("asset_type") or "")
        file_path = str(asset.get("file_path") or "")
        if asset_type in {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix", "tcga_expression_matrix", "gtex_expression_matrix"}:
            tasks.append(_processing_task("expression_matrix_cleaning", "表达矩阵清洗", file_path, asset_type, "pending_confirmation"))
            tasks.append(_processing_task("gene_annotation_mapping", "基因注释映射", file_path, asset_type, "pending_annotation_source"))
        elif asset_type in {"platform_annotation", "gene_annotation", "platform_reference_hint"}:
            tasks.append(_processing_task("gene_annotation_mapping", "基因注释映射", file_path, asset_type, "pending_confirmation"))
        elif asset_type in {"sample_metadata", "phenotype_metadata", "tcga_sample_metadata", "gtex_sample_metadata", "group_design"}:
            tasks.append(_processing_task("sample_annotation_review", "样本注释整理", file_path, asset_type, "pending_group_confirmation"))
        elif asset_type in {"clinical_metadata", "survival_metadata", "tcga_clinical_metadata"}:
            tasks.append(_processing_task("clinical_metadata_standardization", "临床/生存信息整理", file_path, asset_type, "pending_field_mapping"))
        elif asset_type in IMPORTED_RESULT_ASSET_TYPES:
            tasks.append(_processing_task("imported_result_registration", "导入结果登记", file_path, asset_type, "registered"))
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
    repository_manifest_path = root / REPOSITORY_MANIFEST
    validation_report_path = root / REPOSITORY_VALIDATION_REPORT
    confirmation = load_standardization_confirmation_artifacts(root)
    registry = _read_json(registry_path) if registry_path.exists() else None
    repository_manifest = _read_json(repository_manifest_path) if repository_manifest_path.exists() else None
    stale_status = _repository_stale_status(root, registry if isinstance(registry, dict) else None)
    return {
        "registry": registry,
        "analysis_ready_manifest": _read_json(manifest_path) if manifest_path.exists() else None,
        "data_processing_task_plan": _read_json(root / DATA_PROCESSING_TASK_PLAN) if (root / DATA_PROCESSING_TASK_PLAN).exists() else None,
        "repository_manifest": repository_manifest,
        "validation_report": _read_json(validation_report_path) if validation_report_path.exists() else None,
        "repository_stale_status": stale_status,
        "standardization_confirmation": confirmation.get("confirmation"),
        "standardization_candidates": confirmation.get("candidates"),
        "standardization_confirmation_path": confirmation.get("confirmation_path"),
        "registry_path": str(registry_path),
        "manifest_path": str(manifest_path),
        "repository_manifest_path": str(repository_manifest_path),
        "validation_report_path": str(validation_report_path),
        "asset_lineage_path": str(root / ASSET_LINEAGE),
        "data_processing_task_plan_path": str(root / DATA_PROCESSING_TASK_PLAN),
    }


def _repository_stale_status(root: Path, registry: dict[str, object] | None) -> dict[str, object]:
    if not registry:
        return {"is_stale": True, "reason": "missing_registry", "message": "尚未生成标准化资产仓库。"}
    current_recognition = load_recognition_report(root) or {}
    confirmation = load_standardization_confirmation_artifacts(root).get("confirmation")
    current_state = _source_state(current_recognition if isinstance(current_recognition, dict) else {}, confirmation if isinstance(confirmation, dict) else {})
    saved_state = registry.get("source_state") if isinstance(registry.get("source_state"), dict) else {}
    if saved_state.get("source_state_hash") != current_state.get("source_state_hash"):
        return {
            "is_stale": True,
            "reason": "recognition_or_confirmation_changed",
            "message": "识别结果或标准化确认已变化，请重新生成资产仓库。",
            "saved_state": saved_state,
            "current_state": current_state,
        }
    return {"is_stale": False, "reason": "", "message": "", "source_state_hash": current_state.get("source_state_hash")}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
