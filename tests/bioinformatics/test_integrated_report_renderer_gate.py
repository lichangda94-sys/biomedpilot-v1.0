from __future__ import annotations

from types import SimpleNamespace

from app.bioinformatics.reports import integrated
from app.bioinformatics.reports import renderer_capability
from app.bioinformatics.reports.integrated import evaluate_full_integrated_report_renderer_gate


def test_markdown_renderer_gate_uses_builtin_renderer_without_external_dependencies() -> None:
    gate = evaluate_full_integrated_report_renderer_gate("markdown")

    assert gate["status"] == "passed"
    assert gate["export_format"] == "markdown"
    assert gate["renderer_id"] == "builtin_markdown"
    assert gate["required_dependencies"] == []
    assert gate["checks"]["detect_first_no_install_action"] is True
    assert gate["blockers"] == []


def test_pdf_renderer_gate_is_detect_first_and_blocked_when_dependencies_are_missing(monkeypatch) -> None:
    monkeypatch.setattr(renderer_capability.shutil, "which", lambda _command, path=None: None)

    gate = evaluate_full_integrated_report_renderer_gate("pdf")

    assert gate["status"] == "blocked"
    assert gate["renderer_id"] == "pandoc_pdf"
    assert "renderer_dependency_missing:pandoc" in gate["blockers"]
    assert "renderer_dependency_missing:xelatex" in gate["blockers"]
    assert "full_integrated_pdf_renderer_not_enabled_in_b23_4" in gate["blockers"]
    assert gate["required_dependencies"] == ["pandoc", "xelatex"]
    assert gate["checks"]["detect_first_no_install_action"] is True
    assert gate["checks"]["external_renderers_bundled"] is False
    assert gate["renderer_capability_snapshot"]["checks"]["no_report_export_enabled"] is True


def test_docx_renderer_gate_remains_disabled_even_when_pandoc_is_detected(monkeypatch) -> None:
    monkeypatch.setattr(renderer_capability.shutil, "which", lambda command, path=None: f"/usr/local/bin/{command}")
    monkeypatch.setattr(renderer_capability.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout="pandoc 3.1\n", stderr="", returncode=0))

    gate = evaluate_full_integrated_report_renderer_gate("docx")

    assert gate["status"] == "blocked"
    assert gate["detected_dependencies"]["pandoc"]["available"] is True
    assert gate["checks"]["dependencies_detected"] is True
    assert gate["checks"]["implementation_enabled"] is False
    assert gate["blockers"] == ["full_integrated_docx_renderer_not_enabled_in_b23_4"]


def test_docx_renderer_gate_can_pass_only_when_activation_is_explicit_and_pandoc_detected(monkeypatch) -> None:
    monkeypatch.setattr(renderer_capability.shutil, "which", lambda command, path=None: f"/usr/local/bin/{command}")
    monkeypatch.setattr(renderer_capability.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout="pandoc 3.1\n", stderr="", returncode=0))

    gate = evaluate_full_integrated_report_renderer_gate("docx", allow_docx_activation=True)

    assert gate["status"] == "passed"
    assert gate["detected_dependencies"]["pandoc"]["available"] is True
    assert gate["checks"]["implementation_enabled"] is True
    assert gate["checks"]["docx_activation_requested"] is True
    assert gate["blockers"] == []


def test_unsupported_renderer_format_is_blocked_without_traceback() -> None:
    gate = evaluate_full_integrated_report_renderer_gate("xlsx")

    assert gate["status"] == "blocked"
    assert "full_integrated_export_format_unsupported:xlsx" in gate["blockers"]
    assert gate["disabled_reason"] == "full_integrated_export_format_unsupported:xlsx"
