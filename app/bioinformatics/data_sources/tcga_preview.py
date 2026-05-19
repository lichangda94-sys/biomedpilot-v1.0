from __future__ import annotations

import json
import ssl
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

from app.bioinformatics.tcga_project_registry import TCGAAnalysisPurpose, TCGAProjectEntry, TCGASampleScope


GDC_API_ROOT = "https://api.gdc.cancer.gov"
DEFAULT_PAGE_SIZE = 500

GDCFetcher = Callable[[str, dict[str, object], int], dict[str, Any]]

FILE_FIELDS = ",".join(
    (
        "file_id",
        "file_name",
        "file_size",
        "data_category",
        "data_type",
        "data_format",
        "experimental_strategy",
        "access",
        "analysis.workflow_type",
        "workflow_type",
        "cases.case_id",
        "cases.submitter_id",
        "cases.project.project_id",
        "cases.samples.sample_id",
        "cases.samples.submitter_id",
        "cases.samples.sample_type",
        "cases.samples.tissue_type",
        "cases.samples.tumor_descriptor",
    )
)
CASE_FIELDS = ",".join(
    (
        "case_id",
        "submitter_id",
        "project.project_id",
        "diagnoses.vital_status",
        "diagnoses.days_to_death",
        "diagnoses.days_to_last_follow_up",
        "diagnoses.tumor_stage",
        "diagnoses.primary_diagnosis",
        "demographic.gender",
        "demographic.race",
        "demographic.ethnicity",
        "demographic.days_to_birth",
        "samples.sample_id",
        "samples.sample_type",
        "samples.submitter_id",
    )
)


@dataclass(frozen=True)
class TCGAPreviewRequest:
    project_id: str
    project_label_zh: str
    analysis_purpose: str
    analysis_purpose_zh: str
    sample_scope: str
    sample_scope_zh: str
    sample_types: tuple[str, ...]
    include_expression: bool
    include_clinical: bool
    created_at: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["sample_types"] = list(self.sample_types)
        return payload


