from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.meta_analysis.literature_import_core import (
    append_import_batch,
    build_import_diagnostics,
    normalize_record_payload,
    parse_literature_file,
    write_import_diagnostics,
)
from app.shared.storage import default_storage_root


@dataclass(frozen=True)
class LiteratureBatchImportRequest:
    project_id: str
    source_path: str
    import_format: str = "auto"
    source_database: str = ""
    search_date: str = ""
    search_strategy: str = ""
    dedup_mode: str = "detect_only"


@dataclass(frozen=True)
class LiteratureBatchImportSummary:
    success: bool
    message: str
    project_id: str
    batch_id: str = ""
    source_path: str = ""
    import_format: str = ""
    source_database: str = ""
    search_date: str = ""
    search_strategy: str = ""
    dedup_mode: str = ""
    status: str = ""
    raw_record_count: int = 0
    parsed_record_count: int = 0
    normalized_record_count: int = 0
    failed_record_count: int = 0
    warning_count: int = 0
    duplicate_candidate_count: int = 0
    records_after_dedup_count: int = 0
    diagnostics_path: str = ""
    warnings_path: str = ""
    next_step: str = "Review duplicates"
    error_message: str = ""


class LiteratureBatchImportService:
    def __init__(self, *, storage_root: Path | None = None) -> None:
        self._storage_root = storage_root or default_storage_root()

    def execute_import(self, request: LiteratureBatchImportRequest) -> LiteratureBatchImportSummary:
        validation_error = self._validate(request)
        if validation_error:
            return LiteratureBatchImportSummary(
                success=False,
                message=validation_error,
                project_id=request.project_id,
                source_path=request.source_path,
                import_format=request.import_format,
                source_database=request.source_database,
                search_date=request.search_date,
                search_strategy=request.search_strategy,
                dedup_mode=request.dedup_mode,
                error_message=validation_error,
            )

        source_path = Path(request.source_path).expanduser().resolve()
        import_format = self._detect_format(source_path, request.import_format)
        if import_format == "unknown":
            message = "无法识别导入格式，请选择 ris、nbib 或 csv。"
            return LiteratureBatchImportSummary(
                success=False,
                message=message,
                project_id=request.project_id,
                source_path=str(source_path),
                import_format=request.import_format,
                source_database=request.source_database,
                search_date=request.search_date,
                search_strategy=request.search_strategy,
                dedup_mode=request.dedup_mode,
                error_message=message,
            )

        try:
            root_dir = self._project_dir(request.project_id)
            adapter_result = parse_literature_file(source_path, request.project_id, import_format)
            records = [
                normalize_record_payload(
                    asdict(record),
                    batch_id=adapter_result.batch_id,
                    project_id=request.project_id,
                    source_type=import_format,
                )
                for record in adapter_result.records
            ]
            diagnostics = build_import_diagnostics(adapter_result.batch_id, records)
            diagnostics_path, warnings_path = write_import_diagnostics(root_dir, adapter_result.batch_id, diagnostics)
            now = datetime.now(timezone.utc).isoformat()
            append_import_batch(
                root_dir,
                {
                    "batch_id": adapter_result.batch_id,
                    "project_id": request.project_id,
                    "source_path": str(source_path),
                    "import_format": import_format,
                    "source_type": "file",
                    "metadata": {
                        "source_database": request.source_database,
                        "search_date": request.search_date,
                        "search_strategy": request.search_strategy,
                        "dedup_mode": request.dedup_mode,
                        "ui_entry": "meta_literature_import_panel",
                        "software_status": "active_runtime",
                    },
                    "status": "completed",
                    "created_at": now,
                    "completed_at": now,
                    "raw_record_count": diagnostics.raw_record_count,
                    "parsed_record_count": diagnostics.parsed_record_count,
                    "normalized_record_count": diagnostics.normalized_record_count,
                    "failed_records": diagnostics.failed_record_count,
                    "warning_count": diagnostics.warning_count,
                    "duplicate_candidate_count": diagnostics.duplicate_candidate_count,
                    "records_after_dedup_count": diagnostics.records_after_dedup_count,
                    "diagnostics_path": str(diagnostics_path),
                    "warnings_path": str(warnings_path),
                    "records": records,
                },
            )
            return LiteratureBatchImportSummary(
                success=True,
                message=f"Import batch completed: {diagnostics.normalized_record_count} records imported.",
                project_id=request.project_id,
                batch_id=adapter_result.batch_id,
                source_path=str(source_path),
                import_format=import_format,
                source_database=request.source_database,
                search_date=request.search_date,
                search_strategy=request.search_strategy,
                dedup_mode=request.dedup_mode,
                status="completed",
                raw_record_count=diagnostics.raw_record_count,
                parsed_record_count=diagnostics.parsed_record_count,
                normalized_record_count=diagnostics.normalized_record_count,
                failed_record_count=diagnostics.failed_record_count,
                warning_count=diagnostics.warning_count,
                duplicate_candidate_count=diagnostics.duplicate_candidate_count,
                records_after_dedup_count=diagnostics.records_after_dedup_count,
                diagnostics_path=str(diagnostics_path),
                warnings_path=str(warnings_path),
            )
        except Exception as exc:
            return LiteratureBatchImportSummary(
                success=False,
                message="文献批量导入失败，请检查文件格式、导入格式和文件内容。",
                project_id=request.project_id,
                source_path=str(source_path),
                import_format=import_format,
                source_database=request.source_database,
                search_date=request.search_date,
                search_strategy=request.search_strategy,
                dedup_mode=request.dedup_mode,
                error_message=str(exc),
            )

    def _validate(self, request: LiteratureBatchImportRequest) -> str:
        if not request.project_id.strip():
            return "缺少 project_id，无法写入项目目录。"
        if not request.source_path.strip():
            return "请选择要导入的 RIS、NBIB 或 CSV 文件。"
        source_path = Path(request.source_path).expanduser()
        if not source_path.exists():
            return "导入文件不存在，请检查路径。"
        if not source_path.is_file():
            return "导入路径不是文件，请选择 RIS、NBIB 或 CSV 文件。"
        if request.dedup_mode and request.dedup_mode not in {"detect_only", "skip", "manual_review"}:
            return "dedup_mode 仅支持 detect_only、skip 或 manual_review。"
        return ""

    def _detect_format(self, source_path: Path, import_format: str) -> str:
        requested = import_format.strip().lower() or "auto"
        if requested in {"auto", "auto-detect", "autodetect"}:
            return {".ris": "ris", ".nbib": "nbib", ".csv": "csv"}.get(source_path.suffix.lower(), "unknown")
        if requested in {"ris", "nbib", "csv"}:
            return requested
        return "unknown"

    def _project_dir(self, project_id: str) -> Path:
        return self._storage_root / "projects" / project_id / "meta_analysis"

    def _diagnostics_path(self, project_id: str, batch_id: str) -> Path:
        return self._project_dir(project_id) / "literature" / "import_diagnostics" / f"{batch_id}_import_diagnostics.json"

    def _warnings_path(self, project_id: str, batch_id: str) -> Path:
        return self._project_dir(project_id) / "literature" / "import_diagnostics" / f"{batch_id}_import_warnings.csv"
