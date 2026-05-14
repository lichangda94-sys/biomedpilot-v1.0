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
from app.bioinformatics.project_recognition import load_recognition_report
from app.bioinformatics.standardization_confirmation import load_standardization_confirmation


READINESS_REPORT = Path("logs") / "readiness" / "readiness_report.json"
CAPABILITY_MATRIX = Path("manifests") / "analysis_capability_matrix.json"

ANALYSIS_ROWS = (
    ("differential_expression", "差异表达分析", {"expression_matrix", "sample_metadata", "comparison_config"}),
    ("enrichment", "富集分析", {"expression_matrix"}),
    ("gsea", "GSEA", {"expression_matrix", "gmt_gene_set"}),
    ("correlation", "相关性分析", {"expression_matrix"}),
    ("survival", "生存分析", {"expression_matrix", "clinical_metadata"}),
    ("clinical_association", "临床变量关联", {"clinical_metadata"}),
    ("tcga_gtex_joint", "TCGA + GTEx 联合分析", {"expression_matrix", "sample_metadata"}),
    ("reporting", "报告生成", {"analysis_result"}),
)

CORE_INPUTS = {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix"}
EXPRESSION_COMPATIBLE_INPUTS = {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix"}


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
    if key == "differential_expression":
        if "样本 ID 不匹配。" in warnings:
            return "请修正比较组样本 ID，或选择与比较组匹配的表达矩阵。"
        if "比较组已确认，但缺少表达矩阵。" in warnings or "expression_matrix" in missing:
            return "请补充表达矩阵。"
        if "comparison_config" in missing:
            return "请确认比较组。"
    return "请补充缺失输入或返回前序页面。"


def _add_available_input(available: set[str], role: str) -> None:
    if not role or role in {"unknown", "differential_result_table", "unsupported", "archive"}:
        return
    available.add(role)
    if role in EXPRESSION_COMPATIBLE_INPUTS:
        available.add("expression_matrix")


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
