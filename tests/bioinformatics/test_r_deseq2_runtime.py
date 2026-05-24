from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import pytest

from app.bioinformatics.deg_engine.r_deseq2_planning import build_r_deseq2_parameter_manifest
from app.bioinformatics.deg_engine.r_deseq2_runtime import detect_r_deseq2_runtime_capabilities, run_r_deseq2_rscript_execution
from app.bioinformatics.deg_engine.r_deseq2_runtime_validation import run_r_deseq2_runtime_validation


def test_real_rscript_deseq2_controlled_count_fixture_registers_formal_result(tmp_path: Path) -> None:
    runtime = detect_r_deseq2_runtime_capabilities(timeout_seconds=20)
    if runtime["status"] != "passed":
        pytest.skip(f"Rscript/DESeq2 runtime unavailable: {runtime.get('blockers')}")

    count_table = _write_count_fixture(tmp_path)
    preflight = _preflight()
    parameter_manifest = build_r_deseq2_parameter_manifest(
        _deg_ready(count_table),
        multi_factor_preflight=preflight,
        dependency_snapshot=runtime["dependency_snapshot"],
        fdr_threshold=0.5,
        dispersion_fit_type="mean",
    )
    assert parameter_manifest["status"] == "passed"

    result = run_r_deseq2_rscript_execution(
        tmp_path,
        count_table_path=count_table,
        sample_group_map=parameter_manifest["sample_group_map"],
        case_group=parameter_manifest["case_group"],
        control_group=parameter_manifest["control_group"],
        multi_factor_preflight=preflight,
        parameters_manifest=parameter_manifest,
        rscript_path=str(runtime["rscript_path"]),
        external_capabilities=runtime["external_capabilities"],
        dependency_snapshot=runtime["dependency_snapshot"],
        timeout_seconds=120,
        result_id="r-deseq2-real-fixture",
        task_run_id="task-r-deseq2-real-fixture",
        input_package_id=parameter_manifest["input_package_id"],
        source_dataset_id="deseq2-real-count-fixture",
        source_repository_manifest="standardized_data/repositories/repository_manifest.json",
    )

    assert result["status"] == "passed"
    assert result["result_semantics"] == "formal_computed_result"
    assert result["report_ready_eligible"] is False
    assert result["plot_artifacts"] == []
    assert result["report_artifacts"] == []
    assert result["output_schema_gate"]["status"] == "passed"
    assert result["registration_gate"]["status"] == "passed"
    assert result["result_index_gate"]["status"] == "passed"

    entry = result["result_index_entry"]
    assert entry["engine_name"] == "r_deseq2_rscript_adapter"
    assert entry["result_semantics"] == "formal_computed_result"
    assert entry["report_ready_eligible"] is False
    assert {artifact["artifact_type"] for artifact in entry["output_artifacts"]} == {"deg_result_table", "deseq2_result_table"}
    assert entry["plot_artifacts"] == []
    assert entry["report_artifacts"] == []

    canonical_rows = list(csv.DictReader(Path(result["canonical_table_path"]).open(encoding="utf-8"), delimiter="\t"))
    deseq2_rows = list(csv.DictReader(Path(result["deseq2_table_path"]).open(encoding="utf-8"), delimiter="\t"))
    assert len(canonical_rows) == 24
    assert len(deseq2_rows) == 24
    assert all(row["p_value"] for row in canonical_rows)
    assert all(row["adjusted_p_value"] for row in canonical_rows)
    assert any(float(row["adjusted_p_value"]) <= 0.5 for row in canonical_rows)

    index_payload = json.loads((tmp_path / "results" / "summaries" / "result_index.json").read_text(encoding="utf-8"))
    assert index_payload["results"][0]["result_id"] == "r-deseq2-real-fixture"


def test_rscript_deseq2_execution_blocks_invalid_count_table_without_result_index(tmp_path: Path) -> None:
    count_table = tmp_path / "bad_counts.tsv"
    count_table.write_text(
        "feature_id\tgene_symbol\tcase_1\tcase_2\tcontrol_1\tcontrol_2\n"
        "ENSG000001\tGENE1\t1.5\t2\t3\t4\n",
        encoding="utf-8",
    )
    result = run_r_deseq2_rscript_execution(
        tmp_path,
        count_table_path=count_table,
        sample_group_map={"case_1": "case", "case_2": "case", "control_1": "control", "control_2": "control"},
        case_group="case",
        control_group="control",
        multi_factor_preflight=_preflight(),
        parameters_manifest={},
        external_capabilities={
            "runtime.r.available": {"available": True},
            "runtime.bioconductor.available": {"available": True},
            "package.r.deseq2.available": {"available": True},
        },
        dependency_snapshot={"status": "passed", "dependencies": {}, "blockers": []},
    )

    assert result["status"] == "blocked"
    assert "count_fixture_row_0:non_integer_count:case_1" in result["blockers"]
    assert not (tmp_path / "results" / "summaries" / "result_index.json").exists()


