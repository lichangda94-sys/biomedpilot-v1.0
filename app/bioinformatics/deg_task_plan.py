from __future__ import annotations

import csv
import gzip
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from app.bioinformatics.comparison_config import (
    comparison_sample_match_status,
    comparison_summary_text,
    confirmed_group_assignments,
    expression_samples_from_recognition_report,
    load_confirmed_comparison_config,
)
from app.bioinformatics.project_recognition import load_recognition_report
from app.bioinformatics.project_standardization import load_standardization_artifacts


DEG_PREFLIGHT_MANIFEST = Path("analysis") / "deg" / "preflight" / "deg_preflight_manifest.json"
EXPRESSION_ASSET_TYPES = {"raw_count_matrix", "expression_matrix", "normalized_expression_matrix"}
METADATA_ASSET_TYPES = {"sample_metadata", "phenotype_metadata"}
MINIMUM_GROUP_SAMPLES = 1
RECOMMENDED_GROUP_SAMPLES = 2


@dataclass(frozen=True)
class DegPreflightResult:
    status: str
    manifest_path: Path
    manifest: dict[str, object]


def build_deg_preflight(
    project_root: str | Path,
    *,
    method: str = "DEG executor not connected",
    log2fc_threshold: float = 1.0,
    p_value_threshold: float = 0.05,
    fdr_threshold: float = 0.05,
) -> DegPreflightResult:
    """Validate and materialize DEG inputs without running DEG analysis."""

    root = Path(project_root).expanduser().resolve()
    recognition = load_recognition_report(root) or {}
    standardization = load_standardization_artifacts(root)
    registry = standardization.get("registry")
    assets = [item for item in (registry or {}).get("assets", []) or [] if isinstance(item, dict)] if isinstance(registry, dict) else []
    expression_assets = [asset for asset in assets if str(asset.get("asset_type") or "") in EXPRESSION_ASSET_TYPES]
    metadata_assets = [asset for asset in assets if str(asset.get("asset_type") or "") in METADATA_ASSET_TYPES]
    imported_deg_assets = [asset for asset in assets if str(asset.get("asset_type") or "") == "differential_result_table"]
    imported_deg_detected = bool(imported_deg_assets or _recognition_has_imported_deg(recognition))
    selected_expression = _preferred_expression_asset(expression_assets)
    matrix_profile = _matrix_profile(_asset_path(root, selected_expression)) if selected_expression is not None else {}
    expression_samples = set(str(item) for item in matrix_profile.get("sample_columns", []) or [] if str(item).strip())
    if not expression_samples:
        expression_samples = expression_samples_from_recognition_report(recognition if isinstance(recognition, dict) else {})

    comparison_config = load_confirmed_comparison_config(root)
    assignments = confirmed_group_assignments(comparison_config)
    match_status = comparison_sample_match_status(comparison_config, expression_samples)

    checks: list[dict[str, object]] = []
    blockers: list[str] = []
    warnings: list[str] = []
    _add_check(
        checks,
        blockers,
        "expression_matrix",
        bool(selected_expression),
        "已找到可用于校验的表达矩阵。",
        "缺 count matrix 或可用表达矩阵。",
    )
    _add_check(
        checks,
        blockers,
        "sample_columns",
        bool(expression_samples),
        f"识别到 {len(expression_samples)} 个表达矩阵样本列。",
        "样本列未能从表达矩阵或识别报告中确认。",
    )
    _add_check(
        checks,
        blockers,
        "sample_metadata",
        bool(metadata_assets or assignments),
        "样本信息可由样本表或已确认分组构建。",
        "缺 sample metadata，且无法从已确认分组构建样本信息。",
    )
    _add_check(
        checks,
        blockers,
        "group_design",
        comparison_config is not None,
        "分组与比较设计已确认。",
        "缺分组设计，请先确认分组与比较设计。",
    )
    case_group = str(getattr(comparison_config, "case_group", "") or "")
    control_group = str(getattr(comparison_config, "control_group", "") or "")
    _add_check(
        checks,
        blockers,
        "comparison_design",
        bool(case_group and control_group and case_group != control_group),
        "case/control 或用户确认比较设计合法。",
        "比较设计不合法，case/control 不能为空且不能相同。",
    )

    group_sizes = dict(getattr(comparison_config, "group_sizes", {}) or {}) if comparison_config is not None else {}
    case_count = int(group_sizes.get(case_group, 0) or 0)
    control_count = int(group_sizes.get(control_group, 0) or 0)
    if comparison_config is not None and getattr(comparison_config, "assignments", ()):
        _add_check(
            checks,
            blockers,
            "case_control_non_empty",
            case_count >= MINIMUM_GROUP_SAMPLES and control_count >= MINIMUM_GROUP_SAMPLES,
            f"{case_group or 'case'}={case_count}，{control_group or 'control'}={control_count}。",
            "case/control 至少需要各有 1 个样本。",
        )
        if case_count < RECOMMENDED_GROUP_SAMPLES or control_count < RECOMMENDED_GROUP_SAMPLES:
            warnings.append("每组少于 2 个样本，只能作为配置校验，不适合正式 DEG。")

    match = str(match_status.get("sample_id_match_status") or "not_checked")
    matched_count = int(match_status.get("matched_sample_count") or 0)
    sample_match_ok = match in {"matched", "partial", "not_checked"} and (not assignments or matched_count > 0)
    _add_check(
        checks,
        blockers,
        "sample_name_match",
        sample_match_ok,
        f"样本名匹配状态：{_sample_match_label(match)}。",
        "样本名在表达矩阵和分组中不匹配。",
    )
    if match == "partial":
        warnings.append("部分样本名未匹配；正式执行前需要人工确认样本范围。")
    elif match == "not_checked" and comparison_config is not None:
        warnings.append("比较设计已确认，但样本名尚未完全校验。")

    matrix_numeric_status = str(matrix_profile.get("numeric_status") or "not_checked")
    _add_check(
        checks,
        blockers,
        "numeric_matrix",
        matrix_numeric_status in {"ok", "not_checked"},
        str(matrix_profile.get("numeric_message") or "数值矩阵未检查。"),
        str(matrix_profile.get("numeric_message") or "表达矩阵包含明显非数值问题。"),
    )
    if matrix_numeric_status == "warning":
        warnings.append(str(matrix_profile.get("numeric_message") or "表达矩阵存在轻量数值警告。"))

    if imported_deg_detected and not selected_expression:
        warnings.append("识别到 imported DEG，但导入差异结果不能作为重新计算 DEG 的表达矩阵输入。")

    status = "blocked" if blockers else ("warning" if warnings else "passed")
    generated_at = _now()
    manifest = {
        "schema_version": "biomedpilot.deg_preflight_manifest.v1",
        "generated_at": generated_at,
        "status": status,
        "status_label_zh": _status_label(status),
        "semantic_boundary": "input_preflight_only_not_deg_result",
        "not_a_result": True,
        "execution": "not_run",
        "project_root": str(root),
        "config_draft": {
            "method": method,
            "log2fc_threshold": log2fc_threshold,
            "p_value_threshold": p_value_threshold,
            "fdr_threshold": fdr_threshold,
            "note": "仅配置草稿和输入校验；未运行真实差异分析。",
        },
        "input_summary": {
            "has_count_matrix": _has_asset_type(expression_assets, "raw_count_matrix"),
            "has_expression_matrix": bool(expression_assets),
            "has_normalized_matrix": _has_asset_type(expression_assets, "normalized_expression_matrix"),
            "has_sample_metadata": bool(metadata_assets or assignments),
            "has_group_design": comparison_config is not None,
            "selected_expression_label": _asset_label(selected_expression),
            "sample_count": len(expression_samples),
            "gene_count_preview": matrix_profile.get("gene_count_preview", 0),
            "imported_deg_detected": imported_deg_detected,
        },
        "comparison_summary": {
            "comparison_id": str(getattr(comparison_config, "comparison_id", "") or ""),
            "case_group": case_group,
            "control_group": control_group,
            "group_sizes": group_sizes,
            "sample_match": match_status,
            "summary_zh": comparison_summary_text(comparison_config),
        },
        "checks": checks,
        "blockers": blockers,
        "warnings": warnings,
        "developer_diagnostics": {
            "selected_expression_asset": selected_expression or {},
            "metadata_assets": metadata_assets,
            "standardization_registry_path": standardization.get("registry_path") or "",
            "matrix_profile": matrix_profile,
        },
        "forbidden_outputs": [
            "DEG result table",
            "volcano plot",
            "enrichment result",
            "formal report conclusion",
        ],
    }
    path = root / DEG_PREFLIGHT_MANIFEST
    _write_json(path, manifest)
    return DegPreflightResult(status=status, manifest_path=path, manifest=manifest)


