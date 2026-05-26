from __future__ import annotations

import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


PADDLEOCR_SOURCE_REFERENCE = "/Users/changdali/Desktop/PaddleOCR-main"
PADDLEOCR_VERSION = "PP-OCRv5"


@dataclass(frozen=True)
class EngineBlock:
    text: str
    confidence: float = 0.0
    bbox: tuple[float, float, float, float] = (0, 0, 0, 0)
    order: int = 0


@dataclass(frozen=True)
class EnginePage:
    page_index: int
    page_label: str
    text: str
    width: int = 0
    height: int = 0
    blocks: tuple[EngineBlock, ...] = ()
    tables: tuple[dict[str, Any], ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class PaddleOcrEngine:
    ocr: Any
    engine_version: str
    source_reference: str = PADDLEOCR_SOURCE_REFERENCE


class PaddleOcrEngineError(RuntimeError):
    pass


def create_paddleocr_engine(lang: str) -> PaddleOcrEngine:
    os.environ.setdefault("FLAGS_allocator_strategy", "auto_growth")
    source_reference = _prepare_source_override()
    try:
        import paddleocr as paddleocr_module  # type: ignore[import-not-found]
        from paddleocr import PaddleOCR  # type: ignore[import-not-found]
    except Exception as exc:
        raise PaddleOcrEngineError("paddleocr_import_failed") from exc

    kwargs = _paddleocr_kwargs(lang)
    try:
        ocr = PaddleOCR(**kwargs)
    except TypeError:
        kwargs.pop("ocr_version", None)
        ocr = PaddleOCR(**kwargs)
    return PaddleOcrEngine(
        ocr=ocr,
        engine_version=str(getattr(paddleocr_module, "__version__", "") or ""),
        source_reference=source_reference or str(Path(getattr(paddleocr_module, "__file__", "")).resolve()),
    )


def ocr_image_path(engine: PaddleOcrEngine, image_path: Path, *, page_index: int, page_label: str | None = None) -> EnginePage:
    result = engine.ocr.predict(str(image_path))
    if not result:
        return EnginePage(page_index=page_index, page_label=page_label or str(page_index + 1), text="", warnings=("no_ocr_result",))
    payload = result_to_mapping(result[0])
    blocks = blocks_from_result_payload(payload)
    text = "\n".join(block.text for block in blocks).strip()
    width, height = image_size(image_path)
    return EnginePage(
        page_index=page_index,
        page_label=page_label or str(page_index + 1),
        text=text,
        width=width,
        height=height,
        blocks=blocks,
        tables=(),
    )


def ocr_pdf_path(engine: PaddleOcrEngine, source: Path) -> tuple[EnginePage, ...]:
    try:
        import fitz  # type: ignore[import-not-found]
    except Exception as exc:
        raise PaddleOcrEngineError("pymupdf_missing") from exc

    pages: list[EnginePage] = []
    with tempfile.TemporaryDirectory(prefix="biomedpilot_ocr_pdf_") as tmp_dir:
        temp_path = Path(tmp_dir)
        with fitz.open(str(source)) as pdf:
            for page_index in range(pdf.page_count):
                page = pdf[page_index]
                image_path = temp_path / f"page_{page_index + 1}.png"
                _render_pdf_page(page, image_path, fitz)
                pages.append(ocr_image_path(engine, image_path, page_index=page_index, page_label=str(page_index + 1)))
    return tuple(pages)


def blocks_from_result_payload(payload: dict[str, Any]) -> tuple[EngineBlock, ...]:
    rec_texts = [str(item) for item in payload.get("rec_texts", [])]
    rec_scores = payload.get("rec_scores", [])
    polys = payload.get("rec_polys") or payload.get("dt_polys") or []
    blocks = [
        EngineBlock(
            text=text,
            confidence=float_at(rec_scores, index),
            bbox=bbox_at(polys, index),
            order=index,
        )
        for index, text in enumerate(rec_texts)
        if text.strip()
    ]
    return tuple(_sort_blocks_reading_order(blocks))


def result_to_mapping(result: Any) -> dict[str, Any]:
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


def paddle_lang(lang: str) -> str:
    normalized = lang.strip().lower()
    if normalized in {"", "auto", "zh", "zho", "ch", "chi", "cn", "zh-cn"}:
        return "ch"
    if normalized in {"en", "eng", "english"}:
        return "en"
    if normalized in {"cht", "traditional", "traditional_chinese", "zh-tw", "zh-hk"}:
        return "chinese_cht"
    return normalized


def bbox_at(polys: Any, index: int) -> tuple[float, float, float, float]:
    try:
        poly = polys[index]
        points = poly.tolist() if hasattr(poly, "tolist") else poly
        xs = [float(point[0]) for point in points]
        ys = [float(point[1]) for point in points]
        return (min(xs), min(ys), max(xs), max(ys))
    except Exception:
        return (0, 0, 0, 0)


def float_at(values: Any, index: int) -> float:
    try:
        return float(values[index])
    except Exception:
        return 0.0


def image_size(path: Path) -> tuple[int, int]:
    try:
        from PIL import Image  # type: ignore[import-not-found]

        with Image.open(path) as image:
            return int(image.width), int(image.height)
    except Exception:
        return 0, 0


def _paddleocr_kwargs(lang: str) -> dict[str, Any]:
    return {
        "lang": paddle_lang(lang),
        "ocr_version": PADDLEOCR_VERSION,
        "use_doc_orientation_classify": False,
        "use_doc_unwarping": False,
        "use_textline_orientation": False,
    }


def _prepare_source_override() -> str:
    source_root = os.environ.get("BIOMEDPILOT_PADDLEOCR_SOURCE_ROOT", "").strip()
    if not source_root:
        return ""
    root = Path(source_root).expanduser()
    if not (root / "paddleocr" / "__init__.py").exists():
        raise PaddleOcrEngineError("paddleocr_source_root_invalid")
    root_text = str(root.resolve())
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    return root_text


def _render_pdf_page(page: Any, image_path: Path, fitz: Any) -> None:
    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    if pixmap.width > 2000 or pixmap.height > 2000:
        pixmap = page.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)
    pixmap.save(str(image_path))


def _sort_blocks_reading_order(blocks: Iterable[EngineBlock]) -> list[EngineBlock]:
    ordered = sorted(blocks, key=lambda block: (block.bbox[1], block.bbox[0], block.order))
    for index in range(1, len(ordered)):
        current = ordered[index]
        previous = ordered[index - 1]
        if abs(current.bbox[1] - previous.bbox[1]) < 10 and current.bbox[0] < previous.bbox[0]:
            ordered[index - 1], ordered[index] = current, previous
    return [EngineBlock(text=block.text, confidence=block.confidence, bbox=block.bbox, order=index) for index, block in enumerate(ordered)]
