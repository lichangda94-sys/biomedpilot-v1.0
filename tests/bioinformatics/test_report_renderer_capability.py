from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from app.bioinformatics.reports import renderer_capability
from app.bioinformatics.reports.renderer_capability import build_report_renderer_capability_snapshot, detect_renderer_dependency


def test_renderer_capability_snapshot_is_detect_first_without_install_action(monkeypatch) -> None:
    monkeypatch.setattr(renderer_capability.shutil, "which", lambda _command, path=None: None)

    snapshot = build_report_renderer_capability_snapshot(environment="source")

    assert snapshot["status"] == "passed"
    assert snapshot["detection_mode"] == "detect_first_no_install_no_download"
    assert snapshot["environment"] == "source"
    assert snapshot["checks"]["detect_first_no_install_action"] is True
    assert snapshot["checks"]["no_renderer_invoked"] is True
    assert snapshot["checks"]["no_report_export_enabled"] is True
    assert snapshot["capabilities"]["pandoc"]["available"] is False
    assert snapshot["capabilities"]["pandoc"]["missing_reason"] == "pandoc_not_found_on_renderer_search_paths"
    assert "renderer_dependency_missing:pandoc" in snapshot["blockers"]
    assert "renderer_dependency_missing:xelatex_or_wkhtmltopdf" in snapshot["blockers"]
    assert snapshot["runtime_packaging_policy"]["policy_id"] == "b24_3_system_path_no_bundled_renderers"
    assert snapshot["packaging_impact"]["pandoc"] == "external_binary_required_for_docx_and_pdf_activation_not_bundled"


def test_renderer_dependency_records_version_and_packaging_impact(monkeypatch) -> None:
    monkeypatch.setattr(renderer_capability.shutil, "which", lambda command, path=None: f"/usr/local/bin/{command}")
    monkeypatch.setattr(renderer_capability.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout="pandoc 3.2\n", stderr="", returncode=0))

    dependency = detect_renderer_dependency("pandoc")

    assert dependency["available"] is True
    assert dependency["path"] == "/usr/local/bin/pandoc"
    assert dependency["version"] == "pandoc 3.2"
    assert dependency["capability_key"] == "renderer.pandoc.available"
    assert dependency["packaging_impact"] == "external_binary_required_for_docx_and_pdf_activation_not_bundled"
    assert dependency["detection_mode"] == "detect_first_no_install_no_download"


def test_renderer_capability_detection_can_use_injected_packaged_search_path() -> None:
    snapshot = build_report_renderer_capability_snapshot(
        commands=("pandoc", "xelatex"),
        command_finder=lambda command: f"/opt/homebrew/bin/{command}" if command == "pandoc" else None,
        runner=lambda command, **_kwargs: SimpleNamespace(stdout=f"{Path(command[0]).name} 3.2\n", stderr="", returncode=0),
    )

    assert snapshot["capabilities"]["pandoc"]["available"] is True
    assert snapshot["capabilities"]["pandoc"]["path"] == "/opt/homebrew/bin/pandoc"
    assert snapshot["capabilities"]["xelatex"]["available"] is False
    assert snapshot["runtime_packaging_policy"]["docx"]["runtime_provider"] == "user_system_pandoc_on_search_path"


def test_renderer_capability_snapshot_can_be_written_to_json(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(renderer_capability.shutil, "which", lambda _command, path=None: None)
    output = tmp_path / "renderer_snapshot.json"

    snapshot = build_report_renderer_capability_snapshot(environment="open_w", output_path=output)

    assert output.is_file()
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["schema_version"] == snapshot["schema_version"]
    assert written["environment"] == "open_w"
    assert written["capabilities"]["quarto"]["packaging_impact"] == "future_renderer_detect_only_not_enabled"
