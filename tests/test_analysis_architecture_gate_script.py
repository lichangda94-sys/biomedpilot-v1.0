from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analysis_architecture_gate.py"


def test_analysis_architecture_gate_script_allows_current_partial_state_without_full_ready(tmp_path: Path) -> None:
    output = tmp_path / "analysis_architecture_gate.json"
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--json-output", str(output), "--pretty"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert completed.returncode == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "biomedpilot.analysis.architecture_gate_report.v1"
    assert payload["schema_validation_status"] == "passed"
    assert payload["schema_blockers"] == []
    assert payload["status"] == "passed"
    assert payload["require_full_ready"] is False
    assert payload["architecture_status"] == "partial_with_p1_gaps"
    assert payload["p0_issues"] == []
    assert set(payload["p1_issues"]) == {
        "full_analysis_environment_locks_not_restored",
        "full_analysis_resource_locks_not_complete",
        "formal_algorithms_not_universally_migrated_to_isolated_standard_worker",
    }
    assert payload["full_analysis_activation_gate"]["status"] == "blocked"
    assert payload["environment_readiness"]["status"] == "passed"
    assert payload["environment_readiness"]["full_mode_ready"] is False
    assert set(payload["environment_readiness"]["blocked_environment_ids"]) == {
        "r-bio-full",
        "r-spatial-full",
        "r-chem-full",
        "r-chem-gpu",
    }
    assert payload["resource_readiness"]["status"] == "passed"
    assert payload["resource_readiness"]["full_mode_ready"] is False
    assert "reactome_full" in payload["resource_readiness"]["blocked_resource_ids"]
    assert "gromacs_tool" in payload["resource_readiness"]["blocked_resource_ids"]
    assert payload["standard_worker_migration_matrix"]["status"] == "partial"
    assert payload["standard_worker_migration_matrix"]["evidence_registry_status"] == "passed"
    assert payload["standard_worker_migration_matrix"]["evidence_entry_count"] == 0
    migration_rows = {row["module_id"]: row for row in payload["standard_worker_migration_rows"]}
    assert set(migration_rows) >= {
        "deg",
        "enrichment",
        "survival",
        "spatial_transcriptomics",
        "docking",
        "molecular_dynamics",
    }
    assert migration_rows["deg"]["formal_worker_status"] == "pending_standard_worker_migration"
    assert migration_rows["spatial_transcriptomics"]["analysis_environment"] == "r-bio-core"
    assert migration_rows["spatial_transcriptomics"]["full_environment"] == "r-spatial-full"
    assert migration_rows["docking"]["full_environment"] == "r-chem-full"
    assert migration_rows["molecular_dynamics"]["full_environment"] == "r-chem-gpu"
    assert "analysis_architecture_has_p1_gaps" in payload["warnings"]
    assert "full_analysis_activation_gate_blocked_but_allowed_by_default_gate" in payload["warnings"]
    assert payload["execution_policy"] == "read_only_no_worker_execution_no_runtime_install_no_resource_download"


def test_analysis_architecture_gate_script_can_require_full_ready(tmp_path: Path) -> None:
    output = tmp_path / "analysis_architecture_full_required.json"
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--require-full-ready", "--json-output", str(output)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert completed.returncode == 1
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "blocked"
    assert payload["schema_validation_status"] == "passed"
    assert payload["schema_blockers"] == []
    assert payload["require_full_ready"] is True
    assert payload["blockers"] == ["full_analysis_activation_gate_not_ready"]
    assert payload["full_analysis_activation_gate"]["blockers"] == [
        "full_analysis_environment_locks_not_ready",
        "full_analysis_resource_locks_not_ready",
        "full_analysis_standard_worker_migration_incomplete",
    ]
    assert payload["exit_policy"] == "exit_nonzero_until_full_analysis_activation_gate_is_eligible"


def test_analysis_architecture_gate_script_is_read_only_and_has_no_runtime_acquisition_commands() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    assert "subprocess.run(" not in text
    assert "install.packages" not in text
    assert "BiocManager::install" not in text
    assert "pak::pkg_install" not in text
    assert "remotes::install_github" not in text
    assert "download.file" not in text


def test_analysis_architecture_gate_report_schema_is_present_and_matches_payload_contract() -> None:
    schema = json.loads((ROOT / "analysis" / "schemas" / "output" / "architecture_gate_report.schema.json").read_text(encoding="utf-8"))

    assert schema["$id"] == "biomedpilot.analysis.architecture_gate_report.v1"
    assert "schema_version" in schema["required"]
    assert "full_analysis_activation_gate" in schema["required"]
    assert "environment_readiness" in schema["required"]
    assert "resource_readiness" in schema["required"]
    assert "standard_worker_migration_matrix" in schema["required"]
    assert "standard_worker_migration_rows" in schema["required"]
    assert "remediation_queue" in schema["required"]
    assert schema["properties"]["schema_version"]["const"] == "biomedpilot.analysis.architecture_gate_report.v1"
    assert schema["properties"]["execution_policy"]["const"] == "read_only_no_worker_execution_no_runtime_install_no_resource_download"
