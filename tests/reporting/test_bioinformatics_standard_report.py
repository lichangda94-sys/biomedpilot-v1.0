from __future__ import annotations

from pathlib import Path

from reporting.bioinformatics_standard_report import (
    DEFAULT_RISK_WARNINGS,
    generate_standard_report,
    load_bioinformatics_configs,
    render_standard_report_markdown,
)


def test_bioinformatics_yaml_configs_are_readable() -> None:
    configs = load_bioinformatics_configs()

    assert set(configs) == {
        "analysis_defaults",
        "enrichment_defaults",
        "package_requirements",
        "plotting_defaults",
        "survival_defaults",
    }
    assert configs["plotting_defaults"]["output"]["dpi"] == 300
    assert configs["plotting_defaults"]["figure_sizes"]["default"]["width"] == 8
    assert configs["analysis_defaults"]["global"]["p_adjust_method"] == "BH"
    assert configs["analysis_defaults"]["example_gene_panel"]["hard_coded_default"] is False


def test_standard_report_template_renders_missing_sections() -> None:
    markdown, warnings = render_standard_report_markdown(
        {
            "analysis_id": "demo-run",
            "project_summary": {"name": "Demo project"},
            "datasets": [{"dataset_id": "GSE_DEMO", "source_type": "geo"}],
        }
    )

    assert "## Survival Analysis Results" in markdown
    assert "Not available in this run." in markdown
    assert "Demo project" in markdown
    assert DEFAULT_RISK_WARNINGS[0] in warnings


def test_warning_can_enter_report() -> None:
    markdown, warnings = render_standard_report_markdown(
        {
            "warnings": ["Custom validation warning"],
            "requested_output_formats": ["docx"],
        }
    )

    assert "Custom validation warning" in markdown
    assert "Custom validation warning" in warnings
    assert "DOCX/PDF export is not available" in markdown


def test_config_snapshot_and_markdown_report_are_generated(tmp_path: Path) -> None:
    result = generate_standard_report(
        {
            "analysis_id": "snapshot-demo",
            "project_summary": {"name": "Snapshot demo"},
            "input_files": [{"path": "inputs/expression.csv", "type": "expression_matrix"}],
            "figures": [{"path": "figures/volcano.png", "type": "volcano"}],
            "tables": [{"path": "tables/deg.csv", "type": "deg"}],
        },
        output_dir=tmp_path,
    )

    assert result.markdown_path.exists()
    assert result.config_snapshot_path.exists()
    assert result.config_snapshot_path == tmp_path / "reproducibility" / "config_snapshot" / "bioinformatics_config_snapshot.yaml"
    snapshot_text = result.config_snapshot_path.read_text(encoding="utf-8")
    assert "plotting_defaults:" in snapshot_text
    assert "analysis_defaults:" in snapshot_text
    assert "Snapshot demo" in result.markdown
    assert "figures/volcano.png" in result.markdown


def test_report_generation_does_not_require_real_downloads(tmp_path: Path) -> None:
    result = generate_standard_report({"analysis_id": "no-download"}, output_dir=tmp_path)

    assert result.markdown_path.exists()
    assert "Not available in this run." in result.markdown
    assert "DESeq2 requires raw integer counts" in result.markdown
