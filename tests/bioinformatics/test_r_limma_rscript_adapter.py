from __future__ import annotations

import json
import os
from pathlib import Path

from app.bioinformatics.deg_engine.rscript_adapter import (
    detect_r_limma_runtime_capabilities,
    run_r_limma_rscript_execution,
)


def test_detect_r_limma_runtime_capabilities_with_fake_rscript(tmp_path: Path) -> None:
    fake_rscript = _fake_rscript(
        tmp_path,
        """
import sys
if sys.argv[1] == "-e":
    print("R=R version 4.4.2")
    print("platform=aarch64-apple-darwin20")
    print("BiocManager=1.30.25")
    print("limma=3.62.2")
    sys.exit(0)
sys.exit(2)
""",
    )

    result = detect_r_limma_runtime_capabilities(str(fake_rscript))

    assert result["status"] == "passed"
    assert result["external_capabilities"]["runtime.r.available"]["available"] is True
    assert result["external_capabilities"]["package.r.limma.available"]["version"] == "3.62.2"
    assert result["dependency_snapshot"]["status"] == "passed"


def test_run_r_limma_rscript_execution_registers_formal_result(tmp_path: Path) -> None:
    expression_path = _write_expression_table(tmp_path)
    fake_rscript = _fake_rscript(
        tmp_path,
        """
import pathlib
import sys
output = pathlib.Path(sys.argv[4])
output.write_text(
    "feature_id\\tgene_symbol\\tlogFC\\tAveExpr\\tt\\tP.Value\\tadj.P.Val\\tB\\n"
    "ENSG000001\\tGENE1\\t1.4\\t8.0\\t3.5\\t0.002\\t0.02\\t4.1\\n"
    "ENSG000002\\tGENE2\\t-0.3\\t7.2\\t-0.9\\t0.3\\t0.6\\t-2.0\\n",
    encoding="utf-8",
)
print("limma fake execution ok")
sys.exit(0)
""",
    )

    result = run_r_limma_rscript_execution(
        tmp_path,
        expression_table_path=expression_path,
        sample_group_map={"case_1": "case", "case_2": "case", "control_1": "control", "control_2": "control"},
        case_group="case",
        control_group="control",
        multi_factor_preflight=_preflight(),
        parameters_manifest=_parameters(),
        rscript_path=str(fake_rscript),
        external_capabilities=_capabilities(str(fake_rscript)),
        dependency_snapshot=_dependency_snapshot(str(fake_rscript)),
        result_id="r-limma-rscript-test",
        task_run_id="task-r-limma-rscript-test",
        input_package_id="input-r-limma-1",
        source_dataset_id="dataset-r-limma-1",
        source_repository_manifest="manifests/source.json",
    )

    assert result["status"] == "passed"
    assert result["result_semantics"] == "formal_computed_result"
    assert result["report_ready_eligible"] is False
    assert result["plot_artifacts"] == []
    assert result["report_artifacts"] == []
    assert Path(result["command_manifest_path"]).is_file()
    assert Path(result["command_log_path"]).is_file()
    assert Path(result["limma_output_path"]).is_file()

    command_manifest = json.loads(Path(result["command_manifest_path"]).read_text(encoding="utf-8"))
    command_log = json.loads(Path(result["command_log_path"]).read_text(encoding="utf-8"))
    assert command_manifest["shell"] is False
    assert command_manifest["command"][0] == str(fake_rscript)
    assert command_log["status"] == "succeeded"
    assert command_log["returncode"] == 0

    entry = result["result_index_entry"]
    assert entry["engine_name"] == "r_limma_rscript_adapter"
    assert entry["engine_version"] == "0.1.0"
    assert entry["result_semantics"] == "formal_computed_result"
    assert entry["report_ready_eligible"] is False
    assert entry["plot_artifacts"] == []
    assert entry["report_artifacts"] == []
    assert {artifact["artifact_type"] for artifact in entry["log_artifacts"]} == {
        "r_limma_external_handoff_log",
        "r_limma_rscript_command_manifest",
        "r_limma_rscript_command_log",
    }

    result_index = json.loads((tmp_path / "results" / "summaries" / "result_index.json").read_text(encoding="utf-8"))
    assert result_index["results"][0]["result_id"] == "r-limma-rscript-test"


