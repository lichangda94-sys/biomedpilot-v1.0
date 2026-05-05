from __future__ import annotations

import importlib
import json
import ssl
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from urllib.request import urlopen
from uuid import uuid4

from app.bioinformatics.project_workspace_binding import AcquisitionSummary, register_acquisition
from app.bioinformatics.search_center.models import BioinformaticsSearchCenterResult, UnifiedDatasetCandidate


@dataclass(frozen=True)
class DatasetDownloadRequest:
    download_id: str
    project_root: str
    source: str
    source_type: str
    accession_or_project: str
    display_title: str
    original_chinese_topic: str
    generated_query_or_mapping: str
    target_dir: str
    execute_download: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CandidateDownloadResult:
    success: bool
    status: str
    message: str
    source: str
    accession_or_project: str
    download_id: str
    request_path: str
    receipt_path: str
    target_dir: str
    downloaded_files: tuple[str, ...] = ()
    download_executed: bool = False
    acquisition_summary: AcquisitionSummary | None = None
    details: dict[str, Any] = field(default_factory=dict)


class GeoFamilySoftDownloader(Protocol):
    def download(self, accession: str, target_dir: Path) -> dict[str, Any]:
        ...


class HttpsGeoFamilySoftDownloader:
    """Download GEO family SOFT files from the NCBI HTTPS mirror."""

    def download(self, accession: str, target_dir: Path) -> dict[str, Any]:
        normalized = _normalize_gse_accession(accession)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{normalized}_family.soft.gz"
        download_url = _geo_family_soft_https_url(normalized)
        if target_path.exists() and target_path.stat().st_size > 0:
            return {
                "status": "success",
                "accession": normalized,
                "family_soft_path": str(target_path),
                "download_url": download_url,
                "download_method": "ncbi_https_family_soft",
                "bytes_downloaded": target_path.stat().st_size,
                "note": "Loaded existing family SOFT from project cache.",
            }
        partial_path = target_path.with_suffix(target_path.suffix + ".part")
        bytes_downloaded = 0
        try:
            with urlopen(download_url, timeout=45, context=_ssl_context()) as response:  # nosec B310 - fixed NCBI GEO HTTPS endpoint.
                with partial_path.open("wb") as output:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        output.write(chunk)
                        bytes_downloaded += len(chunk)
            if bytes_downloaded <= 0:
                raise RuntimeError("NCBI GEO returned an empty family SOFT file.")
            with partial_path.open("rb") as downloaded:
                if downloaded.read(2) != b"\x1f\x8b":
                    raise RuntimeError("Downloaded GEO family SOFT is not gzip-compressed.")
            partial_path.replace(target_path)
        except Exception:
            try:
                partial_path.unlink()
            except OSError:
                pass
            raise
        return {
            "status": "success",
            "accession": normalized,
            "family_soft_path": str(target_path),
            "download_url": download_url,
            "download_method": "ncbi_https_family_soft",
            "bytes_downloaded": bytes_downloaded,
            "full_download_success": True,
            "note": "GEO family SOFT downloaded via NCBI HTTPS.",
        }


class LegacyGeoFamilySoftDownloader:
    """Thin optional wrapper around the archived GEO full-family-SOFT downloader."""

    def download(self, accession: str, target_dir: Path) -> dict[str, Any]:
        try:
            module = importlib.import_module("app.bioinformatics.legacy.geo_tool.geo_pipeline.download")
        except Exception as exc:
            raise RuntimeError("GEO 下载依赖不可用，请检查 GEOparse 等本地环境。") from exc
        config = module.DownloadConfig(accession=accession, geo_dir=str(target_dir))
        return module.download_full_family_soft(config)


