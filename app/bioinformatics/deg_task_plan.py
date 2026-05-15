from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app.bioinformatics.group_comparison_design import GROUP_COMPARISON_DESIGN, load_group_comparison_design
from app.bioinformatics.standardized_asset_selection import resolve_standardized_assets


DEG_TASK_PLAN = Path("manifests") / "analysis_tasks" / "deg_task_plan.json"
DEG_TASK_PLAN_SCHEMA_VERSION = "bioinformatics_deg_task_plan.v1"
DEG_PREFLIGHT_MANIFEST = Path("analysis") / "deg" / "preflight" / "deg_preflight_manifest.json"


class DegPreflightResult:
    def __init__(self, *, status: str, manifest_path: Path, manifest: dict[str, object]) -> None:
        self.status = status
        self.manifest_path = manifest_path
        self.manifest = manifest


def deg_task_plan_path(project_root: str | Path) -> Path:
    return Path(project_root).expanduser().resolve() / DEG_TASK_PLAN


def load_deg_task_plan(project_root: str | Path) -> dict[str, object] | None:
    path = deg_task_plan_path(project_root)
    if not path.is_file():
        return None
    payload = _read_json(path)
    return payload if payload.get("schema_version") == DEG_TASK_PLAN_SCHEMA_VERSION else None


def build_deg_preflight(
    project_root: str | Path,
    *,
    method: str = "DEG executor not connected",
    log2fc_threshold: float = 1.0,
    p_value_threshold: float = 0.05,
    fdr_threshold: float = 0.05,
) -> DegPreflightResult:
    from app.bioinformatics.comparison_config import (
        comparison_sample_match_status,
        expression_samples_from_recognition_report,
        load_confirmed_comparison_config,
    )
    from app.bioinformatics.project_recognition import load_recognition_report
    from app.bioinformatics.project_standardization import load_standardization_artifacts

    root = Path(project_root).expanduser().resolve()
    recognition = load_recognition_report(root) or {}
    artifacts = load_standardization_artifacts(root)
    registry = artifacts.get("registry")
    assets = [item for item in (registry or {}).get("assets", []) or [] if isinstance(item, dict)] if isinstance(registry, dict) else []
    expression_assets = [item for item in assets if str(item.get("asset_type") or "") in {"raw_count_matrix", "count_matrix", "expression_matrix", "normalized_expression_matrix"}]
    metadata_assets = [item for item in assets if str(item.get("asset_type") or "") in {"sample_metadata", "phenotype_metadata"}]
    comparison = load_confirmed_comparison_config(root)
    expression_samples = expression_samples_from_recognition_report(recognition if isinstance(recognition, dict) else {})
    match = comparison_sample_match_status(comparison, expression_samples)

    checks: list[dict[str, object]] = []
    checks.append(_check("expression_matrix", bool(expression_assets), "已找到可用于校验的表达矩阵。", "缺 count matrix 或可用表达矩阵。"))
    checks.append(_check("sample_metadata", bool(metadata_assets or comparison is not None), "样本信息可由样本表或用户确认的比较组设置构建。", "缺 sample metadata，且无法从用户确认的比较组设置构建样本信息。"))
    checks.append(_check("group_design", comparison is not None, "分组设计已确认。", "缺分组设计，请先确认分组与比较设计。"))
    checks.append(_check("sample_name_match", str(match.get("sample_id_match_status") or "not_checked") != "mismatch", "样本名匹配未发现阻塞。", "样本名在表达矩阵和分组中不匹配。"))
    blockers = [str(item["message_zh"]) for item in checks if item.get("status") == "blocked"]
    warnings = ["当前版本尚未执行真实差异分析；preflight 只保存配置草稿和输入校验。"]
    status = "blocked" if blockers else "passed"
    path = root / DEG_PREFLIGHT_MANIFEST
    manifest = {
        "schema_version": "biomedpilot.deg_preflight_manifest.v1",
        "generated_at": _now(),
        "status": status,
        "status_label_zh": _preflight_status_label(status),
        "semantic_boundary": "input_preflight_only_not_deg_result",
        "not_a_result": True,
        "execution": "not_run",
        "project_root": str(root),
        "manifest_path": str(path),
        "config_draft": {
            "method": method,
            "log2fc_threshold": log2fc_threshold,
            "p_value_threshold": p_value_threshold,
            "fdr_threshold": fdr_threshold,
            "note": "仅配置草稿和输入校验；未运行真实差异分析。",
        },
        "checks": checks,
        "blockers": blockers,
        "warnings": warnings,
        "developer_diagnostics": {
            "expression_assets": expression_assets,
            "metadata_assets": metadata_assets,
            "comparison_sample_match": match,
            "standardization_registry_path": artifacts.get("registry_path") or "",
        },
    }
    _atomic_write_json(path, manifest)
    return DegPreflightResult(
        status=status,
        manifest_path=path,
        manifest=manifest,
    )


def load_deg_preflight_manifest(project_root: str | Path) -> dict[str, object] | None:
    path = Path(project_root).expanduser().resolve() / DEG_PREFLIGHT_MANIFEST
    if not path.is_file():
        return None
    manifest = _read_json(path)
    if manifest.get("schema_version") != "biomedpilot.deg_preflight_manifest.v1":
        return None
    return manifest


