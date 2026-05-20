from __future__ import annotations

from app.bioinformatics.plots.basic_renderers import build_basic_plot_spec
from app.bioinformatics.plots.schema import validate_plot_artifact


def test_volcano_plot_spec_uses_result_artifact_semantics() -> None:
    result = {"result_id": "deg-1", "task_type": "deg", "result_semantics": "formal_computed_result"}

    spec = build_basic_plot_spec(result, "volcano_plot")

    assert spec["encoding"]["x"] == "log2_fold_change"
    assert spec["blockers"] == []


def test_plot_schema_blocks_preflight_only_source() -> None:
    validation = validate_plot_artifact(
        {
            "plot_id": "plot",
            "plot_type": "volcano_plot",
            "source_result_id": "preflight",
            "source_result_semantics": "preflight_only",
            "plot_semantics": "preflight_only",
            "plot_artifact_scope": "formal_deg_plot",
            "input_package_id": "pkg",
            "task_run_id": "task",
            "parameters_manifest": {},
            "plot_spec_artifact": {},
            "image_artifacts": [],
            "table_artifacts": [],
            "engine_name": "spec",
            "engine_version": "1",
            "dependency_snapshot": {},
            "warnings": [],
            "blockers": [],
            "created_at": "now",
            "schema_version": "biomedpilot.plot_artifact.v1",
        }
    )

    assert "preflight_only_source_cannot_generate_formal_plot" in validation["blockers"]


def test_plot_schema_blocks_legacy_preflight_only_source_label() -> None:
    validation = validate_plot_artifact(
        {
            "plot_id": "plot",
            "plot_type": "volcano_plot",
            "source_result_id": "preflight",
            "source_result_semantics": "preflight-only",
            "plot_semantics": "preflight-only",
            "plot_artifact_scope": "formal_deg_plot",
            "input_package_id": "pkg",
            "task_run_id": "task",
            "parameters_manifest": {},
            "plot_spec_artifact": {},
            "image_artifacts": [],
            "table_artifacts": [],
            "engine_name": "spec",
            "engine_version": "1",
            "dependency_snapshot": {},
            "warnings": [],
            "blockers": [],
            "created_at": "now",
            "schema_version": "biomedpilot.plot_artifact.v1",
        }
    )

    assert "preflight_only_source_cannot_generate_formal_plot" in validation["blockers"]
