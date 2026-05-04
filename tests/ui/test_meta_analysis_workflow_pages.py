from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication

    from app.meta_analysis.workflow_pages import (
        ProtocolPage,
        build_protocol_search_strategy_draft,
        protocol_page_state_from_project,
        render_search_strategy_summary,
        write_protocol_search_strategy_artifacts,
    )
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    ProtocolPage = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def _values() -> dict[str, object]:
    return {
        "project_title": "肥胖与甲状腺癌发病风险 Meta 分析",
        "review_question": "肥胖是否增加甲状腺癌发病风险？",
        "population": "甲状腺癌人群",
        "intervention_or_exposure": "肥胖",
        "comparator": "非肥胖",
        "outcomes": "发病风险",
        "primary_outcome": "发病风险",
        "study_design": "systematic review; meta-analysis",
    }


def test_meta_protocol_search_strategy_summary_displays_database_drafts() -> None:
    draft = build_protocol_search_strategy_draft(_values())
    summary = render_search_strategy_summary(draft)

    assert "PICO/PECO mode: PECO" in summary
    assert "target_context: meta_analysis" in summary
    assert "Concept blocks:" in summary
    assert "PubMed query draft (MeSH + tiab):" in summary
    assert '"Obesity"[Mesh]' in summary
    assert '"obesity"[tiab]' in summary
    assert "WOS query draft (draft-only):" in summary
    assert "TS=" in summary
    assert "Embase query draft (draft-only):" in summary
    assert ":ti,ab" in summary
    assert "CNKI query draft (draft-only):" in summary
    assert "主题=" in summary
    assert "search_execution_status=draft_only" in summary
    assert "local_model_status:" in summary


def test_meta_protocol_search_strategy_artifacts_are_draft_only_without_execution_report(tmp_path: Path) -> None:
    draft = build_protocol_search_strategy_draft(_values())
    paths = write_protocol_search_strategy_artifacts(tmp_path, draft)

    payload = json.loads(Path(paths["search_strategy_draft"]).read_text(encoding="utf-8"))
    audit = json.loads(Path(paths["search_strategy_audit"]).read_text(encoding="utf-8"))

    assert payload["target_context"] == "meta_analysis"
    assert payload["search_execution_status"] == "draft_only"
    assert audit["search_execution_status"] == "draft_only"
    assert not (tmp_path / "protocol" / "search_execution_report.json").exists()


def test_meta_protocol_search_strategy_payload_does_not_show_dataset_sources(tmp_path: Path) -> None:
    draft = build_protocol_search_strategy_draft(_values())
    paths = write_protocol_search_strategy_artifacts(tmp_path, draft)
    rendered = (
        Path(paths["search_strategy_draft"]).read_text(encoding="utf-8")
        + Path(paths["search_strategy_audit"]).read_text(encoding="utf-8")
        + render_search_strategy_summary(draft)
    ).lower()

    assert "geo" not in rendered
    assert "gse" not in rendered
    assert "tcga" not in rendered
    assert "gtex" not in rendered


def test_meta_protocol_page_saves_and_displays_search_strategy_draft(qt_app, tmp_path: Path) -> None:
    widget = ProtocolPage()
    widget.set_protocol_inputs(
        project_dir=tmp_path,
        project_title="肥胖与甲状腺癌发病风险 Meta 分析",
        review_question="肥胖是否增加甲状腺癌发病风险？",
        pico="甲状腺癌人群; 肥胖; 非肥胖; 发病风险; systematic review; meta-analysis",
        method_profile="TREATMENT_EFFECT_META",
    )

    draft = widget.save_protocol_draft()
    summary = widget.search_strategy_summary_text()
    state = protocol_page_state_from_project(tmp_path)

    assert draft.target_context == "meta_analysis"
    assert draft.search_execution_status == "draft_only"
    assert "PubMed query draft (MeSH + tiab):" in summary
    assert "WOS query draft (draft-only):" in summary
    assert "Embase query draft (draft-only):" in summary
    assert "CNKI query draft (draft-only):" in summary
    assert state.output_paths["search_strategy_draft"].endswith("protocol/search_strategy_draft.json")
    assert state.output_paths["search_strategy_audit"].endswith("protocol/search_strategy_audit.json")
    assert "PubMed query draft" in state.search_strategy_summary
    assert state.search_execution_status == "draft_only"
    assert not (tmp_path / "protocol" / "search_execution_report.json").exists()
