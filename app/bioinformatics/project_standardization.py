from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.bioinformatics.project_recognition import TYPE_LABELS, load_recognition_report
from app.bioinformatics.project_readiness import load_readiness_artifacts


STANDARDIZED_REGISTRY = Path("manifests") / "standardized_assets_registry.json"
ANALYSIS_READY_MANIFEST = Path("standardized_data") / "analysis_ready_assets" / "analysis_ready_manifest.json"
DATA_PROCESSING_TASK_PLAN = Path("manifests") / "data_processing_task_plan.json"
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
    recognition = load_recognition_report(root) or {}
    files = list(recognition.get("files", []) or [])
    assets = []
    warnings = ["当前为资产注册和轻量校验，不等于正式 biological normalization。"]
    for item in files:
        for asset_type in _asset_types_for_standardization(item):
            assets.append(
                {
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
    assets = _dedupe_standardized_assets(assets)
    readiness = load_readiness_artifacts(root).get("capability_matrix") or {}
    usable = [
        str(row.get("label"))
        for row in readiness.get("rows", []) or []  # type: ignore[union-attr]
        if isinstance(row, dict) and row.get("can_run")
    ]
    missing = sorted({missing for row in readiness.get("rows", []) or [] if isinstance(row, dict) for missing in row.get("missing_inputs", []) or []})  # type: ignore[union-attr]
    registry = {
        "schema_version": "biomedpilot.standardized_assets_registry.v1",
        "generated_at": _now(),
        "project_root": str(root),
        "assets": assets,
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
        "usable_analyses": usable,
        "missing_assets": missing,
        "warnings": warnings,
    }
    _write_json(root / STANDARDIZED_REGISTRY, registry)
    _write_json(root / ANALYSIS_READY_MANIFEST, manifest)
    _write_json(root / DATA_PROCESSING_TASK_PLAN, processing_plan)
    return {"registry": registry, "analysis_ready_manifest": manifest, "data_processing_task_plan": processing_plan}


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
        key = (asset_type, key_path)
        deduped.setdefault(key, asset)
    return list(deduped.values())


def _processing_tasks_from_assets(assets: list[dict[str, object]]) -> list[dict[str, object]]:
    tasks: list[dict[str, object]] = []
    for asset in assets:
        asset_type = str(asset.get("asset_type") or "")
        file_path = str(asset.get("file_path") or "")
        if asset_type in {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix"}:
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
