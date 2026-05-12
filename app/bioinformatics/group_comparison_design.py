from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.project_recognition import CURRENT_RECOGNITION_RUN
from app.bioinformatics.project_standardization import load_standardization_artifacts


GROUP_COMPARISON_DESIGN = Path("manifests") / "group_comparison_design.json"
DESIGN_SCHEMA_VERSION = "bioinformatics_group_comparison_design.v1"


def group_comparison_design_path(project_root: str | Path) -> Path:
    return Path(project_root).expanduser().resolve() / GROUP_COMPARISON_DESIGN


def load_group_comparison_design(project_root: str | Path) -> dict[str, object] | None:
    path = group_comparison_design_path(project_root)
    if not path.is_file():
        return None
    payload = _read_json(path)
    return payload if payload.get("schema_version") == DESIGN_SCHEMA_VERSION else None


def has_confirmed_group_comparison_design(project_root: str | Path) -> bool:
    design = load_group_comparison_design(project_root)
    if not isinstance(design, dict):
        return False
    groups = [item for item in design.get("sample_groups", []) or [] if isinstance(item, dict)]
    comparisons = [item for item in design.get("comparisons", []) or [] if isinstance(item, dict)]
    has_named_group = any(str(item.get("group_role") or "") != "unknown" and str(item.get("user_group_name") or "") for item in groups)
    has_confirmed_comparison = any(str(item.get("status") or "") == "confirmed" for item in comparisons)
    return has_named_group and has_confirmed_comparison


