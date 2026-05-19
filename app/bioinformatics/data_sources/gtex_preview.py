from __future__ import annotations

import json
import ssl
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen
from uuid import uuid4

from app.bioinformatics.gtex_tissue_registry import GTExTissueEntry, GTExUsePurpose


GTEX_API_ROOT = "https://gtexportal.org/api/v2"
GTExFetcher = Callable[[str, dict[str, str], int], dict[str, Any]]


@dataclass(frozen=True)
class GTExPreviewRequest:
    tissue_id: str
    tissue_site_detail: str
    tissue_label_zh: str
    tissue_group: str
    use_purpose: str
    use_purpose_zh: str
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GTExPreviewSummary:
    request: GTExPreviewRequest
    status: str
    donor_count: int
    sample_count: int
    file_count: int
    estimated_size_bytes: int
    warnings: tuple[str, ...]
    is_download_plan_available: bool
    tissue_metadata: dict[str, object]
    file_manifest_entries: tuple[dict[str, object], ...]
    error_message: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["request"] = self.request.to_dict()
        payload["warnings"] = list(self.warnings)
        payload["file_manifest_entries"] = [dict(entry) for entry in self.file_manifest_entries]
        return payload


@dataclass(frozen=True)
class GTExDownloadPlanDraft:
    plan_id: str
    tissue_id: str
    tissue_site_detail: str
    use_purpose: str
    file_count: int
    estimated_size_bytes: int
    warnings: tuple[str, ...]
    status: str
    created_at: str
    plan_path: Path

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["warnings"] = list(self.warnings)
        payload["plan_path"] = str(self.plan_path)
        return payload


def build_gtex_preview_request(*, tissue: GTExTissueEntry, purpose: GTExUsePurpose) -> GTExPreviewRequest:
    return GTExPreviewRequest(
        tissue_id=tissue.tissue_id,
        tissue_site_detail=tissue.tissue_site_detail,
        tissue_label_zh=tissue.chinese_name,
        tissue_group=tissue.tissue_group,
        use_purpose=purpose.purpose_id,
        use_purpose_zh=purpose.chinese_name,
        created_at=_now(),
    )


class GTExMetadataPreviewService:
    def __init__(self, fetcher: GTExFetcher | None = None) -> None:
        self._fetcher = fetcher or _fetch_gtex_json

    def build_preview(self, request: GTExPreviewRequest, *, timeout: int = 10) -> GTExPreviewSummary:
        try:
            payload = self._fetcher(
                f"{GTEX_API_ROOT}/dataset/tissueSiteDetail",
                {"tissueSiteDetailId": request.tissue_site_detail, "format": "json"},
                timeout,
            )
        except Exception as exc:
            warning = _friendly_error(exc)
            return GTExPreviewSummary(
                request=request,
                status="failed",
                donor_count=0,
                sample_count=0,
                file_count=0,
                estimated_size_bytes=0,
                warnings=(warning, "GTEx 不会自动作为 TCGA normal control。"),
                is_download_plan_available=False,
                tissue_metadata={},
                file_manifest_entries=(),
                error_message=str(exc),
            )
        record = _first_record(payload) or {"tissueSiteDetail": request.tissue_site_detail}
        sample_count = _safe_int(_first_value(record, "rnaSeqSampleCount", "sampleCount", "samples", "count"))
        donor_count = _safe_int(_first_value(record, "donorCount", "subjectCount", "donors")) or sample_count
        entries = tuple(_file_entries_from_record(record, request))
        status = "ready" if sample_count or entries else "empty"
        warnings = ["GTEx 是独立正常组织表达资源；不自动作为 TCGA normal control，也不自动与 TCGA 合并。"]
        if not entries:
            warnings.append("未从 GTEx metadata 返回明确公共下载文件；可生成 metadata 计划，但不能执行真实表达矩阵下载。")
        return GTExPreviewSummary(
            request=request,
            status=status,
            donor_count=donor_count,
            sample_count=sample_count,
            file_count=len(entries),
            estimated_size_bytes=sum(_safe_int(entry.get("file_size")) for entry in entries),
            warnings=tuple(dict.fromkeys(warnings)),
            is_download_plan_available=status == "ready",
            tissue_metadata=dict(record),
            file_manifest_entries=entries,
        )


