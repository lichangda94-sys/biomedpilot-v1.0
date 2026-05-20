from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.deg_engine.dependency_check import REQUIRED_PACKAGES
from app.bioinformatics.deg_engine.runtime_validation import run_formal_deg_runtime_validation
from app.main import main, parse_args


def test_formal_deg_runtime_validation_uses_real_environment(tmp_path: Path) -> None:
    result = run_formal_deg_runtime_validation(output_path=tmp_path / "runtime.json")

    assert result["schema_version"] == "biomedpilot.b9_3_formal_deg_runtime_validation.v1"
    assert set(result["import_checks"]) == set(REQUIRED_PACKAGES)
    assert result["packaging_checks"]["required_packages_declared_for_runtime"] == list(REQUIRED_PACKAGES)
    written = json.loads((tmp_path / "runtime.json").read_text(encoding="utf-8"))
    assert written["status"] == result["status"]

    if result["dependency_snapshot"]["status"] == "passed":
        assert result["status"] == "passed"
        assert result["fixture_result"]["status"] == "passed"
        assert result["fixture_result"]["has_numeric_p_value"] is True
        assert result["fixture_result"]["has_numeric_fdr"] is True
        assert result["fixture_result"]["result_semantics"] == "formal_computed_result"
        assert result["fixture_result"]["task_run_log_present"] is True
        assert result["fixture_result"]["parameters_manifest_status"] == "passed"
        assert result["fixture_result"]["dependency_snapshot_status"] == "passed"
    else:
        assert result["status"] == "blocked_missing_dependency"
        assert result["fixture_result"]["status"] == "blocked"
        assert result["fixture_result"]["graceful_missing_dependency_block"] is True
        assert any(str(item).startswith("missing_python_package:") for item in result["dependency_snapshot"]["blockers"])


def test_app_main_runtime_validation_cli_writes_json(tmp_path: Path) -> None:
    output = tmp_path / "runtime.json"
    exit_code = main(["--bio-formal-deg-runtime-check", "--bio-formal-deg-runtime-check-output", str(output)])

    assert exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] in {"passed", "blocked_missing_dependency"}
    assert payload["runtime_context"]["launch_mode"] in {"source", "packaged-local-python"}


def test_parse_args_accepts_runtime_validation_with_launchservices_psn() -> None:
    args = parse_args(["-psn_0_12345", "--bio-formal-deg-runtime-check", "--bio-formal-deg-runtime-check-output", "/tmp/out.json"])

    assert args.bio_formal_deg_runtime_check is True
    assert args.bio_formal_deg_runtime_check_output == "/tmp/out.json"
