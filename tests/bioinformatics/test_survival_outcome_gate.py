from __future__ import annotations

from pathlib import Path

from app.bioinformatics.survival_clinical import build_survival_outcome_gate


def test_os_time_os_event_direct_fields_pass(tmp_path: Path) -> None:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text("case_id\tOS_time\tOS_event\nC1\t10\t1\nC2\t20\t0\nC3\t30\t1\nC4\t40\t0\nC5\t50\t1\nC6\t60\t1\n", encoding="utf-8")
    gate = build_survival_outcome_gate(tmp_path, _input(clinical))

    assert gate["status"] == "passed"
    assert gate["time_field"] == "OS_time"
    assert gate["event_field"] == "OS_event"
    assert gate["event_count"] == 4
    assert gate["report_ready_eligible"] if "report_ready_eligible" in gate else True


def test_derived_days_and_vital_status_records_provenance(tmp_path: Path) -> None:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text("case_id\tdays_to_death\tdays_to_last_follow_up\tvital_status\nC1\t10\t\tDead\nC2\t\t20\tAlive\nC3\t30\t\tDead\nC4\t40\t\tDead\nC5\t50\t\tDead\n", encoding="utf-8")
    gate = build_survival_outcome_gate(tmp_path, _input(clinical))

    assert gate["status"] == "passed"
    assert gate["derived_os_time_policy"]["derived"] is True
    assert gate["derived_os_event_policy"]["derived"] is True
    assert "derived_os_time_requires_user_review" in gate["warnings"]


def test_missing_event_ambiguous_event_and_negative_time_block(tmp_path: Path) -> None:
    missing_event = tmp_path / "missing_event.tsv"
    missing_event.write_text("case_id\tOS_time\nC1\t10\n", encoding="utf-8")
    assert "missing_event_field" in build_survival_outcome_gate(tmp_path, _input(missing_event))["blockers"]

    ambiguous = tmp_path / "ambiguous.tsv"
    ambiguous.write_text("case_id\tOS_time\tOS_event\nC1\t10\tmaybe\nC2\t20\tunknown\n", encoding="utf-8")
    assert "ambiguous_event_coding" in build_survival_outcome_gate(tmp_path, _input(ambiguous))["blockers"]

    negative = tmp_path / "negative.tsv"
    negative.write_text("case_id\tOS_time\tOS_event\nC1\t-1\t1\nC2\t20\t0\n", encoding="utf-8")
    assert "negative_survival_time" in build_survival_outcome_gate(tmp_path, _input(negative))["blockers"]


def test_low_event_count_warns(tmp_path: Path) -> None:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text("case_id\tOS_time\tOS_event\nC1\t10\t1\nC2\t20\t0\nC3\t30\t0\n", encoding="utf-8")
    gate = build_survival_outcome_gate(tmp_path, _input(clinical))

    assert "low_event_count" in gate["warnings"]


def _input(clinical: Path) -> dict[str, object]:
    return {"survival_clinical_input_id": "input-1", "clinical_asset": {"path": str(clinical)}, "warnings": [], "blockers": []}