def build_deg_task_plan_context(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    resolved_count = resolve_standardized_assets(root, asset_types={"count_matrix"})
    count_assets = [asset for asset in resolved_count.get("assets", []) or [] if isinstance(asset, dict) and asset.get("asset_type") == "count_matrix"]
    count_asset = count_assets[0] if count_assets else {}
    group_design = load_group_comparison_design(root) or {}
    confirmed_comparisons = [
        comparison
        for comparison in group_design.get("comparisons", []) or []
        if isinstance(comparison, dict) and comparison.get("status") == "confirmed"
    ]
    missing: list[str] = []
    warnings = [str(item) for item in resolved_count.get("warnings", []) or [] if str(item)]
    if not count_asset:
        missing.append("default_count_matrix")
        warnings.append("缺少默认 count matrix。请先在标准化资产页选择默认资产。")
    if not group_design or not confirmed_comparisons:
        missing.append("confirmed_group_design")
        warnings.append("缺少 confirmed group design。请先确认分组与比较设计。")
    plan = load_deg_task_plan(root)
    return {
        "schema_version": "bioinformatics_deg_task_plan_context.v1",
        "project_root": str(root),
        "plan_path": str(root / DEG_TASK_PLAN),
        "source_group_design_path": str(root / GROUP_COMPARISON_DESIGN),
        "count_asset": count_asset,
        "confirmed_comparisons": confirmed_comparisons,
        "existing_plan": plan or {},
        "can_create_plan": not missing,
        "missing": list(dict.fromkeys(missing)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def save_deg_task_plan(
    project_root: str | Path,
    *,
    selected_comparison_names: list[str] | None = None,
    method_name: str = "DESeq2",
    padj: float = 0.05,
    abs_log2fc: float = 1.0,
) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    context = build_deg_task_plan_context(root)
    if not context.get("can_create_plan"):
        warnings = "；".join(str(item) for item in context.get("warnings", []) or [] if str(item))
        raise ValueError(warnings or "缺少 DEG task plan 配置输入。")
    count_asset = context["count_asset"] if isinstance(context.get("count_asset"), dict) else {}
    comparisons = [comparison for comparison in context.get("confirmed_comparisons", []) or [] if isinstance(comparison, dict)]
    if selected_comparison_names:
        selected = set(selected_comparison_names)
        comparisons = [comparison for comparison in comparisons if str(comparison.get("comparison_name") or "") in selected]
    if not comparisons:
        raise ValueError("未选择 confirmed comparison，无法创建 DEG task plan。")
    now = _now()
    existing = load_deg_task_plan(root) or {}
    payload = {
        "schema_version": DEG_TASK_PLAN_SCHEMA_VERSION,
        "task_type": "differential_expression_recompute",
        "status": "configured_not_run",
        "source_count_asset_id": count_asset.get("asset_id") or "",
        "source_count_asset_type": count_asset.get("asset_type") or "count_matrix",
        "source_count_asset_file": count_asset.get("source_file") or count_asset.get("file_path") or "",
        "source_group_design_path": str(GROUP_COMPARISON_DESIGN),
        "comparisons": [_comparison_payload(comparison) for comparison in comparisons],
        "method": {"name": method_name, "status": "planned_placeholder"},
        "thresholds": {"padj": padj, "abs_log2fc": abs_log2fc},
        "created_at": existing.get("created_at") or now,
        "updated_at": now,
        "note": "只保存 DEG 任务配置，不执行真实差异表达分析，不生成 DEG 结果。",
    }
    _atomic_write_json(root / DEG_TASK_PLAN, payload)
    return payload


def _preflight_status(status: str) -> str:
    if status in {"passed", "warning", "blocked"}:
        return status
    if status == "passed_with_warnings":
        return "warning"
    if status == "failed":
        return "blocked"
    return status or "draft"


def _preflight_status_label(status: str) -> str:
    return {
        "passed": "通过",
        "warning": "警告",
        "blocked": "阻塞",
        "draft": "草稿",
    }.get(status, status or "未知")


def _check(check_id: str, passed: bool, ok_message: str, blocked_message: str) -> dict[str, object]:
    return {
        "check_id": check_id,
        "status": "passed" if passed else "blocked",
        "message_zh": ok_message if passed else blocked_message,
    }


def _preflight_checks(manifest: dict[str, object]) -> list[dict[str, object]]:
    if isinstance(manifest.get("checks"), list):
        return [item for item in manifest["checks"] if isinstance(item, dict)]  # type: ignore[index]
    checks: list[dict[str, object]] = []
    errors = [str(item) for item in manifest.get("errors", []) or [] if str(item)]
    warnings = [str(item) for item in manifest.get("warnings", []) or [] if str(item)]
    if errors:
        checks.append({"check_id": "blockers", "status": "blocked", "message_zh": "；".join(errors)})
    if warnings:
        checks.append({"check_id": "warnings", "status": "warning", "message_zh": "；".join(warnings)})
    if not checks:
        checks.append({"check_id": "inputs", "status": "passed", "message_zh": "preflight 输入检查通过。"})
    return checks


def _comparison_payload(comparison: dict[str, object]) -> dict[str, object]:
    return {
        "comparison_name": comparison.get("comparison_name") or "",
        "case_group": comparison.get("case_group") or "",
        "control_group": comparison.get("control_group") or "",
        "status": "selected",
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    data = json.dumps(payload, ensure_ascii=False, indent=2)
    with temp_path.open("w", encoding="utf-8") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp_path, path)
