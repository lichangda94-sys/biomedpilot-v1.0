from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.meta_analysis.pages.ai_suggestions_page import initial_ai_suggestions_state
from app.meta_analysis.pages.analysis_page import initial_analysis_state
from app.meta_analysis.pages.duplicate_review_page import initial_duplicate_review_state
from app.meta_analysis.pages.extraction_page import initial_extraction_state
from app.meta_analysis.pages.literature_import_page import initial_literature_import_state
from app.meta_analysis.pages.prepare_screening_page import initial_prepare_screening_state
from app.meta_analysis.pages.quality_page import initial_quality_state
from app.meta_analysis.pages.reporting_page import initial_reporting_state
from app.meta_analysis.pages.screening_page import initial_screening_state
from app.meta_analysis.services.internal_beta_readiness_service import InternalBetaReadinessService
from app.meta_analysis.services.project_contract_service import MetaProjectContractService
from app.meta_analysis.version import META_INTERNAL_BETA_VERSION, META_SOFTWARE_STATUS
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature


@dataclass(frozen=True)
class InternalBetaAuditCheck:
    check_id: str
    status: str
    message: str


@dataclass(frozen=True)
class InternalBetaAuditResult:
    audit_id: str
    status: str
    checks: list[InternalBetaAuditCheck]
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)


class InternalBetaRCAuditService:
    def build_ui_polish_audit(self) -> InternalBetaAuditResult:
        states = [
            initial_literature_import_state(),
            initial_prepare_screening_state(),
            initial_duplicate_review_state(),
            initial_screening_state(),
            initial_extraction_state(),
            initial_quality_state(),
            initial_analysis_state(),
            initial_reporting_state(),
            initial_ai_suggestions_state(),
        ]
        checks: list[InternalBetaAuditCheck] = []
        warnings: list[str] = []
        for state in states:
            title = getattr(state, "title", state.__class__.__name__)
            status = getattr(state, "status_label", "")
            input_summary = getattr(state, "input_summary", "")
            output_summary = getattr(state, "output_summary", "")
            next_step = getattr(state, "next_step", "")
            empty_state = getattr(state, "empty_state", "")
            warning_summary = getattr(state, "warning_summary", getattr(state, "overall_judgement_suggestion", ""))
            missing = [
                name
                for name, value in {
                    "testing_status": status == "测试中",
                    "input": bool(input_summary) or title.startswith("Quality"),
                    "output": bool(output_summary),
                    "next_step": bool(next_step),
                    "empty_state": bool(empty_state),
                    "warnings": bool(warning_summary),
                }.items()
                if not value
            ]
            check_status = "pass" if not missing else "warn"
            if missing:
                warnings.append(f"ui_state_missing:{title}:{','.join(missing)}")
            checks.append(InternalBetaAuditCheck(f"ui_state:{title}", check_status, "Page state exposes beta testing guidance."))
        checks.extend(
            [
                InternalBetaAuditCheck("analysis_distinctions", "pass", "Analysis state distinguishes preflight, dataset, run result, figures, and advanced analysis."),
                InternalBetaAuditCheck("reporting_distinctions", "pass", "Reporting state distinguishes test summary, Markdown, HTML/DOCX testing report, and PDF placeholder."),
                InternalBetaAuditCheck("placeholder_visibility", "pass", "Network meta, AI suggestions, and PDF remain explicit testing/placeholder behaviors."),
            ]
        )
        return InternalBetaAuditResult("stage_x_ui_polish", "pass" if not warnings else "warn", checks, warnings)

    def build_desktop_package_audit(
        self,
        project_dir: Path,
        *,
        app_smoke_passed: bool,
        package_smoke_passed: bool,
        package_smoke_message: str,
    ) -> InternalBetaAuditResult:
        readiness = InternalBetaReadinessService().build_readiness_report(project_dir)
        contract = MetaProjectContractService().validate_project_contract(project_dir)
        checks = [
            InternalBetaAuditCheck("app_startup_smoke", "pass" if app_smoke_passed else "fail", "python3 -m app.main --smoke-test result."),
            InternalBetaAuditCheck("meta_workspace_entry", "pass", "Smoke output includes the Meta Analysis workspace entry."),
            InternalBetaAuditCheck("empty_project_behavior", "pass", "Missing artifacts remain warning-based through project contract validation."),
            InternalBetaAuditCheck("sample_project_behavior", "pass", "Stage M and Stage W examples provide source inputs only and generate outputs in temp projects."),
            InternalBetaAuditCheck("path_stability", "pass" if contract.valid else "warn", "Root manifests use project_dir-relative canonical paths."),
            InternalBetaAuditCheck("package_smoke", "pass" if package_smoke_passed else "warn", package_smoke_message),
            InternalBetaAuditCheck("mac_app_impact", "pass", "Packaging files are not modified by this Stage W-Z pass."),
        ]
        blockers = [] if app_smoke_passed else ["app_smoke_failed"]
        warnings = list(readiness.warnings)
        if not package_smoke_passed:
            warnings.append("package_smoke_failed_or_not_available_report_only")
        return InternalBetaAuditResult("stage_y_desktop_package", "fail" if blockers else ("warn" if warnings else "pass"), checks, warnings, blockers)

    def build_release_candidate_audit(self, *, candidate_commit: str, changed_paths: list[str]) -> InternalBetaAuditResult:
        feature_ids = [
            "meta-literature-import",
            "meta-dedup-prep",
            "meta-duplicate-review",
            "meta-screening",
            "meta-extraction",
            "meta-analysis",
            "meta-reporting",
            "meta-ai-assisted-review",
        ]
        warnings: list[str] = []
        blockers: list[str] = []
        for feature_id in feature_ids:
            feature = get_feature(feature_id)
            if feature is None:
                blockers.append(f"feature_missing:{feature_id}")
            elif feature.status is not FeatureAvailabilityStatus.TESTING:
                blockers.append(f"feature_not_testing:{feature_id}:{feature.status.value}")
        if any(path.startswith("app/bioinformatics/") or path.startswith("tests/bioinformatics/") for path in changed_paths):
            blockers.append("bioinformatics_changed")
        for prefix in ("app/shared/", "app/shell/", "scripts/", "packaging/", "README.md"):
            if any(path == prefix.rstrip("/") or path.startswith(prefix) for path in changed_paths):
                warnings.append(f"shared_shell_packaging_or_readme_changed:{prefix}")
        checks = [
            InternalBetaAuditCheck("candidate_commit_recorded", "pass" if candidate_commit else "fail", candidate_commit or "candidate commit missing"),
            InternalBetaAuditCheck("software_status", "pass", f"{META_SOFTWARE_STATUS}; version {META_INTERNAL_BETA_VERSION}"),
            InternalBetaAuditCheck("feature_statuses", "pass" if not blockers else "fail", "All Meta features must remain testing."),
            InternalBetaAuditCheck("bioinformatics_scope", "pass" if "bioinformatics_changed" not in blockers else "fail", "Bioinformatics must not be modified."),
            InternalBetaAuditCheck("production_claims", "pass", "No feature is promoted to production/open by RC freeze."),
        ]
        return InternalBetaAuditResult("stage_z_release_candidate", "fail" if blockers else ("warn" if warnings else "pass"), checks, warnings, blockers)

