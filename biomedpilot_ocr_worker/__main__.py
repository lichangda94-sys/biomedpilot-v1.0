from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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
    ocr, engine_version = _create_paddleocr(lang)
    page = _ocr_image_path(ocr, source, page_index=0, lang=lang)
    return WorkerDocument(
        source=WorkerSource(path=str(source), media_type=_image_media_type(source), attachment_id=attachment_id, record_id=record_id),
        engine=WorkerEngine(engine_version=engine_version),
        pages=(page,),
    )


def run_pdf_ocr(path: str | Path, *, record_id: str, attachment_id: str = "", lang: str = "auto") -> WorkerDocument:
    source = Path(path).expanduser().resolve()
    if not source.exists() or not source.is_file():
        raise WorkerError("input_file_missing")
    try:
        import fitz  # type: ignore[import-not-found]
    except Exception as exc:
        raise WorkerError("pymupdf_missing") from exc
    ocr, engine_version = _create_paddleocr(lang)
    pages: list[WorkerPage] = []
    with tempfile.TemporaryDirectory(prefix="biomedpilot_ocr_pdf_") as tmp_dir:
        temp_path = Path(tmp_dir)
        with fitz.open(str(source)) as pdf:
            for page_index in range(pdf.page_count):
                page = pdf[page_index]
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                image_path = temp_path / f"page_{page_index + 1}.png"
                pixmap.save(str(image_path))
                pages.append(_ocr_image_path(ocr, image_path, page_index=page_index, page_label=str(page_index + 1), lang=lang))
    return WorkerDocument(
        source=WorkerSource(path=str(source), media_type="application/pdf", attachment_id=attachment_id, record_id=record_id),
        engine=WorkerEngine(engine_version=engine_version),
        pages=tuple(pages),
    )


def _create_paddleocr(lang: str):
    try:
        import paddleocr as paddleocr_module  # type: ignore[import-not-found]
        from paddleocr import PaddleOCR  # type: ignore[import-not-found]
    except Exception as exc:
        raise WorkerError("paddleocr_import_failed") from exc
    kwargs = {
        "lang": _paddle_lang(lang),
        "ocr_version": "PP-OCRv5",
        "use_doc_orientation_classify": False,
        "use_doc_unwarping": False,
        "use_textline_orientation": False,
    }
    try:
        ocr = PaddleOCR(**kwargs)
    except TypeError:
        kwargs.pop("ocr_version", None)
        ocr = PaddleOCR(**kwargs)
    return ocr, str(getattr(paddleocr_module, "__version__", "") or "")


def _ocr_image_path(ocr, image_path: Path, *, page_index: int, page_label: str | None = None, lang: str = "auto") -> WorkerPage:
    result = ocr.predict(str(image_path))
    if not result:
        return WorkerPage(page_index=page_index, page_label=page_label or str(page_index + 1), warnings=("no_ocr_result",))
    payload = _result_to_mapping(result[0])
    rec_texts = [str(item) for item in payload.get("rec_texts", [])]
    rec_scores = payload.get("rec_scores", [])
    polys = payload.get("rec_polys") or payload.get("dt_polys") or []
    blocks = tuple(
        WorkerBlock(
            block_id=f"p{page_index + 1}_b{index + 1}",
            text=text,
            confidence=_float_at(rec_scores, index),
            bbox=_bbox_at(polys, index),
            language=lang,
            order=index,
        )
        for index, text in enumerate(rec_texts)
        if text.strip()
    )
    text = "\n".join(block.text for block in blocks).strip()
    width, height = _image_size(image_path)
    return WorkerPage(
        page_index=page_index,
        page_label=page_label or str(page_index + 1),
        text=text,
        width=width,
        height=height,
        blocks=blocks,
    )


def _result_to_mapping(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return result
    if hasattr(result, "to_dict"):
        payload = result.to_dict()
        if isinstance(payload, dict):
            return payload.get("res", payload) if isinstance(payload.get("res", payload), dict) else payload
    if hasattr(result, "json"):
        payload = json.loads(result.json())
        return payload.get("res", payload) if isinstance(payload, dict) else {}
    try:
        return dict(result)
    except Exception:
        return {}


def _bbox_at(polys: Any, index: int) -> tuple[float, float, float, float]:
    try:
        poly = polys[index]
        points = poly.tolist() if hasattr(poly, "tolist") else poly
        xs = [float(point[0]) for point in points]
        ys = [float(point[1]) for point in points]
        return (min(xs), min(ys), max(xs), max(ys))
    except Exception:
        return (0, 0, 0, 0)


def _float_at(values: Any, index: int) -> float:
    try:
        return float(values[index])
    except Exception:
        return 0.0


def _image_size(path: Path) -> tuple[int, int]:
    try:
        from PIL import Image  # type: ignore[import-not-found]

        with Image.open(path) as image:
            return int(image.width), int(image.height)
    except Exception:
        return 0, 0


def _paddle_lang(lang: str) -> str:
    normalized = lang.strip().lower()
    if normalized in {"", "auto", "zh", "zho", "ch", "chi", "cn", "zh-cn"}:
        return "ch"
    if normalized in {"en", "eng", "english"}:
        return "en"
    if normalized in {"cht", "traditional", "traditional_chinese", "zh-tw", "zh-hk"}:
        return "chinese_cht"
    return normalized


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
