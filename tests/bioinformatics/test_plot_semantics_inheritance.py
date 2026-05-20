from __future__ import annotations

from app.bioinformatics.plots import create_plot_artifact
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result


def test_plot_artifact_inherits_imported_warning(tmp_path) -> None:
    register_result(
        tmp_path,
        ResultIndexEntry(
            result_id="deg-imported",
            task_run_id="task",
            task_type="deg",
            result_semantics="imported_external_result",
            validation_status="warning",
        ),
    )

    plot = create_plot_artifact(tmp_path, "deg-imported", "volcano_plot")

    assert "plot_source_is_imported_external_result" in plot["warnings"]