def test_rscript_deseq2_execution_writes_multifactor_design_table(tmp_path: Path) -> None:
    count_table = _write_multifactor_count_fixture(tmp_path)
    fake_rscript = _fake_rscript(
        tmp_path,
        """
import csv
import pathlib
import sys
design = pathlib.Path(sys.argv[3])
output = pathlib.Path(sys.argv[4])
rows = list(csv.DictReader(design.open(encoding="utf-8"), delimiter="\\t"))
assert {"sample", "group", "batch", "age"}.issubset(rows[0])
output.write_text(
    "feature_id\\tgene_symbol\\tbaseMean\\tlog2FoldChange\\tlfcSE\\tstat\\tpvalue\\tpadj\\n"
    "ENSG000001\\tGENE1\\t72.5\\t2.1\\t0.4\\t5.25\\t0.001\\t0.01\\n",
    encoding="utf-8",
)
""",
    )
    sample_map = {f"case_{i}": "case" for i in range(1, 4)} | {f"control_{i}": "control" for i in range(1, 4)}
    preflight = _preflight_with_covariates()
    parameter_manifest = build_r_deseq2_parameter_manifest(
        _deg_ready(count_table),
        multi_factor_preflight=preflight,
        dependency_snapshot=_dependency_snapshot(str(fake_rscript)),
    )

    result = run_r_deseq2_rscript_execution(
        tmp_path,
        count_table_path=count_table,
        sample_group_map=sample_map,
        case_group="case",
        control_group="control",
        multi_factor_preflight=preflight,
        parameters_manifest=parameter_manifest,
        rscript_path=str(fake_rscript),
        external_capabilities=_capabilities(str(fake_rscript)),
        dependency_snapshot=_dependency_snapshot(str(fake_rscript)),
        result_id="r-deseq2-multifactor-test",
        task_run_id="task-r-deseq2-multifactor-test",
        input_package_id=parameter_manifest["input_package_id"],
    )

    assert result["status"] == "passed"
    command_log = json.loads((tmp_path / "analysis" / "r_deg" / "deseq2_rscript" / "task-r-deseq2-multifactor-test" / "command_manifest.json").read_text(encoding="utf-8"))
    assert command_log["design_formula"] == "~ batch + age + group"
    assert command_log["covariates"] == ["batch", "age"]
    assert result["plot_artifacts"] == []
    assert result["report_artifacts"] == []
    assert result["report_ready_eligible"] is False


def test_r_deseq2_runtime_validation_reports_package_ready_or_graceful_block(tmp_path: Path) -> None:
    output_path = tmp_path / "deseq2_runtime.json"
    validation = run_r_deseq2_runtime_validation(output_path=output_path)

    assert output_path.is_file()
    assert validation["schema_version"] == "biomedpilot.b25_10_r_deseq2_runtime_validation.v1"
    assert validation["status"] in {"passed", "blocked_missing_dependency"}
    assert validation["ui_activation_preflight"]["formal_execution_enabled"] is False
    if validation["status"] == "passed":
        assert validation["ui_activation_preflight"]["blockers"] == []
        assert validation["ui_activation_preflight"]["status"] == "runtime_preflight_passed_ui_gates_required"
        fixture = validation["fixture_result"]
        assert fixture["status"] == "passed"
        assert fixture["result_semantics"] == "formal_computed_result"
        assert fixture["has_numeric_p_value"] is True
        assert fixture["has_numeric_adjusted_p_value"] is True
        assert fixture["plot_artifacts"] == []
        assert fixture["report_artifacts"] == []
        assert fixture["report_ready_eligible"] is False
        assert validation["packaging_checks"]["r_bioconductor_policy"] == "detect_first_external_rscript_no_install_no_bundle"


