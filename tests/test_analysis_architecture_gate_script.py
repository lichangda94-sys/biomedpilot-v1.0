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
    assert payload["standard_worker_migration_matrix"]["status"] == "partial"
    assert payload["standard_worker_migration_matrix"]["evidence_registry_status"] == "passed"
    assert payload["standard_worker_migration_matrix"]["evidence_entry_count"] == 0
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
