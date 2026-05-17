from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.fulltext import (
    OCR_RESULT_SCHEMA_VERSION,
    OCR_RUNTIME_MANIFEST_SCHEMA_VERSION,
    OCR_STATUS_COMPLETED,
    OCR_STATUS_PENDING_RUNTIME,
    ImageOcrWorker,
    MetaOcrRuntimeService,
    OcrBlock,
    OcrDocumentResult,
    OcrEngineInfo,
    OcrPageResult,
    OcrSource,
    PdfOcrWorker,
    ocr_document_from_dict,
)


class _FakeOcrRunner:
    def run_pdf_ocr(self, pdf_path: Path, *, record_id: str, attachment_id: str = "", lang: str = "auto") -> OcrDocumentResult:
        return _document(pdf_path, record_id=record_id, attachment_id=attachment_id, media_type="application/pdf")

    def run_image_ocr(self, image_path: Path, *, record_id: str, attachment_id: str = "", lang: str = "auto") -> OcrDocumentResult:
        return _document(image_path, record_id=record_id, attachment_id=attachment_id, media_type="image/png")


def test_pdf_ocr_worker_writes_txt_and_json_from_injected_runner(tmp_path: Path) -> None:
    pdf = tmp_path / "article.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")

    result = PdfOcrWorker(runner=_FakeOcrRunner()).process_pdf(tmp_path, record_id="rec-1", pdf_path=pdf, attachment_id="att-1")
    payload = json.loads(Path(result.json_path).read_text(encoding="utf-8"))
    text = Path(result.text_path).read_text(encoding="utf-8")

    assert result.success
    assert result.status == OCR_STATUS_COMPLETED
    assert payload["schema_version"] == OCR_RESULT_SCHEMA_VERSION
    assert payload["source"]["record_id"] == "rec-1"
    assert payload["pages"][0]["tables"] == []
    assert "中文 English 繁體" in text
    assert "final Meta extraction" in payload["safety_note"]


def test_image_ocr_worker_writes_same_output_contract(tmp_path: Path) -> None:
    image = tmp_path / "figure.png"
    image.write_bytes(b"not-a-real-image-yet")

    result = ImageOcrWorker(runner=_FakeOcrRunner()).process_image(tmp_path, record_id="fig-1", image_path=image)
    payload = json.loads(Path(result.json_path).read_text(encoding="utf-8"))
    restored = ocr_document_from_dict(payload)

    assert result.success
    assert restored.source.media_type == "image/png"
    assert restored.pages[0].blocks[0].text == "中文 English 繁體"


def test_missing_runtime_runner_exports_pending_runtime_json_without_fake_text(tmp_path: Path) -> None:
    pdf = tmp_path / "article.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")

    result = PdfOcrWorker().process_pdf(tmp_path, record_id="rec-2", pdf_path=pdf)
    payload = json.loads(Path(result.json_path).read_text(encoding="utf-8"))

    assert not result.success
    assert result.status == OCR_STATUS_PENDING_RUNTIME
    assert payload["pages"] == []
    assert payload["errors"] == ["ocr_runtime_runner_not_configured"]
    assert Path(result.text_path).read_text(encoding="utf-8") == ""


def test_missing_image_exports_failure_json(tmp_path: Path) -> None:
    result = ImageOcrWorker().process_image(tmp_path, record_id="fig-missing", image_path=tmp_path / "missing.png")
    payload = json.loads(Path(result.json_path).read_text(encoding="utf-8"))

    assert not result.success
    assert payload["source"]["media_type"] == "image/png"
    assert payload["errors"] == ["image_file_missing"]


def test_meta_ocr_runtime_service_resolves_standard_manifest(tmp_path: Path) -> None:
    python = tmp_path / "runtime" / "bin" / "python"
    python.parent.mkdir(parents=True, exist_ok=True)
    python.write_text("#!/bin/sh\n", encoding="utf-8")
    manifest = tmp_path / "runtime" / "runtime_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": OCR_RUNTIME_MANIFEST_SCHEMA_VERSION,
                "engine_id": "paddleocr_local",
                "packages": {"paddleocr": "3.5.0"},
                "python": {"executable": str(python), "version": "3.12.13"},
                "runtime_id": "runtime-test",
                "smoke_test": {"status": "ok", "result_path": "smoke/result.json"},
            }
        ),
        encoding="utf-8",
    )

    service = MetaOcrRuntimeService(runtime_root=tmp_path / "runtime")
    status = service.status()
    runner = service.runner()

    assert status.available
    assert status.status == "available"
    assert status.python_executable == str(python)
    assert status.engine_version == "3.5.0"
    assert status.runtime_manifest_id == "runtime-test"
    assert runner is not None


def _document(path: Path, *, record_id: str, attachment_id: str, media_type: str) -> OcrDocumentResult:
    return OcrDocumentResult(
        source=OcrSource(path=str(path), media_type=media_type, attachment_id=attachment_id, record_id=record_id),
        engine=OcrEngineInfo(engine_version="3.0.0", runtime_manifest_id="runtime-test"),
        pages=(
            OcrPageResult(
                page_index=0,
                page_label="1",
                text="中文 English 繁體",
                width=100,
                height=200,
                blocks=(OcrBlock(block_id="b1", text="中文 English 繁體", confidence=0.99, bbox=(1, 2, 3, 4), order=1),),
            ),
        ),
    )
