from __future__ import annotations

from pathlib import Path

from app.bioinformatics.gsea import audit_gsea_e2e_acceptance
from app.bioinformatics.plots import create_gsea_plot_artifact
from app.bioinformatics.reports.gsea import create_gsea_report_ready_package

from .test_gsea_report_ready import complete_gsea_fixture


def test_gsea_e2e_acceptance_passes_for_complete_chain(tmp_path: Path) -> None:
    complete_gsea_fixture(tmp_path, with_plot=False)
    assert create_gsea_plot_artifact(tmp_path, result_id="gsea-formal")["status"] == "passed"
    package = create_gsea_report_ready_package(tmp_path, result_id="gsea-formal")
    assert package["status"] == "gsea_report_ready_package_created"

    audit = audit_gsea_e2e_acceptance(tmp_path, result_id="gsea-formal")

    assert audit["status"] == "passed"
    assert audit["traceability"]["source_deg_result_id"] == "deg-source"
    assert audit["traceability"]["gsea_result_id"] == "gsea-formal"
    assert audit["traceability"]["gene_set_resource_id"] == "sets"
    assert audit["consistency"]["review_table_matches_source_table"] is True
    assert audit["consistency"]["packaged_gsea_table_matches_result_table"] is True
    assert audit["consistency"]["plot_artifact_in_result_index"] is True
    assert audit["consistency"]["package_independently_reviewable"] is True


def test_gsea_e2e_acceptance_blocks_missing_dependency_invalid_table_and_missing_plot(tmp_path: Path) -> None:
    complete_gsea_fixture(tmp_path / "missing_dependency", with_plot=False, dependency_passed=False)
    assert create_gsea_report_ready_package(tmp_path / "missing_dependency", result_id="gsea-formal", allow_table_only_report=True)["status"] == "blocked"
    missing_dependency = audit_gsea_e2e_acceptance(tmp_path / "missing_dependency", result_id="gsea-formal", allow_table_only_report=True)
    assert missing_dependency["status"] == "blocked"
    assert any("dependency" in item for item in missing_dependency["blockers"])

    complete_gsea_fixture(tmp_path / "invalid_table", with_plot=False, table_valid=False)
    invalid_table = audit_gsea_e2e_acceptance(tmp_path / "invalid_table", result_id="gsea-formal", allow_table_only_report=True)
    assert invalid_table["status"] == "blocked"
    assert any("gsea_table:" in item or "review:" in item for item in invalid_table["blockers"])

    complete_gsea_fixture(tmp_path / "missing_plot", with_plot=False)
    missing_plot = audit_gsea_e2e_acceptance(tmp_path / "missing_plot", result_id="gsea-formal")
    assert missing_plot["status"] == "blocked"
    assert any("gsea_report_ready_requires_gsea_plot_artifact_or_table_only_mode" in item for item in missing_plot["blockers"])


def test_gsea_e2e_table_only_mode_is_accepted_when_explicit(tmp_path: Path) -> None:
    complete_gsea_fixture(tmp_path, with_plot=False)
    package = create_gsea_report_ready_package(tmp_path, result_id="gsea-formal", allow_table_only_report=True)
    assert package["status"] == "gsea_report_ready_package_created"

    audit = audit_gsea_e2e_acceptance(tmp_path, result_id="gsea-formal", allow_table_only_report=True)

    assert audit["status"] == "passed"
    package_path = Path(audit["traceability"]["latest_package_path"])
    text = (package_path / "README_limitations.md").read_text(encoding="utf-8")
    assert "No-plot GSEA report" in text
