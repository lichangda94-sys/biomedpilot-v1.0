from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.bioinformatics.acquisition_file_records import build_blocked_file_record, build_file_record
from app.bioinformatics.data_sources.live_validation import (
    apply_limit,
    light_validation_enabled,
    tcga_download_limit_files,
    validation_settings,
    validation_warning,
)
from app.bioinformatics.data_sources.tcga_preview import GDCFetcher, fetch_tcga_file_manifest_entries, format_bytes_zh
from app.bioinformatics.download import GdcDataFileDownloader, StandardRemoteFileDownloader
from app.bioinformatics.project_workspace_binding import AcquisitionSummary, register_acquisition


TCGA_PLAN_SCHEMA_VERSION = "biomedpilot.tcga_gdc_download_plan_draft.v1"
TCGA_DOWNLOAD_RECEIPT_SCHEMA_VERSION = "biomedpilot.tcga_gdc_download_receipt.v1"
TCGA_DOWNLOAD_REQUEST_SCHEMA_VERSION = "biomedpilot.tcga_gdc_download_request.v1"
TCGA_DOWNLOAD_MANIFEST_SCHEMA_VERSION = "biomedpilot.tcga_gdc_download_manifest.v2"


@dataclass(frozen=True)
class TCGADownloadExecutionResult:
    success: bool
    status: str
    message: str
    project_id: str
    download_id: str
    plan_path: Path
    request_path: Path
    receipt_path: Path
    manifest_path: Path
    target_dir: Path
    downloaded_files: tuple[str, ...]
    success_count: int
    failed_count: int
    skipped_count: int
    blocked_count: int
    cache_hit_count: int
    total_size_bytes: int
    acquisition_summary: AcquisitionSummary | None = None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        for key in ("plan_path", "request_path", "receipt_path", "manifest_path", "target_dir"):
            payload[key] = str(payload[key])
        payload["downloaded_files"] = list(self.downloaded_files)
        if self.acquisition_summary is not None:
            payload["acquisition_summary"] = {
                "acquisition_id": self.acquisition_summary.acquisition_id,
                "source_files": list(self.acquisition_summary.source_files),
                "record_path": str(self.acquisition_summary.record_path),
            }
        return payload


