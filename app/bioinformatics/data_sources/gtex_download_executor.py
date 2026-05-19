from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.bioinformatics.acquisition_file_records import build_blocked_file_record, build_file_record
from app.bioinformatics.data_sources.gtex_preview import latest_gtex_download_plan_path
from app.bioinformatics.download import HttpsUrlFileDownloader, StandardRemoteFileDownloader
from app.bioinformatics.project_workspace_binding import AcquisitionSummary, register_acquisition


@dataclass(frozen=True)
class GTExDownloadExecutionResult:
    success: bool
    status: str
    message: str
    tissue_id: str
    tissue_site_detail: str
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


class GTExDownloadPlanExecutor:
    def __init__(self, *, downloader: StandardRemoteFileDownloader | None = None) -> None:
        self._downloader = downloader or HttpsUrlFileDownloader()

    def execute_latest_plan(self, project_root: str | Path) -> GTExDownloadExecutionResult:
        plan_path = latest_gtex_download_plan_path(project_root)
        if plan_path is None:
            raise FileNotFoundError("未找到 GTEx 下载计划草案，请先生成 G6.1 下载计划。")
        return self.execute_plan(project_root, plan_path=plan_path)

    def execute_plan(self, project_root: str | Path, *, plan_path: str | Path) -> GTExDownloadExecutionResult:
        root = Path(project_root).expanduser().resolve()
        plan_path = Path(plan_path).expanduser().resolve()
        plan = _read_json(plan_path)
        _validate_plan(plan)
        tissue_id = str(plan.get("tissue_id") or "").strip()
        tissue_detail = str(plan.get("tissue_site_detail") or tissue_id).strip()
        entries = _entry_list(plan.get("file_manifest_entries"))
        download_id = f"gtex-dl-{uuid4().hex[:10]}"
        target_dir = root / "raw_data" / "gtex" / _slug(tissue_id) / download_id
        request_path = root / "acquisition" / "download_requests" / f"{download_id}.json"
        receipt_path = root / "acquisition" / "download_receipts" / f"{download_id}.json"
        manifest_path = target_dir / f"{_slug(tissue_id)}_gtex_download_manifest.json"
        _write_json(
            request_path,
            {
                "schema_version": "biomedpilot.gtex_download_request.v1",
                "download_id": download_id,
                "created_at": _now(),
                "source": "gtex",
                "tissue_id": tissue_id,
                "tissue_site_detail": tissue_detail,
                "plan_path": str(plan_path),
                "target_dir": str(target_dir),
                "candidate_file_count": len(entries),
                "tcga_default_control_status": "disabled",
            },
        )
        target_dir.mkdir(parents=True, exist_ok=True)
        downloaded_files: list[str] = []
        file_records: list[dict[str, Any]] = []
        events: list[dict[str, Any]] = []
        total_size = 0
        for entry in entries:
            if not str(entry.get("url") or entry.get("download_url") or "").strip():
                file_records.append(_blocked_record(entry, "missing_download_url"))
                events.append(_event(entry, "failed", message="missing_download_url"))
                continue
            try:
                result = self._downloader.download_file(entry, target_dir)
                local_path = str(result.get("local_path") or "")
                if not local_path:
                    raise RuntimeError("GTEx downloader did not return local_path.")
                status = "cache_hit" if result.get("cache_hit") else "downloaded"
                size = _safe_int(result.get("bytes_downloaded")) or _file_size(local_path)
                total_size += size
                downloaded_files.append(local_path)
                file_records.append(
                    build_file_record(
                        local_path,
                        source="gtex",
                        role=str(entry.get("role") or "gtex_tissue_expression"),
                        status=status,
                        source_url=str(result.get("source_url") or entry.get("url") or entry.get("download_url") or ""),
                        source_path=str(entry.get("file_name") or ""),
                        message="GTEx expression file downloaded." if status == "downloaded" else "Loaded existing GTEx file from project cache.",
                        extra={
                            "file_id": str(entry.get("file_id") or ""),
                            "file_name": str(entry.get("file_name") or Path(local_path).name),
                            "tissue_id": tissue_id,
                            "tissue_site_detail": tissue_detail,
                            "value_type": str(entry.get("value_type") or "TPM"),
                            "analysis_gate_status": "waiting_gtex_expression_matrix_build",
                            "tcga_default_control_status": "disabled",
                        },
                    )
                )
                events.append(_event(entry, status, local_path=local_path, bytes_downloaded=size))
            except Exception as exc:
                file_records.append(_blocked_record(entry, f"download_failed:{exc}"))
                events.append(_event(entry, "failed", message=str(exc)))
        success_count = sum(1 for event in events if event.get("status") == "downloaded")
        cache_hit_count = sum(1 for event in events if event.get("status") == "cache_hit")
        failed_count = sum(1 for event in events if event.get("status") == "failed")
        skipped_count = sum(1 for event in events if event.get("status") == "skipped")
        status = _execution_status(downloaded_files, failed_count, entries)
        summary = {
            "success_count": success_count,
            "cache_hit_count": cache_hit_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
            "acquired_count": success_count + cache_hit_count,
            "total_size_bytes": total_size,
        }
        message = f"{tissue_detail}：GTEx 原始文件已获取 {summary['acquired_count']} 个；失败 {failed_count} 个；等待 G6.3 构建表达矩阵。"
        manifest = {
            "schema_version": "biomedpilot.gtex_download_manifest.v2",
            "download_id": download_id,
            "created_at": _now(),
            "tissue_id": tissue_id,
            "tissue_site_detail": tissue_detail,
            "status": status,
            "plan_path": str(plan_path),
            "target_dir": str(target_dir),
            "file_manifest_entries": entries,
            "downloaded_files": downloaded_files,
            "file_records": file_records,
            "download_events": events,
            "summary": summary,
            "analysis_gate_status": "waiting_gtex_expression_matrix_build",
            "tcga_default_control_status": "disabled",
        }
        _write_json(manifest_path, manifest)
        receipt = {
            "schema_version": "biomedpilot.gtex_download_receipt.v1",
            "download_id": download_id,
            "created_at": _now(),
            "source": "gtex",
            "source_type": "gtex_tissue",
            "tissue_id": tissue_id,
            "tissue_site_detail": tissue_detail,
            "status": status,
            "message": message,
            "plan_path": str(plan_path),
            "request_path": str(request_path),
            "download_manifest_path": str(manifest_path),
            "target_dir": str(target_dir),
            "downloaded_files": downloaded_files,
            "file_records": file_records,
            "download_events": events,
            "summary": summary,
        }
        _write_json(receipt_path, receipt)
        acquisition = _register_download(
            root=root,
            tissue_id=tissue_id,
            tissue_detail=tissue_detail,
            status=status,
            message=message,
            downloaded_files=downloaded_files,
            request_path=request_path,
            receipt_path=receipt_path,
            manifest_path=manifest_path,
            target_dir=target_dir,
            file_records=file_records,
            summary=summary,
        )
        return GTExDownloadExecutionResult(
            success=bool(downloaded_files) and failed_count == 0,
            status=status,
            message=message,
            tissue_id=tissue_id,
            tissue_site_detail=tissue_detail,
            download_id=download_id,
            plan_path=plan_path,
            request_path=request_path,
            receipt_path=receipt_path,
            manifest_path=manifest_path,
            target_dir=target_dir,
            downloaded_files=tuple(downloaded_files),
            success_count=success_count,
            failed_count=failed_count,
            skipped_count=skipped_count,
            cache_hit_count=cache_hit_count,
            total_size_bytes=total_size,
            acquisition_summary=acquisition,
        )


