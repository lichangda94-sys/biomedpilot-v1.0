from __future__ import annotations

import importlib
import html
import json
import re
import ssl
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import unquote, urljoin
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


class GeoAssetManifestDiscoverer(Protocol):
    def discover(self, accession: str, target_dir: Path, download_result: dict[str, Any]) -> dict[str, Any]:
        ...


class GeoRemoteAssetDownloader(Protocol):
    def download_asset(self, asset: dict[str, Any], target_dir: Path) -> dict[str, Any]:
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


class HttpsGeoAssetManifestDiscoverer:
    """Discover GEO downloadable assets without fetching every remote file."""

    def discover(self, accession: str, target_dir: Path, download_result: dict[str, Any]) -> dict[str, Any]:
        normalized = _normalize_gse_accession(accession)
        assets: list[dict[str, Any]] = []
        warnings: list[str] = []
        family_path = Path(str(download_result.get("family_soft_path") or target_dir / f"{normalized}_family.soft.gz"))
        family_exists = family_path.is_file()
        assets.append(
            _geo_asset_entry(
                asset_type="family_soft",
                role="metadata_container",
                file_name=family_path.name,
                remote_url=_geo_family_soft_https_url(normalized),
                status="downloaded" if family_exists else "remote_discovered",
                local_path=str(family_path.resolve()) if family_exists else "",
                input_eligible=family_exists,
                notes=("GEO family SOFT metadata container.",),
                size_bytes=family_path.stat().st_size if family_exists else None,
            )
        )
        for url, asset_type in (
            (_geo_series_matrix_dir_url(normalized), "series_matrix"),
            (_geo_supplementary_dir_url(normalized), "supplementary_file"),
        ):
            try:
                entries = _list_remote_geo_directory(url)
            except Exception as exc:
                warnings.append(f"{asset_type}_discovery_failed:{exc}")
                continue
            for entry in entries:
                if asset_type == "series_matrix" and "series_matrix" not in entry["file_name"].lower():
                    continue
                assets.append(
                    _geo_asset_entry(
                        asset_type=asset_type,
                        role=_remote_geo_asset_role(asset_type, entry["file_name"]),
                        file_name=entry["file_name"],
                        remote_url=entry["remote_url"],
                        status="remote_discovered",
                        local_path="",
                        input_eligible=False,
                        notes=("Remote asset discovered; not downloaded in this step.",),
                        size_bytes=None,
                    )
                )
        manifest = {
            "schema_version": "biomedpilot.geo_asset_manifest.v1",
            "accession": normalized,
            "created_at": _now(),
            "discovery_method": "ncbi_https_directory_listing",
            "target_dir": str(target_dir),
            "assets": assets,
            "summary": _geo_asset_manifest_summary(assets),
            "warnings": warnings,
        }
        manifest["ui_status_parts"] = _geo_asset_ui_status_parts(manifest)
        return manifest