def load_deg_preflight_manifest(project_root: str | Path) -> dict[str, object] | None:
    path = Path(project_root).expanduser().resolve() / DEG_PREFLIGHT_MANIFEST
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _preferred_expression_asset(assets: list[dict[str, object]]) -> dict[str, object] | None:
    priority = {"raw_count_matrix": 0, "expression_matrix": 1, "normalized_expression_matrix": 2}
    return min(assets, key=lambda item: priority.get(str(item.get("asset_type") or ""), 99), default=None)


def _asset_path(root: Path, asset: dict[str, object] | None) -> Path | None:
    if not asset:
        return None
    for key in ("file_path", "source_file"):
        value = str(asset.get(key) or "")
        if not value:
            continue
        path = Path(value).expanduser()
        resolved = path if path.is_absolute() else root / path
        if resolved.is_file() or key == "source_file":
            return resolved
    return None


def _recognition_has_imported_deg(recognition: dict[str, object] | None) -> bool:
    if not isinstance(recognition, dict):
        return False
    for item in recognition.get("files", []) or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("recognized_type") or "") == "differential_result_table":
            return True
        for asset in item.get("detected_assets", []) or []:
            if isinstance(asset, dict) and str(asset.get("asset_type") or asset.get("role") or "") == "differential_result_table":
                return True
    return False


