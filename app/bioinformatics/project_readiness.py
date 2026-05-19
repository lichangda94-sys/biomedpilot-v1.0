from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.comparison_config import (
    comparison_sample_match_status,
    comparison_summary_text,
    expression_samples_from_recognition_report,
    load_confirmed_comparison_config,
)
from app.bioinformatics.data_sources.gtex_expression_builder import latest_gtex_expression_build_manifest_path
from app.bioinformatics.data_sources.live_validation import validation_warning
from app.bioinformatics.gene_set_resources import build_gsea_gene_set_readiness, get_selected_gene_set, validate_gene_set_registry
from app.bioinformatics.project_recognition import load_recognition_report
from app.bioinformatics.standardization_confirmation import load_standardization_confirmation


READINESS_REPORT = Path("logs") / "readiness" / "readiness_report.json"
CAPABILITY_MATRIX = Path("manifests") / "analysis_capability_matrix.json"

ANALYSIS_ROWS = (
    ("differential_expression", "差异表达分析", {"expression_matrix", "sample_metadata", "comparison_config"}),
    ("enrichment", "富集分析", {"expression_matrix"}),
    ("gsea", "GSEA", {"expression_matrix"}),
    ("correlation", "相关性分析", {"expression_matrix"}),
    ("survival", "生存分析", {"expression_matrix", "clinical_metadata"}),
    ("clinical_association", "临床变量关联", {"clinical_metadata"}),
    ("tcga_gtex_joint", "TCGA + GTEx 联合分析", {"expression_matrix", "sample_metadata"}),
    ("reporting", "报告生成", {"analysis_result"}),
)