def latest_gtex_raw_expression_record_path(project_root: str | Path) -> Path | None:
    root = Path(project_root).expanduser().resolve()
    records_dir = root / "acquisition" / "records"
    if not records_dir.exists():
        return None
    candidates: list[Path] = []
    for path in records_dir.glob("*.json"):
        if path.name == "latest_acquisition_record.json":
            continue
        try:
            payload = _read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        if not isinstance(metadata, dict):
            continue
        if str(metadata.get("analysis_gate_status") or "") != "waiting_gtex_expression_matrix_build":
            continue
        if str(metadata.get("source") or "") == "gtex" and payload.get("source_files"):
            candidates.append(path)
    return max(candidates, key=lambda item: item.stat().st_mtime) if candidates else None


def _register_download(
    *,
    root: Path,
    tissue_id: str,
    tissue_detail: str,
    status: str,
    message: str,
    downloaded_files: list[str],
    request_path: Path,
    receipt_path: Path,
    manifest_path: Path,
    target_dir: Path,
    file_records: list[dict[str, Any]],
    summary: dict[str, object],
) -> AcquisitionSummary:
    return register_acquisition(
        root,
        source_type="gtex_tissue",
        source_label=tissue_id,
        strategy="reference" if downloaded_files else "plan_only",
        selected_paths=[Path(path) for path in downloaded_files],
        metadata={
            "source": "gtex",
            "ui_source": "gtex_database_page",
            "registration_status": "registered_gtex_raw_files_waiting_expression_build" if downloaded_files else "registered_gtex_download_attempt",
            "download_status": status,
            "download_message": message,
            "download_request_path": str(request_path),
            "download_receipt_path": str(receipt_path),
            "download_manifest_path": str(manifest_path),
            "download_target_dir": str(target_dir),
            "ready_for_recognition": "pending_expression_matrix_build",
            "recognition_scope": "gtex_raw_files_waiting_g6_3",
            "analysis_gate_status": "waiting_gtex_expression_matrix_build",
            "analysis_gate_message": "GTEx 原始文件已获取，等待 G6.3 构建表达矩阵。",
            "tissue_id": tissue_id,
            "tissue_site_detail": tissue_detail,
            "display_title_zh": f"GTEx {tissue_detail}",
            "gtex_download_summary": summary,
            "tcga_merge_status": "not_merged",
            "tcga_default_control_status": "disabled",
            "requires_explicit_joint_config": True,
            "warnings": ["GTEx 不自动作为 TCGA normal control；TCGA+GTEx 需要显式联合配置。"],
        },
        file_records=file_records,
    )


