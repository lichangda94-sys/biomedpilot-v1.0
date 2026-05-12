from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app.bioinformatics.group_comparison_design import GROUP_COMPARISON_DESIGN, load_group_comparison_design
from app.bioinformatics.standardized_asset_selection import resolve_standardized_assets


DEG_TASK_PLAN = Path("manifests") / "analysis_tasks" / "deg_task_plan.json"
DEG_TASK_PLAN_SCHEMA_VERSION = "bioinformatics_deg_task_plan.v1"


def deg_task_plan_path(project_root: str | Path) -> Path:
    return Path(project_root).expanduser().resolve() / DEG_TASK_PLAN


def load_deg_task_plan(project_root: str | Path) -> dict[str, object] | None:
    path = deg_task_plan_path(project_root)
    if not path.is_file():
        return None
    payload = _read_json(path)
    return payload if payload.get("schema_version") == DEG_TASK_PLAN_SCHEMA_VERSION else None


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
