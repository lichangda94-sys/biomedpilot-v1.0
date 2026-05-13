from __future__ import annotations

import json
import zipfile
from pathlib import Path

from tests.meta_analysis.e2e_project_builder import build_meta_analysis_e2e_project


REALISTIC_INPUT = Path("examples/meta_analysis_realistic_project/inputs/pubmed_hydroxychloroquine_trials.csv")


def test_realistic_pubmed_derived_project_runs_full_internal_beta_chain(tmp_path: Path) -> None:
    project = build_meta_analysis_e2e_project(
        tmp_path,
        project_id="meta-realistic-hcq-or",
        input_path=REALISTIC_INPUT,
        intervention_or_exposure="Hydroxychloroquine",
        comparator="Placebo or standard care",
        source_location="PubMed-derived metadata fixture; extraction values manually seeded for validation.",
        seeded_note="Stage W validation-only manual binary outcome seed; not published trial extraction.",
        outcome_data=[
            (49, 414, 58, 407, "postexposure prophylaxis"),
            (421, 1561, 790, 3155, "hospitalized treatment"),
            (39, 1116, 45, 1198, "cluster prevention"),
        ],
    )

    paths = project["paths"]
    required = [
        "literature_records",
        "screening_decisions",
        "fulltext_registry",
        "extraction_records",
        "quality_assessment_table",
        "analysis_ready_dataset",
        "analysis_result",
        "forest_plot",
        "funnel_plot",
        "formal_report",
        "reproducibility_package",
    ]
    for key in required:
        assert paths[key].exists(), key
        assert paths[key].stat().st_size > 0, key

    for manifest_name in ["project.json", "data_manifest.json", "artifact_manifest.json", "task_manifest.json", "lineage_manifest.json"]:
        assert (project["project_dir"] / manifest_name).exists(), manifest_name
    assert (project["project_dir"] / "reports" / "report_manifest.json").exists()

    literature = json.loads(paths["literature_records"].read_text(encoding="utf-8"))
    assert literature["records"][0]["pmid"] == "32492293"
    extraction = json.loads(paths["extraction_records"].read_text(encoding="utf-8"))
    assert "validation-only manual binary outcome seed" in extraction["records"][0]["notes"]
    report_text = paths["formal_report"].read_text(encoding="utf-8")
    assert "Developer Preview" in report_text

    with zipfile.ZipFile(paths["reproducibility_package"]) as archive:
        names = set(archive.namelist())
    assert "project.json" in names
    assert "reports/report_manifest.json" in names

    assert project["warnings"]["seeded_note"].startswith("Stage W validation-only")
