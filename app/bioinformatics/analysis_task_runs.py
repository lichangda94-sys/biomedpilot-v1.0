from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.bioinformatics.deg_task_plan import DEG_TASK_PLAN, build_deg_task_plan_context, load_deg_task_plan
from app.bioinformatics.group_comparison_design import GROUP_COMPARISON_DESIGN, load_group_comparison_design
from app.bioinformatics.standardized_asset_selection import resolve_standardized_assets


ANALYSIS_RUNS_ROOT = Path("analysis_runs")
ANALYSIS_TASK_RUN_SCHEMA_VERSION = "bioinformatics_analysis_task_run.v1"
ALLOWED_TASK_RUN_STATUSES = {
    "configured_not_run",
    "queued",
    "running",
    "completed",
    "failed",
    "cancelled",
    "skipped_dry_run",
}


def analysis_runs_root(project_root: str | Path) -> Path:
    return Path(project_root).expanduser().resolve() / ANALYSIS_RUNS_ROOT


def task_run_path(project_root: str | Path, task_family: str, run_id: str) -> Path:
    root = Path(project_root).expanduser().resolve()
    safe_family = _safe_segment(task_family)
    safe_run_id = _safe_segment(run_id)
    path = root / ANALYSIS_RUNS_ROOT / safe_family / safe_run_id
    _ensure_within_root(root, path)
    return path


def load_analysis_task_run(project_root: str | Path, task_family: str, run_id: str) -> dict[str, object] | None:
    manifest = task_run_path(project_root, task_family, run_id) / "task_run.json"
    if not manifest.is_file():
        return None
    payload = _read_json(manifest)
    if payload.get("schema_version") != ANALYSIS_TASK_RUN_SCHEMA_VERSION:
        return None
    payload["run_dir"] = str(manifest.parent)
    payload["task_run_path"] = str(manifest)
    return payload


def list_analysis_task_runs(project_root: str | Path, *, task_family: str | None = None) -> list[dict[str, object]]:
    root = Path(project_root).expanduser().resolve()
    base = root / ANALYSIS_RUNS_ROOT
    families = [_safe_segment(task_family)] if task_family else []
    if not families and base.is_dir():
        families = [path.name for path in sorted(base.iterdir()) if path.is_dir()]
    runs: list[dict[str, object]] = []
    for family in families:
        family_dir = base / family
        if not family_dir.is_dir():
            continue
        for manifest in sorted(family_dir.glob("*/task_run.json")):
            try:
                payload = _read_json(manifest)
            except Exception:
                continue
            if payload.get("schema_version") != ANALYSIS_TASK_RUN_SCHEMA_VERSION:
                continue
            payload["run_dir"] = str(manifest.parent)
            payload["task_run_path"] = str(manifest)
            runs.append(payload)
    return sorted(runs, key=lambda item: str(item.get("created_at") or ""), reverse=True)