def test_run_r_limma_rscript_execution_writes_multifactor_design_table(tmp_path: Path) -> None:
    expression_path = _write_multifactor_expression_table(tmp_path)
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
assert sys.argv[5] == "groupcase-groupcontrol"
output.write_text(
    "feature_id\\tgene_symbol\\tlogFC\\tAveExpr\\tt\\tP.Value\\tadj.P.Val\\tB\\n"
    "ENSG000001\\tGENE1\\t1.2\\t8.0\\t3.0\\t0.004\\t0.04\\t3.1\\n",
    encoding="utf-8",
)
""",
    )

    sample_map = {f"case_{i}": "case" for i in range(1, 4)} | {f"control_{i}": "control" for i in range(1, 4)}
    result = run_r_limma_rscript_execution(
        tmp_path,
        expression_table_path=expression_path,
        sample_group_map=sample_map,
        case_group="case",
        control_group="control",
        multi_factor_preflight=_preflight_with_covariates(method="limma", method_family="limma_normalized_expression"),
        parameters_manifest=_parameters(),
        rscript_path=str(fake_rscript),
        external_capabilities=_capabilities(str(fake_rscript)),
        dependency_snapshot=_dependency_snapshot(str(fake_rscript)),
        result_id="r-limma-multifactor-test",
        task_run_id="task-r-limma-multifactor-test",
        input_package_id="input-r-limma-1",
    )

    assert result["status"] == "passed"
    command_manifest = json.loads(Path(result["command_manifest_path"]).read_text(encoding="utf-8"))
    assert command_manifest["design_formula"] == "~ batch + age + group"
    assert command_manifest["covariates"] == ["batch", "age"]
    assert result["result_index_entry"]["report_ready_eligible"] is False


def test_run_r_limma_rscript_execution_blocks_nonzero_exit_without_result_index(tmp_path: Path) -> None:
    expression_path = _write_expression_table(tmp_path)
    fake_rscript = _fake_rscript(
        tmp_path,
        """
import sys
print("limma failed", file=sys.stderr)
sys.exit(7)
""",
    )

    result = run_r_limma_rscript_execution(
        tmp_path,
        expression_table_path=expression_path,
        sample_group_map={"case_1": "case", "case_2": "case", "control_1": "control", "control_2": "control"},
        case_group="case",
        control_group="control",
        multi_factor_preflight=_preflight(),
        parameters_manifest=_parameters(),
        rscript_path=str(fake_rscript),
        external_capabilities=_capabilities(str(fake_rscript)),
        dependency_snapshot=_dependency_snapshot(str(fake_rscript)),
        input_package_id="input-r-limma-1",
    )

    assert result["status"] == "blocked"
    assert "r_limma_rscript_exit_code:7" in result["blockers"]
    assert Path(result["command_log_path"]).is_file()
    assert not (tmp_path / "results" / "summaries" / "result_index.json").exists()


def test_run_r_limma_rscript_execution_blocks_timeout_without_result_index(tmp_path: Path) -> None:
    expression_path = _write_expression_table(tmp_path)
    fake_rscript = _fake_rscript(
        tmp_path,
        """