def _write_count_fixture(root: Path) -> Path:
    path = root / "counts.tsv"
    lines = ["feature_id\tgene_symbol\tcase_1\tcase_2\tcontrol_1\tcontrol_2"]
    for index in range(1, 25):
        if index <= 8:
            values = (120 + index * 2, 116 + index * 2, 24 + index, 28 + index)
        elif index <= 16:
            values = (24 + index, 28 + index, 118 + index * 2, 122 + index * 2)
        else:
            values = (60 + index, 58 + index, 61 + index, 59 + index)
        lines.append(f"ENSG{index:06d}\tGENE{index}\t{values[0]}\t{values[1]}\t{values[2]}\t{values[3]}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_multifactor_count_fixture(root: Path) -> Path:
    path = root / "counts_multifactor.tsv"
    path.write_text(
        "feature_id\tgene_symbol\tcase_1\tcase_2\tcase_3\tcontrol_1\tcontrol_2\tcontrol_3\n"
        "ENSG000001\tGENE1\t120\t115\t118\t24\t31\t28\n"
        "ENSG000002\tGENE2\t20\t23\t21\t80\t77\t81\n",
        encoding="utf-8",
    )
    return path


def _deg_ready(count_table: Path) -> dict[str, object]:
    return {
        "input_package_id": "input-deseq2-real-fixture",
        "deg_ready_package_id": "deg-ready-deseq2-real-fixture",
        "value_type": "count",
        "gene_id_type": "symbol",
        "matrix_asset": {"asset_type": "raw_count_matrix", "path": str(count_table)},
        "gene_mapping_status": {"status": "passed"},
        "sample_alignment_status": {"status": "passed"},
        "blockers": [],
        "warnings": [],
    }


def _preflight() -> dict[str, object]:
    return {
        "status": "design_ready",
        "method": "deseq2",
        "method_family": "deseq2_count_model",
        "value_type": "count",
        "value_type_policy": "deseq2_requires_raw_integer_counts",
        "input_package_id": "input-deseq2-real-fixture",
        "deg_ready_package_id": "deg-ready-deseq2-real-fixture",
        "gene_id_type": "symbol",
        "contrast": {
            "contrast_id": "case_vs_control",
            "factor": "group",
            "case_level": "case",
            "control_level": "control",
            "case_samples": ["case_1", "case_2"],
            "control_samples": ["control_1", "control_2"],
        },
        "blockers": [],
        "warnings": [],
    }


def _preflight_with_covariates() -> dict[str, object]:
    return {
        **_preflight(),
        "contrast": {
            "contrast_id": "case_vs_control",
            "factor": "group",
            "case_level": "case",
            "control_level": "control",
            "case_samples": ["case_1", "case_2", "case_3"],
            "control_samples": ["control_1", "control_2", "control_3"],
        },
        "design_config": {
            "primary_factor": "group",
            "case_group": "case",
            "control_group": "control",
            "sample_table": [
                {"sample_id": "case_1", "group": "case", "batch": "b1", "age": 50},
                {"sample_id": "case_2", "group": "case", "batch": "b2", "age": 55},
                {"sample_id": "case_3", "group": "case", "batch": "b1", "age": 65},
                {"sample_id": "control_1", "group": "control", "batch": "b2", "age": 52},
                {"sample_id": "control_2", "group": "control", "batch": "b1", "age": 59},
                {"sample_id": "control_3", "group": "control", "batch": "b2", "age": 70},
            ],
            "covariates": [{"name": "batch", "variable_type": "categorical"}, {"name": "age", "variable_type": "continuous"}],
        },
    }


def _fake_rscript(tmp_path: Path, body: str) -> Path:
    path = tmp_path / f"fake_rscript_{abs(hash(body))}.py"
    path.write_text(f"#!/usr/bin/env python3\n{body.strip()}\n", encoding="utf-8")
    os.chmod(path, 0o755)
    return path


def _capabilities(rscript_path: str) -> dict[str, object]:
    return {
        "runtime.r.available": {"available": True, "path": rscript_path, "version": "R version 4.4.2"},
        "runtime.bioconductor.available": {"available": True, "version": "3.20"},
        "package.r.deseq2.available": {"available": True, "version": "1.46.0"},
    }


def _dependency_snapshot(rscript_path: str) -> dict[str, object]:
    return {
        "status": "passed",
        "runtime": "system_rscript",
        "rscript_path": rscript_path,
        "dependencies": {
            "R": {"available": True, "path": rscript_path, "version": "R version 4.4.2"},
            "BiocManager": {"available": True, "version": "3.20"},
            "DESeq2": {"available": True, "version": "1.46.0"},
        },
        "blockers": [],
    }
