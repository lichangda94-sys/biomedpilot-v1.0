from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.adapters.literature_import_adapter import _legacy_path
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
            with _legacy_path():
                from literature.batch_service import ImportBatchService
                from literature.models import ImportFormatHint, ImportSourceKind, LiteratureProject
                from literature.store import LiteratureStore

                root_dir = self._project_dir(request.project_id)
                store = LiteratureStore(root_dir)
                if store.get_project(request.project_id) is None:
                    store.save_project(
                        LiteratureProject(
                            project_id=request.project_id,
                            name=request.project_id,
                            description="BioMedPilot Meta Analysis Developer Preview literature import project.",
                            metadata={"created_by": "BioMedPilot Meta Literature Import Panel"},
                        )
                    )
                batch_service = ImportBatchService(store)
                batch = batch_service.create_batch(
                    request.project_id,
                    str(source_path),
                    source_type=ImportSourceKind.FILE,
                    format_hint=ImportFormatHint(import_format),
                    metadata={
                        "source_database": request.source_database,
                        "search_date": request.search_date,
                        "search_strategy": request.search_strategy,
                        "dedup_mode": request.dedup_mode,
                        "ui_entry": "meta_literature_import_panel",
                        "software_status": "developer_preview_testing",
                    },
                )
                executed = batch_service.execute_batch(batch.batch_id)
            diagnostics_path = self._diagnostics_path(request.project_id, executed.batch_id)
            warnings_path = self._warnings_path(request.project_id, executed.batch_id)
            return LiteratureBatchImportSummary(
                success=True,
                message=f"Import batch completed: {executed.imported_records} records imported.",
                project_id=request.project_id,
                batch_id=executed.batch_id,
                source_path=str(source_path),
                import_format=import_format,
                source_database=request.source_database,
                search_date=request.search_date,
                search_strategy=request.search_strategy,
                dedup_mode=request.dedup_mode,
                status=executed.status.value,
                raw_record_count=executed.raw_record_count,
                parsed_record_count=executed.parsed_record_count,
                normalized_record_count=executed.normalized_record_count,
                failed_record_count=executed.failed_records,
                warning_count=executed.warning_count,
                duplicate_candidate_count=executed.duplicate_candidate_count,
                records_after_dedup_count=executed.records_after_dedup_count,
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
