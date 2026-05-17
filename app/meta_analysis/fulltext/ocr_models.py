from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


OCR_RESULT_SCHEMA_VERSION = "biomedpilot_ocr_result.v1"
OCR_STATUS_COMPLETED = "completed"
OCR_STATUS_FAILED = "failed"
OCR_STATUS_PENDING_RUNTIME = "pending_runtime"


@dataclass(frozen=True)
class OcrSource:
    path: str
    media_type: str
    attachment_id: str = ""
    record_id: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class OcrEngineInfo:
    engine_id: str = "paddleocr_local"
    engine_version: str = ""
    runtime_manifest_id: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class OcrBlock:
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
class OcrPageResult:
    page_index: int
    page_label: str
    text: str = ""
    width: int = 0
    height: int = 0
    blocks: tuple[OcrBlock, ...] = ()
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
class OcrDocumentResult:
    source: OcrSource
    engine: OcrEngineInfo
    pages: tuple[OcrPageResult, ...] = ()
    status: str = OCR_STATUS_COMPLETED
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    schema_version: str = OCR_RESULT_SCHEMA_VERSION

    @property
    def text(self) -> str:
        return "\n\n".join(page.text for page in self.pages if page.text.strip()).strip()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "created_at": self.created_at,
            "source": self.source.to_dict(),
            "engine": self.engine.to_dict(),
            "pages": [page.to_dict() for page in self.pages],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "safety_note": "OCR output is auxiliary fulltext acquisition only and does not create final Meta extraction, screening, statistics, or medical conclusions.",
        }


def ocr_document_from_dict(payload: Any) -> OcrDocumentResult:
    if not isinstance(payload, dict):
        raise ValueError("ocr_result_must_be_object")
    if payload.get("schema_version") != OCR_RESULT_SCHEMA_VERSION:
        raise ValueError("unsupported_ocr_result_schema")
    source_payload = payload.get("source") if isinstance(payload.get("source"), dict) else {}
    engine_payload = payload.get("engine") if isinstance(payload.get("engine"), dict) else {}
    pages = tuple(_page_from_payload(item) for item in payload.get("pages", []) if isinstance(item, dict))
    return OcrDocumentResult(
        source=OcrSource(
            path=str(source_payload.get("path") or ""),
            media_type=str(source_payload.get("media_type") or ""),
            attachment_id=str(source_payload.get("attachment_id") or ""),
            record_id=str(source_payload.get("record_id") or ""),
        ),
        engine=OcrEngineInfo(
            engine_id=str(engine_payload.get("engine_id") or "paddleocr_local"),
            engine_version=str(engine_payload.get("engine_version") or ""),
            runtime_manifest_id=str(engine_payload.get("runtime_manifest_id") or ""),
        ),
        pages=pages,
        status=str(payload.get("status") or OCR_STATUS_FAILED),
        created_at=str(payload.get("created_at") or ""),
        warnings=tuple(str(item) for item in payload.get("warnings", [])),
        errors=tuple(str(item) for item in payload.get("errors", [])),
    )


def _page_from_payload(payload: dict[str, Any]) -> OcrPageResult:
    blocks = tuple(_block_from_payload(item) for item in payload.get("blocks", []) if isinstance(item, dict))
    return OcrPageResult(
        page_index=int(payload.get("page_index") or 0),
        page_label=str(payload.get("page_label") or ""),
        text=str(payload.get("text") or ""),
        width=int(payload.get("width") or 0),
        height=int(payload.get("height") or 0),
        blocks=blocks,
        tables=tuple(dict(item) for item in payload.get("tables", []) if isinstance(item, dict)),
        warnings=tuple(str(item) for item in payload.get("warnings", [])),
    )


def _block_from_payload(payload: dict[str, Any]) -> OcrBlock:
    bbox_payload = payload.get("bbox") if isinstance(payload.get("bbox"), list) else []
    bbox = tuple(float(item) for item in [*bbox_payload[:4], 0, 0, 0, 0][:4])
    return OcrBlock(
        block_id=str(payload.get("block_id") or ""),
        text=str(payload.get("text") or ""),
        confidence=float(payload.get("confidence") or 0),
        bbox=bbox,
        language=str(payload.get("language") or "auto"),
        kind=str(payload.get("kind") or "text"),
        order=int(payload.get("order") or 0),
    )
