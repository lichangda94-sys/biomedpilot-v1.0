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
    assert not any(item["issue_id"] == "RARCH-08" for item in payload["priority_issue_lists"]["P2"])
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
    assert payload["runtime_acquisition_scan"]["schema_version"] == "biomedpilot.analysis.runtime_acquisition_scan.v1"
    assert payload["runtime_acquisition_scan"]["status"] == "passed"
    assert payload["runtime_acquisition_scan"]["hit_count"] == 0
    assert payload["runtime_acquisition_scan"]["scanned_roots"] == ["app", "analysis", "scripts", "config"]
    assert payload["runtime_acquisition_scan"]["install_scan"]["scanned_file_count"] > 0
    assert payload["default_dependency_scan"]["schema_version"] == "biomedpilot.analysis.default_dependency_scan.v1"
    assert payload["default_dependency_scan"]["status"] == "passed"
    assert payload["default_dependency_scan"]["heavy_dependency_hits"] == []
    assert "docker/Dockerfile.app-dev" in payload["default_dependency_scan"]["scanned_files"]
    assert payload["module_interface_matrix"]["schema_version"] == "biomedpilot.analysis.module_interface_matrix.v1"
    assert payload["module_interface_matrix"]["status"] == "passed"
    assert payload["module_interface_matrix"]["passed_module_count"] == 10
    assert payload["module_interface_matrix"]["blocked_module_count"] == 0
    module_interface_rows = {row["module_id"]: row for row in payload["module_interface_rows"]}
    assert module_interface_rows["deg"]["mock_fixture_validation_status"] == "passed"
    assert module_interface_rows["deg"]["result_package_required"] == ["result.json", "provenance.json", "tables", "plots", "reports", "logs"]
    assert module_interface_rows["molecular_dynamics"]["full_environment"] == "r-chem-gpu"
    assert payload["module_mode_readiness_matrix"]["schema_version"] == "biomedpilot.analysis.module_mode_readiness_matrix.v1"
    assert payload["module_mode_readiness_matrix"]["status"] == "partial"
    assert payload["module_mode_readiness_matrix"]["partial_module_count"] == 10
    assert payload["module_mode_readiness_matrix"]["blocked_module_count"] == 0
    assert "deg" in payload["module_mode_readiness_matrix"]["full_blocked_module_ids"]
    module_mode_rows = {row["module_id"]: row for row in payload["module_mode_readiness_rows"]}
    assert module_mode_rows["deg"]["mock_status"] == "passed"
    assert module_mode_rows["deg"]["lite_status"] == "passed"
    assert module_mode_rows["deg"]["full_status"] == "blocked"
    assert module_mode_rows["molecular_dynamics"]["full_environment"] == "r-chem-gpu"
    assert payload["environment_artifact_matrix"]["schema_version"] == "biomedpilot.analysis.environment_artifact_matrix.v1"
    assert payload["environment_artifact_matrix"]["status"] == "partial"
    assert payload["environment_artifact_matrix"]["passed_environment_count"] == 2
    assert payload["environment_artifact_matrix"]["partial_environment_count"] == 4
    assert payload["environment_artifact_matrix"]["blocked_environment_count"] == 0
    assert payload["environment_artifact_matrix"]["restored_full_environment_ids"] == []
    assert "r-bio-full" in payload["environment_artifact_matrix"]["full_environment_ids"]
    environment_artifact_rows = {row["environment_id"]: row for row in payload["environment_artifact_rows"]}
    assert environment_artifact_rows["app-dev"]["status"] == "passed"
    assert environment_artifact_rows["app-dev"]["allowed_module_ids"] == []
    assert environment_artifact_rows["r-bio-core"]["status"] == "passed"
    assert environment_artifact_rows["r-bio-full"]["status"] == "partial"
    assert environment_artifact_rows["r-bio-full"]["renv_policy_status"] == "scaffold_only_not_restored"
    assert environment_artifact_rows["r-chem-gpu"]["renv_policy_environment"] == "r-chem-full"
    assert payload["resource_artifact_matrix"]["schema_version"] == "biomedpilot.analysis.resource_artifact_matrix.v1"
    assert payload["resource_artifact_matrix"]["status"] == "partial"
    assert payload["resource_artifact_matrix"]["locked_resource_count"] == 1
    assert payload["resource_artifact_matrix"]["blocked_resource_count"] == 11
    assert payload["resource_artifact_matrix"]["failed_resource_count"] == 0
    assert payload["resource_artifact_matrix"]["evidence_entry_count"] == 0
    assert "reactome_full" in payload["resource_artifact_matrix"]["missing_resource_ids"]
    resource_artifact_rows = {row["resource_id"]: row for row in payload["resource_artifact_rows"]}
    assert resource_artifact_rows["mock_fixture_builtin_v1"]["status"] == "passed"
    assert resource_artifact_rows["reactome_full"]["status"] == "partial"
    assert resource_artifact_rows["reactome_full"]["version_status"] == "placeholder"
    assert resource_artifact_rows["gromacs_tool"]["required_for_modules"] == ["molecular_dynamics"]
    assert payload["standard_worker_entrypoint_matrix"]["schema_version"] == "biomedpilot.analysis.standard_worker_entrypoint_matrix.v1"
    assert payload["standard_worker_entrypoint_matrix"]["status"] == "partial"
    assert payload["standard_worker_entrypoint_matrix"]["passed_row_count"] == 5
    assert payload["standard_worker_entrypoint_matrix"]["partial_row_count"] == 1
    assert payload["standard_worker_entrypoint_matrix"]["blocked_row_count"] == 0
    assert payload["standard_worker_entrypoint_matrix"]["standard_entrypoint"] == "analysis/runners/run_module.R"
    assert "deg" in payload["standard_worker_entrypoint_matrix"]["lite_module_ids"]
    assert "survival" in payload["standard_worker_entrypoint_matrix"]["formal_pending_module_ids"]
    entrypoint_rows = {row["row_id"]: row for row in payload["standard_worker_entrypoint_rows"]}
    assert entrypoint_rows["standard_r_worker_cli_contract"]["status"] == "passed"
    assert entrypoint_rows["standard_r_worker_package_output_contract"]["status"] == "passed"
    assert entrypoint_rows["standard_r_worker_lite_dispatch_contract"]["status"] == "passed"
    assert entrypoint_rows["standard_r_worker_main_backend_invocation_contract"]["status"] == "passed"
    assert entrypoint_rows["standard_r_worker_no_runtime_acquisition"]["status"] == "passed"
    assert entrypoint_rows["standard_r_worker_formal_migration_boundary"]["status"] == "partial"
    assert payload["external_tool_adapter_matrix"]["schema_version"] == "biomedpilot.analysis.external_tool_adapter_matrix.v1"
    assert payload["external_tool_adapter_matrix"]["status"] == "passed"
    assert payload["external_tool_adapter_matrix"]["passed_module_count"] == 2
    assert payload["external_tool_adapter_matrix"]["blocked_module_count"] == 0
    external_tool_rows = {row["module_id"]: row for row in payload["external_tool_adapter_rows"]}
    assert external_tool_rows["docking"]["lite_external_tool_execution"] == "not_executed_in_lite_mode"
    assert external_tool_rows["docking"]["external_tool_policy"] == "R_adapter_calls_AutoDock_Vina_in_chem_environment_only"
    assert external_tool_rows["docking"]["full_environment"] == "r-chem-full"
    assert external_tool_rows["docking"]["required_resource_ids"] == ["autodock_vina_tool", "docking_template_bundle"]
    assert external_tool_rows["molecular_dynamics"]["external_tool_policy"] == "R_adapter_calls_GROMACS_in_chem_gpu_environment_only"
    assert external_tool_rows["molecular_dynamics"]["full_environment"] == "r-chem-gpu"
    assert external_tool_rows["molecular_dynamics"]["required_resource_ids"] == ["gromacs_tool", "md_forcefield_template_bundle"]
    assert external_tool_rows["molecular_dynamics"]["blockers"] == []
    assert payload["task_system_boundary_matrix"]["schema_version"] == "biomedpilot.analysis.task_system_boundary_matrix.v1"
    assert payload["task_system_boundary_matrix"]["status"] == "passed"
    assert payload["task_system_boundary_matrix"]["passed_module_count"] == 10
    assert payload["task_system_boundary_matrix"]["blocked_module_count"] == 0
    task_boundary_rows = {row["module_id"]: row for row in payload["task_system_boundary_rows"]}
    assert task_boundary_rows["deg"]["task_bridge_entrypoint"] == "app/analysis_runtime/task_bridge.py::run_analysis_module_task"
    assert task_boundary_rows["deg"]["required_task_system_invocation"] == "task_center_registered"
    assert task_boundary_rows["deg"]["worker_invocation_manifest_required"] is True
    assert task_boundary_rows["deg"]["result_index_task_types"] == ["deg", "recomputed_deg", "differential_expression"]
    assert task_boundary_rows["correlation"]["direct_cli_is_not_ui_task_result"] is True
    assert "legacy_sidecar_boundary_transitional:correlation" in task_boundary_rows["correlation"]["warnings"]
    assert payload["lite_task_bridge_coverage_matrix"]["schema_version"] == "biomedpilot.analysis.lite_task_bridge_coverage_matrix.v1"
    assert payload["lite_task_bridge_coverage_matrix"]["status"] == "passed"
    assert payload["lite_task_bridge_coverage_matrix"]["module_count"] == 10
    assert payload["lite_task_bridge_coverage_matrix"]["covered_module_count"] == 10
    assert payload["lite_task_bridge_coverage_matrix"]["blocked_module_count"] == 0
    assert payload["lite_task_bridge_coverage_matrix"]["blocker_counts"] == {}
    assert payload["lite_task_bridge_coverage_matrix"]["test_file"] == "tests/test_analysis_runtime_task_bridge.py"
    lite_coverage_rows = {row["module_id"]: row for row in payload["lite_task_bridge_coverage_rows"]}
    assert lite_coverage_rows["deg"]["status"] == "passed"
    assert lite_coverage_rows["deg"]["worker_backend"] == "rscript"
    assert lite_coverage_rows["deg"]["fixture_input_status"] == "present"
    assert lite_coverage_rows["molecular_dynamics"]["fixture_input_status"] == "present"
    assert lite_coverage_rows["molecular_dynamics"]["fixture_input"] == "analysis/fixtures/inputs/molecular_dynamics/module_input_lite.json"
    assert "standard_result_package validation passed" in lite_coverage_rows["deg"]["required_contracts"]
    assert "result_index registered testing_level result" in lite_coverage_rows["deg"]["required_contracts"]
    assert "report_ready_eligible false" in lite_coverage_rows["deg"]["required_contracts"]
    assert payload["legacy_sidecar_transition_matrix"]["schema_version"] == "biomedpilot.analysis.legacy_sidecar_transition_matrix.v1"
    assert payload["legacy_sidecar_transition_matrix"]["status"] == "partial"
    assert payload["legacy_sidecar_transition_matrix"]["passed_row_count"] == 5
    assert payload["legacy_sidecar_transition_matrix"]["partial_row_count"] == 1
    assert payload["legacy_sidecar_transition_matrix"]["blocked_row_count"] == 0
    assert payload["legacy_sidecar_transition_matrix"]["blocker_counts"] == {}
    assert payload["legacy_sidecar_transition_matrix"]["sidecar_producer_count"] == 6
    assert set(payload["legacy_sidecar_transition_matrix"]["transitional_module_ids"]) == {
        "correlation",
        "deg",
        "enrichment",
        "immune_infiltration",
        "survival",
    }
    assert "correlation" in payload["legacy_sidecar_transition_matrix"]["transitional_module_ids"]
    legacy_sidecar_rows = {row["row_id"]: row for row in payload["legacy_sidecar_transition_rows"]}
    assert legacy_sidecar_rows["legacy_sidecar_writer_contract"]["status"] == "passed"
    assert legacy_sidecar_rows["catalog_task_center_guard"]["status"] == "passed"
    assert legacy_sidecar_rows["migration_evidence_forbids_sidecar"]["status"] == "passed"
    assert legacy_sidecar_rows["registry_adapter_transition_scope"]["status"] == "passed"
    assert legacy_sidecar_rows["source_sidecar_producer_inventory"]["status"] == "partial"
    assert legacy_sidecar_rows["sidecar_boundary_test_coverage"]["status"] == "passed"
    assert payload["frontend_consumption_matrix"]["schema_version"] == "biomedpilot.analysis.frontend_standard_package_consumption_matrix.v1"
    assert payload["frontend_consumption_matrix"]["status"] == "passed"
    assert payload["frontend_consumption_matrix"]["passed_consumer_count"] == 5
    assert payload["frontend_consumption_matrix"]["partial_consumer_count"] == 0
    assert payload["frontend_consumption_matrix"]["pending_detail_view_count"] == 0
    assert payload["frontend_consumption_matrix"]["pending_detail_view_ids"] == []
    assert payload["frontend_consumption_matrix"]["migrated_detail_view_count"] == 3
    assert payload["frontend_consumption_matrix"]["migrated_detail_view_ids"] == ["formal_deg_review_panel", "formal_deg_plot_report_controls", "immune_tme_scoring_page"]
    frontend_rows = {row["row_id"]: row for row in payload["frontend_consumption_rows"]}
    assert frontend_rows["catalog_source_policy"]["status"] == "passed"
    assert frontend_rows["results_browser_tables"]["consumer_surface"] == "BioinformaticsResultsBrowserWidget"
    assert frontend_rows["detailed_result_views_migration"]["status"] == "passed"
    assert frontend_rows["detailed_result_views_migration"]["pending_detail_view_count"] == 0
    assert frontend_rows["detailed_result_views_migration"]["migrated_detail_view_ids"] == ["formal_deg_review_panel", "formal_deg_plot_report_controls", "immune_tme_scoring_page"]
    assert frontend_rows["detailed_result_views_migration"]["warnings"] == []
    assert payload["reproducibility_provenance_matrix"]["schema_version"] == "biomedpilot.analysis.reproducibility_provenance_matrix.v1"
    assert payload["reproducibility_provenance_matrix"]["status"] == "partial"
    assert payload["reproducibility_provenance_matrix"]["passed_row_count"] == 5
    assert payload["reproducibility_provenance_matrix"]["partial_row_count"] == 1
    assert payload["reproducibility_provenance_matrix"]["blocked_row_count"] == 0
    assert payload["reproducibility_provenance_matrix"]["blocker_counts"] == {}
    assert "input_hash" in payload["reproducibility_provenance_matrix"]["required_fields"]
    assert "package_versions" in payload["reproducibility_provenance_matrix"]["required_runtime_fields"]
    provenance_rows = {row["row_id"]: row for row in payload["reproducibility_provenance_rows"]}
    assert provenance_rows["provenance_payload_schema"]["status"] == "passed"
    assert provenance_rows["standard_package_validator_required_provenance"]["status"] == "passed"
    assert provenance_rows["task_bridge_provenance_writer"]["status"] == "passed"
    assert provenance_rows["standard_r_worker_provenance_writer"]["status"] == "passed"
    assert provenance_rows["worker_invocation_schema"]["status"] == "passed"
    assert provenance_rows["legacy_sidecar_provenance_boundary"]["status"] == "partial"
    assert provenance_rows["legacy_sidecar_provenance_boundary"]["warnings"] == [
        "legacy_service_adapter_sidecars_are_not_isolated_standard_worker_provenance_evidence"
    ]
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
    remediation_items = {item["item_id"]: item for item in payload["remediation_queue"]["items"]}
    environment_remediation = remediation_items["restore_full_analysis_environment_locks"]
    environment_actions = {item["environment_id"]: item for item in environment_remediation["environment_next_actions"]}
    assert environment_remediation["environment_action_summary"]["blocked_environment_count"] == len(environment_actions)
    assert environment_actions["r-bio-full"]["next_action"] == "register_schema_valid_restored_environment_evidence"
    assert environment_actions["r-chem-gpu"]["allowed_module_ids"] == ["molecular_dynamics"]
    resource_remediation = remediation_items["lock_full_analysis_resources"]
    resource_actions = {item["resource_id"]: item for item in resource_remediation["resource_next_actions"]}
    assert resource_remediation["resource_action_summary"]["blocked_resource_count"] == len(resource_actions)
    assert resource_actions["reactome_full"]["next_action"] == "register_schema_valid_prelocked_resource_evidence"
    assert resource_actions["gromacs_tool"]["required_for_modules"] == ["molecular_dynamics"]
    migration_remediation = remediation_items["migrate_formal_algorithms_to_isolated_standard_worker"]
    migration_actions = {item["module_id"]: item for item in migration_remediation["module_next_actions"]}
    assert migration_remediation["module_action_summary"]["blocked_module_count"] == len(migration_actions)
    assert migration_actions["deg"]["migration_next_action"] == "declare_scoped_full_mode_only_after_environment_and_resource_locks"
    assert migration_actions["univariate"]["migration_next_action"] == "declare_scoped_full_mode_only_after_environment_and_resource_locks"
    assert migration_actions["univariate"]["prerequisite_status"]["formal_runtime_contract"] == "available_or_not_required"
    assert payload["remediation_summary"]["minimal_remediation_path"] == [
        "restore_full_analysis_environment_locks",
        "lock_full_analysis_resources",
        "migrate_formal_algorithms_to_isolated_standard_worker",
    ]
    decisions = {item["item_id"]: item for item in payload["remediation_summary"]["manual_decision_points"]}
    assert decisions["migrate_formal_algorithms_to_isolated_standard_worker"]["scope"].startswith("missing=10; passed=0; blocked=0")
    assert "modules=deg, survival, univariate, multivariate, enrichment" in decisions["migrate_formal_algorithms_to_isolated_standard_worker"]["scope"]
    assert (
        decisions["restore_full_analysis_environment_locks"]["environment_action_summary"]["next_action_counts"][
            "register_schema_valid_restored_environment_evidence"
        ]
        >= 1
    )
    assert (
        decisions["migrate_formal_algorithms_to_isolated_standard_worker"]["module_action_summary"]["next_action_counts"][
            "declare_scoped_full_mode_only_after_environment_and_resource_locks"
        ]
        >= 1
    )
    assert (
        decisions["lock_full_analysis_resources"]["resource_action_summary"]["next_action_counts"][
            "register_schema_valid_prelocked_resource_evidence"
        ]
        >= 1
    )
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
    assert payload["standard_worker_migration_matrix"]["adapter_status_counts"][
        "existing_controlled_python_and_r_contracts_pending_standard_worker_migration"
    ] == 1
    assert payload["standard_worker_migration_matrix"]["migration_next_action_counts"][
        "declare_scoped_full_mode_only_after_environment_and_resource_locks"
    ] == payload["standard_worker_migration_matrix"]["module_count"]
    assert payload["standard_worker_migration_matrix"]["migration_blocker_counts"][
        "registry_evidence_entry_missing_or_blocked"
    ] == payload["standard_worker_migration_matrix"]["module_count"]
    assert payload["full_activation_module_matrix"]["status"] == "blocked"
    assert payload["full_activation_module_matrix"]["blocked_module_count"] == 10
    assert payload["full_activation_module_matrix"]["blocker_counts"]["full_mode_not_supported_in_registry"] == 10
    full_rows = {row["module_id"]: row for row in payload["full_activation_module_rows"]}
    assert full_rows["deg"]["resource_status"] == "not_required"
    assert full_rows["enrichment"]["resource_status"] == "blocked"
    assert "analysis_resource_not_locked:reactome_full" in full_rows["enrichment"]["blockers"]
    assert full_rows["molecular_dynamics"]["full_environment"] == "r-chem-gpu"
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
    assert migration_rows["univariate"]["migration_next_action"] == "declare_scoped_full_mode_only_after_environment_and_resource_locks"
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
    assert "Runtime Boundary Scan Evidence" in text
    assert "Module Interface Matrix" in text
    assert "Standard Worker Entrypoint Matrix" in text
    assert "External Tool Adapter Isolation Matrix" in text
    assert "Task System Boundary Matrix" in text
    assert "Lite Task Bridge Coverage Matrix" in text
    assert "Legacy Sidecar Transition Matrix" in text
    assert "Frontend Standard Package Consumption Matrix" in text
    assert "Reproducibility Provenance Matrix" in text
    assert "mock=True; lite=True; full=False" in text
    assert "standard_r_worker_lite_dispatch_contract" in text
    assert "standard_worker_entrypoint_formal_migration_pending:deg" in text
    assert "not_executed_in_lite_mode" in text
    assert "R_adapter_calls_AutoDock_Vina_in_chem_environment_only" in text
    assert "R_adapter_calls_GROMACS_in_chem_gpu_environment_only" in text
    assert "task_center_registered" in text
    assert "test_all_registered_lite_modules_run_through_standard_r_worker_package_contract" in text
    assert "standard_result_package validation passed" in text
    assert "report_ready_eligible false" in text
    assert "pending_standard_worker_migration" in text
    assert "legacy_sidecar_writer_contract" in text
    assert "legacy_sidecar_producer_transitional:correlation" in text
    assert "Frontend Standard Package Consumption Matrix" in text
    assert "Migrated detail views | 3 | formal_deg_review_panel, formal_deg_plot_report_controls, immune_tme_scoring_page" in text
    assert "standard_r_worker_provenance_writer" in text
    assert "package_versions" in text
    assert "legacy_service_adapter_sidecars_are_not_isolated_standard_worker_provenance_evidence" in text
    assert "Runtime package install" in text
    assert "Runtime resource download" in text
    assert "Default app-dev heavy dependency" in text
    assert "runtime_package_install_and_resource_download_forbidden_in_active_app_analysis_scripts_config" in text
    assert "heavy_full_analysis_dependencies_excluded_from_default_app_dev_surface" in text
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
    assert template_package["full_activation_module_matrix"]["schema_version"] == "biomedpilot.analysis.full_activation_module_matrix.v1"
    assert template_package["full_activation_module_matrix"]["status"] == "blocked"
    assert template_package["full_activation_module_matrix"]["blocked_module_count"] == 10
    assert template_package["full_activation_module_matrix"]["boundary"] == "read_only_module_level_full_activation_diagnostics"
    full_activation_rows = {
        item["module_id"]: item
        for item in template_package["full_activation_module_rows"]
    }
    assert full_activation_rows["deg"]["resource_status"] == "not_required"
    assert full_activation_rows["enrichment"]["resource_status"] == "blocked"
    assert "analysis_resource_not_locked:reactome_full" in full_activation_rows["enrichment"]["blockers"]
    assert full_activation_rows["molecular_dynamics"]["full_environment"] == "r-chem-gpu"
    remediation_actions = template_package["remediation_actions"]
    assert remediation_actions["schema_version"] == "biomedpilot.analysis.evidence_template_remediation_actions.v1"
    assert remediation_actions["action_policy"] == "planning_only_not_readiness_evidence"
    assert remediation_actions["environment_action_summary"]["blocked_environment_count"] == 4
    assert remediation_actions["resource_action_summary"]["blocked_resource_count"] == 11
    assert remediation_actions["module_action_summary"]["blocked_module_count"] == 10
    environment_actions = {item["environment_id"]: item for item in remediation_actions["environment_next_actions"]}
    resource_actions = {item["resource_id"]: item for item in remediation_actions["resource_next_actions"]}
    module_actions = {item["module_id"]: item for item in remediation_actions["module_next_actions"]}
    assert environment_actions["r-bio-full"]["next_action"] == "register_schema_valid_restored_environment_evidence"
    assert resource_actions["reactome_full"]["next_action"] == "register_schema_valid_prelocked_resource_evidence"
    assert module_actions["deg"]["migration_next_action"] == "declare_scoped_full_mode_only_after_environment_and_resource_locks"
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
    assert "Full Activation Module Matrix" in text
    assert "Full activation" not in text  # section is summary-only, no UI labels in report
    assert "analysis_resource_not_locked:reactome_full" in text
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
    assert "module_interface_matrix" in schema["required"]
    assert "module_interface_rows" in schema["required"]
    assert "module_mode_readiness_matrix" in schema["required"]
    assert "module_mode_readiness_rows" in schema["required"]
    assert "environment_artifact_matrix" in schema["required"]
    assert "environment_artifact_rows" in schema["required"]
    assert "resource_artifact_matrix" in schema["required"]
    assert "resource_artifact_rows" in schema["required"]
    assert "standard_worker_entrypoint_matrix" in schema["required"]
    assert "standard_worker_entrypoint_rows" in schema["required"]
    assert "external_tool_adapter_matrix" in schema["required"]
    assert "external_tool_adapter_rows" in schema["required"]
    assert "task_system_boundary_matrix" in schema["required"]
    assert "task_system_boundary_rows" in schema["required"]
    assert "lite_task_bridge_coverage_matrix" in schema["required"]
    assert "lite_task_bridge_coverage_rows" in schema["required"]
    assert "legacy_sidecar_transition_matrix" in schema["required"]
    assert "legacy_sidecar_transition_rows" in schema["required"]
    assert "frontend_consumption_matrix" in schema["required"]
    assert "frontend_consumption_rows" in schema["required"]
    assert "reproducibility_provenance_matrix" in schema["required"]
    assert "reproducibility_provenance_rows" in schema["required"]
    assert "runtime_acquisition_scan" in schema["required"]
    assert "default_dependency_scan" in schema["required"]
    assert "environment_readiness" in schema["required"]
    assert "resource_readiness" in schema["required"]
    assert "standard_worker_migration_matrix" in schema["required"]
    assert "full_activation_module_matrix" in schema["required"]
    assert "full_activation_module_rows" in schema["required"]
    assert "standard_worker_migration_rows" in schema["required"]
    assert "remediation_queue" in schema["required"]
    assert "remediation_summary" in schema["required"]
    assert schema["properties"]["schema_version"]["const"] == "biomedpilot.analysis.architecture_gate_report.v1"
    assert schema["properties"]["execution_policy"]["const"] == "read_only_no_worker_execution_no_runtime_install_no_resource_download"
    assert schema["properties"]["module_interface_matrix"]["type"] == "object"
    assert schema["properties"]["module_interface_rows"]["type"] == "array"
    assert schema["properties"]["module_mode_readiness_matrix"]["type"] == "object"
    assert schema["properties"]["module_mode_readiness_rows"]["type"] == "array"
    assert schema["properties"]["environment_artifact_matrix"]["type"] == "object"
    assert schema["properties"]["environment_artifact_rows"]["type"] == "array"
    assert schema["properties"]["resource_artifact_matrix"]["type"] == "object"
    assert schema["properties"]["resource_artifact_rows"]["type"] == "array"
    assert schema["properties"]["standard_worker_entrypoint_matrix"]["type"] == "object"
    assert schema["properties"]["standard_worker_entrypoint_rows"]["type"] == "array"
    assert schema["properties"]["external_tool_adapter_matrix"]["type"] == "object"
    assert schema["properties"]["external_tool_adapter_rows"]["type"] == "array"
    assert schema["properties"]["task_system_boundary_matrix"]["type"] == "object"
    assert schema["properties"]["task_system_boundary_rows"]["type"] == "array"
    assert schema["properties"]["lite_task_bridge_coverage_matrix"]["type"] == "object"
    assert schema["properties"]["lite_task_bridge_coverage_rows"]["type"] == "array"
    assert schema["properties"]["legacy_sidecar_transition_matrix"]["type"] == "object"
    assert schema["properties"]["legacy_sidecar_transition_rows"]["type"] == "array"
    assert schema["properties"]["frontend_consumption_matrix"]["type"] == "object"
    assert schema["properties"]["frontend_consumption_rows"]["type"] == "array"
    assert schema["properties"]["reproducibility_provenance_matrix"]["type"] == "object"
    assert schema["properties"]["reproducibility_provenance_rows"]["type"] == "array"
    assert schema["properties"]["runtime_acquisition_scan"]["type"] == "object"
    assert schema["properties"]["default_dependency_scan"]["type"] == "object"
    assert schema["properties"]["full_activation_module_matrix"]["type"] == "object"
    assert schema["properties"]["full_activation_module_rows"]["type"] == "array"