class TCGADownloadPlanExecutor:
    def __init__(
        self,
        *,
        downloader: StandardRemoteFileDownloader | None = None,
        fetcher: GDCFetcher | None = None,
        page_size: int = 500,
    ) -> None:
        self._downloader = downloader or GdcDataFileDownloader()
        self._fetcher = fetcher
        self._page_size = page_size

    def execute_latest_plan(
        self,
        project_root: str | Path,
        *,
        timeout: int = 10,
        project_id: str | None = None,
    ) -> TCGADownloadExecutionResult:
        plan_path = latest_tcga_download_plan_path(project_root, project_id=project_id)
        if plan_path is None:
            raise FileNotFoundError("未找到 TCGA 下载计划草案，请先生成 B6.2 下载计划。")
        return self.execute_plan(project_root, plan_path=plan_path, timeout=timeout)

    def execute_plan(self, project_root: str | Path, *, plan_path: str | Path, timeout: int = 10) -> TCGADownloadExecutionResult:
        root = Path(project_root).expanduser().resolve()
        plan = _read_json(Path(plan_path).expanduser().resolve())
        _validate_plan(plan)
        project_id = str(plan.get("project_id") or "").strip().upper()
        entries = self._entries_from_plan(plan, timeout=timeout)
        original_candidate_count = len(entries)
        validation_limited = light_validation_enabled() or bool(plan.get("validation_limited"))
        if validation_limited:
            entries = apply_limit(entries, tcga_download_limit_files())
        download_id = f"tcga-dl-{uuid4().hex[:10]}"
        target_dir = root / "raw_data" / "tcga" / project_id / download_id
        request_path = root / "acquisition" / "download_requests" / f"{download_id}.json"
        receipt_path = root / "acquisition" / "download_receipts" / f"{download_id}.json"
        manifest_path = target_dir / f"{project_id}_gdc_download_manifest.json"
        request_payload = _request_payload(download_id, root, plan, entries, target_dir)
        _write_json(request_path, request_payload)

        target_dir.mkdir(parents=True, exist_ok=True)
        downloaded_files: list[str] = []
        file_records: list[dict[str, Any]] = []
        events: list[dict[str, Any]] = []
        total_size_bytes = 0
        for entry in entries:
            allowed, reason = _allowed_tcga_entry(entry)
            file_id = str(entry.get("file_id") or entry.get("id") or "").strip()
            file_name = str(entry.get("file_name") or entry.get("filename") or file_id).strip()
            if not allowed:
                file_records.append(_blocked_record(entry, reason))
                events.append(_event(entry, status="blocked", message=reason))
                continue
            try:
                result = self._downloader.download_file(entry, target_dir)
                local_path = str(result.get("local_path") or "")
                if not local_path:
                    raise RuntimeError("GDC downloader did not return local_path.")
                status = "cache_hit" if result.get("cache_hit") else "downloaded"
                size_bytes = _safe_int(result.get("bytes_downloaded")) or _file_size(local_path)
                total_size_bytes += size_bytes
                downloaded_files.append(local_path)
                file_records.append(
                    build_file_record(
                        local_path,
                        source="tcga_gdc",
                        role=_tcga_entry_role(entry),
                        status=status,
                        source_url=str(result.get("source_url") or f"https://api.gdc.cancer.gov/data/{file_id}"),
                        source_path=file_name,
                        remote_checksum=str(entry.get("md5sum") or ""),
                        message="GDC file downloaded for B6.3 raw acquisition." if status == "downloaded" else "Loaded existing GDC file from project cache.",
                        extra={
                            "file_id": file_id,
                            "file_name": file_name,
                            **_tcga_entry_mapping_fields(entry),
                            "analysis_gate_status": "waiting_b6_4_expression_matrix_build",
                            "validation_limited": validation_limited,
                        },
                    )
                )
                events.append(_event(entry, status=status, local_path=local_path, bytes_downloaded=size_bytes))
            except Exception as exc:
                file_records.append(_blocked_record(entry, f"download_failed:{exc}", status="failed"))
                events.append(_event(entry, status="failed", message=str(exc)))

        success_count = sum(1 for event in events if event.get("status") == "downloaded")
        cache_hit_count = sum(1 for event in events if event.get("status") == "cache_hit")
        failed_count = sum(1 for event in events if event.get("status") == "failed")
        blocked_count = sum(1 for event in events if event.get("status") == "blocked")
        skipped_count = sum(1 for event in events if event.get("status") == "skipped")
        status = _execution_status(downloaded_files, failed_count, blocked_count, entries)
        message = _execution_message(project_id, success_count, cache_hit_count, failed_count, blocked_count, total_size_bytes)
        manifest = {
            "schema_version": TCGA_DOWNLOAD_MANIFEST_SCHEMA_VERSION,
            "download_id": download_id,
            "created_at": _now(),
            "project_id": project_id,
            "status": status,
            "plan_path": str(Path(plan_path).expanduser().resolve()),
            "target_dir": str(target_dir),
            "file_manifest_entries": entries,
            "downloaded_files": downloaded_files,
            "file_records": file_records,
            "download_events": events,
            "summary": _summary(success_count, cache_hit_count, failed_count, skipped_count, blocked_count, total_size_bytes),
            "analysis_gate_status": "waiting_b6_4_expression_matrix_build",
            "original_candidate_file_count": original_candidate_count,
            "validation_limited": validation_limited,
            "validation_settings": validation_settings() if validation_limited else {},
            "warnings": [validation_warning()] if validation_limited else [],
        }
        _write_json(manifest_path, manifest)
        receipt = {
            "schema_version": TCGA_DOWNLOAD_RECEIPT_SCHEMA_VERSION,
            "download_id": download_id,
            "created_at": _now(),
            "source": "tcga_gdc",
            "source_type": "tcga_project",
            "project_id": project_id,
            "status": status,
            "message": message,
            "download_executed": True,
            "plan_path": str(Path(plan_path).expanduser().resolve()),
            "request_path": str(request_path),
            "download_manifest_path": str(manifest_path),
            "target_dir": str(target_dir),
            "downloaded_files": downloaded_files,
            "file_records": file_records,
            "download_events": events,
            "summary": manifest["summary"],
            "analysis_gate_status": "waiting_b6_4_expression_matrix_build",
            "original_candidate_file_count": original_candidate_count,
            "validation_limited": validation_limited,
            "validation_settings": validation_settings() if validation_limited else {},
            "warnings": [validation_warning()] if validation_limited else [],
        }
        _write_json(receipt_path, receipt)
        acquisition = self._register_acquisition(
            root=root,
            project_id=project_id,
            plan=plan,
            status=status,
            message=message,
            downloaded_files=downloaded_files,
            request_path=request_path,
            receipt_path=receipt_path,
            manifest_path=manifest_path,
            target_dir=target_dir,
            file_records=file_records,
            summary=manifest["summary"],
            validation_limited=validation_limited,
        )
        return TCGADownloadExecutionResult(
            success=bool(downloaded_files) and failed_count == 0,
            status=status,
            message=message,
            project_id=project_id,
            download_id=download_id,
            plan_path=Path(plan_path).expanduser().resolve(),
            request_path=request_path,
            receipt_path=receipt_path,
            manifest_path=manifest_path,
            target_dir=target_dir,
            downloaded_files=tuple(downloaded_files),
            success_count=success_count,
            failed_count=failed_count,
            skipped_count=skipped_count,
            blocked_count=blocked_count,
            cache_hit_count=cache_hit_count,
            total_size_bytes=total_size_bytes,
            acquisition_summary=acquisition,
        )

    def _entries_from_plan(self, plan: dict[str, Any], *, timeout: int) -> list[dict[str, Any]]:
        entries = _entry_list(plan.get("file_manifest_entries"))
        if not entries:
            preview = plan.get("preview_summary")
            if isinstance(preview, dict):
                entries = _entry_list(preview.get("file_manifest_entries"))
        if entries:
            return entries
        filters = plan.get("gdc_filters")
        if not isinstance(filters, dict) or not filters.get("content"):
            return []
        return [dict(entry) for entry in fetch_tcga_file_manifest_entries(filters, fetcher=self._fetcher, page_size=self._page_size, timeout=timeout)]

    def _register_acquisition(
        self,
        *,
        root: Path,
        project_id: str,
        plan: dict[str, Any],
        status: str,
        message: str,
        downloaded_files: list[str],
        request_path: Path,
        receipt_path: Path,
        manifest_path: Path,
        target_dir: Path,
        file_records: list[dict[str, Any]],
        summary: dict[str, object],
        validation_limited: bool,
    ) -> AcquisitionSummary:
        preview = plan.get("preview_summary") if isinstance(plan.get("preview_summary"), dict) else {}
        request = preview.get("request") if isinstance(preview, dict) and isinstance(preview.get("request"), dict) else {}
        metadata = {
            "source": "tcga_gdc",
            "ui_source": "tcga_database_page",
            "registration_status": "registered_tcga_raw_files_waiting_b6_4" if downloaded_files else "registered_tcga_download_attempt",
            "download_status": status,
            "download_message": message,
            "download_plan_draft_id": str(plan.get("plan_id") or ""),
            "download_plan_draft_path": str(plan.get("plan_path") or ""),
            "download_request_path": str(request_path),
            "download_receipt_path": str(receipt_path),
            "download_manifest_path": str(manifest_path),
            "download_target_dir": str(target_dir),
            "ready_for_recognition": "pending_expression_matrix_build",
            "recognition_scope": "tcga_raw_files_waiting_b6_4",
            "analysis_gate_status": "waiting_b6_4_expression_matrix_build",
            "analysis_gate_message": "TCGA 原始文件已获取，等待 B6.4 构建表达矩阵。",
            "project_id": project_id,
            "analysis_purpose": str(plan.get("analysis_purpose") or request.get("analysis_purpose") or ""),
            "sample_scope": str(plan.get("sample_scope") or request.get("sample_scope") or ""),
            "expected_assets": list(_expected_assets(plan)),
            "display_title_zh": f"TCGA {project_id}",
            "tcga_download_summary": summary,
            "file_records_summary": summary,
            "validation_limited": validation_limited,
            "validation_settings": validation_settings() if validation_limited else {},
            "warnings": [validation_warning()] if validation_limited else [],
        }
        return register_acquisition(
            root,
            source_type="tcga_project",
            source_label=project_id,
            strategy="reference" if downloaded_files else "plan_only",
            selected_paths=[Path(path) for path in downloaded_files],
            metadata=metadata,
            file_records=file_records,
        )