class HttpsGeoRemoteAssetDownloader:
    """Download a remote GEO asset discovered in the asset manifest."""

    def download_asset(self, asset: dict[str, Any], target_dir: Path) -> dict[str, Any]:
        remote_url = str(asset.get("remote_url") or "").strip()
        if not remote_url.startswith("https://ftp.ncbi.nlm.nih.gov/geo/"):
            raise ValueError("Only NCBI GEO HTTPS assets can be downloaded.")
        file_name = Path(str(asset.get("file_name") or remote_url.rstrip("/").rsplit("/", 1)[-1])).name
        if not file_name:
            raise ValueError("GEO asset file name is empty.")
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / file_name
        if target_path.exists() and target_path.stat().st_size > 0:
            return {
                "status": "success",
                "remote_url": remote_url,
                "local_path": str(target_path.resolve()),
                "bytes_downloaded": target_path.stat().st_size,
                "note": "Loaded existing asset from project cache.",
            }
        partial_path = target_path.with_suffix(target_path.suffix + ".part")
        bytes_downloaded = 0
        try:
            with urlopen(remote_url, timeout=60, context=_ssl_context()) as response:  # nosec B310 - validated NCBI GEO HTTPS URL.
                with partial_path.open("wb") as output:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        output.write(chunk)
                        bytes_downloaded += len(chunk)
            if bytes_downloaded <= 0:
                raise RuntimeError("NCBI GEO returned an empty asset file.")
            partial_path.replace(target_path)
        except Exception:
            try:
                partial_path.unlink()
            except OSError:
                pass
            raise
        return {
            "status": "success",
            "remote_url": remote_url,
            "local_path": str(target_path.resolve()),
            "bytes_downloaded": bytes_downloaded,
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

    def __init__(
        self,
        *,
        geo_downloader: GeoFamilySoftDownloader | None = None,
        geo_asset_discoverer: GeoAssetManifestDiscoverer | None = None,
        geo_asset_downloader: GeoRemoteAssetDownloader | None = None,
    ) -> None:
        self._geo_downloader = geo_downloader or HttpsGeoFamilySoftDownloader()
        self._geo_asset_discoverer = geo_asset_discoverer or HttpsGeoAssetManifestDiscoverer()
        self._geo_asset_downloader = geo_asset_downloader or HttpsGeoRemoteAssetDownloader()

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
        asset_manifest: dict[str, Any] | None = None
        asset_manifest_path: Path | None = None
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
                if success:
                    asset_manifest = self._discover_geo_asset_manifest(request, target_dir, download_result)
                    asset_manifest_path = _write_geo_asset_manifest(target_dir, request.accession_or_project, asset_manifest)
                    download_result["asset_manifest_path"] = str(asset_manifest_path)
                    download_result["asset_manifest_summary"] = asset_manifest.get("summary", {})
                status = "geo_metadata_downloaded" if success else "download_failed"
                message = (
                    _geo_download_message(request.accession_or_project, asset_manifest)
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
            "asset_manifest_path": str(asset_manifest_path) if asset_manifest_path is not None else "",
            "asset_manifest": asset_manifest or {},
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
            asset_manifest_path=asset_manifest_path,
            asset_manifest=asset_manifest,
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
        asset_manifest_path: Path | None = None,
        asset_manifest: dict[str, Any] | None = None,
    ) -> AcquisitionSummary:
        metadata = dict(request.metadata)
        asset_summary = asset_manifest.get("summary", {}) if isinstance(asset_manifest, dict) else {}
        metadata.update(
            {
                "download_id": request.download_id,
                "download_status": status,
                "download_executed": download_executed,
                "download_request_path": str(request_path),
                "download_receipt_path": str(receipt_path),
                "asset_manifest_path": str(asset_manifest_path) if asset_manifest_path is not None else "",
                "asset_manifest_summary": asset_summary if isinstance(asset_summary, dict) else {},
                "registration_status": "registered_with_download_task" if not downloaded_files else "registered_metadata_source",
                "ready_for_recognition": "ready" if downloaded_files else "pending_source_download",
                "recognition_scope": "geo_metadata_and_manifest" if downloaded_files else "pending_source_download",
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

    def _discover_geo_asset_manifest(
        self,
        request: DatasetDownloadRequest,
        target_dir: Path,
        download_result: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            return self._geo_asset_discoverer.discover(request.accession_or_project, target_dir, download_result)
        except Exception as exc:
            family_assets = [
                _geo_asset_entry(
                    asset_type="family_soft",
                    role="metadata_container",
                    file_name=Path(str(path)).name,
                    remote_url=_geo_family_soft_https_url(request.accession_or_project),
                    status="downloaded",
                    local_path=str(path),
                    input_eligible=True,
                    notes=("GEO family SOFT metadata container.",),
                    size_bytes=Path(str(path)).stat().st_size if Path(str(path)).is_file() else None,
                )
                for path in _downloaded_geo_files(download_result)
            ]
            manifest = {
                "schema_version": "biomedpilot.geo_asset_manifest.v1",
                "accession": _normalize_gse_accession(request.accession_or_project),
                "created_at": _now(),
                "discovery_method": "family_soft_only_after_discovery_error",
                "target_dir": str(target_dir),
                "assets": family_assets,
                "warnings": [f"asset_discovery_failed:{exc}"],
            }
            manifest["summary"] = _geo_asset_manifest_summary(family_assets)
            manifest["ui_status_parts"] = _geo_asset_ui_status_parts(manifest)
            return manifest

    def download_geo_manifest_assets(
        self,
        *,
        project_root: str | Path,
        accession_or_project: str,
        asset_types: tuple[str, ...] = ("series_matrix", "supplementary_file"),
    ) -> CandidateDownloadResult:
        root = Path(project_root).expanduser().resolve()
        _ensure_download_dirs(root)
        accession = _normalize_gse_accession(accession_or_project)
        manifest_path = _find_geo_asset_manifest_path(root, accession)
        if manifest_path is None:
            raise FileNotFoundError(f"未找到 {accession} 的 GEO asset manifest，请先下载 family SOFT 元数据。")
        manifest = _read_json(manifest_path)
        target_dir = manifest_path.parent
        request = DatasetDownloadRequest(
            download_id=f"dl-{uuid4().hex[:10]}",
            project_root=str(root),
            source="geo",
            source_type="geo_accession",
            accession_or_project=accession,
            display_title=accession,
            original_chinese_topic="",
            generated_query_or_mapping=accession,
            target_dir=str(target_dir),
            execute_download=True,
            metadata={
                "query_source": "geo_asset_manifest",
                "ui_source": "chinese_research_question_search",
                "source": "geo",
                "source_type": "geo_accession",
                "source_name": accession,
                "source_id": accession,
                "source_origin": "geo_asset_manifest",
                "accession_or_project": accession,
                "generated_query_or_mapping": accession,
                "asset_manifest_path": str(manifest_path),
            },
            created_at=_now(),
        )
        request_path = root / "acquisition" / "download_requests" / f"{request.download_id}.json"
        receipt_path = root / "acquisition" / "download_receipts" / f"{request.download_id}.json"
        _write_json(request_path, _request_payload(request))
        assets = [asset for asset in manifest.get("assets", []) or [] if isinstance(asset, dict)]
        selected_types = set(asset_types)
        downloaded_files: list[str] = []
        downloaded_asset_count = 0
        errors: list[str] = []
        for asset in assets:
            if asset.get("asset_type") not in selected_types or asset.get("status") == "downloaded":
                continue
            remote_url = str(asset.get("remote_url") or "")
            if not remote_url:
                continue
            asset_target_dir = _geo_asset_download_dir(target_dir, str(asset.get("asset_type") or "supplementary_file"))
            try:
                result = self._geo_asset_downloader.download_asset(asset, asset_target_dir)
            except Exception as exc:
                errors.append(f"{asset.get('file_name') or remote_url}: {exc}")
                continue
            local_path = str(result.get("local_path") or "")
            if local_path and Path(local_path).is_file():
                downloaded_asset_count += 1
                downloaded_files.append(str(Path(local_path).resolve()))
                asset["status"] = "downloaded"
                asset["local_path"] = str(Path(local_path).resolve())
                asset["input_eligible"] = True
                asset["needs_download"] = False
                asset["size_bytes"] = Path(local_path).stat().st_size
        manifest["assets"] = assets
        manifest["summary"] = _geo_asset_manifest_summary(assets)
        manifest["ui_status_parts"] = _geo_asset_ui_status_parts(manifest)
        manifest.setdefault("download_events", [])
        if isinstance(manifest["download_events"], list):
            manifest["download_events"].append(
                {
                    "download_id": request.download_id,
                    "created_at": _now(),
                    "asset_types": list(asset_types),
                    "downloaded_asset_count": downloaded_asset_count,
                    "downloaded_files": downloaded_files,
                    "errors": errors,
                }
            )
        _write_json(manifest_path, manifest)
        success = bool(downloaded_files)
        status = "geo_assets_downloaded_with_warnings" if downloaded_files and errors else ("geo_assets_downloaded" if downloaded_files else "geo_asset_download_failed")
        message = _geo_supplement_download_message(accession, manifest, downloaded_asset_count, errors)
        receipt = {
            "schema_version": "biomedpilot.dataset_download_receipt.v1",
            "download_id": request.download_id,
            "created_at": _now(),
            "source": "geo",
            "source_type": "geo_accession",
            "accession_or_project": accession,
            "display_title": accession,
            "status": status,
            "message": message,
            "download_executed": True,
            "target_dir": str(target_dir),
            "downloaded_files": downloaded_files,
            "asset_manifest_path": str(manifest_path),
            "asset_manifest": manifest,
            "request_path": str(request_path),
            "download_result": {"downloaded_asset_count": downloaded_asset_count, "errors": errors},
            "metadata": request.metadata,
        }
        _write_json(receipt_path, receipt)
        summary = self._register_download_acquisition(
            request=request,
            receipt_path=receipt_path,
            request_path=request_path,
            status=status,
            downloaded_files=downloaded_files,
            download_executed=True,
            asset_manifest_path=manifest_path,
            asset_manifest=manifest,
        )
        return CandidateDownloadResult(
            success=success,
            status=status,
            message=message,
            source="geo",
            accession_or_project=accession,
            download_id=request.download_id,
            request_path=str(request_path),
            receipt_path=str(receipt_path),
            target_dir=str(target_dir),
            downloaded_files=tuple(downloaded_files),
            download_executed=True,
            acquisition_summary=summary,
            details=receipt,
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


def _write_geo_asset_manifest(target_dir: Path, accession: str, manifest: dict[str, Any]) -> Path:
    path = target_dir / f"{_normalize_gse_accession(accession)}_asset_manifest.json"
    _write_json(path, manifest)
    return path


def _find_geo_asset_manifest_path(root: Path, accession: str) -> Path | None:
    normalized = _normalize_gse_accession(accession)
    records_dir = root / "acquisition" / "records"
    if records_dir.exists():
        for path in sorted(records_dir.glob("*.json"), reverse=True):
            try:
                payload = _read_json(path)
            except (OSError, json.JSONDecodeError):
                continue
            metadata = payload.get("metadata")
            if not isinstance(metadata, dict):
                continue
            if str(metadata.get("source") or "") != "geo":
                continue
            record_accession = str(metadata.get("accession_or_project") or payload.get("source_label") or "").upper()
            if record_accession != normalized:
                continue
            manifest_path = Path(str(metadata.get("asset_manifest_path") or ""))
            if manifest_path.is_file():
                return manifest_path
    candidate = root / "raw_data" / "geo" / normalized / f"{normalized}_asset_manifest.json"
    return candidate if candidate.is_file() else None


def _geo_asset_download_dir(target_dir: Path, asset_type: str) -> Path:
    if asset_type == "series_matrix":
        return target_dir / "matrix"
    if asset_type == "supplementary_file":
        return target_dir / "supplementary"
    return target_dir


def _geo_asset_entry(
    *,
    asset_type: str,
    role: str,
    file_name: str,
    remote_url: str,
    status: str,
    local_path: str,
    input_eligible: bool,
    notes: tuple[str, ...] = (),
    size_bytes: int | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "asset_type": asset_type,
        "role": role,
        "file_name": file_name,
        "remote_url": remote_url,
        "status": status,
        "local_path": local_path,
        "input_eligible": input_eligible,
        "needs_download": status == "remote_discovered",
        "notes": list(notes),
    }
    if size_bytes is not None:
        payload["size_bytes"] = size_bytes
    return payload


def _geo_asset_manifest_summary(assets: list[dict[str, Any]]) -> dict[str, Any]:
    family_soft = [item for item in assets if item.get("asset_type") == "family_soft"]
    series_matrix = [item for item in assets if item.get("asset_type") == "series_matrix"]
    supplementary = [item for item in assets if item.get("asset_type") == "supplementary_file"]
    downloaded_family = [item for item in family_soft if item.get("status") == "downloaded"]
    downloaded_matrix = [item for item in series_matrix if item.get("status") == "downloaded"]
    downloaded_supplementary = [item for item in supplementary if item.get("status") == "downloaded"]
    expression_candidates = [
        item
        for item in [*series_matrix, *supplementary]
        if "expression" in str(item.get("role") or "") or "matrix" in str(item.get("role") or "")
    ]
    downloaded_expression_candidates = [item for item in expression_candidates if item.get("status") == "downloaded"]
    return {
        "family_soft_count": len(family_soft),
        "downloaded_family_soft_count": len(downloaded_family),
        "series_matrix_count": len(series_matrix),
        "downloaded_series_matrix_count": len(downloaded_matrix),
        "supplementary_file_count": len(supplementary),
        "downloaded_supplementary_file_count": len(downloaded_supplementary),
        "expression_candidate_count": len(expression_candidates),
        "downloaded_expression_candidate_count": len(downloaded_expression_candidates),
        "metadata_downloaded": bool(downloaded_family),
        "series_matrix_discovered": bool(series_matrix),
        "series_matrix_downloaded": bool(downloaded_matrix),
        "supplementary_files_discovered": bool(supplementary),
        "supplementary_files_downloaded": bool(downloaded_supplementary),
        "expression_matrix_status": "downloaded" if downloaded_expression_candidates else ("remote_discovered" if expression_candidates else "pending_confirmation"),
        "recognition_ready": bool(downloaded_family or downloaded_matrix),
    }


def _geo_asset_ui_status_parts(manifest: dict[str, Any] | None) -> list[str]:
    summary = manifest.get("summary", {}) if isinstance(manifest, dict) else {}
    if not isinstance(summary, dict):
        summary = {}
    parts: list[str] = []
    if summary.get("metadata_downloaded"):
        parts.append("元数据已下载")
    if summary.get("expression_matrix_status") == "downloaded":
        parts.append("表达矩阵已下载")
    elif summary.get("series_matrix_discovered") or summary.get("expression_candidate_count"):
        parts.append("表达矩阵待确认")
    else:
        parts.append("表达矩阵待确认")
    if summary.get("supplementary_files_downloaded"):
        parts.append("补充文件已下载")
    elif summary.get("supplementary_files_discovered"):
        parts.append("已发现补充文件")
    if summary.get("recognition_ready"):
        parts.append("可进入识别")
    return parts or ["待下载"]


def _geo_download_message(accession: str, manifest: dict[str, Any] | None) -> str:
    return f"{_normalize_gse_accession(accession)}：" + " / ".join(_geo_asset_ui_status_parts(manifest))


def _geo_supplement_download_message(accession: str, manifest: dict[str, Any], downloaded_asset_count: int, errors: list[str]) -> str:
    prefix = f"{_normalize_gse_accession(accession)}：已下载 {downloaded_asset_count} 个补充/Matrix 资产"
    status = " / ".join(_geo_asset_ui_status_parts(manifest))
    if errors:
        return f"{prefix}，部分失败 {len(errors)} 个。{status}"
    return f"{prefix}。{status}"


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


def _geo_series_matrix_dir_url(accession: str) -> str:
    normalized = _normalize_gse_accession(accession)
    return f"https://ftp.ncbi.nlm.nih.gov/geo/series/{_geo_series_prefix(normalized)}/{normalized}/matrix/"


def _geo_supplementary_dir_url(accession: str) -> str:
    normalized = _normalize_gse_accession(accession)
    return f"https://ftp.ncbi.nlm.nih.gov/geo/series/{_geo_series_prefix(normalized)}/{normalized}/suppl/"


def _list_remote_geo_directory(url: str) -> list[dict[str, str]]:
    with urlopen(url, timeout=20, context=_ssl_context()) as response:  # nosec B310 - fixed NCBI GEO HTTPS endpoint.
        text = response.read().decode("utf-8", errors="replace")
    entries: list[dict[str, str]] = []
    for match in re.finditer(r'href=["\']([^"\']+)["\']', text, flags=re.I):
        href = html.unescape(match.group(1).strip())
        if not href or href.startswith("?") or href.startswith("#") or href in {"../", "/"}:
            continue
        if href.endswith("/"):
            continue
        remote_url = urljoin(url, href)
        file_name = unquote(remote_url.rstrip("/").rsplit("/", 1)[-1])
        if not file_name or file_name in {".", ".."} or file_name.endswith("/"):
            continue
        if file_name.lower() in {"index.html", "filelist.txt"}:
            continue
        entries.append({"file_name": file_name, "remote_url": remote_url})
    deduped: dict[str, dict[str, str]] = {}
    for entry in entries:
        deduped.setdefault(entry["remote_url"], entry)
    return list(deduped.values())


def _remote_geo_asset_role(asset_type: str, file_name: str) -> str:
    lowered = file_name.lower()
    if asset_type == "series_matrix":
        return "expression_matrix_candidate"
    if any(token in lowered for token in ("count", "counts", "expression", "expr", "matrix", "tpm", "fpkm", "rpkm", "normalized")):
        return "supplementary_expression_candidate"
    if any(token in lowered for token in ("clinical", "clinic", "survival", "phenotype", "pheno", "sample", "metadata")):
        return "supplementary_sample_metadata_candidate"
    if any(token in lowered for token in ("annot", "annotation", "platform", "gene", "probe")):
        return "supplementary_annotation_candidate"
    return "supplementary_file"


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


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
