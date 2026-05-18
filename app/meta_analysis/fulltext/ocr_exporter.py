from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.fulltext.ocr_models import OcrDocumentResult


@dataclass(frozen=True)
class OcrExportResult:
    text_path: str
    json_path: str
    status: str
    page_count: int
    warnings: tuple[str, ...] = ()


def write_ocr_outputs(result: OcrDocumentResult, output_dir: str | Path, *, base_name: str | None = None) -> OcrExportResult:
    output_path = Path(output_dir).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    safe_base = _safe_base_name(base_name or result.source.record_id or Path(result.source.path).stem or "ocr_result")
    text_path = output_path / f"{safe_base}.txt"
    json_path = output_path / f"{safe_base}.ocr.json"
    text_path.write_text(_document_text(result), encoding="utf-8")
    json_path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return OcrExportResult(
        text_path=str(text_path),
        json_path=str(json_path),
        status=result.status,
        page_count=len(result.pages),
        warnings=result.warnings,
    )


def _document_text(result: OcrDocumentResult) -> str:
    parts: list[str] = []
    for page in result.pages:
        label = page.page_label or str(page.page_index + 1)
        parts.append(f"--- page {label} ---")
        parts.append(page.text.strip())
    text = "\n".join(parts).strip()
    if text:
        return text + "\n"
    return ""


def _safe_base_name(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return safe.strip("._-") or "ocr_result"