def build_deg_task_run_context(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    plan = load_deg_task_plan(root) or {}
    plan_context = build_deg_task_plan_context(root)
    group_design = load_group_comparison_design(root) or {}
    resolved_count = resolve_standardized_assets(root, asset_types={"count_matrix"})
    count_assets = [asset for asset in resolved_count.get("assets", []) or [] if isinstance(asset, dict) and asset.get("asset_type") == "count_matrix"]
    default_count_asset = count_assets[0] if count_assets else {}
    confirmed_comparisons = [
        comparison
        for comparison in group_design.get("comparisons", []) or []
        if isinstance(comparison, dict) and comparison.get("status") == "confirmed"
    ]
    missing: list[str] = []
    warnings = [str(item) for item in resolved_count.get("warnings", []) or [] if str(item)]
    if not plan:
        missing.append("deg_task_plan")
        warnings.append("请先配置 DEG 分析任务。")
    if not default_count_asset:
        missing.append("default_count_matrix")
        warnings.append("请先在标准化资产页面选择默认 count matrix。")
    elif plan and str(plan.get("source_count_asset_id") or "") != str(default_count_asset.get("asset_id") or ""):
        missing.append("default_count_matrix")
        warnings.append("默认 count matrix 与 DEG task plan 不一致，请重新配置 DEG 分析任务。")
    if not group_design or not confirmed_comparisons:
        missing.append("confirmed_group_design")
        warnings.append("请先确认分组与比较设计。")
    if plan and not [item for item in plan.get("comparisons", []) or [] if isinstance(item, dict)]:
        missing.append("selected_comparisons")
        warnings.append("DEG task plan 中没有可运行的比较。")
    return {
        "schema_version": "bioinformatics_deg_task_run_context.v1",
        "project_root": str(root),
        "plan_path": str(root / DEG_TASK_PLAN),
        "group_design_path": str(root / GROUP_COMPARISON_DESIGN),
        "plan": plan,
        "default_count_asset": default_count_asset,
        "group_design": group_design,
        "confirmed_comparisons": confirmed_comparisons,
        "can_create_run": not missing,
        "missing": list(dict.fromkeys(missing)),
        "warnings": list(dict.fromkeys(warnings + [str(item) for item in plan_context.get("warnings", []) or [] if str(item) and not plan])),
    }


def create_deg_task_run(project_root: str | Path, *, execution_mode: str = "dry_run") -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    context = build_deg_task_run_context(root)
    if not context.get("can_create_run"):
        warnings = "；".join(str(item) for item in context.get("warnings", []) or [] if str(item))
        raise ValueError(warnings or "缺少 DEG task run 输入。")
    plan = context["plan"] if isinstance(context.get("plan"), dict) else {}
    count_asset = context["default_count_asset"] if isinstance(context.get("default_count_asset"), dict) else {}
    comparisons = [item for item in plan.get("comparisons", []) or [] if isinstance(item, dict)]
    now = _now()
    run_id = _unique_run_id(root, "deg", "deg_run")
    run_dir = task_run_path(root, "deg", run_id)
    run_dir.mkdir(parents=True, exist_ok=False)
    log_dir = run_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    status = "skipped_dry_run" if execution_mode == "dry_run" else "configured_not_run"
    parameters = {
        "method": (plan.get("method") or {}).get("name") if isinstance(plan.get("method"), dict) else "",
        "method_status": (plan.get("method") or {}).get("status") if isinstance(plan.get("method"), dict) else "",
        "padj_threshold": (plan.get("thresholds") or {}).get("padj") if isinstance(plan.get("thresholds"), dict) else None,
        "abs_log2fc_threshold": (plan.get("thresholds") or {}).get("abs_log2fc") if isinstance(plan.get("thresholds"), dict) else None,
    }
    payload = {
        "schema_version": ANALYSIS_TASK_RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "task_type": "differential_expression_recompute",
        "task_family": "deg",
        "status": status,
        "execution_mode": execution_mode,
        "source_task_plan": str(DEG_TASK_PLAN),
        "source_assets": [
            {
                "asset_id": count_asset.get("asset_id") or "",
                "asset_type": "count_matrix",
                "role": "primary_count_matrix",
            }
        ],
        "source_group_design": str(GROUP_COMPARISON_DESIGN),
        "comparisons": [
            {
                "comparison_name": comparison.get("comparison_name") or "",
                "case_group": comparison.get("case_group") or "",
                "control_group": comparison.get("control_group") or "",
            }
            for comparison in comparisons
        ],
        "parameters": parameters,
        "outputs": [],
        "warnings": ["当前版本尚未执行真实差异分析；此 run 仅保存输入、比较设计和参数。"],
        "created_at": now,
        "updated_at": now,
        "started_at": None,
        "finished_at": None,
        "error": None,
    }
    _atomic_write_json(run_dir / "task_run.json", payload)
    _atomic_write_json(
        run_dir / "inputs.json",
        {
            "schema_version": "bioinformatics_analysis_task_run_inputs.v1",
            "source_task_plan": str(DEG_TASK_PLAN),
            "source_group_design": str(GROUP_COMPARISON_DESIGN),
            "source_assets": payload["source_assets"],
        },
    )
    _atomic_write_json(run_dir / "parameters.json", {"schema_version": "bioinformatics_analysis_task_run_parameters.v1", **parameters})
    _atomic_write_json(
        run_dir / "outputs_manifest.json",
        {
            "schema_version": "bioinformatics_analysis_task_run_outputs.v1",
            "outputs": [],
            "note": "dry-run 未生成 DEG 表、火山图或富集结果。",
        },
    )
    _atomic_write_json(run_dir / "warnings.json", {"warnings": payload["warnings"]})
    (log_dir / "task.log").write_text("dry-run: real DEG execution is not implemented in this stage.\n", encoding="utf-8")
    return {**payload, "run_dir": str(run_dir), "task_run_path": str(run_dir / "task_run.json")}


def update_analysis_task_run_status(
    project_root: str | Path,
    task_family: str,
    run_id: str,
    status: str,
    *,
    error: str | None = None,
) -> dict[str, object]:
    if status not in ALLOWED_TASK_RUN_STATUSES:
        raise ValueError(f"未知 task run 状态：{status}")
    payload = load_analysis_task_run(project_root, task_family, run_id)
    if payload is None:
        raise ValueError(f"未找到 task run：{run_id}")
    payload = {key: value for key, value in payload.items() if key not in {"run_dir", "task_run_path"}}
    payload["status"] = status
    payload["updated_at"] = _now()
    if error is not None:
        payload["error"] = error
    if status in {"completed", "failed", "cancelled", "skipped_dry_run"}:
        payload["finished_at"] = payload.get("finished_at") or payload["updated_at"]
    run_dir = task_run_path(project_root, task_family, run_id)
    _atomic_write_json(run_dir / "task_run.json", payload)
    return {**payload, "run_dir": str(run_dir), "task_run_path": str(run_dir / "task_run.json")}


def task_run_status_label(status: str) -> str:
    return {
        "configured_not_run": "已配置，未运行",
        "queued": "排队中",
        "running": "运行中",
        "completed": "已完成",
        "failed": "失败",
        "cancelled": "已取消",
        "skipped_dry_run": "当前版本仅生成任务记录",
    }.get(status, status or "未知")


def _unique_run_id(root: Path, task_family: str, prefix: str) -> str:
    for _ in range(20):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        candidate = f"{prefix}_{stamp}_{uuid4().hex[:6]}"
        if not task_run_path(root, task_family, candidate).exists():
            return candidate
    raise RuntimeError("无法生成唯一 analysis task run id。")


def _safe_segment(value: str | None) -> str:
    segment = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "").strip())
    segment = segment.strip("._")
    if not segment or segment in {".", ".."}:
        raise ValueError("非法 analysis task run 路径片段。")
    return segment


def _ensure_within_root(root: Path, path: Path) -> None:
    resolved = path.resolve()
    allowed = (root / ANALYSIS_RUNS_ROOT).resolve()
    if resolved != allowed and allowed not in resolved.parents:
        raise ValueError(f"analysis task run 路径越界：{resolved}")


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