import time
time.sleep(5)
""",
    )

    result = run_r_limma_rscript_execution(
        tmp_path,
        expression_table_path=expression_path,
        sample_group_map={"case_1": "case", "case_2": "case", "control_1": "control", "control_2": "control"},
        case_group="case",
        control_group="control",
        multi_factor_preflight=_preflight(),
        parameters_manifest=_parameters(),
        rscript_path=str(fake_rscript),
        external_capabilities=_capabilities(str(fake_rscript)),
        dependency_snapshot=_dependency_snapshot(str(fake_rscript)),
        timeout_seconds=1,
        input_package_id="input-r-limma-1",
    )

    assert result["status"] == "blocked"
    assert "r_limma_rscript_timeout" in result["blockers"]
    assert Path(result["command_log_path"]).is_file()
    assert not (tmp_path / "results" / "summaries" / "result_index.json").exists()


def test_run_r_limma_rscript_execution_blocks_sample_group_mismatch(tmp_path: Path) -> None:
    expression_path = _write_expression_table(tmp_path)

    result = run_r_limma_rscript_execution(
        tmp_path,
        expression_table_path=expression_path,
        sample_group_map={"case_1": "case", "case_2": "case", "control_1": "control"},
        case_group="case",
        control_group="control",
        multi_factor_preflight=_preflight(),
        parameters_manifest=_parameters(),
        rscript_path="/does/not/matter",
        external_capabilities=_capabilities("/does/not/matter"),
        dependency_snapshot=_dependency_snapshot("/does/not/matter"),
        input_package_id="input-r-limma-1",
    )

    assert result["status"] == "blocked"
    assert "sample_missing_group:control_2" in result["blockers"]
    assert not (tmp_path / "results" / "summaries" / "result_index.json").exists()


def _fake_rscript(tmp_path: Path, body: str) -> Path:
    path = tmp_path / f"fake_rscript_{abs(hash(body))}.py"
    path.write_text(f"#!/usr/bin/env python3\n{body.strip()}\n", encoding="utf-8")
    os.chmod(path, 0o755)
    return path


def _write_expression_table(tmp_path: Path) -> Path:
    path = tmp_path / "expression.tsv"
    path.write_text(
        "feature_id\tgene_symbol\tcase_1\tcase_2\tcontrol_1\tcontrol_2\n"
        "ENSG000001\tGENE1\t8.1\t8.4\t6.2\t6.1\n"
        "ENSG000002\tGENE2\t4.2\t4.0\t4.4\t4.1\n",
        encoding="utf-8",
    )
    return path


def _write_multifactor_expression_table(tmp_path: Path) -> Path:
    path = tmp_path / "expression_multifactor.tsv"
    path.write_text(
        "feature_id\tgene_symbol\tcase_1\tcase_2\tcase_3\tcontrol_1\tcontrol_2\tcontrol_3\n"
        "ENSG000001\tGENE1\t8.1\t8.4\t8.0\t6.2\t6.1\t6.0\n"
        "ENSG000002\tGENE2\t4.2\t4.0\t4.4\t4.1\t4.5\t4.3\n",
        encoding="utf-8",
    )
    return path


def _preflight() -> dict[str, object]:
    return {
        "status": "design_ready",
        "method": "limma",
        "method_family": "limma_normalized_expression",
        "input_package_id": "input-r-limma-1",
        "result_semantics": "preflight_only",
        "blockers": [],
        "warnings": [],
    }


def _preflight_with_covariates(*, method: str, method_family: str) -> dict[str, object]:
    return {
        **_preflight(),
        "method": method,
        "method_family": method_family,
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


def _parameters() -> dict[str, object]:
    return {
        "schema_version": "test.r_limma.rscript.params.v1",
        "input_package_id": "input-r-limma-1",
        "comparison_id": "case-v-control",
        "case_group": "case",
        "control_group": "control",
        "method": "limma",
        "log2fc_threshold": 1.0,
        "fdr_threshold": 0.05,
    }


def _capabilities(rscript_path: str) -> dict[str, object]:
    return {
        "runtime.r.available": {"available": True, "path": rscript_path, "version": "R version 4.4.2"},
        "runtime.bioconductor.available": {"available": True, "version": "3.20"},
        "package.r.limma.available": {"available": True, "version": "3.62.2"},
    }


def _dependency_snapshot(rscript_path: str) -> dict[str, object]:
    return {
        "status": "passed",
        "runtime": "system_rscript",
        "rscript_path": rscript_path,
        "dependencies": {
            "R": {"installed": True, "path": rscript_path, "version": "R version 4.4.2"},
            "BiocManager": {"installed": True, "version": "3.20"},
            "limma": {"installed": True, "version": "3.62.2"},
        },
        "blockers": [],
    }
