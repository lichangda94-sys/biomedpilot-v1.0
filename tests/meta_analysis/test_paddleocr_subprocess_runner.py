from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from app.meta_analysis.fulltext import (
    OCR_RESULT_SCHEMA_VERSION,
    OCR_STATUS_FAILED,
    OcrBlock,
    OcrDocumentResult,
    OcrEngineInfo,
    OcrPageResult,
    OcrSource,
    PaddleOcrRuntimeConfig,
    PaddleOcrSubprocessError,
    PaddleOcrSubprocessRunner,
    PdfOcrWorker,
    build_paddleocr_worker_command,
)


def test_subprocess_runner_builds_command_and_parses_stdout_json(tmp_path: Path) -> None:
    python = _fake_python(tmp_path)
    pdf = tmp_path / "文献 full text.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    captured: dict[str, object] = {}

    def fake_runner(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps(_payload(str(pdf)), ensure_ascii=False), stderr="")

    runner = PaddleOcrSubprocessRunner(PaddleOcrRuntimeConfig(python_executable=str(python), timeout_seconds=12), runner=fake_runner)
    result = runner.run_pdf_ocr(pdf, record_id="rec-1", attachment_id="att-1", lang="ch")

    assert result.source.path == str(pdf)
    assert result.pages[0].blocks[0].text == "中文 English 繁體"
    assert captured["command"] == [
        str(python),
        "-m",
        "biomedpilot_ocr_worker",
        "--mode",
        "pdf",
        "--input",
        str(pdf),
        "--record-id",
        "rec-1",
        "--lang",
        "ch",
        "--attachment-id",
        "att-1",
    ]
    assert captured["kwargs"]["capture_output"] is True
    assert captured["kwargs"]["text"] is True
    assert captured["kwargs"]["timeout"] == 12


def test_subprocess_runner_accepts_json_after_log_lines(tmp_path: Path) -> None:
    python = _fake_python(tmp_path)
    image = tmp_path / "figure.png"
    image.write_bytes(b"image")

    def fake_runner(command, **kwargs):
        stdout = "loading model\n" + json.dumps(_payload(str(image), media_type="image/png"), ensure_ascii=False) + "\n"
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    result = PaddleOcrSubprocessRunner(PaddleOcrRuntimeConfig(python_executable=str(python)), runner=fake_runner).run_image_ocr(
        image,
        record_id="fig-1",
    )

    assert result.source.media_type == "image/png"


def test_subprocess_runner_adds_configured_pythonpath(tmp_path: Path) -> None:
    python = _fake_python(tmp_path)
    image = tmp_path / "figure.png"
    image.write_bytes(b"image")
    worker_source = tmp_path / "worker-source"
    captured: dict[str, object] = {}

    def fake_runner(command, **kwargs):
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps(_payload(str(image), media_type="image/png"), ensure_ascii=False), stderr="")

    PaddleOcrSubprocessRunner(
        PaddleOcrRuntimeConfig(python_executable=str(python), pythonpath_entries=(str(worker_source),)),
        runner=fake_runner,
    ).run_image_ocr(image, record_id="fig-1")

    env = captured["kwargs"]["env"]
    assert env["PYTHONPATH"].split(os.pathsep)[0] == str(worker_source)


def test_subprocess_runner_failure_modes_are_structured(tmp_path: Path) -> None:
    missing_python = tmp_path / "missing-python"
    with pytest.raises(PaddleOcrSubprocessError, match="python_missing"):
        PaddleOcrSubprocessRunner(PaddleOcrRuntimeConfig(python_executable=str(missing_python))).run_pdf_ocr(
            tmp_path / "x.pdf",
            record_id="rec-1",
        )

    python = _fake_python(tmp_path)

    def nonzero(command, **kwargs):
        return subprocess.CompletedProcess(command, 2, stdout="", stderr="model missing")

    with pytest.raises(PaddleOcrSubprocessError, match="model missing"):
        PaddleOcrSubprocessRunner(PaddleOcrRuntimeConfig(python_executable=str(python)), runner=nonzero).run_pdf_ocr(
            tmp_path / "x.pdf",
            record_id="rec-1",
        )

    def invalid_json(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="not json", stderr="")

    with pytest.raises(PaddleOcrSubprocessError, match="invalid_json"):
        PaddleOcrSubprocessRunner(PaddleOcrRuntimeConfig(python_executable=str(python)), runner=invalid_json).run_pdf_ocr(
            tmp_path / "x.pdf",
            record_id="rec-1",
        )

    def timeout(command, **kwargs):
        raise subprocess.TimeoutExpired(command, 1)

    with pytest.raises(PaddleOcrSubprocessError, match="timeout"):
        PaddleOcrSubprocessRunner(PaddleOcrRuntimeConfig(python_executable=str(python), timeout_seconds=1), runner=timeout).run_pdf_ocr(
            tmp_path / "x.pdf",
            record_id="rec-1",
        )


def test_pdf_worker_records_subprocess_failure_without_fake_text(tmp_path: Path) -> None:
    python = _fake_python(tmp_path)
    pdf = tmp_path / "article.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")

    def nonzero(command, **kwargs):
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="runtime failed")

    runner = PaddleOcrSubprocessRunner(PaddleOcrRuntimeConfig(python_executable=str(python)), runner=nonzero)
    result = PdfOcrWorker(runner=runner).process_pdf(tmp_path, record_id="rec-2", pdf_path=pdf)
    payload = json.loads(Path(result.json_path).read_text(encoding="utf-8"))

    assert not result.success
    assert payload["status"] == OCR_STATUS_FAILED
    assert payload["pages"] == []
    assert payload["errors"] == ["ocr_runtime_failed:PaddleOcrSubprocessError"]


def test_command_builder_rejects_unknown_mode() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        build_paddleocr_worker_command("python", input_path="x", mode="audio", record_id="rec-1")


def _fake_python(tmp_path: Path) -> Path:
    python = tmp_path / "runtime" / "bin" / "python"
    python.parent.mkdir(parents=True, exist_ok=True)
    python.write_text("#!/bin/sh\n", encoding="utf-8")
    return python


def _payload(path: str, *, media_type: str = "application/pdf") -> dict[str, object]:
    return OcrDocumentResult(
        source=OcrSource(path=path, media_type=media_type, attachment_id="att-1", record_id="rec-1"),
        engine=OcrEngineInfo(engine_version="3.0.0", runtime_manifest_id="runtime-test"),
        pages=(
            OcrPageResult(
                page_index=0,
                page_label="1",
                text="中文 English 繁體",
                blocks=(OcrBlock(block_id="b1", text="中文 English 繁體", confidence=0.98),),
            ),
        ),
    ).to_dict() | {"schema_version": OCR_RESULT_SCHEMA_VERSION}
