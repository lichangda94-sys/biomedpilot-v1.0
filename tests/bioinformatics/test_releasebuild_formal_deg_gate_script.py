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