class DatasetDownloadService:
    """Create mainline download requests and acquisition records for dataset candidates."""

    def __init__(self, *, geo_downloader: GeoFamilySoftDownloader | None = None) -> None:
        self._geo_downloader = geo_downloader or HttpsGeoFamilySoftDownloader()

    def create_request_from_candidate(
        self,
        *,
        project_root: str | Path,
        candidate: UnifiedDatasetCandidate,
        search_result: BioinformaticsSearchCenterResult | None = None,
        original_chinese_topic: str = "",
        execute_download: bool = False,
    ) -> DatasetDownloadRequest:
        root = Path(project_root).expanduser().resolve()
        download_id = f"dl-{uuid4().hex[:10]}"
        source_type = _candidate_source_type(candidate)
        generated = _candidate_generated_query_or_mapping(candidate, search_result)
        target_dir = _download_target_dir(root, candidate)
        metadata = {
            "query_source": "chinese_topic_search",
            "ui_source": "chinese_research_question_search",
            "source": candidate.source,
            "source_type": source_type,
            "source_name": candidate.display_title,
            "source_id": candidate.accession_or_project,
            "source_origin": "online_search" if candidate.source == "geo" else "local_mapping",
            "accession_or_project": candidate.accession_or_project,
            "original_chinese_topic": original_chinese_topic,
            "generated_query_or_mapping": generated,
            "download_plan_available": candidate.download_plan_available,
            "source_specific_metadata": dict(candidate.source_specific_metadata),
            "warnings": list(candidate.warnings),
        }
        return DatasetDownloadRequest(
            download_id=download_id,
            project_root=str(root),
            source=candidate.source,
            source_type=source_type,
            accession_or_project=candidate.accession_or_project,
            display_title=candidate.display_title,
            original_chinese_topic=original_chinese_topic,
            generated_query_or_mapping=generated,
            target_dir=str(target_dir),
            execute_download=execute_download,
            metadata=metadata,
            created_at=_now(),
        )

    def create_candidate_download_task(
        self,
        *,
        project_root: str | Path,
        candidate: UnifiedDatasetCandidate,
        search_result: BioinformaticsSearchCenterResult | None = None,
        original_chinese_topic: str = "",
        execute_download: bool = False,
    ) -> CandidateDownloadResult:
        request = self.create_request_from_candidate(
            project_root=project_root,
            candidate=candidate,
            search_result=search_result,
            original_chinese_topic=original_chinese_topic,
            execute_download=execute_download,
        )
        return self.execute_request(request)

    def execute_request(self, request: DatasetDownloadRequest) -> CandidateDownloadResult:
        root = Path(request.project_root).expanduser().resolve()
        _ensure_download_dirs(root)
        request_path = root / "acquisition" / "download_requests" / f"{request.download_id}.json"
        receipt_path = root / "acquisition" / "download_receipts" / f"{request.download_id}.json"
        target_dir = Path(request.target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        _write_json(request_path, _request_payload(request))

        downloaded_files: list[str] = []
        download_result: dict[str, Any] = {}
        status = _planned_status(request.source)
        message = _planned_message(request.source, request.accession_or_project)
        success = True
        download_executed = False

        if request.execute_download and request.source == "geo":
            download_executed = True
            try:
                download_result = self._geo_downloader.download(request.accession_or_project, target_dir)
                downloaded_files = _downloaded_geo_files(download_result)
                success = str(download_result.get("status") or "").startswith("success") and bool(downloaded_files)
                status = "downloaded" if success else "download_failed"
                message = (
                    f"已下载 GEO 数据：{request.accession_or_project}"
                    if success
                    else f"GEO 下载未完成：{download_result.get('note') or download_result.get('error') or request.accession_or_project}"
                )
            except Exception as exc:
                success = False
                status = "download_failed"
                message = f"GEO 下载失败：{exc}"
                download_result = {"error": str(exc)}
        elif request.execute_download and request.source != "geo":
            status = _planned_status(request.source)
            message = "当前阶段仅生成下载任务；TCGA/GDC 或 GTEx 真实下载待接入。"

        receipt = {
            "schema_version": "biomedpilot.dataset_download_receipt.v1",
            "download_id": request.download_id,
            "created_at": _now(),
            "source": request.source,
            "source_type": request.source_type,
            "accession_or_project": request.accession_or_project,
            "display_title": request.display_title,
            "status": status,
            "message": message,
            "download_executed": download_executed,
            "target_dir": str(target_dir),
            "downloaded_files": downloaded_files,
            "request_path": str(request_path),
            "download_result": download_result,
            "metadata": request.metadata,
        }
        _write_json(receipt_path, receipt)
        summary = self._register_download_acquisition(
            request=request,
            receipt_path=receipt_path,
            request_path=request_path,
            status=status,
            downloaded_files=downloaded_files,
            download_executed=download_executed,
        )
        return CandidateDownloadResult(
            success=success,
            status=status,
            message=message,
            source=request.source,
            accession_or_project=request.accession_or_project,
            download_id=request.download_id,
            request_path=str(request_path),
            receipt_path=str(receipt_path),
            target_dir=str(target_dir),
            downloaded_files=tuple(downloaded_files),
            download_executed=download_executed,
            acquisition_summary=summary,
            details=receipt,
        )

    def _register_download_acquisition(
        self,
        *,
        request: DatasetDownloadRequest,
        receipt_path: Path,
        request_path: Path,
        status: str,
        downloaded_files: list[str],
        download_executed: bool,
    ) -> AcquisitionSummary:
        metadata = dict(request.metadata)
        metadata.update(
            {
                "download_id": request.download_id,
                "download_status": status,
                "download_executed": download_executed,
                "download_request_path": str(request_path),
                "download_receipt_path": str(receipt_path),
                "registration_status": "registered_with_download_task" if not downloaded_files else "registered_downloaded_source",
                "ready_for_recognition": "ready" if downloaded_files else "pending_source_download",
            }
        )
        selected_paths = [Path(path) for path in downloaded_files]
        return register_acquisition(
            Path(request.project_root),
            source_type=request.source_type,
            source_label=request.accession_or_project,
            strategy="reference" if selected_paths else "plan_only",
            selected_paths=selected_paths,
            metadata=metadata,
        )


def _ensure_download_dirs(root: Path) -> None:
    for relative in (
        "acquisition/download_requests",
        "acquisition/download_receipts",
        "raw_data/geo",
        "raw_data/tcga",
        "raw_data/gtex",
    ):
        (root / relative).mkdir(parents=True, exist_ok=True)


def _request_payload(request: DatasetDownloadRequest) -> dict[str, object]:
    payload = request.to_dict()
    payload["schema_version"] = "biomedpilot.dataset_download_request.v1"
    payload["requires_user_confirmation"] = not request.execute_download
    payload["planned_actions"] = _planned_actions(request)
    return payload


def _planned_actions(request: DatasetDownloadRequest) -> list[str]:
    if request.source == "geo":
        return [
            "download_geo_family_soft",
            "register_downloaded_files_for_recognition",
        ]
    if request.source == "tcga_gdc":
        return [
            "create_gdc_manifest_for_project",
            "download_gene_expression_and_clinical_files_after_confirmation",
        ]
    if request.source == "gtex":
        return [
            "resolve_public_gtex_normal_reference_files",
            "download_or_register_user_supplied_gtex_files_after_confirmation",
        ]
    return ["register_candidate_source"]


def _downloaded_geo_files(result: dict[str, Any]) -> list[str]:
    files: list[str] = []
    for key in ("family_soft_path", "series_matrix_path", "supplementary_index_path"):
        value = result.get(key)
        if value and Path(str(value)).is_file():
            files.append(str(Path(str(value)).resolve()))
    extra = result.get("downloaded_files")
    if isinstance(extra, list):
        for value in extra:
            path = Path(str(value))
            if path.is_file():
                files.append(str(path.resolve()))
    return list(dict.fromkeys(files))


def _candidate_source_type(candidate: UnifiedDatasetCandidate) -> str:
    if candidate.source == "geo":
        return "geo_accession"
    if candidate.source == "tcga_gdc":
        return "tcga_project"
    if candidate.source == "gtex":
        return "gtex_tissue"
    return f"dataset_candidate_{candidate.source}"


def _candidate_generated_query_or_mapping(
    candidate: UnifiedDatasetCandidate,
    result: BioinformaticsSearchCenterResult | None,
) -> str:
    metadata = candidate.source_specific_metadata
    if candidate.source == "geo":
        query = metadata.get("query_used") or metadata.get("executed_query")
        if query:
            return str(query)
        if result is not None and result.query.geo_query_candidates:
            return result.query.geo_query_candidates[0]
    if candidate.source == "tcga_gdc":
        return str(metadata.get("project_id") or candidate.accession_or_project)
    if candidate.source == "gtex":
        return str(metadata.get("tissue_name") or candidate.tissue or candidate.accession_or_project)
    return candidate.accession_or_project


def _download_target_dir(root: Path, candidate: UnifiedDatasetCandidate) -> Path:
    if candidate.source == "geo":
        return root / "raw_data" / "geo" / candidate.accession_or_project.upper()
    if candidate.source == "tcga_gdc":
        return root / "raw_data" / "tcga" / candidate.accession_or_project.upper()
    if candidate.source == "gtex":
        slug = "".join(char if char.isalnum() else "_" for char in candidate.accession_or_project).strip("_")
        return root / "raw_data" / "gtex" / slug
    return root / "raw_data" / candidate.source / candidate.accession_or_project


def _normalize_gse_accession(accession: str) -> str:
    normalized = str(accession).strip().upper()
    if not normalized.startswith("GSE") or not normalized[3:].isdigit():
        raise ValueError(f"Only GSE accessions are supported for GEO download, got: {accession}")
    return normalized


def _geo_series_prefix(accession: str) -> str:
    digits = accession[3:]
    prefix = digits[:-3] if len(digits) > 3 else "0"
    return f"GSE{prefix}nnn"


def _geo_family_soft_https_url(accession: str) -> str:
    normalized = _normalize_gse_accession(accession)
    return f"https://ftp.ncbi.nlm.nih.gov/geo/series/{_geo_series_prefix(normalized)}/{normalized}/soft/{normalized}_family.soft.gz"


def _ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _planned_status(source: str) -> str:
    if source == "geo":
        return "registered_pending_geo_download"
    if source == "tcga_gdc":
        return "registered_pending_gdc_download"
    if source == "gtex":
        return "registered_pending_gtex_source_selection"
    return "registered_pending_download"


def _planned_message(source: str, accession_or_project: str) -> str:
    if source == "geo":
        return f"已生成 GEO 下载任务：{accession_or_project}。尚未下载数据文件。"
    if source == "tcga_gdc":
        return f"已生成 TCGA/GDC 下载任务：{accession_or_project}。真实下载待接入。"
    if source == "gtex":
        return f"已生成 GTEx 来源任务：{accession_or_project}。真实下载待接入。"
    return f"已生成下载任务：{accession_or_project}。"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
