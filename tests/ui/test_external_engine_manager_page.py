from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPlainTextEdit, QPushButton

    from app.shared.local_engines import (
        ENGINE_STATUS_AVAILABLE,
        OllamaInstalledModel,
        OllamaLLMPreflightResult,
        OllamaLLMRuntimeManifest,
        OllamaSmokeResult,
        default_ollama_llm_status,
        ollama_model_role_registry_payload,
        write_ollama_llm_runtime_manifest,
    )
    from app.shared.local_engines.external_engine_manager_page import ExternalEngineManagerPage, _ollama_status_from_manifest
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    ExternalEngineManagerPage = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def test_external_engine_page_can_be_created_without_manifest(qt_app, tmp_path: Path) -> None:
    config_path = tmp_path / "ai_gateway_config.json"
    widget = ExternalEngineManagerPage(
        manifest_path=tmp_path / "missing_manifest.json",
        ai_gateway_config_path=config_path,
    )

    labels = _label_text(widget)
    details = widget.findChild(QPlainTextEdit, "ollamaLLMDetailText").toPlainText()

    assert "外部引擎" in labels
    assert "local_llm_ollama" in _card_state_text(widget)
    assert "尚未检查" in details
    assert "AI Gateway 当前 provider：disabled" in labels
    assert "本地模型默认关闭" in labels
    assert "模型文件较大，缺失模型不会自动下载" in labels
    assert not config_path.exists()


def test_ollama_manifest_roles_and_gateway_disabled_are_displayed(qt_app, tmp_path: Path) -> None:
    manifest_path = tmp_path / "ollama_llm_runtime_manifest.json"
    write_ollama_llm_runtime_manifest(_manifest(), manifest_path)
    widget = ExternalEngineManagerPage(
        manifest_path=manifest_path,
        ai_gateway_config_path=tmp_path / "missing_ai_gateway_config.json",
    )

    details = widget.findChild(QPlainTextEdit, "ollamaLLMDetailText").toPlainText()
    labels = _label_text(widget)

    assert "general_3b -> qwen2.5:3b" in details
    assert "translator -> translategemma:latest" in details
    assert "medical -> medgemma:4b" in details
    assert "general_3b / qwen2.5:3b: passed" in details
    assert "privacy mode：local_only" in details
    assert "AI Gateway 当前 provider：disabled" in labels


def test_ollama_preflight_status_mapping() -> None:
    assert _ollama_status_from_manifest(_manifest()) == "available"
    assert _ollama_status_from_manifest(_manifest(service_available=False)) == "missing"
    assert _ollama_status_from_manifest(_manifest(missing_models=("medgemma:4b",))) == "partial"
    assert _ollama_status_from_manifest(_manifest(smoke_status="failed")) == "partial"
    assert _ollama_status_from_manifest(_manifest(command_path="")) == "missing"


def test_run_check_updates_manifest_display_from_preflight(qt_app, tmp_path: Path) -> None:
    manifest = _manifest(detected_at="2026-05-18T08:00:00+00:00")

    def _fake_preflight(**_kwargs):
        return OllamaLLMPreflightResult(
            status=default_ollama_llm_status(ENGINE_STATUS_AVAILABLE),
            manifest=manifest,
            manifest_path=str(tmp_path / "ollama_llm_runtime_manifest.json"),
        )

    widget = ExternalEngineManagerPage(
        manifest_path=tmp_path / "ollama_llm_runtime_manifest.json",
        ai_gateway_config_path=tmp_path / "missing_ai_gateway_config.json",
        preflight_runner=_fake_preflight,
    )
    button = widget.findChild(QPushButton, "runOllamaPreflightButton")

    button.click()

    assert "Ollama command path：/opt/homebrew/bin/ollama" in widget.findChild(QPlainTextEdit, "ollamaLLMDetailText").toPlainText()
    assert "local_llm_ollama" in _card_state_text(widget)
    assert "available" in _card_state_text(widget)


def test_manifest_summary_and_config_draft_do_not_create_gateway_config(qt_app, tmp_path: Path) -> None:
    manifest_path = tmp_path / "ollama_llm_runtime_manifest.json"
    config_path = tmp_path / "ai_gateway_config.json"
    write_ollama_llm_runtime_manifest(_manifest(), manifest_path)
    widget = ExternalEngineManagerPage(manifest_path=manifest_path, ai_gateway_config_path=config_path)

    widget.findChild(QPushButton, "showOllamaManifestSummaryButton").click()
    summary = widget.findChild(QPlainTextEdit, "ollamaManifestSummaryText").toPlainText()
    assert '"engine_family": "local_llm_ollama"' in summary
    assert '"privacy_mode": "local_only"' in summary

    widget.findChild(QPushButton, "generateLocalModelConfigDraftButton").click()
    draft = widget.findChild(QPlainTextEdit, "ollamaManifestSummaryText").toPlainText()

    assert '"default_provider": "ollama"' in draft
    assert '"role_model_mapping"' in draft
    assert '"translator": "translategemma:latest"' in draft
    assert not config_path.exists()


def test_settings_page_contains_external_engine_manager(qt_app) -> None:
    from app.shell.main_window import MainWindow

    window = MainWindow.__new__(MainWindow)
    settings_page = window._build_settings_page()

    assert settings_page.findChild(ExternalEngineManagerPage, "externalEngineManagerPage") is not None
    assert "外部引擎" in _label_text(settings_page)


def _manifest(
    *,
    command_path: str = "/opt/homebrew/bin/ollama",
    service_available: bool = True,
    missing_models: tuple[str, ...] = (),
    smoke_status: str = "passed",
    detected_at: str = "2026-05-18T00:00:00+00:00",
) -> OllamaLLMRuntimeManifest:
    installed = (
        OllamaInstalledModel("qwen2.5:3b", size=1_000, modified_at="2026-05-18T00:00:00Z"),
        OllamaInstalledModel("translategemma:latest", size=2_000, modified_at="2026-05-18T00:00:01Z"),
        OllamaInstalledModel("medgemma:4b", size=3_000, modified_at="2026-05-18T00:00:02Z"),
    )
    return OllamaLLMRuntimeManifest(
        detected_at=detected_at,
        ollama_command_path=command_path,
        ollama_version="ollama version is 0.21.0",
        http_endpoint="http://localhost:11434",
        service_available=service_available,
        model_roles=ollama_model_role_registry_payload(),
        installed_models=installed,
        missing_models=missing_models,
        smoke_results=(
            OllamaSmokeResult("general_3b", "qwen2.5:3b", smoke_status),
            OllamaSmokeResult("translator", "translategemma:latest", smoke_status),
            OllamaSmokeResult("medical", "medgemma:4b", smoke_status),
        ),
        privacy_mode="local_only",
    )


def _label_text(widget) -> str:
    return "\n".join(label.text() for label in widget.findChildren(QLabel))


def _card_state_text(widget: ExternalEngineManagerPage) -> str:
    return "\n".join(f"{state.engine_family}:{state.status}:{state.summary}" for state in widget.card_states())
