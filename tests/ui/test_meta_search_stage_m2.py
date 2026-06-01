from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QPushButton

    from app.meta_analysis.project_workspace import create_meta_analysis_project
    from app.meta_analysis.search.search_strategy_builder_service import SearchStrategyBuilderService
    from app.meta_analysis.services.pico_workspace_service import PICOWorkspaceService
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget
except Exception as exc:  # pragma: no cover
    QApplication = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def _confirmed_meta_project(tmp_path: Path) -> Path:
    summary = create_meta_analysis_project("Stage M2", tmp_path)
    service = PICOWorkspaceService()
    service.generate_draft(summary.project_root, "肥胖暴露与甲状腺癌风险是否相关？", pico_mode="peco")
    service.edit_draft(
        summary.project_root,
        actor="reviewer",
        updates={
            "population": "甲状腺癌人群",
            "exposure": "肥胖",
            "comparator": "非肥胖",
            "outcome": "发病风险",
            "study_design": "observational study",
        },
    )
    service.confirm_protocol(
        summary.project_root,
        actor="reviewer",
        confirmed_meta_type="exposure_disease_risk_meta",
        overrides={
            "confirmed_pico_mode": "peco",
            "confirmed_population": "甲状腺癌人群",
            "confirmed_intervention_or_exposure": "肥胖",
            "confirmed_comparator": "非肥胖",
            "confirmed_outcomes": ("发病风险",),
            "confirmed_study_design": "observational study",
        },
    )
    return summary.project_root


def test_search_strategy_service_remains_available_as_old_capability_source(tmp_path: Path) -> None:
    project_dir = _confirmed_meta_project(tmp_path)

    SearchStrategyBuilderService().generate_from_confirmed_protocol(project_dir, actor="reviewer")

    draft_path = project_dir / "protocol" / "search_strategy_v2" / "search_strategy_drafts.json"
    assert draft_path.exists()
    payload = json.loads(draft_path.read_text(encoding="utf-8"))
    assert payload["strategies"]
    assert not (project_dir / "protocol" / "search_execution_report.json").exists()


def test_search_strategy_ui_uses_uishell_gate_instead_of_old_page(qt_app, tmp_path: Path) -> None:
    project_dir = _confirmed_meta_project(tmp_path)
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(project_dir)
    widget.show_target_ia_page("search_strategy")

    assert widget.page_keys() == ("target_ia",)
    assert widget.current_target_page_key() == "search_strategy"
    save = widget.findChild(QPushButton, "metaSaveSearchDraftButton")
    assert save is not None
    assert save.property("buttonBehavior") == "calls_search_strategy_builder_or_writes_disabled_reason"
    save.click()
    qt_app.processEvents()

    gate = project_dir / "ui_runtime" / "meta_search_strategy_gate.json"
    assert gate.exists()
    assert json.loads(gate.read_text(encoding="utf-8"))["service"] == "SearchStrategyBuilderService.generate_from_confirmed_protocol"
