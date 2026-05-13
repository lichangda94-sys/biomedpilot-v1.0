from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.bioinformatics.analysis_task_runs import load_analysis_task_run, task_run_path
from app.bioinformatics.deg_task_plan import DEG_TASK_PLAN, load_deg_task_plan
from app.bioinformatics.group_comparison_design import GROUP_COMPARISON_DESIGN, load_group_comparison_design
from app.bioinformatics.standardized_asset_selection import resolve_standardized_assets


DEG_INPUTS_ROOT = Path("standardized_data") / "deg_inputs"
DEG_PREFLIGHT_SCHEMA_VERSION = "bioinformatics_deg_preflight.v1"


def run_deg_executor_preflight(project_root: str | Path, *, task_run_id: str | None = None) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    output_dir = root / DEG_INPUTS_ROOT / _unique_preflight_id(root)
    manifest_path = output_dir / "deg_preflight_manifest.json"
    warnings: list[str] = ["当前版本尚未执行真实差异分析；preflight 只保存执行输入引用并做基础校验。"]
    errors: list[str] = []

    task_plan = load_deg_task_plan(root)
    group_design = load_group_comparison_design(root)
    count_asset = _default_count_asset(root)
    comparisons = _comparisons(task_plan, group_design)

    if not task_plan:
        errors.append("缺少 DEG task plan。")
    if not group_design:
        errors.append("缺少 confirmed group design。")
    elif not _has_confirmed_group_design(group_design):
        errors.append("缺少 confirmed comparison。")
    if not count_asset:
        errors.append("缺少默认 count matrix。")
    if not comparisons:
        errors.append("comparison 为空。")

    species = str(count_asset.get("species") or (group_design or {}).get("species") or "unknown")
    gene_id_type = str(count_asset.get("gene_id_type") or (group_design or {}).get("gene_id_type") or "unknown")
    if species.lower() in {"", "unknown"}:
        warnings.append("species unknown，请在真实 DEG 或富集前确认物种。")
    if gene_id_type.lower() in {"", "unknown"}:
        warnings.append("gene_id_type unknown，请在真实 DEG 或富集前确认基因 ID 类型。")
    if species.lower() in {"mouse", "mus musculus"} or "mus musculus" in species.lower():
        warnings.append("检测到 mouse 数据；后续不得默认使用 human 参数。")

    status = "failed" if errors else "passed_with_warnings" if warnings else "passed"
    materialized_inputs = _materialized_input_paths(root, output_dir)
    manifest = {
        "schema_version": DEG_PREFLIGHT_SCHEMA_VERSION,
        "preflight_id": output_dir.name,
        "status": status,
        "source_count_asset_id": str(count_asset.get("asset_id") or ""),
        "source_group_design": str(GROUP_COMPARISON_DESIGN),
        "source_deg_task_plan": str(DEG_TASK_PLAN),
        "species": species,
        "gene_id_type": gene_id_type,
        "materialized_inputs": materialized_inputs,
        "summary": {
            "comparison_count": len(comparisons),
            "task_run_id": task_run_id or "",
            "note": "当前版本尚未执行真实差异分析；preflight 只生成执行输入引用并做校验。",
        },
        "comparisons": comparisons,
        "warnings": warnings,
        "errors": errors,
        "created_at": _now(),
    }

    _atomic_write_json(manifest_path, manifest)
    _atomic_write_json(
        output_dir / "warnings.json",
        {
            "schema_version": "bioinformatics_deg_preflight_warnings.v1",
            "status": status,
            "warnings": warnings,
            "errors": errors,
        },
    )
    _write_tsv(output_dir / "comparisons.tsv", ["comparison_name", "case_group", "control_group"], comparisons)

    if task_run_id:
        _link_preflight_to_task_run(root, task_run_id, manifest, manifest_path)

    return {**manifest, "manifest_path": str(manifest_path), "output_dir": str(output_dir)}


