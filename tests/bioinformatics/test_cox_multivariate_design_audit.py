from __future__ import annotations

from app.bioinformatics.clinical_analysis import build_clinical_association_preflight, build_survival_package
from app.bioinformatics.survival_clinical import audit_cox_multivariate_design


def test_cox_multivariate_design_blocks_too_many_covariates_for_events(tmp_path) -> None:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text(
        "sample_id\tOS_time\tOS_event\tage\tsex\tstage\n"
        "S1\t5\t1\t50\tF\tI\nS2\t8\t0\t55\tM\tII\nS3\t12\t1\t60\tF\tIII\n"
        "S4\t6\t1\t65\tM\tII\nS5\t9\t0\t70\tF\tIII\nS6\t15\t1\t75\tM\tI\n",
        encoding="utf-8",
    )
    package = build_survival_package({"input_package_id": "pkg", "clinical_asset": {"path": str(clinical)}})
    audit = build_clinical_association_preflight([
        {"age": "50", "sex": "F", "stage": "I"},
        {"age": "55", "sex": "M", "stage": "II"},
        {"age": "60", "sex": "F", "stage": "III"},
    ])

    design = audit_cox_multivariate_design(package, audit, selected_covariates=["age", "sex", "stage"])

    assert design["provenance"]["design_audit_only"] is True
    assert "too_few_events_for_multivariate" in design["blockers"]
    assert "too_many_covariates_for_events" in design["blockers"]
    assert "user_confirmation_missing" in design["blockers"]
    assert "risk_score" not in str(design)
