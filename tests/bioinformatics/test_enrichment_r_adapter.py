from __future__ import annotations

from pathlib import Path

from app.bioinformatics.enrichment_r_adapter import (
    run_controlled_gsea_preranked_r_fixture,
    run_controlled_ora_r_fixture,
)


def test_controlled_ora_r_fixture_is_blocked_until_full_standard_worker_migration(tmp_path: Path) -> None:
    result = run_controlled_ora_r_fixture(tmp_path, detection_path=tmp_path / "detection.json", runner=_runner_must_not_run)

    assert result["status"] == "blocked"
    assert result["analysis_type"] == "ora"
    assert result["result_semantics"] == "blocked"
    assert result["standard_worker_required"] is True
    assert result["required_worker_boundary"] == "standard_r_worker"
    assert result["required_task_system_invocation"] == "task_center_registered"
    assert result["legacy_execution_policy"] == "disabled_until_full_standard_worker_migration_evidence_passes"
    assert "controlled_enrichment_legacy_formal_execution_disabled" in result["blockers"]
    assert "enrichment_full_standard_worker_migration_required" in result["blockers"]
    assert "analysis_environment_renv_lock_not_restored:r-bio-full:scaffold_only_not_restored" in result["blockers"]
    assert "analysis_resource_not_locked:reactome_full" in result["blockers"]
    assert result["plot_artifacts"] == []
    assert result["report_artifacts"] == []
    assert result["report_ready_eligible"] is False
    assert not (tmp_path / "results" / "summaries" / "result_index.json").exists()


def test_controlled_gsea_r_fixture_is_blocked_until_full_standard_worker_migration(tmp_path: Path) -> None:
    result = run_controlled_gsea_preranked_r_fixture(tmp_path, detection_path=tmp_path / "detection.json", runner=_runner_must_not_run)

    assert result["status"] == "blocked"
    assert result["analysis_type"] == "gsea_preranked"
    assert result["result_semantics"] == "blocked"
    assert result["required_mode"] == "full"
    assert "controlled_enrichment_legacy_formal_execution_disabled" in result["blockers"]
    assert "enrichment_full_standard_worker_migration_required" in result["blockers"]
    assert "analysis_resource_not_locked:msigdb_full" in result["blockers"]
    assert not (tmp_path / "results" / "summaries" / "result_index.json").exists()


def _runner_must_not_run(*_args: object, **_kwargs: object) -> object:
    raise AssertionError("legacy enrichment R subprocess runner must not be called before full standard-worker migration evidence passes")
