from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.deg_engine import create_deg_production_audit_package
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import load_registry, register_result


def test_deg_audit_package_requires_formal_computed_result(tmp_path: Path) -> None:
    register_result(
        tmp_path,
        ResultIndexEntry(
            result_id="imported",
            task_run_id="task",
            task_type="deg",
            result_semantics="imported_external_result",
            validation_status="passed",
        ),
    )

    manifest = create_deg_production_audit_package(tmp_path, result_id="imported")

    assert manifest["status"] == "blocked"
    assert "deg_audit_package_requires_formal_computed_result" in manifest["blockers"]


def test_deg_audit_package_copies_tables_logs_and_manifests_without_report_ready_upgrade(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "formal.tsv"
    table.parent.mkdir(parents=True)
    table.write_text("feature_id\tgene_symbol\tp_value\tadjusted_p_value\nf1\tTP53\t0.01\t0.02\n", encoding="utf-8")
    log = tmp_path / "analysis" / "formal_deg" / "formal_run_log.json"
    log.parent.mkdir(parents=True)
    log.write_text(json.dumps({"task_run_id": "task"}), encoding="utf-8")
    register_result(
        tmp_path,
        ResultIndexEntry(
            result_id="formal",
            task_run_id="task",
            task_type="deg",
            result_semantics="formal_computed_result",
            input_package_id="pkg-1",
            source_dataset_id="dataset-1",
            source_repository_manifest="standardized_data/repositories/repository_manifest.json",
            parameters_manifest={"status": "passed"},
            engine_name="python_scipy_statsmodels_deg_mvp",
            engine_version="0.1.0",
            dependency_snapshot={"status": "passed"},
            output_artifacts=({"artifact_type": "deg_table", "path": "results/tables/formal.tsv"},),
            log_artifacts=({"artifact_type": "formal_deg_run_log", "path": "analysis/formal_deg/formal_run_log.json"},),
            validation_status="passed",
        ),
    )

    manifest = create_deg_production_audit_package(
        tmp_path,
        result_id="formal",
        input_adaptation_gate={"status": "passed"},
        design_quality_gate={"status": "passed"},
        data_quality_gate={"status": "passed"},
        method_recommendation_gate={"status": "passed"},
    )

    assert manifest["status"] == "deg_production_audit_package_created"
    assert manifest["report_ready_eligible_changed"] is False
    package = Path(str(manifest["package_path"]))
    assert (package / "deg_audit_package_manifest.json").is_file()
    assert (package / "tables" / "formal.tsv").is_file()
    assert (package / "logs" / "formal_run_log.json").is_file()
    assert (package / "manifests" / "input_adaptation.json").is_file()
    assert (package / "manifests" / "design_quality.json").is_file()
    assert (package / "manifests" / "data_quality.json").is_file()
    assert (package / "manifests" / "method_recommendation.json").is_file()
    checksums = json.loads((package / "manifests" / "checksums.json").read_text(encoding="utf-8"))
    assert checksums["files"]
    entry = load_registry(tmp_path)["results"][0]
    assert entry["report_ready_eligible"] is False