def latest_tcga_download_plan_path(project_root: str | Path, *, project_id: str | None = None) -> Path | None:
    root = Path(project_root).expanduser().resolve()
    selected_project = str(project_id or "").strip().upper()
    plans_dir = root / "acquisition" / "tcga_download_plans"
    if not plans_dir.exists():
        return None
    paths: list[Path] = []
    for path in plans_dir.glob("*.json"):
        if not path.is_file():
            continue
        if selected_project:
            try:
                plan = _read_json(path)
            except (OSError, json.JSONDecodeError):
                continue
            plan_project = str(plan.get("project_id") or "").strip().upper()
            if plan_project and plan_project != selected_project:
                continue
        paths.append(path)
    if not paths:
        return None
    return max(paths, key=lambda path: path.stat().st_mtime)


def _validate_plan(plan: dict[str, Any]) -> None:
    if str(plan.get("schema_version") or "") != TCGA_PLAN_SCHEMA_VERSION:
        raise ValueError("不是 B6.2 TCGA 下载计划草案。")
    if str(plan.get("status") or "") != "draft_only":
        raise ValueError("TCGA 下载计划状态不是 draft_only。")
    if not str(plan.get("project_id") or "").strip():
        raise ValueError("TCGA 下载计划缺少 project_id。")


def _request_payload(download_id: str, root: Path, plan: dict[str, Any], entries: list[dict[str, Any]], target_dir: Path) -> dict[str, object]:
    validation_limited = light_validation_enabled() or bool(plan.get("validation_limited"))
    return {
        "schema_version": TCGA_DOWNLOAD_REQUEST_SCHEMA_VERSION,
        "download_id": download_id,
        "created_at": _now(),
        "project_root": str(root),
        "source": "tcga_gdc",
        "source_type": "tcga_project",
        "project_id": str(plan.get("project_id") or ""),
        "plan_id": str(plan.get("plan_id") or ""),
        "plan_path": str(plan.get("plan_path") or ""),
        "target_dir": str(target_dir),
        "execute_download": True,
        "candidate_file_count": len(entries),
        "validation_limited": validation_limited,
        "validation_settings": validation_settings() if validation_limited else {},
        "analysis_gate_status": "waiting_b6_4_expression_matrix_build",
    }


