from __future__ import annotations

import json
import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analysis_architecture_gate.py"


def _load_gate_module():
    spec = importlib.util.spec_from_file_location("analysis_architecture_gate", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


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
    assert payload["requirement_summary"]["requirement_count"] == 20
    assert payload["requirement_summary"]["fail_count"] == 0
    assert payload["requirement_summary"]["warn_count"] >= 1
    assert payload["requirement_summary"]["pass_count"] >= 1
    requirement_rows = {row["requirement_id"]: row for row in payload["requirement_rows"]}
    assert len(requirement_rows) == 20
    assert requirement_rows["RARCH-01"]["status"] == "pass"
    assert requirement_rows["RARCH-03"]["status"] == "warn"
    assert requirement_rows["RARCH-10"]["status"] == "pass"
    assert requirement_rows["RARCH-11"]["status"] == "pass"
    assert payload["priority_issue_lists"]["P0"] == []
    assert {item["issue_id"] for item in payload["priority_issue_lists"]["P1"]} == {
        "full_analysis_environment_locks_not_restored",
        "full_analysis_resource_locks_not_complete",
        "formal_algorithms_not_universally_migrated_to_isolated_standard_worker",
    }
    assert any(item["issue_id"] == "RARCH-08" for item in payload["priority_issue_lists"]["P2"])
    assert any(item["issue_id"] == "RARCH-12" for item in payload["priority_issue_lists"]["P3"])
    assert len(payload["top_architecture_risks"]) == 5
    assert payload["top_architecture_risks"][0]["risk_id"] == "full_analysis_environment_locks_not_restored"
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
    environment_templates = {item["environment_id"]: item for item in payload["environment_readiness"]["environment_lock_evidence_templates"]}
    assert environment_templates["r-bio-full"]["schema_version"] == "biomedpilot.analysis.environment_lock_evidence.v1"
    assert environment_templates["r-bio-full"]["runtime_package_install"] == "forbidden"
    assert environment_templates["r-bio-full"]["runtime_resource_download"] == "forbidden"
    assert payload["resource_readiness"]["status"] == "passed"
    assert payload["resource_readiness"]["full_mode_ready"] is False
    assert "reactome_full" in payload["resource_readiness"]["blocked_resource_ids"]
    assert "gromacs_tool" in payload["resource_readiness"]["blocked_resource_ids"]
    resource_templates = {item["resource_id"]: item for item in payload["resource_readiness"]["resource_lock_evidence_templates"]}
    assert resource_templates["reactome_full"]["schema_version"] == "biomedpilot.analysis.resource_lock_evidence.v1"
    assert resource_templates["reactome_full"]["runtime_download_allowed"] is False
    assert resource_templates["reactome_full"]["hash"]["algorithm"] == "sha256"
    assert payload["standard_worker_migration_matrix"]["status"] == "partial"
    assert payload["standard_worker_migration_matrix"]["evidence_registry_status"] == "passed"
    assert payload["standard_worker_migration_matrix"]["evidence_entry_count"] == 0
    assert payload["standard_worker_migration_matrix"]["passed_evidence_module_ids"] == []
    assert payload["standard_worker_migration_matrix"]["blocked_evidence_module_ids"] == []
    assert payload["standard_worker_migration_matrix"]["missing_evidence_module_ids"] == payload["standard_worker_migration_matrix"]["expected_evidence_module_ids"]
    assert payload["remediation_queue"]["item_count"] == 3
    assert len(payload["remediation_queue"]["items"]) == 3
    assert payload["remediation_queue"]["automation_policy"] == "manual_scoped_changes_only"
    assert payload["remediation_queue"]["install_policy"] == "no_runtime_package_install_or_resource_download"
    assert payload["remediation_summary"]["minimal_remediation_path"] == [
        "restore_full_analysis_environment_locks",
        "lock_full_analysis_resources",
        "migrate_formal_algorithms_to_isolated_standard_worker",
    ]
    decisions = {item["item_id"]: item for item in payload["remediation_summary"]["manual_decision_points"]}
    assert decisions["migrate_formal_algorithms_to_isolated_standard_worker"]["scope"].startswith("missing=10; passed=0; blocked=0")
    assert "modules=deg, survival, univariate, multivariate, enrichment" in decisions["migrate_formal_algorithms_to_isolated_standard_worker"]["scope"]
    assert "analysis/registry/analysis_environments.json" in payload["remediation_summary"]["involved_files"]
    assert "analysis/resources/manifest.json" in payload["remediation_summary"]["involved_files"]
    assert "analysis/registry/standard_worker_migration_evidence.json" in payload["remediation_summary"]["involved_files"]
    assert len(payload["remediation_summary"]["manual_decision_points"]) == 3
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
    assert migration_rows["deg"]["migration_readiness_status"] == "blocked"
    assert migration_rows["deg"]["migration_prerequisite_status"]["overall"] == "blocked"
    assert migration_rows["deg"]["migration_prerequisite_status"]["required_environment_lock"] == "required_before_migration_evidence"
    assert migration_rows["deg"]["migration_next_action"] == "declare_scoped_full_mode_only_after_environment_and_resource_locks"
    assert migration_rows["deg"]["migration_evidence_template"]["mode"] == "full"
    assert migration_rows["deg"]["migration_evidence_template"]["required_worker_boundary"] == "standard_r_worker"
    assert "legacy_service_adapter_sidecar" in migration_rows["deg"]["migration_evidence_template"]["forbidden_evidence_sources"]
    assert "registry_evidence_entry_missing_or_blocked" in migration_rows["deg"]["migration_blockers"]
    assert migration_rows["spatial_transcriptomics"]["analysis_environment"] == "r-bio-core"
    assert migration_rows["spatial_transcriptomics"]["full_environment"] == "r-spatial-full"
    assert migration_rows["docking"]["full_environment"] == "r-chem-full"
    assert migration_rows["molecular_dynamics"]["full_environment"] == "r-chem-gpu"
    assert migration_rows["univariate"]["migration_next_action"] == "implement_formal_runtime_contract_before_standard_worker_migration"
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


def test_analysis_architecture_gate_script_writes_markdown_report(tmp_path: Path) -> None:
    output = tmp_path / "analysis_architecture_gate.json"
    markdown = tmp_path / "analysis_architecture_gate.md"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--json-output",
            str(output),
            "--markdown-output",
            str(markdown),
            "--pretty",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert completed.returncode == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    text = markdown.read_text(encoding="utf-8")
    assert "# BioMedPilot R Analysis Architecture Gate Report" in text
    expected_headings = [
        "## 1. 当前是否符合目标模式",
        "## 2. PASS / WARN / FAIL 总表",
        "## 3. 最大的 5 个架构风险",
        "## 4. P0/P1/P2/P3 问题清单",
        "## 5. 涉及的文件路径",
        "## 6. 最小可行整改路径",
        "## 7. 建议优先修改的文件",
        "## 8. 已完成的修改",
        "## 9. 尚需人工决定的问题",
    ]
    for heading in expected_headings:
        assert heading in text
    assert payload["architecture_status"] == "partial_with_p1_gaps"
    assert "`partial_with_p1_gaps`" in text
    assert "`blocked`" in text
    assert "full_analysis_environment_locks_not_restored" in text
    assert "Standard Worker Migration Evidence Coverage" in text
    assert "Missing evidence modules" in text
    assert "deg, survival, univariate, multivariate, enrichment, immune_infiltration, correlation, spatial_transcriptomics, docking, molecular_dynamics" in text
    assert "missing=10; passed=0; blocked=0; modules=deg, survival, univariate, multivariate, enrichment" in text
    assert "restore_full_analysis_environment_locks" in text
    assert "analysis/registry/analysis_environments.json" in text
    assert "Architecture gate report schema validation is currently `passed`" in text
    assert "Current P0 issue list is empty" in text


def test_analysis_architecture_gate_script_writes_evidence_template_package(tmp_path: Path) -> None:
    output = tmp_path / "analysis_architecture_gate.json"
    template_output = tmp_path / "analysis_architecture_evidence_templates.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--json-output",
            str(output),
            "--evidence-template-output",
            str(template_output),
            "--pretty",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert completed.returncode == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    template_package = json.loads(template_output.read_text(encoding="utf-8"))
    assert template_package["schema_version"] == "biomedpilot.analysis.evidence_template_package.v1"
    assert template_package["schema_validation_status"] == "passed"
    assert template_package["schema_blockers"] == []
    assert template_package["architecture_status"] == "partial_with_p1_gaps"
    assert template_package["full_analysis_activation_gate_status"] == "blocked"
    assert template_package["template_policy"]["templates_are_not_readiness_evidence"] is True
    assert template_package["template_policy"]["runtime_install_forbidden"] is True
    assert template_package["template_policy"]["runtime_download_forbidden"] is True
    assert template_package["registry_paths"] == {
        "environment_lock_evidence_registry": "analysis/registry/environment_lock_evidence.json",
        "resource_lock_evidence_registry": "analysis/registry/resource_lock_evidence.json",
        "standard_worker_migration_evidence_registry": "analysis/registry/standard_worker_migration_evidence.json",
    }
    assert template_package["template_counts"]["environment_lock_evidence_templates"] == 4
    assert template_package["template_counts"]["resource_lock_evidence_templates"] == 11
    assert template_package["template_counts"]["standard_worker_migration_evidence_templates"] == len(payload["standard_worker_migration_rows"])
    assert template_package["expected_evidence_scope"] == {
        "scope_policy": "authoritative_registry_scope",
        "expected_environment_ids": payload["environment_readiness"]["expected_environment_ids"],
        "missing_environment_ids": payload["environment_readiness"]["missing_environment_ids"],
        "expected_resource_ids": payload["resource_readiness"]["expected_resource_ids"],
        "missing_resource_ids": payload["resource_readiness"]["missing_resource_ids"],
        "expected_module_ids": payload["standard_worker_migration_matrix"]["expected_evidence_module_ids"],
        "passed_module_ids": payload["standard_worker_migration_matrix"]["passed_evidence_module_ids"],
        "blocked_module_ids": payload["standard_worker_migration_matrix"]["blocked_evidence_module_ids"],
        "missing_module_ids": payload["standard_worker_migration_matrix"]["missing_evidence_module_ids"],
    }
    assert template_package["expected_evidence_scope"]["expected_environment_ids"] == [
        "r-bio-full",
        "r-spatial-full",
        "r-chem-full",
        "r-chem-gpu",
    ]
    assert "reactome_full" in template_package["expected_evidence_scope"]["expected_resource_ids"]
    assert "molecular_dynamics" in template_package["expected_evidence_scope"]["missing_module_ids"]
    remediation_scope = {
        item["item_id"]: item
        for item in template_package["remediation_scope"]["manual_decision_points"]
    }
    assert remediation_scope["migrate_formal_algorithms_to_isolated_standard_worker"]["scope"].startswith("missing=10; passed=0; blocked=0")
    assert "modules=deg, survival, univariate, multivariate, enrichment" in remediation_scope["migrate_formal_algorithms_to_isolated_standard_worker"]["scope"]
    assert template_package["remediation_scope"]["minimal_remediation_path"] == payload["remediation_summary"]["minimal_remediation_path"]
    environment_templates = {item["environment_id"]: item for item in template_package["environment_lock_evidence_templates"]}
    resource_templates = {item["resource_id"]: item for item in template_package["resource_lock_evidence_templates"]}
    migration_templates = {item["module_id"]: item for item in template_package["standard_worker_migration_evidence_templates"]}
    assert environment_templates["r-bio-full"]["runtime_package_install"] == "forbidden"
    assert environment_templates["r-bio-full"]["renv_lock_content"]["policy_status"] == "restored"
    assert environment_templates["r-bio-full"]["renv_lock_content"]["packages_non_empty"] is True
    assert environment_templates["r-bio-full"]["docker_image"]["digest"]["algorithm"] == "sha256"
    assert environment_templates["r-bio-full"]["docker_image"]["build_status"] == "built"
    assert resource_templates["reactome_full"]["runtime_download_allowed"] is False
    assert resource_templates["reactome_full"]["cache_content"]["non_empty"] is True
    assert migration_templates["deg"]["required_worker_boundary"] == "standard_r_worker"
    assert "registry_evidence_entry_missing_or_blocked" in template_package["blockers"]["standard_worker_migration"]["deg"]


def test_analysis_architecture_gate_full_required_writes_blocked_markdown_report(tmp_path: Path) -> None:
    output = tmp_path / "analysis_architecture_full_required.json"
    markdown = tmp_path / "analysis_architecture_full_required.md"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--require-full-ready",
            "--json-output",
            str(output),
            "--markdown-output",
            str(markdown),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert completed.returncode == 1
    payload = json.loads(output.read_text(encoding="utf-8"))
    text = markdown.read_text(encoding="utf-8")
    assert payload["status"] == "blocked"
    assert payload["blockers"] == ["full_analysis_activation_gate_not_ready"]
    assert "| Gate status | `blocked` |" in text
    assert "| Require full ready | `True` |" in text
    assert "Full analysis activation remains explicitly blocked rather than silently enabled" in text


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
    assert "requirement_summary" in schema["required"]
    assert "requirement_rows" in schema["required"]
    assert "priority_issue_lists" in schema["required"]
    assert "top_architecture_risks" in schema["required"]
    assert "full_analysis_activation_gate" in schema["required"]
    assert "environment_readiness" in schema["required"]
    assert "resource_readiness" in schema["required"]
    assert "standard_worker_migration_matrix" in schema["required"]
    assert "standard_worker_migration_rows" in schema["required"]
    assert "remediation_queue" in schema["required"]
    assert "remediation_summary" in schema["required"]
    assert schema["properties"]["schema_version"]["const"] == "biomedpilot.analysis.architecture_gate_report.v1"
    assert schema["properties"]["execution_policy"]["const"] == "read_only_no_worker_execution_no_runtime_install_no_resource_download"


def test_analysis_evidence_template_package_schema_is_present_and_matches_payload_contract() -> None:
    schema = json.loads((ROOT / "analysis" / "schemas" / "output" / "evidence_template_package.schema.json").read_text(encoding="utf-8"))

    assert schema["$id"] == "biomedpilot.analysis.evidence_template_package.v1"
    assert "environment_lock_evidence_templates" in schema["required"]
    assert "resource_lock_evidence_templates" in schema["required"]
    assert "standard_worker_migration_evidence_templates" in schema["required"]
    assert "template_policy" in schema["required"]
    assert "registry_paths" in schema["required"]
    assert "expected_evidence_scope" in schema["required"]
    assert "template_counts" in schema["required"]
    assert schema["properties"]["remediation_scope"]["type"] == "object"
    assert schema["properties"]["expected_evidence_scope"]["type"] == "object"
    assert "expected_module_ids" in schema["properties"]["expected_evidence_scope"]["required"]
    assert "renv_lock_content" in schema["properties"]["environment_lock_evidence_templates"]["items"]["required"]
    assert "docker_image" in schema["properties"]["environment_lock_evidence_templates"]["items"]["required"]
    assert "cache_content" in schema["properties"]["resource_lock_evidence_templates"]["items"]["required"]
    assert schema["properties"]["schema_version"]["const"] == "biomedpilot.analysis.evidence_template_package.v1"
    assert schema["properties"]["execution_policy"]["const"] == "read_only_no_worker_execution_no_runtime_install_no_resource_download"
    assert schema["properties"]["install_policy"]["const"] == "no_runtime_package_install_or_resource_download"


def test_analysis_evidence_template_package_schema_blocks_missing_content_declarations() -> None:
    gate = _load_gate_module()
    blockers = gate._evidence_template_package_schema_blockers(
        {
            "schema_version": "biomedpilot.analysis.evidence_template_package.v1",
            "created_at": "2026-06-05T00:00:00+00:00",
            "worktree": str(ROOT),
            "architecture_status": "partial_with_p1_gaps",
            "full_analysis_activation_gate_status": "blocked",
            "execution_policy": "read_only_no_worker_execution_no_runtime_install_no_resource_download",
            "install_policy": "no_runtime_package_install_or_resource_download",
            "template_policy": {},
            "registry_paths": {},
            "expected_evidence_scope": {},
            "environment_lock_evidence_templates": [{"environment_id": "r-bio-full"}],
            "resource_lock_evidence_templates": [{"resource_id": "reactome_full"}],
            "standard_worker_migration_evidence_templates": [],
            "blockers": {},
            "template_counts": {},
        },
        root=ROOT,
    )

    assert "analysis_evidence_template_package_environment_template_renv_lock_content_missing:r-bio-full" in blockers
    assert "analysis_evidence_template_package_environment_template_docker_image_missing:r-bio-full" in blockers
    assert "analysis_evidence_template_package_resource_template_cache_content_missing:reactome_full" in blockers
    assert "analysis_evidence_template_package_expected_scope_policy_invalid" in blockers
    assert "analysis_evidence_template_package_expected_scope_invalid:expected_environment_ids" in blockers
