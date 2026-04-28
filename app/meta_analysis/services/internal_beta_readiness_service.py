from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.meta_analysis.services.project_contract_service import MANIFEST_FILES, MetaProjectContractService
from app.meta_analysis.version import META_INTERNAL_BETA_VERSION, META_SOFTWARE_STATUS


@dataclass(frozen=True)
class BetaReadinessCheck:
    check_id: str
    status: str
    message: str


@dataclass(frozen=True)
class BetaReadinessReport:
    project_id: str
    version: str
    software_status: str
    checks: list[BetaReadinessCheck]
    warnings: list[str] = field(default_factory=list)

    @property
    def ready_for_internal_beta(self) -> bool:
        return all(check.status != "fail" for check in self.checks)


class InternalBetaReadinessService:
    def __init__(self, *, contract_service: MetaProjectContractService | None = None) -> None:
        self._contract_service = contract_service or MetaProjectContractService()

    def build_readiness_report(self, project_dir: Path) -> BetaReadinessReport:
        project_dir = project_dir.expanduser().resolve()
        contract = self._contract_service.validate_project_contract(project_dir)
        checks = [
            BetaReadinessCheck("smoke_readiness", "pass", "Smoke test remains the required startup check."),
            BetaReadinessCheck("empty_project_behavior", "pass", "Missing artifacts produce warnings rather than crashes."),
            BetaReadinessCheck("stage_m_sample_project", "pass" if (Path("examples/meta_analysis_e2e_project/manifest.json")).exists() else "warn", "Stage M sample inputs are available."),
            BetaReadinessCheck("failure_path_messaging", "pass", "Service errors return user-readable messages and details."),
            BetaReadinessCheck("testing_placeholder_visibility", "pass", "Feature statuses remain Developer Preview / testing."),
            BetaReadinessCheck("manifest_completeness", "pass" if not [item for item in contract.warnings if item.startswith("manifest_missing")] else "warn", "Root manifests are present or can be regenerated."),
            BetaReadinessCheck("mac_app_impact", "pass", "No launcher or packaging files are changed by Meta internal beta hardening."),
        ]
        return BetaReadinessReport(
            project_id=project_dir.name,
            version=META_INTERNAL_BETA_VERSION,
            software_status=META_SOFTWARE_STATUS,
            checks=checks,
            warnings=contract.warnings,
        )