def write_gtex_download_plan_draft(project_root: str | Path, summary: GTExPreviewSummary) -> GTExDownloadPlanDraft:
    root = Path(project_root).expanduser().resolve()
    plan_id = f"gtex-plan-{uuid4().hex[:10]}"
    plan_path = root / "acquisition" / "gtex_download_plans" / f"{plan_id}.json"
    created_at = _now()
    draft = GTExDownloadPlanDraft(
        plan_id=plan_id,
        tissue_id=summary.request.tissue_id,
        tissue_site_detail=summary.request.tissue_site_detail,
        use_purpose=summary.request.use_purpose,
        file_count=summary.file_count,
        estimated_size_bytes=summary.estimated_size_bytes,
        warnings=summary.warnings,
        status="draft_only",
        created_at=created_at,
        plan_path=plan_path,
    )
    payload = {
        "schema_version": "biomedpilot.gtex_download_plan_draft.v1",
        **draft.to_dict(),
        "preview_summary": summary.to_dict(),
        "file_manifest_entries": [dict(entry) for entry in summary.file_manifest_entries],
        "constraints": {
            "downloads_files": False,
            "writes_source_files": False,
            "builds_expression_matrix": False,
            "ready_for_deg_or_gsea": False,
            "not_tcga_normal_control": True,
            "requires_explicit_joint_config": True,
        },
    }
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return draft


def latest_gtex_download_plan_path(project_root: str | Path) -> Path | None:
    root = Path(project_root).expanduser().resolve()
    plans_dir = root / "acquisition" / "gtex_download_plans"
    if not plans_dir.exists():
        return None
    paths = [path for path in plans_dir.glob("*.json") if path.is_file()]
    return max(paths, key=lambda item: item.stat().st_mtime) if paths else None


def _file_entries_from_record(record: dict[str, Any], request: GTExPreviewRequest) -> list[dict[str, object]]:
    raw = record.get("file_manifest_entries") or record.get("downloadableFiles") or record.get("expression_files") or record.get("files") or []
    entries: list[dict[str, object]] = []
    if not isinstance(raw, list):
        return entries
    for item in raw:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or item.get("download_url") or item.get("href") or "").strip()
        file_name = str(item.get("file_name") or item.get("filename") or Path(url).name or "").strip()
        if not url or not file_name:
            continue
        entries.append(
            {
                "file_id": str(item.get("file_id") or item.get("id") or file_name),
                "file_name": file_name,
                "file_size": _safe_int(item.get("file_size") or item.get("size")),
                "url": url,
                "data_type": str(item.get("data_type") or "Gene Expression Matrix"),
                "data_format": str(item.get("data_format") or Path(file_name).suffix.lstrip(".").upper() or "TSV"),
                "value_type": str(item.get("value_type") or item.get("metric") or "TPM"),
                "tissue_id": request.tissue_id,
                "tissue_site_detail": request.tissue_site_detail,
                "role": str(item.get("role") or "gtex_tissue_expression"),
            }
        )
    return entries


def _first_record(payload: dict[str, Any]) -> dict[str, Any] | None:
    data = payload.get("data", payload)
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data[0]
    if isinstance(data, dict):
        for key in ("tissueSiteDetail", "tissueSiteDetails", "items", "results"):
            value = data.get(key)
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value[0]
        return data
    return None


def _first_value(payload: dict[str, Any], *keys: str) -> object:
    for key in keys:
        value = payload.get(key)
        if value not in (None, ""):
            return value
    return None


def _safe_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _fetch_gtex_json(url: str, params: dict[str, str], timeout: int) -> dict[str, Any]:
    full_url = f"{url}?{urlencode(params)}" if params else url
    with urlopen(full_url, timeout=timeout, context=ssl.create_default_context()) as handle:
        return json.loads(handle.read().decode("utf-8"))


def _friendly_error(exc: Exception) -> str:
    text = str(exc)
    if isinstance(exc, ssl.SSLError) or "CERTIFICATE_VERIFY_FAILED" in text or "certificate verify failed" in text.lower():
        return "GTEx metadata 预览失败：证书验证失败。"
    return f"GTEx metadata 预览失败：{exc}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


__all__ = [
    "GTExDownloadPlanDraft",
    "GTExMetadataPreviewService",
    "GTExPreviewRequest",
    "GTExPreviewSummary",
    "build_gtex_preview_request",
    "latest_gtex_download_plan_path",
    "write_gtex_download_plan_draft",
]