def load_latest_deg_preflight_manifest(project_root: str | Path) -> dict[str, object] | None:
    root = Path(project_root).expanduser().resolve()
    base = root / DEG_INPUTS_ROOT
    if not base.is_dir():
        return None
    manifests = sorted(base.glob("*/deg_preflight_manifest.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    for manifest in manifests:
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and payload.get("schema_version") == DEG_PREFLIGHT_SCHEMA_VERSION:
            payload["manifest_path"] = str(manifest)
            try:
                payload["manifest_relative_path"] = str(manifest.relative_to(root))
            except ValueError:
                payload["manifest_relative_path"] = str(manifest)
            return payload
    return None


def _default_count_asset(root: Path) -> dict[str, object]:
    resolved = resolve_standardized_assets(root, asset_types={"count_matrix"})
    for asset in resolved.get("assets", []) or []:
        if isinstance(asset, dict) and asset.get("asset_type") == "count_matrix":
            return dict(asset)
    return {}


def _has_confirmed_group_design(group_design: dict[str, object]) -> bool:
    comparisons = [item for item in group_design.get("comparisons", []) or [] if isinstance(item, dict)]
    return any(item.get("status") == "confirmed" for item in comparisons)


def _comparisons(task_plan: dict[str, object] | None, group_design: dict[str, object] | None) -> list[dict[str, str]]:
    source = task_plan if isinstance(task_plan, dict) and task_plan.get("comparisons") else group_design
    rows: list[dict[str, str]] = []
    if not isinstance(source, dict):
        return rows
    for item in source.get("comparisons", []) or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("comparison_name") or "").strip()
        case = str(item.get("case_group") or "").strip()
        control = str(item.get("control_group") or "").strip()
        if name or case or control:
            rows.append({"comparison_name": name, "case_group": case, "control_group": control})
    return rows


def _link_preflight_to_task_run(root: Path, task_run_id: str, manifest: dict[str, object], manifest_path: Path) -> None:
    run = load_analysis_task_run(root, "deg", task_run_id)
    if not run:
        return
    relative_manifest = str(manifest_path.relative_to(root))
    run_dir = task_run_path(root, "deg", task_run_id)
    payload = {key: value for key, value in run.items() if key not in {"run_dir", "task_run_path"}}
    payload["deg_preflight_manifest"] = relative_manifest
    payload["deg_preflight_status"] = manifest.get("status", "")
    payload["updated_at"] = _now()
    _atomic_write_json(run_dir / "task_run.json", payload)

    inputs_path = run_dir / "inputs.json"
    try:
        inputs = json.loads(inputs_path.read_text(encoding="utf-8")) if inputs_path.exists() else {}
    except (OSError, json.JSONDecodeError):
        inputs = {}
    if not isinstance(inputs, dict):
        inputs = {}
    inputs["deg_preflight_manifest"] = relative_manifest
    inputs["deg_preflight_status"] = manifest.get("status", "")
    _atomic_write_json(inputs_path, inputs)


def _materialized_input_paths(root: Path, output_dir: Path) -> dict[str, str]:
    return {
        "comparisons": str((output_dir / "comparisons.tsv").relative_to(root)),
        "manifest": str((output_dir / "deg_preflight_manifest.json").relative_to(root)),
        "warnings": str((output_dir / "warnings.json").relative_to(root)),
    }


def _write_tsv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    table = ["\t".join(header)]
    for row in rows:
        table.append("\t".join(str(row.get(column, "")) for column in header))
    _atomic_write_text(path, "\n".join(table) + "\n")


def _unique_preflight_id(root: Path) -> str:
    for _ in range(20):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        candidate = f"deg_preflight_{stamp}_{uuid4().hex[:6]}"
        if not (root / DEG_INPUTS_ROOT / candidate).exists():
            return candidate
    raise RuntimeError("无法生成唯一 DEG preflight id。")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    data = json.dumps(payload, ensure_ascii=False, indent=2)
    with temp_path.open("w", encoding="utf-8") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp_path, path)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    with temp_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp_path, path)
