from __future__ import annotations

import zipfile
from pathlib import Path

from tests.meta_analysis.e2e_project_builder import build_meta_analysis_e2e_project


def test_stage_m_example_project_runs_from_import_to_reproducibility_package(tmp_path: Path) -> None:
    result = build_meta_analysis_e2e_project(tmp_path)
    paths: dict[str, Path] = result["paths"]

    required_artifacts = {
        "literature_records",
        "screening_ready_records",
        "duplicate_candidate_groups",
        "deduplicated_literature",
        "screening_decisions",
        "fulltext_registry",
        "fulltext_exclusion_report",
        "extraction_records",
        "quality_assessment_table",
        "analysis_ready_dataset",
        "analysis_result",
        "forest_plot",
        "result_table",
        "funnel_plot",
        "publication_bias_result",
        "prisma_summary_json",
        "prisma_summary_md",
        "formal_report",
        "html_report",
        "word_report",
        "supplementary_exports",
        "figure_package",
        "snapshot",
        "reproducibility_package",
    }
    for key in required_artifacts:
        path = paths[key]
        assert path.exists(), key
        if path.is_file():
            assert path.stat().st_size > 0, key

    formal_report = paths["formal_report"].read_text(encoding="utf-8")
    assert "testing / developer preview" in formal_report
    assert str(paths["forest_plot"]) in formal_report
    assert str(paths["result_table"]) in formal_report
    assert "Network meta-analysis" in formal_report

    assert result["warnings"]["publication_bias"]
    assert any("full-text workflow incomplete" in note for note in result["warnings"]["prisma"])

    with zipfile.ZipFile(paths["reproducibility_package"]) as archive:
        names = set(archive.namelist())
    assert "project.json" in names
    assert "reports/formal_meta_report.md" in names
    assert "extraction/extraction_records.json" in names
    assert "analysis/analysis_results.json" in names
    assert any(name.startswith("figures/forest_plot_") for name in names)
    assert "software_version.json" in names

    data_types = {asset.data_type for asset in result["data_center"].list_assets(result["project_dir"].name)}
    assert {
        "literature_records",
        "screening_ready_records",
        "duplicate_candidate_groups",
        "deduplicated_literature",
        "screening_decisions",
        "fulltext_registry",
        "extraction_records",
        "quality_assessments",
        "analysis_ready_dataset",
        "analysis_result",
        "forest_plot",
        "funnel_plot",
        "formal_meta_report",
        "supplementary_exports",
        "reproducibility_package",
    } <= data_types

