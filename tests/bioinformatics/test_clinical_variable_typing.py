from __future__ import annotations

from pathlib import Path

from app.bioinformatics.survival_clinical import audit_clinical_variables


def test_clinical_variable_typing_covers_supported_types(tmp_path: Path) -> None:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text(
        "case_id\tsex\tstage\tage\tdiagnosis_date\tcomment\tOS_time\tunknown_blob\n"
        "C1\tF\tII\t50\t2020-01-01\tfree text one\t10\tA very long free text value one\n"
        "C2\tM\tIII\t60\t2020-02-01\tfree text two\t20\tA very long free text value two\n"
        "C3\tF\tIV\t70\t2020-03-01\tfree text three\t30\tA very long free text value three\n",
        encoding="utf-8",
    )

    audit = audit_clinical_variables(tmp_path, _input(clinical))
    by_name = {item["variable_name"]: item for item in audit["variables"]}

    assert by_name["case_id"]["variable_type"] == "identifier"
    assert by_name["sex"]["variable_type"] == "binary"
    assert by_name["stage"]["variable_type"] == "ordinal"
    assert by_name["age"]["variable_type"] == "continuous"
    assert by_name["diagnosis_date"]["variable_type"] == "date"
    assert by_name["comment"]["variable_type"] == "text"
    assert by_name["OS_time"]["variable_type"] == "time_to_event"
    assert "identifier_not_allowed_for_statistics" in by_name["case_id"]["blockers"]
    assert "ordinal_order_needs_confirmation" in by_name["stage"]["warnings"]


def _input(clinical: Path) -> dict[str, object]:
    return {"survival_clinical_input_id": "input-1", "clinical_asset": {"path": str(clinical)}}