@dataclass(frozen=True)
class TCGAPreviewSummary:
    request: TCGAPreviewRequest
    status: str
    case_count: int
    sample_count: int
    file_count: int
    estimated_size_bytes: int
    size_has_unknown: bool
    sample_type_counts: dict[str, int]
    access_counts: dict[str, int]
    workflow_type_counts: dict[str, int]
    data_format_counts: dict[str, int]
    warnings: tuple[str, ...]
    is_download_plan_available: bool
    gdc_filters: dict[str, object]
    case_filters: dict[str, object]
    selected_file_ids_preview: tuple[str, ...]
    files_fetched: int
    cases_fetched: int
    files_total: int | None
    cases_total: int | None
    error_message: str = ""
    file_manifest_entries: tuple[dict[str, object], ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["request"] = self.request.to_dict()
        payload["warnings"] = list(self.warnings)
        payload["selected_file_ids_preview"] = list(self.selected_file_ids_preview)
        payload["file_manifest_entries"] = [dict(entry) for entry in self.file_manifest_entries]
        return payload


@dataclass(frozen=True)
class TCGADownloadPlanDraft:
    plan_id: str
    project_id: str
    analysis_purpose: str
    sample_scope: str
    gdc_filters: dict[str, object]
    case_filters: dict[str, object]
    file_count: int
    estimated_size_bytes: int
    selected_file_ids_preview: tuple[str, ...]
    warnings: tuple[str, ...]
    status: str
    created_at: str
    plan_path: Path

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["selected_file_ids_preview"] = list(self.selected_file_ids_preview)
        payload["warnings"] = list(self.warnings)
        payload["plan_path"] = str(self.plan_path)
        return payload


def build_tcga_preview_request(
    *,
    project: TCGAProjectEntry,
    purpose: TCGAAnalysisPurpose,
    scope: TCGASampleScope,
) -> TCGAPreviewRequest:
    include_expression = purpose.purpose_id in {"differential_expression", "expression_clinical"}
    include_clinical = purpose.purpose_id in {"expression_clinical", "survival", "project_overview"}
    return TCGAPreviewRequest(
        project_id=project.project_id,
        project_label_zh=project.chinese_name,
        analysis_purpose=purpose.purpose_id,
        analysis_purpose_zh=purpose.chinese_name,
        sample_scope=scope.scope_id,
        sample_scope_zh=scope.chinese_name,
        sample_types=tuple(scope.internal_sample_types),
        include_expression=include_expression,
        include_clinical=include_clinical,
        created_at=_now(),
    )


class TCGAMetadataPreviewService:
    def __init__(self, fetcher: GDCFetcher | None = None, *, page_size: int = DEFAULT_PAGE_SIZE) -> None:
        self._fetcher = fetcher or _fetch_gdc_json
        self._page_size = max(1, page_size)

    def build_preview(self, request: TCGAPreviewRequest, *, timeout: int = 10) -> TCGAPreviewSummary:
        file_filters = build_gdc_file_filters(request)
        case_filters = build_gdc_case_filters(request)
        try:
            files = self._fetch_all("/files", file_filters, FILE_FIELDS, timeout) if request.include_expression else _PagedHits((), 0, 0)
            cases = self._fetch_all("/cases", case_filters, CASE_FIELDS, timeout)
        except Exception as exc:
            return TCGAPreviewSummary(
                request=request,
                status="failed",
                case_count=0,
                sample_count=0,
                file_count=0,
                estimated_size_bytes=0,
                size_has_unknown=False,
                sample_type_counts={},
                access_counts={},
                workflow_type_counts={},
                data_format_counts={},
                warnings=(f"GDC metadata 预览失败：{exc}",),
                is_download_plan_available=False,
                gdc_filters=file_filters,
                case_filters=case_filters,
                selected_file_ids_preview=(),
                files_fetched=0,
                cases_fetched=0,
                files_total=None,
                cases_total=None,
                error_message=str(exc),
                file_manifest_entries=(),
            )
        return _summary_from_hits(request, file_filters, case_filters, files, cases)

    def _fetch_all(self, endpoint: str, filters: dict[str, object], fields: str, timeout: int) -> _PagedHits:
        offset = 0
        total: int | None = None
        hits: list[dict[str, Any]] = []
        while total is None or offset < total:
            payload = self._fetcher(
                endpoint,
                {
                    "filters": filters,
                    "fields": fields,
                    "format": "JSON",
                    "size": self._page_size,
                    "from": offset,
                    "sort": "file_name:asc" if endpoint == "/files" else "submitter_id:asc",
                },
                timeout,
            )
            page_hits, pagination_total = _payload_hits_and_total(payload)
            hits.extend(page_hits)
            total = pagination_total if pagination_total is not None else len(hits)
            if not page_hits or pagination_total is None:
                break
            offset += len(page_hits)
        return _PagedHits(tuple(hits), len(hits), total or 0)


def build_gdc_file_filters(request: TCGAPreviewRequest) -> dict[str, object]:
    operands: list[dict[str, object]] = [
        _in_filter("cases.project.project_id", [request.project_id]),
        _in_filter("data_category", ["Transcriptome Profiling"]),
        _in_filter("data_type", ["Gene Expression Quantification"]),
        _in_filter("experimental_strategy", ["RNA-Seq"]),
        _in_filter("access", ["open"]),
    ]
    if request.analysis_purpose in {"differential_expression", "expression_clinical"}:
        operands.append(_in_filter("analysis.workflow_type", ["STAR - Counts"]))
    if request.sample_types:
        operands.append(_in_filter("cases.samples.sample_type", list(request.sample_types)))
    return {"op": "and", "content": operands}


def build_gdc_case_filters(request: TCGAPreviewRequest) -> dict[str, object]:
    operands: list[dict[str, object]] = [_in_filter("project.project_id", [request.project_id])]
    if request.sample_types:
        operands.append(_in_filter("samples.sample_type", list(request.sample_types)))
    return {"op": "and", "content": operands}


def fetch_tcga_file_manifest_entries(
    filters: dict[str, object],
    *,
    fetcher: GDCFetcher | None = None,
    page_size: int = DEFAULT_PAGE_SIZE,
    timeout: int = 10,
) -> tuple[dict[str, object], ...]:
    resolved_fetcher = fetcher or _fetch_gdc_json
    offset = 0
    total: int | None = None
    entries: list[dict[str, object]] = []
    while total is None or offset < total:
        payload = resolved_fetcher(
            "/files",
            {
                "filters": filters,
                "fields": FILE_FIELDS,
                "format": "JSON",
                "size": max(1, page_size),
                "from": offset,
                "sort": "file_name:asc",
            },
            timeout,
        )
        hits, pagination_total = _payload_hits_and_total(payload)
        entries.extend(_file_manifest_entry(hit) for hit in hits)
        total = pagination_total if pagination_total is not None else len(entries)
        if not hits or pagination_total is None:
            break
        offset += len(hits)
    return tuple(entries)


def write_tcga_download_plan_draft(project_root: str | Path, summary: TCGAPreviewSummary) -> TCGADownloadPlanDraft:
    root = Path(project_root).expanduser().resolve()
    plan_id = f"tcga-plan-{uuid4().hex[:10]}"
    created_at = _now()
    plan_path = root / "acquisition" / "tcga_download_plans" / f"{plan_id}.json"
    draft = TCGADownloadPlanDraft(
        plan_id=plan_id,
        project_id=summary.request.project_id,
        analysis_purpose=summary.request.analysis_purpose,
        sample_scope=summary.request.sample_scope,
        gdc_filters=summary.gdc_filters,
        case_filters=summary.case_filters,
        file_count=summary.file_count,
        estimated_size_bytes=summary.estimated_size_bytes,
        selected_file_ids_preview=summary.selected_file_ids_preview,
        warnings=summary.warnings,
        status="draft_only",
        created_at=created_at,
        plan_path=plan_path,
    )
    payload = {
        "schema_version": "biomedpilot.tcga_gdc_download_plan_draft.v1",
        **draft.to_dict(),
        "file_manifest_entries": [dict(entry) for entry in summary.file_manifest_entries],
        "preview_summary": summary.to_dict(),
        "constraints": {
            "downloads_files": False,
            "writes_source_files": False,
            "builds_expression_matrix": False,
            "ready_for_deg_or_gsea": False,
        },
    }
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return draft


def format_bytes_zh(value: int, *, has_unknown: bool = False) -> str:
    size = max(0, int(value or 0))
    if size < 1024 * 1024:
        text = f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        text = f"{size / (1024 * 1024):.1f} MB"
    else:
        text = f"{size / (1024 * 1024 * 1024):.2f} GB"
    return f"{text}（部分文件大小未知）" if has_unknown else text


@dataclass(frozen=True)
class _PagedHits:
    hits: tuple[dict[str, Any], ...]
    fetched: int
    total: int


def _summary_from_hits(
    request: TCGAPreviewRequest,
    file_filters: dict[str, object],
    case_filters: dict[str, object],
    files: _PagedHits,
    cases: _PagedHits,
) -> TCGAPreviewSummary:
    file_hits = list(files.hits)
    case_hits = list(cases.hits)
    warnings: list[str] = []
    case_ids = _unique(_case_id(case) for case in case_hits) or _unique(_case_id_from_file(file) for file in file_hits)
    sample_records = list(_iter_case_samples(case_hits)) or list(_iter_file_samples(file_hits))
    sample_ids = _unique(record[0] for record in sample_records)
    sample_types = [record[1] for record in sample_records if record[1]]
    sample_type_counts = dict(Counter(sample_types))
    access_counts = dict(Counter(_clean(file.get("access")) or "未知" for file in file_hits))
    workflow_type_counts = dict(Counter(_workflow_type(file) or "未知" for file in file_hits))
    data_format_counts = dict(Counter(_clean(file.get("data_format")) or "未知" for file in file_hits))
    size_total, size_unknown = _sum_file_sizes(file_hits)
    if size_unknown:
        warnings.append("部分 GDC 文件缺少 file_size，下载大小为估算值。")
    if request.sample_types and "Solid Tissue Normal" in request.sample_types and sample_type_counts.get("Solid Tissue Normal", 0) == 0:
        warnings.append("当前项目按所选条件未找到癌旁正常样本，可仅使用肿瘤样本或更改样本范围。")
    if request.include_expression and not file_hits:
        warnings.append("未找到符合当前项目、分析目的和样本范围的开放 RNA-Seq 表达文件。")
    if request.include_clinical and not case_hits:
        warnings.append("GDC cases 查询未返回 clinical/sample metadata，后续临床完整性需要复核。")
    if request.analysis_purpose == "survival":
        warnings.append("本阶段仅检查临床/随访 metadata 可用性，不执行生存分析；如按表达高低分组还需要后续表达数据。")
    if request.analysis_purpose == "project_overview":
        warnings.append("项目样本概况模式只预览 metadata，不创建可分析表达数据集。")
    status = "ready"
    if not case_hits and not file_hits:
        status = "empty"
    if request.include_expression and not file_hits:
        status = "empty"
    plan_available = request.include_expression and bool(file_hits) and status == "ready"
    return TCGAPreviewSummary(
        request=request,
        status=status,
        case_count=len(case_ids),
        sample_count=len(sample_ids),
        file_count=len(file_hits),
        estimated_size_bytes=size_total,
        size_has_unknown=size_unknown,
        sample_type_counts=sample_type_counts,
        access_counts=access_counts,
        workflow_type_counts=workflow_type_counts,
        data_format_counts=data_format_counts,
        warnings=tuple(dict.fromkeys(warnings)),
        is_download_plan_available=plan_available,
        gdc_filters=file_filters,
        case_filters=case_filters,
        selected_file_ids_preview=tuple(_clean(file.get("file_id") or file.get("id")) for file in file_hits[:50] if _clean(file.get("file_id") or file.get("id"))),
        files_fetched=files.fetched,
        cases_fetched=cases.fetched,
        files_total=files.total,
        cases_total=cases.total,
        file_manifest_entries=tuple(_file_manifest_entry(file) for file in file_hits),
    )


def _file_manifest_entry(file: dict[str, Any]) -> dict[str, object]:
    return {
        "file_id": _clean(file.get("file_id") or file.get("id")),
        "file_name": _clean(file.get("file_name") or file.get("filename")),
        "file_size": file.get("file_size") or 0,
        "access": _clean(file.get("access")),
        "data_category": _clean(file.get("data_category")),
        "data_type": _clean(file.get("data_type")),
        "data_format": _clean(file.get("data_format")),
        "experimental_strategy": _clean(file.get("experimental_strategy")),
        "workflow_type": _workflow_type(file),
        "sample_types": _unique(sample_type for _sample_id, sample_type in _iter_file_samples([file])),
    }


def _payload_hits_and_total(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], int | None]:
    data = payload.get("data", payload)
    if not isinstance(data, dict):
        return [], None
    hits = [item for item in data.get("hits", []) or [] if isinstance(item, dict)]
    pagination = data.get("pagination") if isinstance(data.get("pagination"), dict) else {}
    total = pagination.get("total")
    try:
        return hits, int(total) if total is not None else None
    except (TypeError, ValueError):
        return hits, None


