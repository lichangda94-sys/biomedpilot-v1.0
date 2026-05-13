from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.workspace import literature_import_quality_dashboard_state, recent_import_batch_quality_summaries, recent_import_batch_summaries


def test_import_quality_dashboard_empty_state(tmp_path: Path) -> None:
    state = literature_import_quality_dashboard_state(tmp_path)

    assert state.title == "Meta Literature Import Quality Dashboard"
    assert state.status_label == "Testing / Developer Preview"
    assert state.batch_count == 0
    assert state.batches == ()
    assert "暂无导入批次" in state.empty_state


def test_import_quality_dashboard_reads_legacy_import_batches_and_diagnostics(tmp_path: Path) -> None:
    literature_dir = tmp_path / "literature"
    diagnostics_dir = literature_dir / "import_diagnostics"
    diagnostics_dir.mkdir(parents=True)
    (literature_dir / "import_batches.json").write_text(
        json.dumps(
            [
                {
                    "batch_id": "batch-legacy",
                    "project_id": "meta-test",
                    "source_type": "file",
                    "input_path": "/tmp/sample.ris",
                    "format_hint": "ris",
                    "status": "completed",
                    "total_records": 4,
                    "imported_records": 3,
                    "failed_records": 1,
                    "warning_count": 2,
                    "raw_record_count": 4,
                    "parsed_record_count": 4,
                    "normalized_record_count": 3,
                    "duplicate_candidate_count": 1,
                    "records_after_dedup_count": 2,
                    "created_at": "2026-01-02T00:00:00+00:00",
                    "metadata": {"source_database": "PubMed"},
                }
            ]
        ),
        encoding="utf-8",
    )
    (diagnostics_dir / "batch-legacy_import_diagnostics.json").write_text(
        json.dumps(
            {
                "warning_count": 2,
                "duplicate_candidate_count": 1,
                "missing_title_count": 1,
                "missing_doi_count": 2,
            }
        ),
        encoding="utf-8",
    )

    summaries = recent_import_batch_quality_summaries(tmp_path)
    state = literature_import_quality_dashboard_state(tmp_path)

    assert len(summaries) == 1
    summary = summaries[0]
    assert summary.source_database == "PubMed"
    assert summary.source_format == "ris"
    assert summary.status == "completed"
    assert summary.raw_record_count == 4
    assert summary.parsed_record_count == 4
    assert summary.normalized_record_count == 3
    assert summary.failed_record_count == 1
    assert summary.warning_count == 2
    assert summary.duplicate_candidate_count == 1
    assert summary.diagnostics_path.endswith("batch-legacy_import_diagnostics.json")
    assert "missing_title_count=1" in summary.diagnostics_summary
    assert state.batch_count == 1


def test_import_quality_dashboard_reads_unified_import_output_without_crashing(tmp_path: Path) -> None:
    project_dir = tmp_path / "projects" / "meta-test" / "meta_analysis"
    import_dir = project_dir / "literature_import"
    diagnostics_dir = project_dir / "literature" / "import_diagnostics"
    import_dir.mkdir(parents=True)
    diagnostics_dir.mkdir(parents=True)
    diagnostics_path = diagnostics_dir / "batch-unified_import_diagnostics.json"
    diagnostics_path.write_text(
        json.dumps(
            {
                "raw_record_count": 3,
                "parsed_record_count": 3,
                "normalized_record_count": 3,
                "failed_record_count": 0,
                "warning_count": 1,
                "duplicate_candidate_count": 1,
                "missing_pmid_count": 1,
            }
        ),
        encoding="utf-8",
    )
    (import_dir / "batch-unified_records.json").write_text(
        json.dumps(
            {
                "project_id": "meta-test",
                "batch_id": "batch-unified",
                "source_type": "csv",
                "status": "completed",
                "created_at": "2026-01-03T00:00:00+00:00",
                "diagnostics_path": str(diagnostics_path),
                "records": [{"record_id": "rec-1"}, {"record_id": "rec-2"}, {"record_id": "rec-3"}],
            }
        ),
        encoding="utf-8",
    )

    legacy_dicts = recent_import_batch_summaries(tmp_path)
    summary = recent_import_batch_quality_summaries(tmp_path)[0]

    assert summary.batch_id == "batch-unified"
    assert summary.source_database == "csv"
    assert summary.source_format == "csv"
    assert summary.raw_record_count == 3
    assert summary.warning_count == 1
    assert summary.duplicate_candidate_count == 1
    assert "missing_pmid_count=1" in summary.diagnostics_summary
    assert legacy_dicts[0]["parsed_count"] == 3
    assert legacy_dicts[0]["diagnostics_path"] == str(diagnostics_path)
