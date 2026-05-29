from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QPushButton

    from app.meta_analysis.pages.analysis_page import AnalysisPage, meta_statistics_engine_state_from_project
    from app.meta_analysis.services.manual_extraction_effect_row_service import ManualExtractionEffectRowService
    from app.meta_analysis.services.pico_workspace_service import PICOWorkspaceService
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    QPushButton = None  # type: ignore[assignment]
    AnalysisPage = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def test_meta_analysis_l3_current_ui_drives_one_v2_contract_artifact_loop(qt_app, tmp_path: Path) -> None:
    """Prove the current Meta UI can drive one v2 statistics result into canonical artifacts."""
    _seed_current_meta_inputs(tmp_path)
    widget = AnalysisPage(project_id="meta-l3-ui")
    widget._project_dir_input.setText(str(tmp_path))

    draft_button = _button(widget, "生成分析计划草稿")
    draft_button.click()
    assert (tmp_path / "analysis" / "analysis_plan_draft_v1.json").is_file()
    assert "Draft ID" in widget._analysis_plan_label.text()

    confirm_button = _button(widget, "确认分析计划")
    confirm_button.click()
    confirmed_plan = _read_json(tmp_path / "analysis" / "analysis_plan_confirmed_v1.json")
    assert confirmed_plan["locked_for_analysis_run"] is True
    assert confirmed_plan["medical_interpretation_status"] == "not_generated"
    assert "Confirmed plan ID" in widget._analysis_plan_label.text()

    run_button = _button(widget, "运行统计分析")
    run_button.click()
    state_after_run = meta_statistics_engine_state_from_project(tmp_path)
    run_id = state_after_run.latest_run_id
    assert run_id
    standardized_result = _read_json(tmp_path / "analysis" / "results" / f"{run_id}_result.json")
    run_manifest = _read_json(tmp_path / "analysis" / "runs" / f"{run_id}.json")
    assert standardized_result["analysis_run_id"] == run_id
    assert run_manifest["result_status"] == "testing_result_generated"
    assert standardized_result["testing_level_notice"] == "Developer Preview / testing-level statistics only; not production-grade statistical software."
    assert standardized_result["production_grade"] is False
    assert standardized_result["medical_conclusion_status"] == "not_generated"
    assert "testing-level" in widget._statistics_engine_label.text()

    artifact_button = _button(widget, "生成 canonical result artifacts")
    assert hasattr(widget, "generate_meta_result_contract_artifacts")
    artifact_button.click()
    QApplication.processEvents()

    state = meta_statistics_engine_state_from_project(tmp_path)
    contract_path = Path(state.canonical_contract_path)
    assert state.latest_run_id == run_id
    assert contract_path.is_file()
    assert state.canonical_artifact_count == 3
    assert state.canonical_statistics_result_hash
    assert "testing-level / developer-preview" in widget._statistics_engine_label.text()

    contract = _read_json(contract_path)
    artifacts = contract["artifacts"]
    artifact_types = {item["artifact_type"] for item in artifacts}
    assert artifact_types == {"result_table", "forest_plot", "report_export"}
    assert contract["analysis_run_id"] == run_id
    assert contract["source_statistics_result_hash"] == state.canonical_statistics_result_hash
    assert contract["testing_level"] is True
    assert contract["production_grade"] is False
    assert contract["medical_conclusion_status"] == "not_generated"

    for artifact in artifacts:
        assert artifact["source_analysis_run_id"] == run_id
        assert artifact["source_statistics_result_hash"] == state.canonical_statistics_result_hash
        assert artifact["testing_level"] is True
        assert artifact["production_grade"] is False
        assert artifact["medical_conclusion_status"] == "not_generated"
        assert (tmp_path / artifact["path"]).is_file()

    table = next(item for item in artifacts if item["artifact_type"] == "result_table")
    plot = next(item for item in artifacts if item["artifact_type"] == "forest_plot")
    report = next(item for item in artifacts if item["artifact_type"] == "report_export")
    assert run_id in (tmp_path / table["path"]).read_text(encoding="utf-8")
    assert (tmp_path / plot["path"]).read_bytes().startswith(b"\x89PNG")
    report_text = (tmp_path / report["path"]).read_text(encoding="utf-8")
    assert run_id in report_text
    assert "Developer Preview / testing-level output." in report_text
    assert "not production-grade" in report_text
    assert "No clinical diagnosis, prognosis, treatment recommendation" in report_text
    assert not (tmp_path / "analysis" / "analysis_results.json").exists()


def _seed_current_meta_inputs(project_dir: Path) -> None:
    pico = PICOWorkspaceService()
    pico.generate_draft(project_dir, "成人肺炎患者使用糖皮质激素能否降低死亡率", pico_mode="pico")
    pico.confirm_protocol(project_dir, actor="reviewer", confirmed_meta_type="treatment_comparative_meta")

    manual = ManualExtractionEffectRowService()
    rows = (
        (24, 80, 15, 80),
        (18, 76, 20, 75),
        (11, 60, 21, 62),
    )
    for index, (e1, n1, e0, n0) in enumerate(rows, start=1):
        unit = manual.create_study_unit(
            project_dir,
            record_id=f"rec-{index}",
            study_unit_label=f"Study {index}",
            study_design="trial",
        ).payload
        manual.create_effect_row(
            project_dir,
            study_unit_id=str(unit["study_unit_id"]),
            schema_meta_type="binary_outcome_meta",
            outcome_name="Mortality",
            timepoint="28 days",
            subgroup_label="severe" if index < 3 else "non-severe",
            data_fields={
                "group_1_n": n1,
                "group_1_events": e1,
                "group_2_n": n0,
                "group_2_events": e0,
            },
            analysis_role="primary_effect_candidate",
            analysis_eligibility="candidate",
        )


def _button(widget, text: str) -> QPushButton:
    for button in widget.findChildren(QPushButton):
        if button.text() == text:
            return button
    raise AssertionError(f"button not found: {text}")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))