def _fetch_gdc_json(endpoint: str, params: dict[str, object], timeout: int) -> dict[str, Any]:
    url = endpoint if endpoint.startswith("http") else f"{GDC_API_ROOT}{endpoint}"
    encoded = {
        key: json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        for key, value in params.items()
    }
    # GDC accepts POST form payloads for search endpoints; this avoids long filter URLs.
    body = urlencode(encoded).encode("utf-8")
    request = Request(url, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    with urlopen(request, timeout=timeout, context=_ssl_context()) as handle:
        return json.loads(handle.read().decode("utf-8"))


def _ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _in_filter(field: str, values: Iterable[str]) -> dict[str, object]:
    return {"op": "in", "content": {"field": field, "value": list(values)}}


def _sum_file_sizes(files: Iterable[dict[str, Any]]) -> tuple[int, bool]:
    total = 0
    unknown = False
    for file in files:
        try:
            total += int(file.get("file_size") or 0)
            if file.get("file_size") in (None, ""):
                unknown = True
        except (TypeError, ValueError):
            unknown = True
    return total, unknown


def _iter_case_samples(cases: Iterable[dict[str, Any]]) -> Iterable[tuple[str, str]]:
    for case in cases:
        case_id = _case_id(case)
        for sample in case.get("samples", []) or []:
            if isinstance(sample, dict):
                sample_id = _clean(sample.get("sample_id") or sample.get("submitter_id")) or f"{case_id}:{_clean(sample.get('sample_type'))}"
                yield sample_id, _clean(sample.get("sample_type"))


def _iter_file_samples(files: Iterable[dict[str, Any]]) -> Iterable[tuple[str, str]]:
    for file in files:
        for case in file.get("cases", []) or []:
            if not isinstance(case, dict):
                continue
            case_id = _case_id(case)
            for sample in case.get("samples", []) or []:
                if isinstance(sample, dict):
                    sample_id = _clean(sample.get("sample_id") or sample.get("submitter_id")) or f"{case_id}:{_clean(sample.get('sample_type'))}"
                    yield sample_id, _clean(sample.get("sample_type"))


def _case_id(case: dict[str, Any]) -> str:
    return _clean(case.get("case_id") or case.get("submitter_id"))


def _case_id_from_file(file: dict[str, Any]) -> str:
    for case in file.get("cases", []) or []:
        if isinstance(case, dict):
            value = _case_id(case)
            if value:
                return value
    return ""


def _workflow_type(file: dict[str, Any]) -> str:
    analysis = file.get("analysis")
    if isinstance(analysis, dict):
        value = _clean(analysis.get("workflow_type"))
        if value:
            return value
    return _clean(file.get("workflow_type"))


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        text = _clean(value)
        if text and text not in seen:
            seen.add(text)
            items.append(text)
    return items


def _clean(value: object) -> str:
    return str(value or "").strip()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