def load_group_design_context(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    assets = _standardized_assets(root)
    count_assets = [asset for asset in assets if asset.get("asset_type") == "count_matrix"]
    normalized_assets = [asset for asset in assets if asset.get("asset_type") == "normalized_expression_matrix"]
    deg_assets = [asset for asset in assets if asset.get("asset_type") == "deg_result_table"]
    count_asset = count_assets[0] if count_assets else {}
    normalized_asset = normalized_assets[0] if normalized_assets else {}
    primary_asset = count_asset or normalized_asset
    sample_groups = _sample_groups_from_asset(primary_asset) if primary_asset else []
    imported = _imported_deg_references(deg_assets)
    existing_design = load_group_comparison_design(root)
    current = _current_recognition(root)
    warnings = _context_warnings(count_asset, normalized_asset, sample_groups)
    species = str(primary_asset.get("species") or _first_value(assets, "species") or "")
    gene_id_type = str(primary_asset.get("gene_id_type") or _first_value(assets, "gene_id_type") or "")
    return {
        "schema_version": "bioinformatics_group_design_context.v1",
        "project_root": str(root),
        "source_recognition_run_id": current.get("run_id") or "",
        "source_standardized_asset_ids": [str(asset.get("asset_id") or "") for asset in assets if asset.get("asset_id")],
        "assets": assets,
        "has_count_matrix": bool(count_asset),
        "has_normalized_expression_matrix": bool(normalized_asset),
        "count_asset": count_asset,
        "normalized_asset": normalized_asset,
        "count_fpkm_sample_match": _sample_ids(count_asset) == _sample_ids(normalized_asset) if count_asset and normalized_asset else None,
        "sample_groups": sample_groups,
        "group_count": len(sample_groups),
        "imported_deg_references": imported,
        "imported_deg_count": len(imported),
        "species": species,
        "species_group": str(primary_asset.get("species_group") or _first_value(assets, "species_group") or ""),
        "gene_id_type": gene_id_type,
        "existing_design": existing_design or {},
        "has_confirmed_design": has_confirmed_group_comparison_design(root),
        "design_path": str(group_comparison_design_path(root)),
        "warnings": warnings,
    }


def build_default_group_rows(context: dict[str, object]) -> list[dict[str, object]]:
    existing = context.get("existing_design") if isinstance(context.get("existing_design"), dict) else {}
    existing_by_id = {
        str(item.get("inferred_group_id") or ""): item
        for item in existing.get("sample_groups", []) or []
        if isinstance(item, dict)
    }
    rows: list[dict[str, object]] = []
    for group in context.get("sample_groups", []) or []:
        if not isinstance(group, dict):
            continue
        group_id = str(group.get("inferred_group_id") or "")
        existing_group = existing_by_id.get(group_id, {})
        rows.append(
            {
                "inferred_group_id": group_id,
                "user_group_name": str(existing_group.get("user_group_name") or group_id),
                "group_role": str(existing_group.get("group_role") or "unknown"),
                "sample_count": int(group.get("sample_count") or 0),
                "sample_ids": list(group.get("sample_ids", []) or []),
                "source_columns": list(group.get("source_columns", []) or []),
                "note": str(existing_group.get("note") or ""),
            }
        )
    return rows


def build_default_comparison_rows(context: dict[str, object], group_rows: list[dict[str, object]] | None = None) -> list[dict[str, object]]:
    existing = context.get("existing_design") if isinstance(context.get("existing_design"), dict) else {}
    comparisons = [dict(item) for item in existing.get("comparisons", []) or [] if isinstance(item, dict)]
    if comparisons:
        return comparisons
    groups = group_rows or build_default_group_rows(context)
    control_groups = [item for item in groups if item.get("group_role") == "control"]
    treatment_groups = [item for item in groups if item.get("group_role") == "treatment"]
    if control_groups and treatment_groups:
        control = control_groups[0]
        return [
            {
                "comparison_name": f"{case.get('user_group_name')}_vs_{control.get('user_group_name')}",
                "case_group": case.get("user_group_name"),
                "control_group": control.get("user_group_name"),
                "case_inferred_group_id": case.get("inferred_group_id"),
                "control_inferred_group_id": control.get("inferred_group_id"),
                "status": "draft",
                "source": "one_vs_control_suggestion",
            }
            for case in treatment_groups
            if case.get("user_group_name") != control.get("user_group_name")
        ]
    return []


def validate_group_comparison_design(sample_groups: list[dict[str, object]], comparisons: list[dict[str, object]]) -> list[str]:
    warnings: list[str] = []
    group_names = {str(item.get("user_group_name") or "") for item in sample_groups if str(item.get("user_group_name") or "")}
    roles = {str(item.get("group_role") or "unknown") for item in sample_groups}
    if not sample_groups:
        warnings.append("未检测到可确认的样本分组。")
    if roles <= {"unknown"}:
        warnings.append("所有组角色仍为 unknown，重新差异分析不能标记为 ready。")
    seen_names: set[str] = set()
    for comparison in comparisons:
        name = str(comparison.get("comparison_name") or "").strip()
        case = str(comparison.get("case_group") or "").strip()
        control = str(comparison.get("control_group") or "").strip()
        if not name:
            warnings.append("存在未命名比较。")
        elif name in seen_names:
            warnings.append(f"比较名称重复：{name}")
        seen_names.add(name)
        if not case or not control:
            warnings.append(f"{name or '未命名比较'}：实验组和对照组不能为空。")
        if case and control and case == control:
            warnings.append(f"{name or case}：实验组和对照组不能相同。")
        if case and case not in group_names:
            warnings.append(f"{name or case}：实验组不存在于已确认组名中。")
        if control and control not in group_names:
            warnings.append(f"{name or control}：对照组不存在于已确认组名中。")
        for key, label in (("case_group", case), ("control_group", control)):
            group = next((item for item in sample_groups if item.get("user_group_name") == label), None)
            if group and int(group.get("sample_count") or 0) < 2:
                warnings.append(f"{name or label}：{key} 样本数少于 2。")
    return list(dict.fromkeys(warnings))


def save_group_comparison_design(
    project_root: str | Path,
    sample_groups: list[dict[str, object]],
    comparisons: list[dict[str, object]],
    *,
    imported_deg_references: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    context = load_group_design_context(root)
    now = _now()
    existing = load_group_comparison_design(root) or {}
    warnings = validate_group_comparison_design(sample_groups, comparisons)
    normalized_comparisons = []
    for comparison in comparisons:
        item = dict(comparison)
        item["status"] = "confirmed" if not warnings and item.get("status") in {"", None, "draft", "confirmed"} else str(item.get("status") or "draft")
        item["source"] = str(item.get("source") or "user_confirmed")
        normalized_comparisons.append(item)
    payload = {
        "schema_version": DESIGN_SCHEMA_VERSION,
        "source_recognition_run_id": context.get("source_recognition_run_id") or "",
        "source_standardized_asset_ids": context.get("source_standardized_asset_ids") or [],
        "species": context.get("species") or "",
        "species_group": context.get("species_group") or "",
        "gene_id_type": context.get("gene_id_type") or "",
        "sample_groups": sample_groups,
        "comparisons": normalized_comparisons,
        "imported_deg_references": imported_deg_references if imported_deg_references is not None else context.get("imported_deg_references", []),
        "warnings": warnings,
        "created_at": existing.get("created_at") or now,
        "updated_at": now,
    }
    _atomic_write_json(group_comparison_design_path(root), payload)
    return payload


def design_status_summary(project_root: str | Path) -> str:
    design = load_group_comparison_design(project_root)
    if not design:
        return "分组设计：未确认"
    groups = [item for item in design.get("sample_groups", []) or [] if isinstance(item, dict)]
    comparisons = [item for item in design.get("comparisons", []) or [] if isinstance(item, dict)]
    controls = [str(item.get("user_group_name") or "") for item in groups if item.get("group_role") == "control"]
    return "\n".join(
        [
            "分组设计：已确认" if has_confirmed_group_comparison_design(project_root) else "分组设计：已保存但仍需检查",
            f"样本组数：{len(groups)}",
            f"比较数：{len(comparisons)}",
            f"对照组：{'、'.join(controls) if controls else '未设置'}",
            f"保存时间：{design.get('updated_at') or '未记录'}",
        ]
    )


def _standardized_assets(root: Path) -> list[dict[str, object]]:
    artifacts = load_standardization_artifacts(root)
    registry = artifacts.get("registry")
    if not isinstance(registry, dict):
        return []
    assets = registry.get("assets") or registry.get("standardized_assets") or []
    return [asset for asset in assets if isinstance(asset, dict)]


def _current_recognition(root: Path) -> dict[str, object]:
    return _read_json(root / CURRENT_RECOGNITION_RUN)


def _sample_groups_from_asset(asset: dict[str, object]) -> list[dict[str, object]]:
    sample_ids = _sample_ids(asset)
    source_columns = [str(item) for item in asset.get("sample_columns", []) or [] if str(item)]
    grouped: dict[str, dict[str, object]] = {}
    for index, sample_id in enumerate(sample_ids):
        group_id = _sample_group_id(sample_id)
        entry = grouped.setdefault(group_id, {"inferred_group_id": group_id, "sample_ids": [], "source_columns": []})
        entry["sample_ids"].append(sample_id)  # type: ignore[index]
        if index < len(source_columns):
            entry["source_columns"].append(source_columns[index])  # type: ignore[index]
    if not grouped:
        replicate_counts = asset.get("replicate_count_by_group") if isinstance(asset.get("replicate_count_by_group"), dict) else {}
        for group_id, count in replicate_counts.items():
            grouped[str(group_id)] = {
                "inferred_group_id": str(group_id),
                "sample_ids": [],
                "source_columns": [],
                "sample_count": int(count or 0),
            }
    rows = []
    for group_id in sorted(grouped):
        row = grouped[group_id]
        sample_count = int(row.get("sample_count") or len(row.get("sample_ids", []) or []))
        rows.append({**row, "sample_count": sample_count, "status": "待确认"})
    return rows


def _sample_ids(asset: dict[str, object]) -> list[str]:
    explicit = [str(item) for item in asset.get("inferred_sample_ids", []) or [] if str(item)]
    if explicit:
        return explicit
    columns = [str(item) for item in asset.get("sample_columns", []) or [] if str(item)]
    return [_sample_id_from_column(column) for column in columns]


def _sample_id_from_column(column: str) -> str:
    return re.sub(r"(?i)_(count|counts|fpkm|tpm)$", "", column.strip())


def _sample_group_id(sample_id: str) -> str:
    match = re.match(r"^([A-Za-z]+)", sample_id.strip())
    if match:
        return match.group(1)
    return sample_id.split("_", 1)[0] or sample_id


def _imported_deg_references(deg_assets: list[dict[str, object]]) -> list[dict[str, object]]:
    references: list[dict[str, object]] = []
    for asset in deg_assets:
        for comparison in asset.get("comparisons", []) or []:
            if not isinstance(comparison, dict):
                continue
            references.append(
                {
                    "comparison_name": comparison.get("comparison_name") or "",
                    "source_asset_id": asset.get("asset_id") or "",
                    "status": "available_imported_result" if comparison.get("is_complete") else "incomplete_imported_result",
                    "is_complete": bool(comparison.get("is_complete")),
                    "log2fc_column": comparison.get("log2fc_column") or "",
                    "pvalue_column": comparison.get("pvalue_column") or "",
                    "padj_column": comparison.get("padj_column") or "",
                }
            )
    return references


def _context_warnings(count_asset: dict[str, object], normalized_asset: dict[str, object], sample_groups: list[dict[str, object]]) -> list[str]:
    warnings: list[str] = []
    if count_asset and normalized_asset and _sample_ids(count_asset) != _sample_ids(normalized_asset):
        warnings.append("Count 与 FPKM 样本不完全一致，请检查。")
    if not count_asset and normalized_asset:
        value_type = str(normalized_asset.get("value_type") or "FPKM/TPM").upper()
        warnings.append(f"当前仅检测到 {value_type} 表达矩阵；不建议作为 DESeq2/edgeR 式重新差异分析输入。")
    if not count_asset and not normalized_asset:
        warnings.append("未检测到可用于分组设计的表达矩阵。")
    if count_asset and not sample_groups:
        warnings.append("检测到 count matrix，但未能推断样本分组。")
    return warnings


def _first_value(items: list[dict[str, object]], key: str) -> object:
    for item in items:
        if item.get(key):
            return item.get(key)
    return ""


def _read_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
