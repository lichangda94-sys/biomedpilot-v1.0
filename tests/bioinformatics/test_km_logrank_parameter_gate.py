from __future__ import annotations

from pathlib import Path

from app.bioinformatics.clinical_analysis import build_survival_package
from app.bioinformatics.survival_clinical import build_km_logrank_parameter_manifest


def test_km_parameter_gate_passes_for_two_group_b12_inputs(tmp_path: Path) -> None:
    clinical = _clinical_fixture(tmp_path)
    package = build_survival_package({"input_package_id": "pkg", "clinical_asset": {"path": str(clinical)}, "expression_asset": {"path": "expr.tsv"}})

    manifest = build_km_logrank_parameter_manifest(package, outcome_gate=_outcome_gate(), clinical_variable_audit={}, grouping_variable="arm", group_a="A", group_b="B", dependency_snapshot=_dependency_passed())

    assert manifest["status"] == "passed"
    assert manifest["time_field"] == "OS_time"
    assert manifest["event_field"] == "OS_event"
    assert manifest["group_a_case_count"] == 3
    assert manifest["group_b_case_count"] == 3
    assert manifest["group_a_event_count"] == 2
    assert manifest["group_b_event_count"] == 2
    assert manifest["provenance"]["raw_recognition_report_used"] is False


def test_km_parameter_gate_blocks_missing_dependency_and_bad_groups(tmp_path: Path) -> None:
    clinical = _clinical_fixture(tmp_path)
    package = build_survival_package({"input_package_id": "pkg", "clinical_asset": {"path": str(clinical)}})

    manifest = build_km_logrank_parameter_manifest(package, outcome_gate=_outcome_gate(), grouping_variable="arm", group_a="A", group_b="A", dependency_snapshot={"status": "preflight_only"})

    assert manifest["status"] == "blocked"
    assert "same_group_labels" in manifest["blockers"]
    assert "dependency_snapshot_not_passed" in manifest["blockers"]


def test_km_parameter_gate_blocks_low_event_count(tmp_path: Path) -> None:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text("sample_id\tOS_time\tOS_event\tarm\nS1\t1\t1\tA\nS2\t2\t0\tA\nS3\t3\t0\tB\nS4\t4\t0\tB\n", encoding="utf-8")
    package = build_survival_package({"input_package_id": "pkg", "clinical_asset": {"path": str(clinical)}})

    manifest = build_km_logrank_parameter_manifest(package, outcome_gate=_outcome_gate(), grouping_variable="arm", group_a="A", group_b="B", dependency_snapshot=_dependency_passed())

    assert "minimum_event_count_not_met" in manifest["blockers"]
    assert "grouping_contains_no_events" in manifest["blockers"]


def _clinical_fixture(tmp_path: Path) -> Path:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text(
        "sample_id\tOS_time\tOS_event\tarm\n"
        "S1\t5\t1\tA\nS2\t8\t0\tA\nS3\t12\t1\tA\n"
        "S4\t6\t1\tB\nS5\t9\t0\tB\nS6\t15\t1\tB\n",
        encoding="utf-8",
    )
    return clinical


def _outcome_gate() -> dict[str, object]:
    return {"status": "passed", "survival_outcome_gate_id": "outcome-1", "blockers": [], "warnings": []}


def _dependency_passed() -> dict[str, object]:
    return {"status": "passed", "python_lifelines": {"available": True, "version": "test"}, "blockers": [], "warnings": []}
