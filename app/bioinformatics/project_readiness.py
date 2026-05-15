from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.bioinformatics.comparison_config import (
    comparison_sample_match_status,
    comparison_summary_text,
    expression_samples_from_recognition_report,
    load_confirmed_comparison_config,
)
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
    confirmed_comparison = load_confirmed_comparison_config(root)
    if confirmed_comparison is not None:
        available.add("comparison_config")
    expression_samples = expression_samples_from_recognition_report(recognition if isinstance(recognition, dict) else {})
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
    if not has_core_input:
        warnings.append("无表达矩阵。")
    if "sample_metadata" not in available:
        warnings.append("样本信息缺失。")
    if "clinical_metadata" not in available:
        warnings.append("临床信息缺失。")
    rows = []
    deg_ready = False
    for key, label, required in ANALYSIS_ROWS:
        missing = sorted(_missing_inputs_for_row(key, required, available, confirmed_comparison))
        can_run = bool(has_core_input) and not missing and (key not in {"tcga_gtex_joint", "reporting"})
        row_warnings = []
        if key == "differential_expression":
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
        ),
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
            if str(item.get("semantic_type") or "") == "rna_seq_integrated_result_table":
                _add_available_input(available, "raw_count_matrix")
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
    if role == "raw_count_matrix":
        available.add("count_matrix")
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
) -> dict[str, object]:
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
