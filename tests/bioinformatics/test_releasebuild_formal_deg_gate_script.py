from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_releasebuild_formal_deg_gate_script_skip_full_tests_writes_json(tmp_path: Path) -> None:
    output = tmp_path / "gate.json"
    completed = subprocess.run(
        [sys.executable, "scripts/releasebuild_formal_deg_gate.py", "--skip-full-tests", "--json-output", str(output)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert completed.returncode == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "biomedpilot.releasebuild_formal_deg_gate.v1"
    assert payload["status"] == "passed"
    assert payload["skip_full_tests"] is True
    assert payload["runtime_validation"]["status"] == "passed"
    multifactor = payload["multifactor_runtime_validation"]
    assert multifactor["status"] == "passed"
    assert set(multifactor["methods"]) == {"limma", "DESeq2", "edgeR"}
    for method in ("limma", "DESeq2", "edgeR"):
        fixture = multifactor["fixture_results"][method]
        assert fixture["status"] == "passed"
        assert fixture["result_semantics"] == "formal_computed_result"
        assert fixture["result_index_v2_status"] == "passed"
        assert fixture["task_run_log_present"] is True
        assert fixture["has_numeric_p_value"] is True
        assert fixture["has_numeric_fdr"] is True
        assert fixture["plot_artifacts"] == []
        assert fixture["report_artifacts"] == []
        assert fixture["report_ready_eligible"] is False
    assert multifactor["negative_value_type_checks"]["DESeq2"]["status"] == "passed"
    assert multifactor["negative_value_type_checks"]["edgeR"]["status"] == "passed"
