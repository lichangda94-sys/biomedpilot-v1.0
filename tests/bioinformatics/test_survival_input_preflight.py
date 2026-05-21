from __future__ import annotations

from pathlib import Path

from app.bioinformatics.clinical_analysis import build_survival_package, build_survival_preflight


def test_survival_preflight_blocks_missing_event_field(tmp_path: Path) -> None:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text("case_id\tOS_time\nC1\t10\n", encoding="utf-8")
    package = build_survival_package(
        {
            "input_package_id": "pkg",
            "clinical_asset": {"path": str(clinical)},
            "expression_asset": {"path": "expr.tsv"},
        }
    )

    preflight = build_survival_preflight(package)

    assert "missing_event_field" in preflight["blockers"]
    assert "KM plot" in preflight["forbidden_outputs"]


def test_survival_package_warns_low_event_count_and_requires_grouping(tmp_path: Path) -> None:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text("case_id\tOS_time\tOS_event\nC1\t10\t1\nC2\t20\t0\n", encoding="utf-8")

    package = build_survival_package({"input_package_id": "pkg", "clinical_asset": {"path": str(clinical)}}, grouping_policy="")

    assert "low_event_count_for_formal_survival" in package.to_dict()["warnings"]
    assert "expression_grouping_policy_must_be_user_confirmed" in package.to_dict()["blockers"]
