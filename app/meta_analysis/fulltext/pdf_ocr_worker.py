from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.meta_analysis.fulltext.ocr_exporter import OcrExportResult, write_ocr_outputs
from app.meta_analysis.fulltext.ocr_models import (
    OCR_STATUS_FAILED,
    OCR_STATUS_PENDING_RUNTIME,
    OcrDocumentResult,
    OcrEngineInfo,
    OcrSource,
)


class PdfOcrRuntimeRunner(Protocol):
    def run_pdf_ocr(self, pdf_path: Path, *, record_id: str, attachment_id: str = "", lang: str = "auto") -> OcrDocumentResult:
        ...


@dataclass(frozen=True)
class OcrWorkerResult:
    success: bool
    record_id: str
    source_path: str
    text_path: str
    json_path: str
    status: str
    message: str


class PdfOcrWorker:
    def __init__(self, *, runner: PdfOcrRuntimeRunner | None = None) -> None:
        self._runner = runner

    def process_pdf(
        self,
        project_dir: str | Path,
        *,
        record_id: str,
        pdf_path: str | Path,
        attachment_id: str = "",
        lang: str = "auto",
        output_dir: str | Path | None = None,
    ) -> OcrWorkerResult:
        project_path = Path(project_dir).expanduser().resolve()
        source = Path(pdf_path).expanduser().resolve()
        target_dir = Path(output_dir).expanduser().resolve() if output_dir is not None else project_path / "fulltext" / "ocr"
        if not source.exists() or not source.is_file():
            return _export_failure(
                target_dir,
                source=source,
                record_id=record_id,
                attachment_id=attachment_id,
                media_type="application/pdf",
                error_code="pdf_file_missing",
            )
        if self._runner is None:
            return _export_failure(
                target_dir,
                source=source,
                record_id=record_id,
                attachment_id=attachment_id,
                media_type="application/pdf",
                error_code="ocr_runtime_runner_not_configured",
                status=OCR_STATUS_PENDING_RUNTIME,
            )
        try:
            document = self._runner.run_pdf_ocr(source, record_id=record_id, attachment_id=attachment_id, lang=lang)
        except Exception as exc:
            return _export_failure(
                target_dir,
                source=source,
                record_id=record_id,
                attachment_id=attachment_id,
                media_type="application/pdf",
                error_code=f"ocr_runtime_failed:{type(exc).__name__}",
            )
        export = write_ocr_outputs(document, target_dir, base_name=record_id)
        return _worker_result(True, record_id, source, export, "PDF OCR output written.")


def _export_failure(
    output_dir: Path,
    *,
    source: Path,
    record_id: str,
    attachment_id: str,
    media_type: str,
    error_code: str,
    status: str = OCR_STATUS_FAILED,
) -> OcrWorkerResult:
    document = OcrDocumentResult(
        source=OcrSource(path=str(source), media_type=media_type, attachment_id=attachment_id, record_id=record_id),
        engine=OcrEngineInfo(),
        status=status,
        warnings=(error_code,),
        errors=(error_code,),
    )
    export = write_ocr_outputs(document, output_dir, base_name=record_id)
    return _worker_result(False, record_id, source, export, f"PDF OCR not completed: {error_code}.")


def _worker_result(success: bool, record_id: str, source: Path, export: OcrExportResult, message: str) -> OcrWorkerResult:
    return OcrWorkerResult(
        success=success,
        record_id=record_id,
        source_path=str(source),
        text_path=export.text_path,
        json_path=export.json_path,
        status=export.status,
        message=message,
    )
