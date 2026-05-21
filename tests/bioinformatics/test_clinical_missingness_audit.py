from __future__ import annotations

from pathlib import Path

from app.bioinformatics.survival_clinical import audit_clinical_variables


def test_clinical_missingness_blocks_constant_all_missing_and_unknown(tmp_path: Path) -> None:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text(
        "case_id\tconstant\tmostly_missing\tunknown_blob\n"
        "C1\tA\t\talpha beta gamma delta epsilon zeta\n"
        "C2\tA\t\tbeta gamma delta epsilon zeta eta\n"
        "C3\tA\t1\tgamma delta epsilon zeta eta theta\n",
        encoding="utf-8",
    )

    audit = audit_clinical_variables(tmp_path, {"clinical_asset": {"path": str(clinical)}})
    by_name = {item["variable_name"]: item for item in audit["variables"]}

    assert "constant_variable" in by_name["constant"]["blockers"]
    assert "high_missing_rate" in by_name["mostly_missing"]["blockers"]
    assert by_name["case_id"]["allowed_analysis_candidates"] == ["identifier_only"]
    assert by_name["unknown_blob"]["variable_type"] == "text"
    assert by_name["unknown_blob"]["allowed_analysis_candidates"] == ["not_for_formal_statistics"]
