from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from app.bioinformatics.services.geo_metadata_profile_service import (
    GeoMetadataProfileService,
    GeoSupplementaryFile,
)


SELECTION_SCHEMA_VERSION = "biomedpilot.gse_download_candidates.v1"
SELECTION_DIRNAME = "gse_file_download_candidates"


def build_gse_file_download_candidates(
    *,
    project_root: str | Path | None,
    accession: str,
    asset_manifest: dict[str, Any] | None = None,
    candidate_metadata: dict[str, Any] | None = None,
    selected_candidate_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Build user-facing GEO download candidate rows from the current asset profile."""

    normalized = _normalize_gse_accession(accession)
    profile = GeoMetadataProfileService().build_profile(
        accession=normalized,
        project_root=project_root,
        asset_manifest=asset_manifest,
        candidate_metadata=candidate_metadata,
    )
    selected = set(selected_candidate_ids) if selected_candidate_ids is not None else None
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in profile.supplementary_file_preview:
        candidate_id = _candidate_id(normalized, item, seen)
        default_selected = _default_selected(item)
        rows.append(
            {
                "candidate_id": candidate_id,
                "accession": normalized,
                "file_name": item.file_name,
                "asset_type": item.asset_type or "supplementary_file",
                "predicted_role": _predicted_role(item),
                "predicted_type": item.predicted_type,
                "download_priority": item.download_priority,
                "risk_level": item.risk_level,
                "risk_warning": _risk_warning(item),
                "file_source": _file_source_label(item),
                "remote_url": item.remote_url,
                "local_path": item.local_path,
                "status": item.status or "remote_discovered",
                "suggested_for_download": default_selected,
                "selected": candidate_id in selected if selected is not None else default_selected,
                "recommendation": item.recommendation,
                "recommendation_reason": item.recommendation_reason or item.reason,
                "recognition_use": _recognition_use(item),
                "requires_recognition": item.predicted_type not in {"raw_data", "differential_result_table"},
                "requires_standardization_confirmation": item.predicted_type in {"expression_matrix", "sample_metadata", "platform_annotation"},
                "warnings": _candidate_warnings(item),
            }
        )
    return {
        "schema_version": SELECTION_SCHEMA_VERSION,
        "accession": normalized,
        "created_at": _now(),
        "updated_at": _now(),
        "candidate_count": len(rows),
        "selected_count": sum(1 for row in rows if row.get("selected")),
        "candidates": rows,
        "notes": [
            "仅保存 GEO 文件下载候选选择，不代表已完成分析。",
            "下载后仍需进入 recognition 和 standardization confirmation。",
            "RAW/heavy 文件不会默认选择；imported DEG candidate 不作为软件计算结果。",
        ],
    }


def save_gse_file_download_candidate_selection(
    *,
    project_root: str | Path,
    accession: str,
    asset_manifest: dict[str, Any] | None = None,
    candidate_metadata: dict[str, Any] | None = None,
    selected_candidate_ids: Iterable[str] | None = None,
) -> Path:
    root = Path(project_root).expanduser().resolve()
    manifest = build_gse_file_download_candidates(
        project_root=root,
        accession=accession,
        asset_manifest=asset_manifest,
        candidate_metadata=candidate_metadata,
        selected_candidate_ids=selected_candidate_ids,
    )
    target_dir = root / "acquisition" / SELECTION_DIRNAME
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{manifest['accession']}_download_candidates.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_gse_file_download_candidate_selection(
    *,
    project_root: str | Path,
    accession: str,
) -> dict[str, Any] | None:
    root = Path(project_root).expanduser().resolve()
    path = root / "acquisition" / SELECTION_DIRNAME / f"{_normalize_gse_accession(accession)}_download_candidates.json"
    try:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return None


def _candidate_id(accession: str, item: GeoSupplementaryFile, seen: set[str]) -> str:
    base = f"{accession}:{item.asset_type or 'asset'}:{item.file_name}"
    safe = re.sub(r"[^A-Za-z0-9_.:-]+", "_", base).strip("_") or f"{accession}:asset"
    candidate_id = safe
    index = 2
    while candidate_id in seen:
        candidate_id = f"{safe}:{index}"
        index += 1
    seen.add(candidate_id)
    return candidate_id


def _default_selected(item: GeoSupplementaryFile) -> bool:
    if item.status == "downloaded" or item.asset_type == "family_soft":
        return False
    if item.predicted_type in {"raw_data", "differential_result_table"}:
        return False
    if item.risk_level in {"中", "高"} or item.download_priority == "不建议":
        return False
    if item.asset_type == "series_matrix":
        return True
    return item.predicted_type == "expression_matrix" and item.download_priority == "高"


def _predicted_role(item: GeoSupplementaryFile) -> str:
    if item.predicted_type == "expression_matrix":
        return "表达矩阵候选"
    if item.predicted_type == "sample_metadata":
        return "样本注释候选"
    if item.predicted_type == "platform_annotation":
        return "平台注释候选"
    if item.predicted_type == "differential_result_table":
        return "外部 DEG 结果候选"
    if item.predicted_type == "raw_data":
        return "RAW/heavy 风险文件"
    if item.asset_type == "family_soft":
        return "GEO family SOFT 元数据容器"
    return item.role or item.predicted_type or "未知文件"


def _recognition_use(item: GeoSupplementaryFile) -> str:
    if item.predicted_type == "expression_matrix" or item.asset_type == "series_matrix":
        return "expression_matrix_candidate"
    if item.predicted_type == "sample_metadata":
        return "sample_metadata_candidate"
    if item.predicted_type == "platform_annotation":
        return "platform_annotation_candidate"
    if item.predicted_type == "differential_result_table":
        return "imported_deg_candidate"
    if item.predicted_type == "raw_data":
        return "raw_heavy_risk_file"
    if item.asset_type == "family_soft":
        return "geo_metadata_container"
    return "review_candidate"


def _file_source_label(item: GeoSupplementaryFile) -> str:
    if item.asset_type == "series_matrix":
        return "GEO Series Matrix"
    if item.asset_type == "family_soft":
        return "GEO family SOFT"
    if item.asset_type == "supplementary_file":
        return "GEO supplementary"
    return "GEO asset manifest"


def _risk_warning(item: GeoSupplementaryFile) -> str:
    if item.predicted_type == "raw_data" or item.risk_level in {"中", "高"}:
        return "RAW/heavy 文件需人工确认，不默认下载。"
    if item.predicted_type == "differential_result_table":
        return "外部 DEG 结果候选，不代表本软件计算结果。"
    if item.predicted_type == "platform_annotation":
        return "平台注释候选，不代表已完成 ID 映射。"
    if item.predicted_type == "expression_matrix":
        return "表达矩阵候选，下载后仍需识别和标准化确认。"
    return "下载后仍需识别确认。"


def _candidate_warnings(item: GeoSupplementaryFile) -> list[str]:
    warnings: list[str] = []
    if item.predicted_type == "raw_data" or item.risk_level in {"中", "高"}:
        warnings.append("RAW/heavy 文件不会默认选择。")
    if item.predicted_type == "differential_result_table":
        warnings.append("imported DEG candidate 只能作为外部结果浏览候选。")
    if item.predicted_type == "platform_annotation":
        warnings.append("平台注释只作为候选，不能承诺已完成探针到 gene ID 映射。")
    if item.asset_type == "series_matrix":
        warnings.append("Series Matrix 下载后仍需 recognition 和 standardization confirmation。")
    return warnings


def _normalize_gse_accession(value: str) -> str:
    text = str(value or "").strip().upper()
    match = re.search(r"GSE\d+", text)
    return match.group(0) if match else text


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