def test_analysis_evidence_template_package_schema_is_present_and_matches_payload_contract() -> None:
    schema = json.loads((ROOT / "analysis" / "schemas" / "output" / "evidence_template_package.schema.json").read_text(encoding="utf-8"))

    assert schema["$id"] == "biomedpilot.analysis.evidence_template_package.v1"
    assert "environment_lock_evidence_templates" in schema["required"]
    assert "resource_lock_evidence_templates" in schema["required"]
    assert "standard_worker_migration_evidence_templates" in schema["required"]
    assert "full_activation_module_matrix" in schema["required"]
    assert "full_activation_module_rows" in schema["required"]
    assert "template_policy" in schema["required"]
    assert "registry_paths" in schema["required"]
    assert "expected_evidence_scope" in schema["required"]
    assert "template_counts" in schema["required"]
    assert "remediation_actions" in schema["required"]
    assert schema["properties"]["remediation_scope"]["type"] == "object"
    assert schema["properties"]["remediation_actions"]["type"] == "object"
    assert schema["properties"]["expected_evidence_scope"]["type"] == "object"
    assert schema["properties"]["full_activation_module_matrix"]["type"] == "object"
    assert schema["properties"]["full_activation_module_rows"]["type"] == "array"
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
            "full_activation_module_matrix": {},
            "full_activation_module_rows": [],
            "blockers": {},
            "remediation_actions": {},
            "template_counts": {},
        },
        root=ROOT,
    )

    assert "analysis_evidence_template_package_environment_template_renv_lock_content_missing:r-bio-full" in blockers
    assert "analysis_evidence_template_package_environment_template_docker_image_missing:r-bio-full" in blockers
    assert "analysis_evidence_template_package_resource_template_cache_content_missing:reactome_full" in blockers
    assert "analysis_evidence_template_package_full_activation_module_matrix_schema_version_invalid" in blockers
    assert "analysis_evidence_template_package_full_activation_module_matrix_boundary_invalid" in blockers
    assert "analysis_evidence_template_package_full_activation_module_rows_missing" in blockers
    assert "analysis_evidence_template_package_remediation_actions_schema_version_invalid" in blockers
    assert "analysis_evidence_template_package_remediation_actions_policy_invalid" in blockers
    assert "analysis_evidence_template_package_remediation_actions_invalid:environment_next_actions" in blockers
    assert "analysis_evidence_template_package_expected_scope_policy_invalid" in blockers
    assert "analysis_evidence_template_package_expected_scope_invalid:expected_environment_ids" in blockers