def _allowed_tcga_entry(entry: dict[str, Any]) -> tuple[bool, str]:
    if not str(entry.get("file_id") or entry.get("id") or "").strip():
        return False, "missing_file_id"
    access = str(entry.get("access") or "").strip().lower()
    if access and access != "open":
        return False, "controlled_or_non_open_gdc_file"
    lowered = " ".join(
        str(entry.get(key) or "").lower()
        for key in ("file_name", "data_category", "data_type", "data_format", "experimental_strategy", "workflow_type")
    )
    if any(token in lowered for token in ("sequencing reads", "aligned reads", ".bam", ".cram", "bam", "cram")):
        return False, "raw_or_alignment_file_blocked"
    return True, ""


def _blocked_record(entry: dict[str, Any], message: str, *, status: str = "blocked") -> dict[str, Any]:
    record = build_blocked_file_record(
        source="tcga_gdc",
        role=_tcga_entry_role(entry),
        source_url=f"https://api.gdc.cancer.gov/data/{entry.get('file_id') or entry.get('id') or ''}",
        source_path=str(entry.get("file_name") or entry.get("filename") or ""),
        risk_level="high" if status == "blocked" else "medium",
        message=message,
        extra={
            "file_id": str(entry.get("file_id") or entry.get("id") or ""),
            "file_name": str(entry.get("file_name") or entry.get("filename") or ""),
            "status": status,
        },
    )
    record["status"] = status
    return record