CORE_INPUTS = {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix", "tcga_expression_matrix", "gtex_expression_matrix"}
EXPRESSION_COMPATIBLE_INPUTS = {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix", "tcga_expression_matrix", "gtex_expression_matrix"}


def run_project_readiness(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    recognition = load_recognition_report(root) or {}
    files = list(recognition.get("files", []) or [])
    available = _available_inputs(files)
    tcga_readiness = build_tcga_b6_4_readiness_summary(root)
    if tcga_readiness.get("has_tcga_b6_4_build"):
        available.update(str(item) for item in tcga_readiness.get("available_inputs", []) or [] if str(item))
    tcga_clinical_readiness = build_tcga_clinical_readiness_summary(root)
    if tcga_clinical_readiness.get("has_tcga_clinical_build"):
        available.update(str(item) for item in tcga_clinical_readiness.get("available_inputs", []) or [] if str(item))
    gtex_readiness = build_gtex_readiness_summary(root)
    if gtex_readiness.get("has_gtex_expression_build"):
        available.update(str(item) for item in gtex_readiness.get("available_inputs", []) or [] if str(item))
    validation_limited_present = any(
        bool(summary.get("validation_limited"))
        for summary in (tcga_readiness, tcga_clinical_readiness, gtex_readiness)
        if isinstance(summary, dict)
    )
    confirmed_comparison = load_confirmed_comparison_config(root)
    if confirmed_comparison is not None:
        available.add("comparison_config")
    expression_samples = expression_samples_from_recognition_report(recognition if isinstance(recognition, dict) else {})
    expression_samples.update(str(item) for item in tcga_readiness.get("sample_ids", []) or [] if str(item))
    comparison_match = comparison_sample_match_status(confirmed_comparison, expression_samples)
    standardization_ready = bool(available & CORE_INPUTS)
    confirmation = load_standardization_confirmation(root) or {}
    confirmation_readiness = confirmation.get("readiness") if isinstance(confirmation.get("readiness"), dict) else {}
    gene_set_validation = validate_gene_set_registry(root)
    selected_gene_set = get_selected_gene_set(root)
    gsea_gene_set_status = _gsea_gene_set_status(selected_gene_set)
    gsea_gene_set_readiness = build_gsea_gene_set_readiness(root)
    has_core_input = standardization_ready
    warnings: list[str] = [str(item) for item in recognition.get("warnings", []) or []]
    warnings.extend(str(item) for item in tcga_readiness.get("warnings", []) or [] if str(item))
    warnings.extend(str(item) for item in tcga_clinical_readiness.get("warnings", []) or [] if str(item))
    warnings.extend(str(item) for item in gtex_readiness.get("warnings", []) or [] if str(item))
    if not has_core_input:
        warnings.append("无表达矩阵。")
    if "sample_metadata" not in available:
        warnings.append("样本信息缺失。")
    if "clinical_metadata" not in available:
        warnings.append("临床信息缺失。")
    if validation_limited_present:
        warnings.append(validation_warning())
    rows = []
    deg_ready = False
    for key, label, required in ANALYSIS_ROWS:
        missing = sorted(_missing_inputs_for_row(key, required, available, confirmed_comparison))
        can_run = bool(has_core_input) and not missing and (key not in {"tcga_gtex_joint", "reporting"})
        row_warnings = []
        if validation_limited_present and key in {"differential_expression", "enrichment", "gsea", "correlation", "survival", "clinical_association", "tcga_gtex_joint", "reporting"}:
            can_run = False
            row_warnings.append(validation_warning())
        if key == "differential_expression":
            tcga_group_status = str(tcga_readiness.get("default_group_status") or "")
            if tcga_group_status == "available" and confirmed_comparison is None:
                row_warnings.append("已检测到 TCGA Primary Tumor vs Solid Tissue Normal 默认分组候选；仍需确认比较组后进入 DEG preflight。")
            elif tcga_group_status == "insufficient" and tcga_readiness.get("has_tcga_b6_4_build"):
                row_warnings.append("TCGA tumor/normal 样本不足；只能做表达展示、临床联合或手动分组。")
            comparison_status = _comparison_group_status(
                has_core_input=has_core_input,
                confirmed_comparison=confirmed_comparison,
                comparison_match=comparison_match,
                recognition=recognition if isinstance(recognition, dict) else {},
            )
            if comparison_status == "candidate_pending":
                row_warnings.append("已检测到候选分组，但尚未确认比较组。")
            elif comparison_status == "confirmed_missing_expression":
                row_warnings.append("比较组已确认，但缺少表达矩阵。")
            elif comparison_status == "confirmed_sample_mismatch":
                row_warnings.append("样本 ID 不匹配。")
                can_run = False
            elif comparison_status == "confirmed_unverified":
                row_warnings.append("比较组已确认，但尚未验证表达矩阵样本 ID。")
        if key == "tcga_gtex_joint":
            row_warnings.append("TCGA + GTEx 尚未批次校正，结果仅用于 preview / testing。")
            if tcga_readiness.get("has_tcga_b6_4_build"):
                row_warnings.append("B6.5 保留 TCGA + GTEx 不自动合并边界；GTEx 仍需独立接入和批次校正方案。")
            if gtex_readiness.get("has_gtex_expression_build"):
                row_warnings.append("GTEx 已作为独立正常组织表达资源接入；不会自动作为 TCGA normal control，需显式联合配置。")
        if key == "survival" and tcga_clinical_readiness.get("has_tcga_clinical_build"):
            survival_status = str(tcga_clinical_readiness.get("survival_gate_status") or "")
            if survival_status == "survival_ready_basic":
                row_warnings.append("TCGA clinical 仅达到基础 OS preflight 输入就绪；当前不执行 KM/Cox/log-rank，也不生成生存结论。")
            elif survival_status in {"survival_partial", "survival_unavailable"}:
                row_warnings.append("TCGA 基础 OS 字段不足；只能进入字段检查或手动补充，不能直接执行生存分析。")
        if key == "gsea":
            if selected_gene_set is None or gsea_gene_set_status.get("status") != "selected":
                missing.append("gsea_gene_set_selection")
                can_run = False
                row_warnings.append("GSEA 基因集尚未选择；这只阻断后续 GSEA preflight / execution，不影响当前数据检查、标准化准备或 DEG preflight。")
        if key == "reporting":
            row_warnings.append("报告生成不参与 Ready 判定；需先有真实分析结果。")
        next_step = _next_step_for_row(key, can_run, missing, row_warnings)
        if key == "reporting":
            next_step = "请先创建并执行分析任务，生成结果后再进入报告。"
        if key == "differential_expression":
            deg_ready = can_run
        rows.append(
            {
                "analysis_type": key,
                "label": label,
                "can_run": can_run,
                "available_inputs": sorted(required & available),
                "missing_inputs": missing,
                "warnings": row_warnings,
                "next_step": next_step,
            }
        )
    ready_rows = [row for row in rows if row["can_run"] and row["analysis_type"] != "reporting"]
    if not standardization_ready:
        overall = "not_ready"
    elif warnings:
        overall = "ready_with_warnings"
    elif ready_rows:
        overall = "partially_ready"
    else:
        overall = "partially_ready"
    report = {
        "schema_version": "biomedpilot.readiness_report.v1",
        "generated_at": _now(),
        "project_root": str(root),
        "overall_status": overall,
        "available_inputs": sorted(available),
        "has_core_input": has_core_input,
        "standardization_ready": standardization_ready,
        "standardization_confirmed": bool(confirmation_readiness.get("standardization_confirmed")),
        "deg_ready": deg_ready,
        "deg_preflight_ready": bool(confirmation_readiness.get("deg_preflight_ready")),
        "imported_result_ready": bool(confirmation_readiness.get("imported_result_ready")),
        "warnings": warnings,
        "comparison_config_summary": confirmed_comparison.to_dict() if confirmed_comparison is not None else {},
        "comparison_group_summary_zh": comparison_summary_text(confirmed_comparison),
        "comparison_sample_match": comparison_match,
        "comparison_group_status": _comparison_group_status(
            has_core_input=has_core_input,
            confirmed_comparison=confirmed_comparison,
            comparison_match=comparison_match,
            recognition=recognition if isinstance(recognition, dict) else {},
        ),
        "file_statuses": build_file_check_statuses(files),
        "dataset_readiness": build_dataset_readiness_summary(
            files=files,
            available=available,
            confirmed_comparison=confirmed_comparison,
            comparison_match=comparison_match,
            standardization_ready=standardization_ready,
            deg_ready=deg_ready,
            tcga_readiness=tcga_readiness,
            tcga_clinical_readiness=tcga_clinical_readiness,
            gtex_readiness=gtex_readiness,
        ),
        "tcga_readiness": tcga_readiness,
        "tcga_clinical_readiness": tcga_clinical_readiness,
        "gtex_readiness": gtex_readiness,
        "validation_limited": validation_limited_present,
        "gsea_gene_set_status": gsea_gene_set_status,
        "gsea_gene_set_readiness": gsea_gene_set_readiness,
        "gene_set_registry_validation": gene_set_validation,
    }
    matrix = {
        "schema_version": "biomedpilot.analysis_capability_matrix.v1",
        "generated_at": report["generated_at"],
        "rows": rows,
    }
    _write_json(root / READINESS_REPORT, report)
    _write_json(root / CAPABILITY_MATRIX, matrix)
    return {"readiness_report": report, "capability_matrix": matrix}


def _available_inputs(files: list[object]) -> set[str]:
    return available_inputs_from_recognition_files(files)


def available_inputs_from_recognition_files(files: list[object]) -> set[str]:
    available: set[str] = set()
    for item in files:
        if not isinstance(item, dict):
            continue
        detected_assets = [asset for asset in item.get("detected_assets", []) or [] if isinstance(asset, dict)]
        if detected_assets:
            for asset in detected_assets:
                if asset.get("input_eligible") is False:
                    continue
                role = str(asset.get("role") or asset.get("asset_type") or "")
                _add_available_input(available, role)
            continue
        primary = str(item.get("recognized_type") or "")
        _add_available_input(available, primary)
        for role in item.get("recognized_roles", []) or []:
            _add_available_input(available, str(role))
        for role in item.get("secondary_roles", []) or []:
            _add_available_input(available, str(role))
    return available


def has_standardizable_expression_input(files: list[object]) -> bool:
    return bool(available_inputs_from_recognition_files(files) & CORE_INPUTS)


def _missing_inputs_for_row(
    key: str,
    required: set[str],
    available: set[str],
    confirmed_comparison: object | None,
) -> set[str]:
    if key != "differential_expression":
        return set(required - available)
    missing: set[str] = set()
    if not available & CORE_INPUTS:
        missing.add("expression_matrix")
    if confirmed_comparison is None:
        if "sample_metadata" not in available:
            missing.add("sample_metadata")
        missing.add("comparison_config")
        return missing
    if not getattr(confirmed_comparison, "assignments", ()):
        if "sample_metadata" not in available:
            missing.add("sample_metadata")
    return missing


def _comparison_group_status(
    *,
    has_core_input: bool,
    confirmed_comparison: object | None,
    comparison_match: dict[str, object],
    recognition: dict[str, object],
) -> str:
    if confirmed_comparison is None:
        return "candidate_pending" if _recognition_group_preview_has_candidate(recognition) else "no_group_detected"
    if not has_core_input:
        return "confirmed_missing_expression"
    if getattr(confirmed_comparison, "assignments", ()):
        match_status = str(comparison_match.get("sample_id_match_status") or "not_checked")
        if match_status == "mismatch":
            return "confirmed_sample_mismatch"
        if match_status == "not_checked":
            return "confirmed_unverified"
        matched = int(comparison_match.get("matched_sample_count") or 0)
        if matched <= 0:
            return "confirmed_sample_mismatch"
        group_sizes = comparison_match.get("matched_group_sizes")
        if isinstance(group_sizes, dict):
            case_group = str(getattr(confirmed_comparison, "case_group", "") or "")
            control_group = str(getattr(confirmed_comparison, "control_group", "") or "")
            if int(group_sizes.get(case_group, 0) or 0) <= 0 or int(group_sizes.get(control_group, 0) or 0) <= 0:
                return "confirmed_sample_mismatch"
    return "confirmed_ready"


def _recognition_group_preview_has_candidate(recognition: dict[str, object]) -> bool:
    preview = recognition.get("group_preview")
    if not isinstance(preview, dict):
        return False
    try:
        group_count = int(preview.get("group_count") or 0)
    except (TypeError, ValueError):
        group_count = 0
    return str(preview.get("status") or "") == "preview_only" and group_count >= 2


def _next_step_for_row(key: str, can_run: bool, missing: list[str], warnings: list[str]) -> str:
    if can_run:
        return "可创建预览任务。"
    if key == "gsea" and "gsea_gene_set_selection" in missing:
        return "请在后续 GSEA 前选择基因集；这不影响当前数据检查、标准化准备或 DEG preflight。"
    if key == "differential_expression":
        if "样本 ID 不匹配。" in warnings:
            return "请修正比较组样本 ID，或选择与比较组匹配的表达矩阵。"
        if "比较组已确认，但缺少表达矩阵。" in warnings or "expression_matrix" in missing:
            return "请补充表达矩阵。"
        if "comparison_config" in missing:
            return "请确认比较组。"
    return "请补充缺失输入或返回前序页面。"


def _add_available_input(available: set[str], role: str) -> None:
    if not role or role in {"unknown", "differential_result_table", "unsupported", "archive", "raw_heavy_file", "gdc_manifest", "gmt_gene_set"}:
        return
    available.add(role)
    if role in EXPRESSION_COMPATIBLE_INPUTS:
        available.add("expression_matrix")


def build_file_check_statuses(files: list[object]) -> list[dict[str, object]]:
    statuses: list[dict[str, object]] = []
    for item in files:
        if not isinstance(item, dict):
            continue
        primary = str(item.get("recognized_type") or item.get("primary_type") or "unknown")
        roles = {str(role) for role in item.get("recognized_roles", []) or item.get("roles", []) or [] if str(role)}
        assets = [asset for asset in item.get("detected_assets", []) or [] if isinstance(asset, dict)]
        standardization_status = str(item.get("standardization_status") or "")
        color, status, status_zh = _file_check_state(primary, roles, assets, standardization_status, item)
        statuses.append(
            {
                "file_name": str(item.get("file_name") or Path(str(item.get("original_path") or "")).name),
                "file_suffix": Path(str(item.get("file_name") or item.get("original_path") or "")).suffix.lower(),
                "source": _file_source_label(item),
                "source_file": str(item.get("original_path") or ""),
                "recognized_type": primary,
                "recognized_type_zh": str(item.get("recognized_type_zh") or item.get("primary_type_zh") or primary),
                "suggested_use": _file_suggested_use(primary, roles, assets),
                "available_content": _file_available_content(item, roles, assets),
                "missing_content": _file_missing_content(primary, roles, assets, item),
                "risk_notes": _file_risk_notes(primary, roles, item),
                "status": status,
                "status_zh": status_zh,
                "status_color": color,
                "can_enter_standardization": color in {"green", "yellow"} and primary != "differential_result_table" and "differential_result_table" not in roles and primary != "gmt_gene_set",
            }
        )
    return statuses


def build_dataset_readiness_summary(
    *,
    files: list[object],
    available: set[str],
    confirmed_comparison: object | None,
    comparison_match: dict[str, object],
    standardization_ready: bool,
    deg_ready: bool,
    tcga_readiness: dict[str, object] | None = None,
    tcga_clinical_readiness: dict[str, object] | None = None,
    gtex_readiness: dict[str, object] | None = None,
) -> dict[str, object]:
    tcga_readiness = tcga_readiness if isinstance(tcga_readiness, dict) else {}
    tcga_clinical_readiness = tcga_clinical_readiness if isinstance(tcga_clinical_readiness, dict) else {}
    gtex_readiness = gtex_readiness if isinstance(gtex_readiness, dict) else {}
    typed_files = [item for item in files if isinstance(item, dict)]
    imported_deg_present = any(_record_has_role(item, "differential_result_table") for item in typed_files)
    expression_records = [item for item in typed_files if _record_has_any_role(item, CORE_INPUTS)]
    metadata_records = [item for item in typed_files if _record_has_any_role(item, {"sample_metadata", "phenotype_metadata", "clinical_metadata", "tcga_sample_metadata", "gtex_sample_metadata"})]
    gene_id_type = _first_profile_value(expression_records, "matrix_profile", "gene_id_type_candidate")
    species = _first_species_evidence(typed_files)
    needs_platform_annotation = gene_id_type in {"probe_id", "unknown"} or any(_record_has_role(item, "platform_reference_hint") for item in typed_files)
    has_platform_annotation = bool({"platform_annotation", "gene_annotation"} & available)
    has_group_design = confirmed_comparison is not None
    has_recommended_group = any(_record_has_any_role(item, {"phenotype_metadata", "sample_metadata"}) for item in typed_files)
    return {
        "has_expression_matrix": bool(expression_records or available & CORE_INPUTS),
        "has_sample_metadata": bool(metadata_records or {"sample_metadata", "phenotype_metadata", "clinical_metadata"} & available),
        "has_group_design": has_group_design,
        "has_recommended_group": has_recommended_group and not has_group_design,
        "species": species or "unknown",
        "gene_id_type": gene_id_type or "unknown",
        "needs_platform_annotation": needs_platform_annotation,
        "has_platform_annotation": has_platform_annotation,
        "imported_deg_present": imported_deg_present,
        "imported_deg_note": "检测到 imported DEG；它可作为外部结果或富集输入，但不能作为 expression matrix 重新计算输入。" if imported_deg_present else "",
        "can_enter_standardization_confirmation": bool(standardization_ready),
        "can_enter_deg_preflight": bool(deg_ready),
        "has_gsea_data_basis": bool(expression_records or available & CORE_INPUTS),
        "gsea_gene_set_required_now": False,
        "comparison_sample_match": comparison_match,
        "tcga_readiness": tcga_readiness,
        "tcga_clinical_readiness": tcga_clinical_readiness,
        "gtex_readiness": gtex_readiness,
        "tcga_value_type_policy": tcga_readiness.get("value_type_policy", {}),
    }


def build_tcga_b6_4_readiness_summary(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    records = _tcga_b6_4_build_records(root)
    if not records:
        return {
            "has_tcga_b6_4_build": False,
            "status": "not_found",
            "available_inputs": [],
            "warnings": [],
            "builds": [],
            "sample_ids": [],
            "value_type_policy": {},
        }
    builds = [_read_tcga_build_record(record) for record in records]
    latest = builds[-1] if builds else {}
    available_inputs: set[str] = set()
    warnings: list[str] = []
    sample_ids: set[str] = set()
    for build in builds:
        available_inputs.update(str(item) for item in build.get("available_inputs", []) or [] if str(item))
        warnings.extend(str(item) for item in build.get("warnings", []) or [] if str(item))
        sample_ids.update(str(item) for item in build.get("sample_ids", []) or [] if str(item))
    return {
        "has_tcga_b6_4_build": True,
        "status": str(latest.get("status") or "unknown"),
        "project_id": str(latest.get("project_id") or ""),
        "build_id": str(latest.get("build_id") or ""),
        "build_manifest_path": str(latest.get("build_manifest_path") or ""),
        "raw_counts_matrix_path": str(latest.get("raw_counts_matrix_path") or ""),
        "sample_metadata_path": str(latest.get("sample_metadata_path") or ""),
        "gene_annotation_path": str(latest.get("gene_annotation_path") or ""),
        "available_inputs": sorted(available_inputs),
        "sample_ids": sorted(sample_ids),
        "sample_count": int(latest.get("sample_count") or 0),
        "gene_count": int(latest.get("gene_count") or 0),
        "matrix_sample_count": int(latest.get("matrix_sample_count") or 0),
        "metadata_sample_count": int(latest.get("metadata_sample_count") or 0),
        "sample_match_status": str(latest.get("sample_match_status") or "not_checked"),
        "sample_type_counts": latest.get("sample_type_counts") if isinstance(latest.get("sample_type_counts"), dict) else {},
        "default_group_status": str(latest.get("default_group_status") or "unknown"),
        "default_group_suggestion": latest.get("default_group_suggestion") if isinstance(latest.get("default_group_suggestion"), dict) else {},
        "value_type_policy": _tcga_value_type_policy(),
        "deg_input_value_type": "count",
        "display_value_types": ["TPM", "FPKM", "FPKM-UQ"],
        "validation_limited": any(bool(build.get("validation_limited")) for build in builds),
        "warnings": list(dict.fromkeys(warnings)),
        "builds": builds,
        "tcga_gtex_boundary": "TCGA B6.4 构建产物不自动与 GTEx 合并；GTEx 仍需独立接入与批次校正方案。",
    }


def build_tcga_clinical_readiness_summary(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    records = _tcga_clinical_build_records(root)
    if not records:
        return {
            "has_tcga_clinical_build": False,
            "status": "clinical_unavailable",
            "clinical_gate_status": "clinical_unavailable",
            "survival_gate_status": "survival_unavailable",
            "available_inputs": [],
            "warnings": [],
            "builds": [],
        }
    builds = [_read_tcga_clinical_build_record(record) for record in records]
    latest = builds[-1] if builds else {}
    available_inputs: set[str] = set()
    warnings: list[str] = []
    for build in builds:
        available_inputs.update(str(item) for item in build.get("available_inputs", []) or [] if str(item))
        warnings.extend(str(item) for item in build.get("warnings", []) or [] if str(item))
    return {
        "has_tcga_clinical_build": True,
        "status": str(latest.get("clinical_gate_status") or "clinical_unavailable"),
        "project_id": str(latest.get("project_id") or ""),
        "clinical_build_id": str(latest.get("clinical_build_id") or ""),
        "mode": str(latest.get("mode") or ""),
        "clinical_gate_status": str(latest.get("clinical_gate_status") or "clinical_unavailable"),
        "survival_gate_status": str(latest.get("survival_gate_status") or "survival_unavailable"),
        "build_manifest_path": str(latest.get("build_manifest_path") or ""),
        "clinical_manifest_path": str(latest.get("clinical_manifest_path") or ""),
        "case_table_path": str(latest.get("case_table_path") or ""),
        "mapping_table_path": str(latest.get("mapping_table_path") or ""),
        "survival_table_path": str(latest.get("survival_table_path") or ""),
        "case_count": int(latest.get("case_count") or 0),
        "sample_count": int(latest.get("sample_count") or 0),
        "matched_case_count": int(latest.get("matched_case_count") or 0),
        "matched_sample_count": int(latest.get("matched_sample_count") or 0),
        "sample_case_match_ratio": float(latest.get("sample_case_match_ratio") or 0.0),
        "survival_case_count": int(latest.get("survival_case_count") or 0),
        "death_event_count": int(latest.get("death_event_count") or 0),
        "demographic_available_case_count": int(latest.get("demographic_available_case_count") or 0),
        "diagnosis_available_case_count": int(latest.get("diagnosis_available_case_count") or 0),
        "available_inputs": sorted(available_inputs),
        "validation_limited": any(bool(build.get("validation_limited")) for build in builds),
        "warnings": list(dict.fromkeys(warnings)),
        "builds": builds,
        "survival_execution_status": "not_executed",
        "clinical_boundary": "TCGA clinical metadata 只进入 clinical/survival preflight readiness；不自动运行 KM/Cox/log-rank，不生成临床结论。",
    }


def build_gtex_readiness_summary(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    records = _gtex_build_records(root)
    if not records:
        return {
            "has_gtex_expression_build": False,
            "status": "not_found",
            "available_inputs": [],
            "warnings": [],
            "builds": [],
        }
    builds = [_read_gtex_build_record(record) for record in records]
    latest = builds[-1] if builds else {}
    available_inputs: set[str] = set()
    warnings: list[str] = []
    for build in builds:
        available_inputs.update(str(item) for item in build.get("available_inputs", []) or [] if str(item))
        warnings.extend(str(item) for item in build.get("warnings", []) or [] if str(item))
    warnings.append("GTEx 不自动作为 TCGA normal control；TCGA+GTEx 需要显式联合配置和批次校正。")
    return {
        "has_gtex_expression_build": True,
        "status": str(latest.get("status") or "gtex_expression_ready_for_data_check"),
        "tissue_id": str(latest.get("tissue_id") or ""),
        "tissue_site_detail": str(latest.get("tissue_site_detail") or ""),
        "build_id": str(latest.get("build_id") or ""),
        "build_manifest_path": str(latest.get("build_manifest_path") or ""),
        "expression_matrix_path": str(latest.get("expression_matrix_path") or ""),
        "sample_metadata_path": str(latest.get("sample_metadata_path") or ""),
        "donor_metadata_path": str(latest.get("donor_metadata_path") or ""),
        "gene_annotation_path": str(latest.get("gene_annotation_path") or ""),
        "sample_count": int(latest.get("sample_count") or 0),
        "donor_count": int(latest.get("donor_count") or 0),
        "gene_count": int(latest.get("gene_count") or 0),
        "sample_match_status": str(latest.get("sample_match_status") or "not_checked"),
        "value_type_policy": latest.get("value_type_policy") if isinstance(latest.get("value_type_policy"), dict) else {},
        "validation_limited": any(bool(build.get("validation_limited")) for build in builds),
        "available_inputs": sorted(available_inputs),
        "warnings": list(dict.fromkeys(warnings)),
        "builds": builds,
        "tcga_merge_status": "not_merged",
        "tcga_default_control_status": "disabled",
        "requires_explicit_joint_config": True,
    }


def _tcga_b6_4_build_records(root: Path) -> list[dict[str, Any]]:
    records_dir = root / "acquisition" / "records"
    if not records_dir.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(records_dir.glob("*.json"), key=lambda item: item.stat().st_mtime):
        if path.name == "latest_acquisition_record.json":
            continue
        try:
            payload = _read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        if not isinstance(metadata, dict):
            continue
        if str(metadata.get("download_status") or "") != "tcga_expression_matrix_built":
            continue
        records.append({"record_path": str(path), "payload": payload, "metadata": metadata})
    return records


def _gtex_build_records(root: Path) -> list[dict[str, Any]]:
    records_dir = root / "acquisition" / "records"
    if not records_dir.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(records_dir.glob("*.json"), key=lambda item: item.stat().st_mtime):
        if path.name == "latest_acquisition_record.json":
            continue
        try:
            payload = _read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        if not isinstance(metadata, dict):
            continue
        if str(metadata.get("download_status") or "") != "gtex_expression_matrix_built":
            continue
        records.append({"record_path": str(path), "payload": payload, "metadata": metadata})
    return records


def _tcga_clinical_build_records(root: Path) -> list[dict[str, Any]]:
    records_dir = root / "acquisition" / "records"
    if not records_dir.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(records_dir.glob("*.json"), key=lambda item: item.stat().st_mtime):
        if path.name == "latest_acquisition_record.json":
            continue
        try:
            payload = _read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        if not isinstance(metadata, dict):
            continue
        if str(metadata.get("download_status") or "") != "tcga_clinical_metadata_built":
            continue
        records.append({"record_path": str(path), "payload": payload, "metadata": metadata})
    return records


def _read_tcga_build_record(record: dict[str, Any]) -> dict[str, object]:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    if not isinstance(metadata, dict):
        metadata = {}
    manifest_path = Path(str(metadata.get("tcga_expression_build_manifest_path") or ""))
    manifest = _read_json(manifest_path) if manifest_path.is_file() else {}
    metric_paths = manifest.get("metric_matrix_paths") if isinstance(manifest.get("metric_matrix_paths"), dict) else {}
    raw_counts_path = Path(str(metric_paths.get("raw_counts") or metadata.get("tcga_expression_matrix_path") or ""))
    sample_metadata_path = Path(str(manifest.get("sample_metadata_path") or metadata.get("tcga_sample_metadata_path") or ""))
    gene_annotation_path = Path(str(manifest.get("gene_annotation_path") or metadata.get("tcga_gene_annotation_path") or ""))
    matrix_samples = _matrix_sample_columns(raw_counts_path)
    sample_rows = _sample_metadata_rows(sample_metadata_path)
    metadata_samples = _sample_ids_from_metadata(sample_rows)
    sample_match_status, sample_warnings = _sample_match_status(matrix_samples, metadata_samples)
    sample_type_counts = _tcga_sample_type_counts(sample_rows)
    default_group_status = "available" if sample_type_counts.get("Primary Tumor", 0) > 0 and sample_type_counts.get("Solid Tissue Normal", 0) > 0 else "insufficient"
    status = "ready_for_deg_preflight_candidate" if sample_match_status == "matched" and default_group_status == "available" else "expression_display_or_manual_group_only"
    if sample_match_status == "mismatch":
        status = "blocked_sample_metadata_mismatch"
    warnings = [*sample_warnings]
    validation_limited = bool(manifest.get("validation_limited") or metadata.get("validation_limited"))
    if validation_limited:
        warnings.append(validation_warning())
    if not manifest_path.is_file():
        warnings.append(f"tcga_build_manifest_missing:{manifest_path}")
    for label, path in (("raw_counts_matrix", raw_counts_path), ("sample_metadata", sample_metadata_path), ("gene_annotation", gene_annotation_path)):
        if not path.is_file():
            warnings.append(f"tcga_{label}_missing:{path}")
    if default_group_status == "insufficient":
        warnings.append("tcga_default_tumor_normal_group_insufficient")
    available_inputs = {"tcga_expression_matrix", "expression_matrix", "raw_count_matrix"}
    if sample_metadata_path.is_file() and sample_rows:
        available_inputs.update({"tcga_sample_metadata", "sample_metadata"})
    if gene_annotation_path.is_file():
        available_inputs.add("gene_annotation")
    return {
        "status": status,
        "project_id": str(manifest.get("project_id") or metadata.get("project_id") or ""),
        "build_id": str(manifest.get("build_id") or metadata.get("build_id") or ""),
        "build_manifest_path": str(manifest_path),
        "raw_counts_matrix_path": str(raw_counts_path),
        "sample_metadata_path": str(sample_metadata_path),
        "gene_annotation_path": str(gene_annotation_path),
        "available_inputs": sorted(available_inputs),
        "sample_ids": sorted(set(matrix_samples)),
        "sample_count": len(matrix_samples),
        "gene_count": int(manifest.get("gene_count") or 0),
        "matrix_sample_count": len(matrix_samples),
        "metadata_sample_count": len(metadata_samples),
        "sample_match_status": sample_match_status,
        "sample_type_counts": sample_type_counts,
        "default_group_status": default_group_status,
        "default_group_suggestion": {
            "case_group": "Primary Tumor",
            "control_group": "Solid Tissue Normal",
            "case_count": sample_type_counts.get("Primary Tumor", 0),
            "control_count": sample_type_counts.get("Solid Tissue Normal", 0),
            "requires_user_confirmation": True,
            "auto_execute_deg": False,
        },
        "value_type_policy": _tcga_value_type_policy(),
        "validation_limited": validation_limited,
        "warnings": list(dict.fromkeys(warnings)),
    }


def _read_tcga_clinical_build_record(record: dict[str, Any]) -> dict[str, object]:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    if not isinstance(metadata, dict):
        metadata = {}
    manifest_path = Path(str(metadata.get("tcga_clinical_build_manifest_path") or ""))
    manifest = _read_json(manifest_path) if manifest_path.is_file() else {}
    summary = manifest.get("summary") if isinstance(manifest.get("summary"), dict) else {}
    if not summary:
        summary = metadata.get("tcga_clinical_summary") if isinstance(metadata.get("tcga_clinical_summary"), dict) else {}
    case_table_path = Path(str(manifest.get("case_table_path") or ""))
    mapping_table_path = Path(str(manifest.get("mapping_table_path") or ""))
    survival_table_path = Path(str(manifest.get("survival_table_path") or ""))
    warnings = [str(item) for item in manifest.get("warnings", []) or [] if str(item)]
    validation_limited = bool(manifest.get("validation_limited") or metadata.get("validation_limited"))
    if validation_limited:
        warnings.append(validation_warning())
    for label, path in (("case_table", case_table_path), ("mapping_table", mapping_table_path), ("survival_table", survival_table_path)):
        if path and str(path) != "." and not path.is_file():
            warnings.append(f"tcga_clinical_{label}_missing:{path}")
    available_inputs = {"tcga_clinical_metadata", "clinical_metadata"}
    if mapping_table_path.is_file():
        available_inputs.add("tcga_expression_clinical_mapping")
    if str(summary.get("survival_gate_status") or "") == "survival_ready_basic":
        available_inputs.add("basic_survival_metadata")
    return {
        "project_id": str(manifest.get("project_id") or metadata.get("project_id") or ""),
        "clinical_build_id": str(manifest.get("clinical_build_id") or metadata.get("clinical_build_id") or ""),
        "mode": str(manifest.get("mode") or metadata.get("mode") or ""),
        "clinical_gate_status": str(summary.get("clinical_gate_status") or manifest.get("clinical_gate_status") or metadata.get("clinical_gate_status") or "clinical_unavailable"),
        "survival_gate_status": str(summary.get("survival_gate_status") or manifest.get("survival_gate_status") or metadata.get("survival_gate_status") or "survival_unavailable"),
        "build_manifest_path": str(manifest_path),
        "clinical_manifest_path": str(manifest.get("clinical_artifact_manifest_path") or metadata.get("tcga_clinical_artifact_manifest_path") or ""),
        "case_table_path": str(case_table_path),
        "mapping_table_path": str(mapping_table_path),
        "survival_table_path": str(survival_table_path),
        "case_count": int(summary.get("case_count") or 0),
        "sample_count": int(summary.get("sample_count") or 0),
        "matched_case_count": int(summary.get("matched_case_count") or 0),
        "matched_sample_count": int(summary.get("matched_sample_count") or 0),
        "sample_case_match_ratio": float(summary.get("sample_case_match_ratio") or 0.0),
        "survival_case_count": int(summary.get("survival_case_count") or 0),
        "death_event_count": int(summary.get("death_event_count") or 0),
        "demographic_available_case_count": int(summary.get("demographic_available_case_count") or 0),
        "diagnosis_available_case_count": int(summary.get("diagnosis_available_case_count") or 0),
        "available_inputs": sorted(available_inputs),
        "validation_limited": validation_limited,
        "warnings": list(dict.fromkeys(warnings)),
    }


def _read_gtex_build_record(record: dict[str, Any]) -> dict[str, object]:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    if not isinstance(metadata, dict):
        metadata = {}
    manifest_path = Path(str(metadata.get("gtex_expression_build_manifest_path") or ""))
    if not manifest_path.is_file():
        record_path = Path(str(record.get("record_path") or ""))
        fallback = latest_gtex_expression_build_manifest_path(record_path.parents[2]) if len(record_path.parents) > 2 else None
        manifest_path = fallback if fallback is not None else manifest_path
    manifest = _read_json(manifest_path) if manifest_path.is_file() else {}
    expression_path = Path(str(manifest.get("expression_matrix_path") or metadata.get("gtex_expression_matrix_path") or ""))
    sample_metadata_path = Path(str(manifest.get("sample_metadata_path") or metadata.get("gtex_sample_metadata_path") or ""))
    donor_metadata_path = Path(str(manifest.get("donor_metadata_path") or metadata.get("gtex_donor_metadata_path") or ""))
    gene_annotation_path = Path(str(manifest.get("gene_annotation_path") or metadata.get("gtex_gene_annotation_path") or ""))
    matrix_samples = _matrix_sample_columns(expression_path)
    sample_rows = _sample_metadata_rows(sample_metadata_path)
    metadata_samples = _sample_ids_from_metadata(sample_rows)
    sample_match_status, sample_warnings = _sample_match_status(matrix_samples, metadata_samples)
    warnings = [*sample_warnings, *[str(item) for item in manifest.get("warnings", []) or [] if str(item)]]
    validation_limited = bool(manifest.get("validation_limited") or metadata.get("validation_limited"))
    if validation_limited:
        warnings.append(validation_warning())
    for label, path in (("expression_matrix", expression_path), ("sample_metadata", sample_metadata_path), ("donor_metadata", donor_metadata_path), ("gene_annotation", gene_annotation_path)):
        if not path.is_file():
            warnings.append(f"gtex_{label}_missing:{path}")
    available_inputs = {"gtex_expression_matrix", "expression_matrix"}
    if sample_metadata_path.is_file() and sample_rows:
        available_inputs.update({"gtex_sample_metadata", "sample_metadata"})
    if donor_metadata_path.is_file():
        available_inputs.add("gtex_donor_metadata")
    if gene_annotation_path.is_file():
        available_inputs.add("gene_annotation")
    return {
        "status": "gtex_expression_ready_for_data_check" if sample_match_status in {"matched", "not_checked"} else "blocked_sample_metadata_mismatch",
        "tissue_id": str(manifest.get("tissue_id") or metadata.get("tissue_id") or ""),
        "tissue_site_detail": str(manifest.get("tissue_site_detail") or metadata.get("tissue_site_detail") or ""),
        "build_id": str(manifest.get("build_id") or metadata.get("build_id") or ""),
        "build_manifest_path": str(manifest_path),
        "expression_matrix_path": str(expression_path),
        "sample_metadata_path": str(sample_metadata_path),
        "donor_metadata_path": str(donor_metadata_path),
        "gene_annotation_path": str(gene_annotation_path),
        "sample_count": len(matrix_samples) or int(manifest.get("sample_count") or 0),
        "donor_count": int(manifest.get("donor_count") or 0),
        "gene_count": int(manifest.get("gene_count") or 0),
        "sample_match_status": sample_match_status,
        "value_type_policy": manifest.get("value_type_policy") if isinstance(manifest.get("value_type_policy"), dict) else {},
        "validation_limited": validation_limited,
        "available_inputs": sorted(available_inputs),
        "warnings": list(dict.fromkeys(warnings)),
    }


def _matrix_sample_columns(path: Path) -> list[str]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        header = next(csv.reader(handle), [])
    return [cell.strip() for cell in header[1:] if cell.strip()]


def _sample_metadata_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(key or "").strip(): str(value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def _sample_ids_from_metadata(rows: list[dict[str, str]]) -> list[str]:
    ids: list[str] = []
    for row in rows:
        for key in ("sample_id", "barcode", "tcga_barcode", "sample_barcode"):
            value = str(row.get(key) or "").strip()
            if value:
                ids.append(value)
                break
    return ids


def _sample_match_status(matrix_samples: list[str], metadata_samples: list[str]) -> tuple[str, list[str]]:
    if not matrix_samples or not metadata_samples:
        return "not_checked", ["tcga_sample_match_not_checked"]
    matrix = set(matrix_samples)
    metadata = set(metadata_samples)
    if matrix == metadata:
        return "matched", []
    warnings: list[str] = []
    missing_metadata = sorted(matrix - metadata)
    missing_matrix = sorted(metadata - matrix)
    if missing_metadata:
        warnings.append("tcga_matrix_samples_missing_metadata:" + ",".join(missing_metadata))
    if missing_matrix:
        warnings.append("tcga_metadata_samples_missing_matrix:" + ",".join(missing_matrix))
    return "mismatch", warnings


def _tcga_sample_type_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        label = _tcga_sample_type_label(row)
        if not label:
            continue
        counts[label] = counts.get(label, 0) + 1
    return counts


def _tcga_sample_type_label(row: dict[str, str]) -> str:
    code = str(row.get("sample_type_code") or "").strip()
    label = str(row.get("sample_type_label") or row.get("sample_type_gdc") or row.get("sample_type") or "").strip()
    if code == "01" or label.lower() == "primary tumor":
        return "Primary Tumor"
    if code == "11" or label.lower() == "solid tissue normal":
        return "Solid Tissue Normal"
    if label:
        return label
    return code


def _tcga_value_type_policy() -> dict[str, object]:
    return {
        "raw_counts": {
            "value_type": "count",
            "default_for_deg": True,
            "default_for_display": False,
        },
        "TPM": {
            "value_type": "TPM",
            "default_for_deg": False,
            "default_for_display": True,
        },
        "FPKM": {
            "value_type": "FPKM",
            "default_for_deg": False,
            "default_for_display": True,
        },
        "FPKM-UQ": {
            "value_type": "FPKM-UQ",
            "default_for_deg": False,
            "default_for_display": True,
        },
    }


def _file_check_state(
    primary: str,
    roles: set[str],
    assets: list[dict[str, object]],
    standardization_status: str,
    item: dict[str, object],
) -> tuple[str, str, str]:
    if primary == "differential_result_table" or "differential_result_table" in roles:
        return "yellow", "needs_confirmation", "需要用户确认或补充"
    if primary == "gmt_gene_set" or "gmt_gene_set" in roles:
        return "yellow", "gsea_resource_candidate", "后续 GSEA 资源候选"
    if primary in {"raw_heavy_file", "unknown"} or standardization_status == "blocked":
        return "red", "failed", "无法使用 / 不支持 / 检查失败"
    if standardization_status == "reference_only" or roles & {"platform_annotation", "gene_annotation", "platform_reference_hint"}:
        return "yellow", "reference_only", "需要用户确认或补充"
    if any(asset.get("requires_user_confirmation") for asset in assets) or item.get("requires_user_confirmation"):
        return "yellow", "needs_confirmation", "需要用户确认或补充"
    try:
        confidence = float(item.get("confidence") or 0)
    except (TypeError, ValueError):
        confidence = 0
    if confidence and confidence < 0.6:
        return "yellow", "low_confidence", "需要用户确认或补充"
    return "green", "passed", "检查通过 / 可用于后续标准化"


def _file_source_label(item: dict[str, object]) -> str:
    source_ref = item.get("evidence") if isinstance(item.get("evidence"), dict) else {}
    manifest = source_ref.get("source_manifest") if isinstance(source_ref, dict) and isinstance(source_ref.get("source_manifest"), dict) else {}
    source = str(manifest.get("source") or "")
    if "geo" in source:
        return "GEO 下载"
    if source:
        return "本地导入" if "local" in source else source
    path = str(item.get("original_path") or "").lower()
    if "/raw_data/geo/" in path:
        return "GEO 下载"
    return "本地导入"


def _file_suggested_use(primary: str, roles: set[str], assets: list[dict[str, object]]) -> str:
    role_set = set(roles)
    for asset in assets:
        role = str(asset.get("role") or asset.get("asset_type") or "")
        if role:
            role_set.add(role)
    if role_set & CORE_INPUTS:
        return "表达矩阵候选；进入标准化前需确认值类型和样本列。"
    if role_set & {"sample_metadata", "phenotype_metadata", "clinical_metadata"}:
        return "样本 / metadata；可用于分组候选和样本信息整理。"
    if "differential_result_table" in role_set or primary == "differential_result_table":
        return "imported DEG；只能作为外部结果或富集输入。"
    if role_set & {"platform_annotation", "gene_annotation", "platform_reference_hint"}:
        return "注释 / 平台参考；用于 ID 映射确认。"
    if primary == "gmt_gene_set" or "gmt_gene_set" in role_set:
        return "GSEA 基因集资源候选；不属于当前数据文件缺失项。"
    if primary == "raw_heavy_file":
        return "RAW / heavy 文件；默认不进入标准化。"
    return "待人工确认用途。"


def _file_available_content(item: dict[str, object], roles: set[str], assets: list[dict[str, object]]) -> str:
    labels = []
    for role in sorted(roles):
        labels.append(_role_label(role))
    for asset in assets:
        role = str(asset.get("role") or asset.get("asset_type") or "")
        if role:
            labels.append(_role_label(role))
    return "、".join(dict.fromkeys(labels)) if labels else "未检测到可用内容"


def _file_missing_content(primary: str, roles: set[str], assets: list[dict[str, object]], item: dict[str, object]) -> str:
    if primary == "raw_heavy_file":
        return "需要专门预处理；不会默认进入标准化"
    if primary == "unknown":
        return "缺少可识别结构"
    if primary == "gmt_gene_set" or "gmt_gene_set" in roles:
        return "无；GSEA 资源选择在后续分析前处理"
    if (roles & CORE_INPUTS) and str(_first_nested_value(item, "matrix_profile", "gene_id_type_candidate") or "") in {"probe_id", "unknown"}:
        return "gene ID / 平台注释需确认"
    if any(asset.get("requires_user_confirmation") for asset in assets) or item.get("requires_user_confirmation"):
        return "需要用户确认用途或字段"
    return "无明确缺失"


def _file_risk_notes(primary: str, roles: set[str], item: dict[str, object]) -> str:
    if primary == "raw_heavy_file":
        return "RAW / heavy 文件不能默认作为标准化输入。"
    if primary == "differential_result_table" or "differential_result_table" in roles:
        return "imported DEG 不能作为 expression matrix 重新计算输入。"
    warning = str(item.get("warning") or "")
    warnings = [str(value) for value in item.get("warnings", []) or [] if str(value)]
    return "；".join([value for value in [warning, *warnings[:2]] if value]) or "无"


def _record_has_role(item: dict[str, object], role: str) -> bool:
    return _record_has_any_role(item, {role})


def _record_has_any_role(item: dict[str, object], roles: set[str]) -> bool:
    if str(item.get("recognized_type") or "") in roles:
        return True
    if any(str(value) in roles for value in item.get("recognized_roles", []) or []):
        return True
    for asset in item.get("detected_assets", []) or []:
        if isinstance(asset, dict) and str(asset.get("role") or asset.get("asset_type") or "") in roles:
            return True
    return False


def _first_profile_value(records: list[dict[str, object]], profile_key: str, value_key: str) -> str:
    for record in records:
        value = _first_nested_value(record, profile_key, value_key)
        if value:
            return str(value)
    return ""


def _first_nested_value(record: dict[str, object], profile_key: str, value_key: str) -> object:
    profile = record.get(profile_key)
    if isinstance(profile, dict):
        return profile.get(value_key)
    return None


def _first_species_evidence(records: list[dict[str, object]]) -> str:
    for record in records:
        metadata = record.get("metadata_profile") if isinstance(record.get("metadata_profile"), dict) else {}
        evidence = metadata.get("species_evidence") if isinstance(metadata, dict) else []
        if isinstance(evidence, list) and evidence:
            return str(evidence[0])
        profile = record.get("content_profile") if isinstance(record.get("content_profile"), dict) else {}
        evidence = profile.get("species_evidence") if isinstance(profile, dict) else []
        if isinstance(evidence, list) and evidence:
            return str(evidence[0])
    return ""


def _role_label(role: str) -> str:
    labels = {
        "expression_matrix": "表达矩阵",
        "normalized_expression_matrix": "标准化表达矩阵",
        "raw_count_matrix": "原始计数矩阵",
        "sample_metadata": "样本信息",
        "phenotype_metadata": "表型 / 分组候选",
        "clinical_metadata": "临床信息",
        "platform_annotation": "平台注释",
        "gene_annotation": "基因注释",
        "platform_reference_hint": "平台参考提示",
        "differential_result_table": "imported DEG",
        "gmt_gene_set": "GSEA 基因集",
    }
    return labels.get(role, role)


def _gsea_gene_set_status(selected_gene_set: dict[str, object] | None) -> dict[str, object]:
    if selected_gene_set is None:
        return {
            "status": "not_selected",
            "label": "GSEA 基因集：未选择",
            "message": "GSEA 基因集用于后续 GSEA 分析，不属于当前 GEO / TCGA / GTEx 数据文件本身。未选择基因集不影响当前数据检查、标准化准备或 DEG preflight。",
            "blocks_current_data_check": False,
            "blocks_standardization": False,
            "blocks_deg_preflight": False,
            "blocks_gsea_preflight": True,
            "selected_resource": {},
        }
    if str(selected_gene_set.get("status") or "") != "available":
        return {
            "status": "unavailable",
            "label": "GSEA 基因集资源不可用",
            "message": "后续 GSEA 前需要重新选择可用资源。",
            "blocks_current_data_check": False,
            "blocks_standardization": False,
            "blocks_deg_preflight": False,
            "blocks_gsea_preflight": True,
            "selected_resource": selected_gene_set,
        }
    return {
        "status": "selected",
        "label": f"GSEA 基因集：已选择 {selected_gene_set.get('name') or selected_gene_set.get('resource_id')}",
        "message": "已选择本地 GSEA 基因集资源；后续 GSEA preflight 会继续校验该资源。",
        "blocks_current_data_check": False,
        "blocks_standardization": False,
        "blocks_deg_preflight": False,
        "blocks_gsea_preflight": False,
        "selected_resource": selected_gene_set,
    }


def load_readiness_artifacts(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    readiness_path = root / READINESS_REPORT
    matrix_path = root / CAPABILITY_MATRIX
    return {
        "readiness_report": _read_json(readiness_path) if readiness_path.exists() else None,
        "capability_matrix": _read_json(matrix_path) if matrix_path.exists() else None,
        "readiness_path": str(readiness_path),
        "matrix_path": str(matrix_path),
    }


def readiness_status_zh(status: str) -> str:
    return {
        "not_ready": "尚未准备好",
        "partially_ready": "部分准备就绪",
        "ready": "已准备好",
        "ready_with_warnings": "已准备好，但存在警告",
        "unavailable": "暂不可运行",
    }.get(status, "未知")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
