from __future__ import annotations

from pathlib import Path

from app.meta_analysis.services.internal_beta_readiness_service import InternalBetaReadinessService
from app.meta_analysis.services.project_contract_service import MetaProjectContractService
from app.meta_analysis.version import META_INTERNAL_BETA_VERSION, META_SOFTWARE_STATUS


def test_internal_beta_readiness_report_and_version(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    MetaProjectContractService().write_project_manifests(project_dir)

    report = InternalBetaReadinessService().build_readiness_report(project_dir)

    assert report.version == META_INTERNAL_BETA_VERSION
    assert report.software_status == META_SOFTWARE_STATUS
    assert report.ready_for_internal_beta
    assert {check.check_id for check in report.checks} >= {"smoke_readiness", "manifest_completeness", "mac_app_impact"}


def test_internal_beta_docs_are_planned_paths() -> None:
    expected = [
        Path("docs/meta_internal_beta_readiness.md"),
        Path("docs/meta_known_limitations.md"),
        Path("docs/meta_quickstart_internal_beta.md"),
        Path("docs/meta_sample_project_walkthrough.md"),
    ]
    assert all(path.suffix == ".md" for path in expected)