def _event(entry: dict[str, Any], *, status: str, message: str = "", local_path: str = "", bytes_downloaded: int = 0) -> dict[str, object]:
    return {
        "file_id": str(entry.get("file_id") or entry.get("id") or ""),
        "file_name": str(entry.get("file_name") or entry.get("filename") or ""),
        "status": status,
        "message": message,
        "local_path": local_path,
        "bytes_downloaded": bytes_downloaded,
        **_tcga_entry_mapping_fields(entry),
    }


def _execution_status(downloaded_files: list[str], failed_count: int, blocked_count: int, entries: list[dict[str, Any]]) -> str:
    if downloaded_files and (failed_count or blocked_count):
        return "tcga_gdc_raw_files_acquired_with_warnings"
    if downloaded_files:
        return "tcga_gdc_raw_files_acquired"
    if not entries:
        return "tcga_gdc_download_plan_empty"
    return "tcga_gdc_raw_file_download_failed"


def _execution_message(project_id: str, success_count: int, cache_hit_count: int, failed_count: int, blocked_count: int, total_size_bytes: int) -> str:
    acquired = success_count + cache_hit_count
    if acquired:
        return (
            f"{project_id}：TCGA 原始文件已获取 {acquired} 个"
            f"（新下载 {success_count}，缓存 {cache_hit_count}，失败 {failed_count}，阻断 {blocked_count}），"
            f"累计 {format_bytes_zh(total_size_bytes)}；等待 B6.4 构建表达矩阵。"
        )
    return f"{project_id}：未获取 TCGA 原始文件（失败 {failed_count}，阻断 {blocked_count}），请检查下载计划或网络。"


def _summary(success_count: int, cache_hit_count: int, failed_count: int, skipped_count: int, blocked_count: int, total_size_bytes: int) -> dict[str, object]:
    return {
        "success_count": success_count,
        "cache_hit_count": cache_hit_count,
        "failed_count": failed_count,
        "skipped_count": skipped_count,
        "blocked_count": blocked_count,
        "acquired_count": success_count + cache_hit_count,
        "total_size_bytes": total_size_bytes,
        "total_size_display": format_bytes_zh(total_size_bytes),
    }


def _entry_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(entry) for entry in value if isinstance(entry, dict)]


def _expected_assets(plan: dict[str, Any]) -> list[str]:
    preview = plan.get("preview_summary")
    if isinstance(preview, dict):
        request = preview.get("request")
        if isinstance(request, dict):
            analysis_purpose = str(request.get("analysis_purpose") or "")
            if analysis_purpose == "differential_expression":
                return ["rna_seq_expression", "sample_metadata"]
            if analysis_purpose == "expression_clinical":
                return ["rna_seq_expression", "sample_metadata", "clinical_metadata"]
    return ["rna_seq_expression", "sample_metadata"]


def _tcga_entry_role(entry: dict[str, Any]) -> str:
    data_type = str(entry.get("data_type") or "").lower()
    if "gene expression" in data_type or "expression" in data_type:
        return "tcga_gdc_gene_expression_quantification"
    return "tcga_gdc_raw_file"


def _tcga_entry_mapping_fields(entry: dict[str, Any]) -> dict[str, object]:
    return {
        "case_ids": _string_list(entry.get("case_ids")),
        "case_submitter_ids": _string_list(entry.get("case_submitter_ids")),
        "sample_ids": _string_list(entry.get("sample_ids")),
        "sample_submitter_ids": _string_list(entry.get("sample_submitter_ids")),
        "sample_types": _string_list(entry.get("sample_types")),
    }


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


def _safe_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _file_size(path: str | Path) -> int:
    try:
        return Path(path).stat().st_size
    except OSError:
        return 0


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