def _validate_plan(plan: dict[str, Any]) -> None:
    if str(plan.get("schema_version") or "") != "biomedpilot.gtex_download_plan_draft.v1":
        raise ValueError("不是 G6.1 GTEx 下载计划草案。")
    if str(plan.get("status") or "") != "draft_only":
        raise ValueError("GTEx 下载计划状态不是 draft_only。")
    if not str(plan.get("tissue_id") or "").strip():
        raise ValueError("GTEx 下载计划缺少 tissue_id。")


def _entry_list(value: object) -> list[dict[str, Any]]:
    return [dict(entry) for entry in value if isinstance(entry, dict)] if isinstance(value, list) else []


def _blocked_record(entry: dict[str, Any], message: str) -> dict[str, Any]:
    return build_blocked_file_record(
        source="gtex",
        role=str(entry.get("role") or "gtex_tissue_expression"),
        source_url=str(entry.get("url") or entry.get("download_url") or ""),
        source_path=str(entry.get("file_name") or ""),
        risk_level="medium",
        message=message,
        extra={"file_id": str(entry.get("file_id") or ""), "file_name": str(entry.get("file_name") or ""), "status": "failed"},
    )


def _event(entry: dict[str, Any], status: str, *, message: str = "", local_path: str = "", bytes_downloaded: int = 0) -> dict[str, object]:
    return {
        "file_id": str(entry.get("file_id") or ""),
        "file_name": str(entry.get("file_name") or ""),
        "status": status,
        "message": message,
        "local_path": local_path,
        "bytes_downloaded": bytes_downloaded,
    }


def _execution_status(downloaded_files: list[str], failed_count: int, entries: list[dict[str, Any]]) -> str:
    if downloaded_files and failed_count:
        return "gtex_raw_files_acquired_with_warnings"
    if downloaded_files:
        return "gtex_raw_files_acquired"
    if not entries:
        return "gtex_download_plan_empty"
    return "gtex_raw_file_download_failed"


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


def _slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "_" for char in str(value or "")).strip("_") or "gtex"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


__all__ = [
    "GTExDownloadExecutionResult",
    "GTExDownloadPlanExecutor",
    "latest_gtex_raw_expression_record_path",
]
