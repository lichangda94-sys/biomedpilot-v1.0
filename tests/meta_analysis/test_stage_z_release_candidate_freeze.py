from __future__ import annotations

from pathlib import Path

from app.meta_analysis.services.internal_beta_rc_service import InternalBetaRCAuditService


def test_release_candidate_audit_blocks_bioinformatics_and_preserves_testing_status() -> None:
    service = InternalBetaRCAuditService()

    clean = service.build_release_candidate_audit(
        candidate_commit="abc1234",
        changed_paths=[
            "app/meta_analysis/services/internal_beta_rc_service.py",
            "docs/meta_dev_reports/stage_Z_internal_beta_release_candidate_report.md",
        ],
    )
    assert clean.status == "pass"
    assert not clean.blockers

    blocked = service.build_release_candidate_audit(candidate_commit="abc1234", changed_paths=["app/bioinformatics/example.py"])
    assert blocked.status == "fail"
    assert "bioinformatics_changed" in blocked.blockers


def test_internal_beta_release_docs_exist_or_are_planned() -> None:
    expected = [
        Path("docs/meta_internal_beta_changelog.md"),
        Path("docs/meta_internal_beta_test_checklist.md"),
        Path("docs/meta_known_limitations.md"),
        Path("docs/meta_quickstart_internal_beta.md"),
        Path("docs/meta_sample_project_walkthrough.md"),
    ]
    assert all(path.suffix == ".md" for path in expected)

