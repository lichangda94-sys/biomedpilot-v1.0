from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from biomedpilot_ocr_worker.paddleocr_engine import (
    EnginePage,
    PaddleOcrEngineError,
    create_paddleocr_engine,
    ocr_image_path,
    ocr_pdf_path,
    paddle_lang,
)


OCR_RESULT_SCHEMA_VERSION = "biomedpilot_ocr_result.v1"
DEFAULT_ENGINE_ID = "paddleocr_local"


@dataclass(frozen=True)
class WorkerSource:
    path: str
    media_type: str
    attachment_id: str = ""
    record_id: str = ""


@dataclass(frozen=True)
class WorkerEngine:
    engine_id: str = DEFAULT_ENGINE_ID
    engine_version: str = ""
    runtime_manifest_id: str = ""


@dataclass(frozen=True)
class WorkerBlock:
    block_id: str
    text: str
    confidence: float = 0.0
    bbox: tuple[float, float, float, float] = (0, 0, 0, 0)
    language: str = "auto"
    kind: str = "text"
    order: int = 0

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["bbox"] = list(self.bbox)
        return payload


@dataclass(frozen=True)
class WorkerPage:
    page_index: int
    page_label: str
    text: str = ""
    width: int = 0
    height: int = 0
    blocks: tuple[WorkerBlock, ...] = ()
    tables: tuple[dict[str, Any], ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_index": self.page_index,
            "page_label": self.page_label,
            "width": self.width,
            "height": self.height,
            "text": self.text,
            "blocks": [block.to_dict() for block in self.blocks],
            "tables": [dict(item) for item in self.tables],
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class WorkerDocument:
    source: WorkerSource
    engine: WorkerEngine
    pages: tuple[WorkerPage, ...] = ()
    status: str = "completed"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": OCR_RESULT_SCHEMA_VERSION,
            "status": self.status,
            "created_at": self.created_at,
            "source": asdict(self.source),
            "engine": asdict(self.engine),
            "pages": [page.to_dict() for page in self.pages],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "safety_note": "OCR output is auxiliary fulltext acquisition only and does not create final Meta extraction, screening, statistics, or medical conclusions.",
        }


class WorkerError(RuntimeError):
    pass


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    source = Path(args.input).expanduser().resolve()
    try:
        if args.mode == "pdf":
            document = run_pdf_ocr(source, record_id=args.record_id, attachment_id=args.attachment_id, lang=args.lang)
        else:
            document = run_image_ocr(source, record_id=args.record_id, attachment_id=args.attachment_id, lang=args.lang)
    except Exception as exc:
        error_code = _error_code(exc)
        document = _failure_document(
            source,
            media_type="application/pdf" if args.mode == "pdf" else _image_media_type(source),
            record_id=args.record_id,
            attachment_id=args.attachment_id,
            error_code=error_code,
        )
        print(json.dumps(document.to_dict(), ensure_ascii=False), flush=True)
        return _exit_code(error_code)
    print(json.dumps(document.to_dict(), ensure_ascii=False), flush=True)
    return 0


def run_image_ocr(path: str | Path, *, record_id: str, attachment_id: str = "", lang: str = "auto") -> WorkerDocument:
    source = Path(path).expanduser().resolve()
    if not source.exists() or not source.is_file():
        raise WorkerError("input_file_missing")
    engine = _create_paddleocr(lang)
    page = _worker_page(ocr_image_path(engine, source, page_index=0), lang=lang)
    return WorkerDocument(
        source=WorkerSource(path=str(source), media_type=_image_media_type(source), attachment_id=attachment_id, record_id=record_id),
        engine=WorkerEngine(engine_version=engine.engine_version),
        pages=(page,),
    )


def run_pdf_ocr(path: str | Path, *, record_id: str, attachment_id: str = "", lang: str = "auto") -> WorkerDocument:
    source = Path(path).expanduser().resolve()
    if not source.exists() or not source.is_file():
        raise WorkerError("input_file_missing")
    engine = _create_paddleocr(lang)
    pages = [_worker_page(page, lang=lang) for page in ocr_pdf_path(engine, source)]
    return WorkerDocument(
        source=WorkerSource(path=str(source), media_type="application/pdf", attachment_id=attachment_id, record_id=record_id),
        engine=WorkerEngine(engine_version=engine.engine_version),
        pages=tuple(pages),
    )


def _create_paddleocr(lang: str):
    try:
        return create_paddleocr_engine(lang)
    except PaddleOcrEngineError as exc:
        raise WorkerError(str(exc)) from exc
    except Exception as exc:
        raise WorkerError(f"paddleocr_create_failed:{type(exc).__name__}") from exc


def _worker_page(page: EnginePage, *, lang: str) -> WorkerPage:
    blocks = tuple(
        WorkerBlock(
            block_id=f"p{page.page_index + 1}_b{index + 1}",
            text=block.text,
            confidence=block.confidence,
            bbox=block.bbox,
            language=lang,
            kind="text",
            order=index,
        )
        for index, block in enumerate(page.blocks)
    )
    return WorkerPage(
        page_index=page.page_index,
        page_label=page.page_label,
        text=page.text,
        width=page.width,
        height=page.height,
        blocks=blocks,
        tables=page.tables,
        warnings=page.warnings,
    )


def _paddle_lang(lang: str) -> str:
    return paddle_lang(lang)


def _image_media_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix in {".tif", ".tiff"}:
        return "image/tiff"
    return "image/*"


def _failure_document(source: Path, *, media_type: str, record_id: str, attachment_id: str, error_code: str) -> WorkerDocument:
    return WorkerDocument(
        source=WorkerSource(path=str(source), media_type=media_type, attachment_id=attachment_id, record_id=record_id),
        engine=WorkerEngine(),
        pages=(),
        status="failed",
        warnings=(error_code,),
        errors=(error_code,),
    )


def _error_code(exc: Exception) -> str:
    if isinstance(exc, WorkerError):
        return str(exc) or "ocr_worker_failed"
    return f"ocr_worker_failed:{type(exc).__name__}"


def _exit_code(error_code: str) -> int:
    if error_code == "input_file_missing":
        return 2
    if error_code in {"paddleocr_import_failed", "pymupdf_missing"}:
        return 3
    return 4


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BioMedPilot PaddleOCR runtime worker")
    parser.add_argument("--mode", choices=("pdf", "image"), required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--record-id", required=True)
    parser.add_argument("--attachment-id", default="")
    parser.add_argument("--lang", default="auto")
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
