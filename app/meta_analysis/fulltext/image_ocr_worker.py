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
from app.meta_analysis.fulltext.pdf_ocr_worker import OcrWorkerResult


class ImageOcrRuntimeRunner(Protocol):
    def run_image_ocr(self, image_path: Path, *, record_id: str, attachment_id: str = "", lang: str = "auto") -> OcrDocumentResult:
        ...


@dataclass(frozen=True)
class ImageOcrWorker:
    runner: ImageOcrRuntimeRunner | None = None

    def process_image(
        self,
        project_dir: str | Path,
        *,
        record_id: str,
        image_path: str | Path,
        attachment_id: str = "",
        lang: str = "auto",
        output_dir: str | Path | None = None,
    ) -> OcrWorkerResult:
        project_path = Path(project_dir).expanduser().resolve()
        source = Path(image_path).expanduser().resolve()
        target_dir = Path(output_dir).expanduser().resolve() if output_dir is not None else project_path / "fulltext" / "ocr"
        if not source.exists() or not source.is_file():
            return _export_failure(
                target_dir,
                source=source,
                record_id=record_id,
                attachment_id=attachment_id,
                error_code="image_file_missing",
            )
        if self.runner is None:
            return _export_failure(
                target_dir,
                source=source,
                record_id=record_id,
                attachment_id=attachment_id,
                error_code="ocr_runtime_runner_not_configured",
                status=OCR_STATUS_PENDING_RUNTIME,
            )
        try:
            document = self.runner.run_image_ocr(source, record_id=record_id, attachment_id=attachment_id, lang=lang)
        except Exception as exc:
            return _export_failure(
                target_dir,
                source=source,
                record_id=record_id,
                attachment_id=attachment_id,
                error_code=f"ocr_runtime_failed:{type(exc).__name__}",
            )
        export = write_ocr_outputs(document, target_dir, base_name=record_id)
        return _worker_result(True, record_id, source, export, "Image OCR output written.")


def _export_failure(
    output_dir: Path,
    *,
    source: Path,
    record_id: str,
    attachment_id: str,
    error_code: str,
    status: str = OCR_STATUS_FAILED,
) -> OcrWorkerResult:
    document = OcrDocumentResult(
        source=OcrSource(path=str(source), media_type=_image_media_type(source), attachment_id=attachment_id, record_id=record_id),
        engine=OcrEngineInfo(),
        status=status,
        warnings=(error_code,),
        errors=(error_code,),
    )
    export = write_ocr_outputs(document, output_dir, base_name=record_id)
    return _worker_result(False, record_id, source, export, f"Image OCR not completed: {error_code}.")


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


def _image_media_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix in {".tif", ".tiff"}:
        return "image/tiff"
    return "image/*"