def _matrix_profile(path: Path | None) -> dict[str, object]:
    if path is None:
        return {"numeric_status": "not_checked", "numeric_message": "未选择表达矩阵。"}
    if not path.is_file():
        return {"numeric_status": "blocked", "numeric_message": "表达矩阵文件不存在。", "path": str(path)}
    try:
        rows = list(_read_delimited_preview(path, limit=30))
    except Exception as exc:
        return {"numeric_status": "blocked", "numeric_message": f"表达矩阵预览读取失败：{exc}", "path": str(path)}
    if not rows:
        return {"numeric_status": "blocked", "numeric_message": "表达矩阵为空。", "path": str(path)}
    header = rows[0]
    sample_columns = [cell.strip() for cell in header[1:] if str(cell).strip()]
    numeric_cells = 0
    checked_cells = 0
    for row in rows[1:]:
        for cell in row[1 : len(header)]:
            value = str(cell).strip()
            if value == "":
                continue
            checked_cells += 1
            try:
                float(value)
            except ValueError:
                continue
            numeric_cells += 1
    if checked_cells == 0:
        numeric_status = "blocked"
        numeric_message = "表达矩阵预览中没有可检查的数值单元格。"
    else:
        ratio = numeric_cells / checked_cells
        if ratio >= 0.9:
            numeric_status = "ok"
            numeric_message = "表达矩阵预览为数值型。"
        elif ratio >= 0.75:
            numeric_status = "warning"
            numeric_message = "表达矩阵大部分为数值型，但存在少量非数值单元格。"
        else:
            numeric_status = "blocked"
            numeric_message = "表达矩阵包含明显非数值问题。"
    return {
        "path": str(path),
        "sample_columns": sample_columns,
        "sample_count": len(sample_columns),
        "gene_count_preview": max(0, len(rows) - 1),
        "numeric_status": numeric_status,
        "numeric_message": numeric_message,
    }


def _read_delimited_preview(path: Path, *, limit: int) -> Iterable[list[str]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace", newline="") as handle:  # type: ignore[arg-type]
        sample = handle.readline()
        if not sample:
            return
        delimiter = "," if sample.count(",") > sample.count("\t") else "\t"
        yield next(csv.reader([sample], delimiter=delimiter))
        reader = csv.reader(handle, delimiter=delimiter)
        for index, row in enumerate(reader):
            if index >= limit:
                break
            yield row


def _add_check(
    checks: list[dict[str, object]],
    blockers: list[str],
    check_id: str,
    passed: bool,
    passed_message: str,
    blocked_message: str,
) -> None:
    checks.append(
        {
            "check_id": check_id,
            "status": "passed" if passed else "blocked",
            "message_zh": passed_message if passed else blocked_message,
        }
    )
    if not passed:
        blockers.append(blocked_message)


def _has_asset_type(assets: Iterable[dict[str, object]], asset_type: str) -> bool:
    return any(str(item.get("asset_type") or "") == asset_type for item in assets)


def _asset_label(asset: dict[str, object] | None) -> str:
    if not asset:
        return ""
    return str(asset.get("label_zh") or asset.get("asset_type") or "表达矩阵")


def _sample_match_label(status: str) -> str:
    return {
        "matched": "完全匹配",
        "partial": "部分匹配",
        "mismatch": "不匹配",
        "not_checked": "未完成校验",
    }.get(status, status or "未完成校验")


def _status_label(status: str) -> str:
    return {
        "passed": "校验通过",
        "blocked": "存在阻塞",
        "warning": "有警告",
        "draft": "配置草稿",
    }.get(status, "未知状态")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
