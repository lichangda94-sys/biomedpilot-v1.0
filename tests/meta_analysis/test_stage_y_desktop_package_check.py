from __future__ import annotations

from pathlib import Path

from app.meta_analysis.services.internal_beta_rc_service import InternalBetaRCAuditService
from app.meta_analysis.services.project_contract_service import MetaProjectContractService


def test_desktop_package_audit_records_package_smoke_without_requiring_fix(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    MetaProjectContractService().write_project_manifests(project_dir)

    result = InternalBetaRCAuditService().build_desktop_package_audit(
        project_dir,
        app_smoke_passed=True,
        package_smoke_passed=False,
        package_smoke_message="package smoke failed in report-only mode",
    )

    assert result.status == "warn"
    assert not result.blockers
    assert "package_smoke_failed_or_not_available_report_only" in result.warnings
    assert {check.check_id for check in result.checks} >= {"app_startup_smoke", "package_smoke", "mac_app_impact"}

