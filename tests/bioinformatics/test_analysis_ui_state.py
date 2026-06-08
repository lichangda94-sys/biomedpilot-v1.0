from __future__ import annotations

import json
import shutil
from pathlib import Path

from app.analysis_runtime import run_analysis_module_task
from app.bioinformatics.analysis_ui.state import build_analysis_center_state, build_dependency_rows
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import load_registry, register_result, save_registry


def test_analysis_center_state_comes_from_b8_contracts_and_has_no_side_effects(tmp_path: Path) -> None:
    matrix = tmp_path / "expr.tsv"
    matrix.write_text("gene_id\tS1\tS2\nTP53\t10\t20\n", encoding="utf-8")
    sample = tmp_path / "sample.tsv"
    sample.write_text("sample_id\tgroup\nS1\tcase\nS2\tcontrol\n", encoding="utf-8")
    assets = [
        _asset("expr", "raw_count_matrix", "expression_repository", matrix, value_type="count", gene_id_type="symbol"),
        _asset("sample", "sample_metadata", "sample_metadata_repository", sample),
        _asset("group", "group_design", "group_design_repository", tmp_path / "group.json"),
    ]
    _write_standardized_state(tmp_path, assets, default_expression="expr")
    before = _file_set(tmp_path)

    state = build_analysis_center_state(tmp_path)

    assert state["resolver_source"]["source_policy"] == "standardized repository / registry / analysis_input_repository only"
    assert "recognition_report.json" not in json.dumps(state["resolver_source"], ensure_ascii=False)
    assert state["package_rows"]
    assert state["action_rows"]
    assert state["dependency_rows"]
    assert state["gate_rows"]
    assert state["enrichment_gate_rows"]
    assert state["analysis_architecture_gate_rows"]
    assert state["module_interface_rows"]
    assert state["module_mode_readiness_rows"]
    assert state["environment_artifact_rows"]
    assert state["full_activation_module_rows"]
    assert state["standard_worker_migration_rows"]
    assert state["analysis_architecture_remediation_rows"]
    assert state["analysis_environment_gate_rows"]
    assert state["analysis_resource_gate_rows"]
    assert state["survival_clinical_rows"]
    assert _file_set(tmp_path) == before

    formal_deg = _action(state, "formal_deg")
    assert formal_deg["enabled"] is False
    assert any(
        reason in formal_deg["disabled_reason"]
        for reason in ("missing_python_package:scipy", "formal_deg_parameter_confirmation_missing")
    )
    assert _action(state, "formal_gsea")["enabled"] is False
    assert _action(state, "controlled_ora")["enabled"] is False
    assert _action(state, "controlled_gsea_preranked")["enabled"] is False
    assert _action(state, "km_cox_logrank")["enabled"] is False
    assert _action(state, "report_ready_export")["state"] == "blocked_report_ready_gate"
    formal_gate_text = "\n".join(str(row) for row in state["formal_deg_gate_rows"])
    assert "DEG real-project input adaptation" in formal_gate_text
    assert "DEG batch/design QA" in formal_gate_text
    assert "DEG data quality / repair guidance" in formal_gate_text
    assert "DEG method recommendation" in formal_gate_text
    assert "Parameter manifest" in formal_gate_text
    assert "Result schema gate" in formal_gate_text
    assert "B9.2 controlled activation" in formal_gate_text
    multifactor_gate_text = "\n".join(str(row) for row in state["multifactor_deg_gate_rows"])
    assert "Multi-factor design QA" in multifactor_gate_text
    assert "Multi-factor contrast" in multifactor_gate_text
    assert "Multi-factor R dependency" in multifactor_gate_text
    assert "Multi-factor user confirmation" in multifactor_gate_text
    enrichment_gate_text = "\n".join(str(row) for row in state["enrichment_gate_rows"])
    assert "Enrichment resource lock" in enrichment_gate_text
    assert "Enrichment library capability" in enrichment_gate_text
    assert "Enrichment background universe" in enrichment_gate_text
    assert "Enrichment identifier compatibility" in enrichment_gate_text
    assert "Enrichment statistical policy" in enrichment_gate_text
    assert "ORA execution gate" in enrichment_gate_text
    assert "Preranked GSEA execution gate" in enrichment_gate_text
    assert "Enrichment result schema" in enrichment_gate_text
    assert "Enrichment section report" in enrichment_gate_text
    assert "Enrichment production audit package" in enrichment_gate_text
    assert "Enrichment cross-library acceptance" in enrichment_gate_text
    environment_gate_text = "\n".join(str(row) for row in state["analysis_environment_gate_rows"])
    assert "Analysis environment registry" in environment_gate_text
    assert "Full R environment readiness" in environment_gate_text
    assert "analysis_environment_renv_lock_not_restored:r-bio-full:scaffold_only_not_restored" in environment_gate_text
    resource_gate_text = "\n".join(str(row) for row in state["analysis_resource_gate_rows"])
    assert "Analysis resource manifest" in resource_gate_text
    assert "Full analysis resource lock evidence registry" in resource_gate_text
    assert "Full analysis resource readiness" in resource_gate_text
    assert "analysis_resource_not_locked:reactome_full" in resource_gate_text
    assert "missing_resource=reactome_full" in resource_gate_text
    assert "locked_resources=mock_fixture_builtin_v1" in resource_gate_text
    assert "blocked_resources=reactome_full" in resource_gate_text
    architecture_gate_text = "\n".join(str(row) for row in state["analysis_architecture_gate_rows"])
    assert "R analysis architecture snapshot" in architecture_gate_text
    assert "R architecture P0 guard" in architecture_gate_text
    assert "Full analysis activation gate" in architecture_gate_text
    assert "full_analysis_environment_locks_not_ready" in architecture_gate_text
    assert "full_analysis_resource_locks_not_ready" in architecture_gate_text
    assert "full_analysis_standard_worker_migration_incomplete" in architecture_gate_text
    assert "partial_with_p1_gaps" in architecture_gate_text
    assert "Runtime acquisition scan" in architecture_gate_text
    assert "runtime_package_install_and_resource_download_forbidden_in_active_app_analysis_scripts_config" in architecture_gate_text
    assert "roots=app；analysis；scripts；config" in architecture_gate_text
    assert "Default dependency scan" in architecture_gate_text
    assert "heavy_full_analysis_dependencies_excluded_from_default_app_dev_surface" in architecture_gate_text
    assert "files=requirements.txt；pyproject.toml；docker/Dockerfile.app-dev；renv/renv.app.lock" in architecture_gate_text
    architecture_status = state["developer_diagnostics"]["analysis_architecture_status"]
    assert architecture_status["requirement_summary"]["requirement_count"] == 20
    assert "RARCH-03" in architecture_status["p2_issues"]
    assert "RARCH-15" in architecture_status["p3_issues"]
    assert architecture_status["top_architecture_risks"][0]["risk_id"] == "full_analysis_environment_locks_not_restored"
    module_interface_text = "\n".join(str(row) for row in state["module_interface_rows"])
    assert "Analysis module interface matrix" in module_interface_text
    assert "passed=10" in module_interface_text
    assert "blocked=0" in module_interface_text
    assert "Module interface: deg" in module_interface_text
    assert "mock=True" in module_interface_text
    assert "lite=True" in module_interface_text
    assert "full=False" in module_interface_text
    assert "fixture=passed" in module_interface_text
    assert "analysis/modules/deg/module.json" in module_interface_text
    assert "r-bio-core->r-chem-gpu" in module_interface_text
    mode_readiness_text = "\n".join(str(row) for row in state["module_mode_readiness_rows"])
    assert "Analysis module mode readiness matrix" in mode_readiness_text
    assert "partial=10" in mode_readiness_text
    assert "blocked=0" in mode_readiness_text
    assert "full_blocked_modules=deg；survival；univariate；multivariate；enrichment" in mode_readiness_text
    assert "Mode readiness: deg" in mode_readiness_text
    assert "mock=passed" in mode_readiness_text
    assert "lite=passed" in mode_readiness_text
    assert "full=blocked" in mode_readiness_text
    assert "lite_env=r-bio-core" in mode_readiness_text
    assert "full_env=r-chem-gpu" in mode_readiness_text
    assert "module_full_mode_blocked:deg" in mode_readiness_text
    environment_artifact_text = "\n".join(str(row) for row in state["environment_artifact_rows"])
    assert "Analysis environment artifact matrix" in environment_artifact_text
    assert "passed=2" in environment_artifact_text
    assert "partial=4" in environment_artifact_text
    assert "blocked=0" in environment_artifact_text
    assert "full_envs=r-bio-full；r-spatial-full；r-chem-full；r-chem-gpu" in environment_artifact_text
    assert "Environment artifact: app-dev" in environment_artifact_text
    assert "Environment artifact: r-bio-full" in environment_artifact_text
    assert "docker=present:docker/Dockerfile.r-bio-full" in environment_artifact_text
    assert "renv=present:renv/renv.bio-full.lock" in environment_artifact_text
    assert "renv_status=scaffold_only_not_restored" in environment_artifact_text
    assert "analysis_environment_renv_lock_not_restored:r-bio-full:scaffold_only_not_restored" in environment_artifact_text
    resource_artifact_text = "\n".join(str(row) for row in state["resource_artifact_rows"])
    assert "Analysis resource artifact matrix" in resource_artifact_text
    assert "locked=1" in resource_artifact_text
    assert "blocked_full=11" in resource_artifact_text
    assert "evidence_entries=0" in resource_artifact_text
    assert "Resource artifact: mock_fixture_builtin_v1" in resource_artifact_text
    assert "Resource artifact: reactome_full" in resource_artifact_text
    assert "version=placeholder" in resource_artifact_text
    assert "hash=placeholder" in resource_artifact_text
    assert "license=placeholder" in resource_artifact_text
    assert "evidence=missing:" in resource_artifact_text
    assert "resource_full_lock_not_ready:reactome_full" in resource_artifact_text
    assert "resource_lock_evidence_registry_entry_missing:gromacs_tool" in resource_artifact_text
    entrypoint_text = "\n".join(str(row) for row in state["standard_worker_entrypoint_rows"])
    assert "Standard R worker entrypoint matrix" in entrypoint_text
    assert "passed=5" in entrypoint_text
    assert "partial=1" in entrypoint_text
    assert "blocked=0" in entrypoint_text
    assert "lite_modules=deg；survival；univariate；multivariate；enrichment" in entrypoint_text
    assert "Standard R worker contract: standard_r_worker_cli_contract" in entrypoint_text
    assert "Standard R worker contract: standard_r_worker_lite_dispatch_contract" in entrypoint_text
    assert "Standard R worker contract: standard_r_worker_formal_migration_boundary" in entrypoint_text
    assert "standard_worker_entrypoint_formal_migration_pending:deg" in entrypoint_text
    assert "entrypoint_contract_is_not_formal_full_migration_evidence" in entrypoint_text
    external_tool_text = "\n".join(str(row) for row in state["external_tool_adapter_rows"])
    assert "External tool adapter isolation matrix" in external_tool_text
    assert "passed=2" in external_tool_text
    assert "blocked=0" in external_tool_text
    assert "External tool adapter: docking" in external_tool_text
    assert "External tool adapter: molecular_dynamics" in external_tool_text
    assert "exec=not_executed_in_lite_mode" in external_tool_text
    assert "full=r-chem-full" in external_tool_text
    assert "full=r-chem-gpu" in external_tool_text
    assert "resources=autodock_vina_tool；docking_template_bundle" in external_tool_text
    assert "resources=gromacs_tool；md_forcefield_template_bundle" in external_tool_text
    assert "R_adapter_calls_AutoDock_Vina_in_chem_environment_only" in external_tool_text
    assert "R_adapter_calls_GROMACS_in_chem_gpu_environment_only" in external_tool_text
    assert "default_app_dependency=False" in external_tool_text
    task_boundary_text = "\n".join(str(row) for row in state["task_system_boundary_rows"])
    assert "Task system boundary matrix" in task_boundary_text
    assert "passed=10" in task_boundary_text
    assert "blocked=0" in task_boundary_text
    assert "Task boundary: deg" in task_boundary_text
    assert "Task boundary: correlation" in task_boundary_text
    assert "task_invocation=task_center_registered" in task_boundary_text
    assert "worker_manifest=True" in task_boundary_text
    assert "mock=True" in task_boundary_text
    assert "lite=True" in task_boundary_text
    assert "run_analysis_module_task" in task_boundary_text
    assert "task_types=deg；recomputed_deg；differential_expression" in task_boundary_text
    assert "formal_worker=pending_standard_worker_migration" in task_boundary_text
    lite_coverage_text = "\n".join(str(row) for row in state["lite_task_bridge_coverage_rows"])
    assert "Lite task bridge coverage matrix" in lite_coverage_text
    assert "covered=10" in lite_coverage_text
    assert "blocked=0" in lite_coverage_text
    assert "tests/test_analysis_runtime_task_bridge.py" in lite_coverage_text
    assert "Lite task bridge coverage: deg" in lite_coverage_text
    assert "Lite task bridge coverage: molecular_dynamics" in lite_coverage_text
    assert "fixture=present:analysis/fixtures/inputs/deg/module_input_lite.json" in lite_coverage_text
    assert "worker=rscript" in lite_coverage_text
    assert "test_all_registered_lite_modules_run_through_standard_r_worker_package_contract" in lite_coverage_text
    assert "standard_result_package validation passed" in lite_coverage_text
    assert "result_index registered testing_level result" in lite_coverage_text
    sidecar_text = "\n".join(str(row) for row in state["legacy_sidecar_transition_rows"])
    assert "Legacy sidecar transition matrix" in sidecar_text
    assert "passed=4" in sidecar_text
    assert "partial=1" in sidecar_text
    assert "blocked=0" in sidecar_text
    assert "transitional_modules=10" in sidecar_text
    assert "Legacy sidecar contract: legacy_sidecar_writer_contract" in sidecar_text
    assert "Legacy sidecar contract: catalog_task_center_guard" in sidecar_text
    assert "Legacy sidecar contract: migration_evidence_forbids_sidecar" in sidecar_text
    assert "Legacy sidecar contract: registry_adapter_transition_scope" in sidecar_text
    assert "registry_current_adapter_status_transitional:deg" in sidecar_text
    assert "adapter_status_is_inventory_only_not_worker_migration_evidence" in sidecar_text
    frontend_consumption_text = "\n".join(str(row) for row in state["frontend_consumption_rows"])
    assert "Frontend standard package consumption matrix" in frontend_consumption_text
    assert "passed=4" in frontend_consumption_text
    assert "partial=1" in frontend_consumption_text
    assert "blocked=0" in frontend_consumption_text
    assert "Frontend standard package consumer: catalog_source_policy" in frontend_consumption_text
    assert "Frontend standard package consumer: results_browser_tables" in frontend_consumption_text
    assert "Frontend standard package consumer: detailed_result_views_migration" in frontend_consumption_text
    assert "detailed_result_views_still_need_standard_package_only_migration" in frontend_consumption_text
    assert "consume_result_index_registered_standard_result_packages_only" in frontend_consumption_text
    provenance_text = "\n".join(str(row) for row in state["reproducibility_provenance_rows"])
    assert "Reproducibility provenance matrix" in provenance_text
    assert "passed=5" in provenance_text
    assert "partial=1" in provenance_text
    assert "blocked=0" in provenance_text
    assert "field:input_hash" in provenance_text
    assert "field:parameter_hash" in provenance_text
    assert "field:random_seed" in provenance_text
    assert "runtime:package_versions" in provenance_text
    assert "runtime:external_tool_versions" in provenance_text
    assert "Provenance contract: standard_r_worker_provenance_writer" in provenance_text
    assert "Provenance contract: legacy_sidecar_provenance_boundary" in provenance_text
    assert "legacy_service_adapter_sidecars_are_not_isolated_standard_worker_provenance_evidence" in provenance_text
    full_activation_text = "\n".join(str(row) for row in state["full_activation_module_rows"])
    assert "Full analysis module activation matrix" in full_activation_text
    assert "Full activation: deg" in full_activation_text
    assert "Full activation: enrichment" in full_activation_text
    assert "analysis_full_environment_lock_not_restored:r-bio-full=7" in full_activation_text
    assert "analysis_resource_not_locked:reactome_full=1" in full_activation_text
    assert "resources=not_required" in full_activation_text
    assert "resources=blocked" in full_activation_text
    assert "r-bio-core->r-chem-gpu" in full_activation_text
    worker_migration_text = "\n".join(str(row) for row in state["standard_worker_migration_rows"])
    assert "R standard worker migration matrix" in worker_migration_text
    assert "R worker migration evidence coverage" in worker_migration_text
    assert "R worker migration adapter status summary" in worker_migration_text
    assert "adapter:existing_controlled_python_and_r_contracts_pending_standard_worker_migration=1" in worker_migration_text
    assert "adapter:r_native_lite_contract_exists_pending_full_environment_and_standard_worker_migration=2" in worker_migration_text
    assert "next:declare_scoped_full_mode_only_after_environment_and_resource_locks=10" in worker_migration_text
    assert "registry_evidence_entry_missing_or_blocked=10" in worker_migration_text
    assert "missing_standard_worker_migration_evidence:deg" in worker_migration_text
    assert "missing_standard_worker_migration_evidence:molecular_dynamics" in worker_migration_text
    assert "R worker migration: deg" in worker_migration_text
    assert "pending_standard_worker_migration" in worker_migration_text
    assert "standard_worker_lite_ready" in worker_migration_text
    assert "declare_scoped_full_mode_only_after_environment_and_resource_locks" in worker_migration_text
    assert "implement_formal_runtime_contract_before_standard_worker_migration" not in worker_migration_text
    remediation_text = "\n".join(str(row) for row in state["analysis_architecture_remediation_rows"])
    assert "R architecture remediation queue" in remediation_text
    assert "R evidence template handoff preview" in remediation_text
    assert "environment_actions=4" in remediation_text
    assert "resource_actions=11" in remediation_text
    assert "module_actions=10" in remediation_text
    assert "planning_only_not_readiness_evidence" in remediation_text
    assert "scripts/analysis_architecture_gate.py --evidence-template-output <path>" in remediation_text
    assert "restore_full_analysis_environment_locks" in remediation_text
    assert "r-bio-full:register_schema_valid_restored_environment_evidence" in remediation_text
    assert "register_schema_valid_restored_environment_evidence=4" in remediation_text
    assert "lock_full_analysis_resources" in remediation_text
    assert "reactome_full:register_schema_valid_prelocked_resource_evidence" in remediation_text
    assert "register_schema_valid_prelocked_resource_evidence=11" in remediation_text
    assert "migrate_formal_algorithms_to_isolated_standard_worker" in remediation_text
    assert "deg:declare_scoped_full_mode_only_after_environment_and_resource_locks" in remediation_text
    assert "univariate:declare_scoped_full_mode_only_after_environment_and_resource_locks" in remediation_text
    assert "implement_formal_runtime_contract_before_standard_worker_migration" not in remediation_text
    assert "missing_modules=10" in remediation_text
    assert "missing_module:deg" in remediation_text
    assert "missing_module:enrichment" in remediation_text
    assert state["developer_diagnostics"]["analysis_architecture_status"]["p0_issues"] == []
    assert "full_analysis_environment_locks_not_restored" in state["developer_diagnostics"]["analysis_architecture_status"]["p1_issues"]
    activation_gate = state["developer_diagnostics"]["analysis_architecture_status"]["full_analysis_activation_gate"]
    assert activation_gate["status"] == "blocked"
    assert activation_gate["blockers"] == [
        "full_analysis_environment_locks_not_ready",
        "full_analysis_resource_locks_not_ready",
        "full_analysis_standard_worker_migration_incomplete",
    ]
    remediation_queue = state["developer_diagnostics"]["analysis_architecture_remediation_queue"]
    assert remediation_queue["status"] == "open"
    assert remediation_queue["execution_policy"] == "read_only_no_runtime_mutation"
    assert remediation_queue["item_count"] == 3
    assert remediation_queue["schema_validation_status"] == "passed"
    assert remediation_queue["schema_blockers"] == []
    assert state["developer_diagnostics"]["analysis_architecture_gate_rows"] == state["analysis_architecture_gate_rows"]
    assert state["developer_diagnostics"]["module_interface_matrix"]["status"] == "passed"
    assert state["developer_diagnostics"]["module_interface_matrix"]["passed_module_count"] == 10
    assert state["developer_diagnostics"]["module_interface_rows"] == state["module_interface_rows"]
    assert state["developer_diagnostics"]["module_mode_readiness_matrix"]["status"] == "partial"
    assert state["developer_diagnostics"]["module_mode_readiness_matrix"]["partial_module_count"] == 10
    assert state["developer_diagnostics"]["module_mode_readiness_rows"] == state["module_mode_readiness_rows"]
    assert state["developer_diagnostics"]["environment_artifact_matrix"]["status"] == "partial"
    assert state["developer_diagnostics"]["environment_artifact_matrix"]["partial_environment_count"] == 4
    assert state["developer_diagnostics"]["environment_artifact_rows"] == state["environment_artifact_rows"]
    assert state["developer_diagnostics"]["resource_artifact_matrix"]["status"] == "partial"
    assert state["developer_diagnostics"]["resource_artifact_matrix"]["blocked_resource_count"] == 11
    assert state["developer_diagnostics"]["resource_artifact_rows"] == state["resource_artifact_rows"]
    assert state["developer_diagnostics"]["standard_worker_entrypoint_matrix"]["status"] == "partial"
    assert state["developer_diagnostics"]["standard_worker_entrypoint_matrix"]["passed_row_count"] == 5
    assert state["developer_diagnostics"]["standard_worker_entrypoint_rows"] == state["standard_worker_entrypoint_rows"]
    assert state["developer_diagnostics"]["external_tool_adapter_matrix"]["status"] == "passed"
    assert state["developer_diagnostics"]["external_tool_adapter_matrix"]["passed_module_count"] == 2
    assert state["developer_diagnostics"]["external_tool_adapter_rows"] == state["external_tool_adapter_rows"]
    assert state["developer_diagnostics"]["task_system_boundary_matrix"]["status"] == "passed"
    assert state["developer_diagnostics"]["task_system_boundary_matrix"]["passed_module_count"] == 10
    assert state["developer_diagnostics"]["task_system_boundary_rows"] == state["task_system_boundary_rows"]
    assert state["developer_diagnostics"]["lite_task_bridge_coverage_matrix"]["status"] == "passed"
    assert state["developer_diagnostics"]["lite_task_bridge_coverage_matrix"]["covered_module_count"] == 10
    assert state["developer_diagnostics"]["lite_task_bridge_coverage_matrix"]["blocked_module_count"] == 0
    assert state["developer_diagnostics"]["lite_task_bridge_coverage_rows"] == state["lite_task_bridge_coverage_rows"]
    assert state["developer_diagnostics"]["legacy_sidecar_transition_matrix"]["status"] == "partial"
    assert state["developer_diagnostics"]["legacy_sidecar_transition_matrix"]["partial_row_count"] == 1
    assert state["developer_diagnostics"]["legacy_sidecar_transition_rows"] == state["legacy_sidecar_transition_rows"]
    assert state["developer_diagnostics"]["frontend_consumption_matrix"]["status"] == "partial"
    assert state["developer_diagnostics"]["frontend_consumption_matrix"]["partial_consumer_count"] == 1
    assert state["developer_diagnostics"]["frontend_consumption_matrix"]["pending_detail_view_count"] == 1
    assert "formal_deg_review_panel" not in state["developer_diagnostics"]["frontend_consumption_matrix"]["pending_detail_view_ids"]
    assert state["developer_diagnostics"]["frontend_consumption_matrix"]["migrated_detail_view_ids"] == ["formal_deg_review_panel", "formal_deg_plot_report_controls"]
    assert state["developer_diagnostics"]["frontend_consumption_rows"] == state["frontend_consumption_rows"]
    assert "pending_detail_views=1" in frontend_consumption_text
    assert "migrated_detail_views=2" in frontend_consumption_text
    assert "formal_deg_review_panel" in frontend_consumption_text
    assert "formal_deg_plot_report_controls" in frontend_consumption_text
    assert state["developer_diagnostics"]["reproducibility_provenance_matrix"]["status"] == "partial"
    assert state["developer_diagnostics"]["reproducibility_provenance_matrix"]["passed_row_count"] == 5
    assert state["developer_diagnostics"]["reproducibility_provenance_rows"] == state["reproducibility_provenance_rows"]
    assert state["developer_diagnostics"]["full_activation_module_matrix"]["status"] == "blocked"
    assert state["developer_diagnostics"]["full_activation_module_matrix"]["blocked_module_count"] == 10
    assert state["developer_diagnostics"]["full_activation_module_rows"] == state["full_activation_module_rows"]
    migration_matrix = state["developer_diagnostics"]["standard_worker_migration_matrix"]
    assert migration_matrix["formal_pending_count"] == migration_matrix["module_count"]
    assert migration_matrix["passed_evidence_module_ids"] == []
    assert migration_matrix["blocked_evidence_module_ids"] == []
    assert migration_matrix["missing_evidence_module_ids"] == migration_matrix["expected_evidence_module_ids"]
    assert state["developer_diagnostics"]["standard_worker_migration_rows"] == state["standard_worker_migration_rows"]
    assert state["developer_diagnostics"]["analysis_architecture_remediation_rows"] == state["analysis_architecture_remediation_rows"]
    assert state["developer_diagnostics"]["analysis_environment_registry_validation"]["status"] == "passed"
    assert state["developer_diagnostics"]["analysis_environment_registry_validation"]["full_mode_ready"] is False
    assert state["developer_diagnostics"]["analysis_environment_gate_rows"] == state["analysis_environment_gate_rows"]
    assert state["developer_diagnostics"]["analysis_resource_manifest_validation"]["status"] == "passed"
    assert state["developer_diagnostics"]["analysis_resource_manifest_validation"]["full_mode_ready"] is False
    assert state["developer_diagnostics"]["analysis_resource_gate_rows"] == state["analysis_resource_gate_rows"]
    assert _action(state, "enrichment_production_audit_preview")["enabled"] is False
    enrichment_state = state["developer_diagnostics"]["enrichment_gate_state"]
    assert enrichment_state["production_preview_status"] == "blocked"
    assert enrichment_state["resource_lock"]["semantic_boundary"] == "resource_lock_only_not_enrichment_execution"
    assert enrichment_state["production_audit_preview"]["semantic_boundary"] == "preview_only_no_package_write_no_report_ready_upgrade"
    assert enrichment_state["cross_library_acceptance"]["status"] == "passed"
    assert state["developer_diagnostics"]["enrichment_gate_state"]["reactomepa_msigdbr_policy"] == "blocked_capability_until_external_backend_and_resource_gates_pass"
    multifactor_action = _action(state, "multifactor_deg")
    assert multifactor_action["enabled"] is False
    assert "multifactor_deg_parameter_confirmation_missing" in multifactor_action["disabled_reason"]
    assert state["legacy_asset_pipeline"]["formal_analysis_enabled"] is False
    assert state["legacy_asset_pipeline"]["writes_result_index"] is False
    assert _action(state, "legacy_asset_pipeline_review")["enabled"] is False


def test_analysis_center_state_shows_package_repair_guidance_for_deg_blockers(tmp_path: Path) -> None:
    matrix = tmp_path / "expr.tsv"
    matrix.write_text("ID_REF\tS1\tS2\n1007_s_at\t1.1\t2.2\n", encoding="utf-8")
    sample = tmp_path / "sample.tsv"
    sample.write_text("sample_id\tgroup\nS1\tcase\nS2\tcontrol\n", encoding="utf-8")
    feature = _asset("feature", "feature_annotation", "feature_annotation_repository", tmp_path / "feature.tsv", gene_id_type="ID_REF")
    feature["validation_status"] = "blocked"
    assets = [
        _asset("expr", "expression_matrix", "expression_repository", matrix, value_type="TPM", gene_id_type="ID_REF"),
        _asset("sample", "sample_metadata", "sample_metadata_repository", sample),
        _asset("group", "group_design", "group_design_repository", tmp_path / "group.json"),
        feature,
    ]
    _write_standardized_state(tmp_path, assets, default_expression="expr")

    state = build_analysis_center_state(tmp_path)
    deg_row = next(row for row in state["package_rows"] if row["package_type"] == "deg_recompute")

    assert "geo_probe_or_id_ref_requires_platform_mapping" in deg_row["blockers"]
    assert "display_value_type_requires_controlled_two_group_method_not_count_model" in deg_row["warnings"]
    assert "platform probe-to-gene mapping" in deg_row["repair_action"]
    gate = state["developer_diagnostics"]["formal_deg_gate_state"]["input_adaptation_gate"]
    assert "geo_probe_or_id_ref_requires_platform_mapping" in gate["blockers"]
    assert _action(state, "formal_deg")["enabled"] is False


def test_result_plot_and_report_gate_preview_preserves_non_formal_semantics(tmp_path: Path) -> None:
    register_result(
        tmp_path,
        ResultIndexEntry(
            result_id="testing",
            task_run_id="task",
            task_type="deg",
            result_semantics="testing_level",
            validation_status="passed",
        ),
    )

    state = build_analysis_center_state(tmp_path)
    result_row = next(row for row in state["result_rows"] if row["result_id"] == "testing")

    assert result_row["semantics"] == "testing level"
    assert result_row["report_status"] == "draft only / not report-ready"
    assert _action(state, "report_ready_export")["enabled"] is False
    assert "unverified_testing_exploratory_or_imported_results_present" in _action(state, "report_ready_export")["disabled_reason"]


def test_analysis_center_state_exposes_standard_analysis_package_catalog_without_formal_upgrade(tmp_path: Path) -> None:
    run_analysis_module_task(tmp_path, _module_input(tmp_path))
    before = _file_set(tmp_path)

    state = build_analysis_center_state(tmp_path)

    catalog = state["standard_analysis_packages"]
    row = catalog["rows"][0]
    assert catalog["source_policy"] == "result_index_standard_result_package_artifacts_only"
    assert catalog["package_count"] == 1
    assert row["module_id"] == "enrichment"
    assert row["mode"] == "mock"
    assert row["result_semantics"] == "testing_level"
    assert row["validation_status"] == "passed"
    assert row["worker_backend"] == "python_fixture"
    assert row["worker_invocation_status"] == "fixture_copy_completed"
    assert row["worker_boundary_type"] == "analysis_task_bridge_fixture"
    assert row["worker_invocation"]["runtime_install_policy"] == "forbidden"
    assert row["worker_invocation"]["resource_download_policy"] == "forbidden"
    assert row["input_manifest"]["validation_status"] == "passed"
    assert row["input_manifest"]["package_relative_path"] == "module_input.json"
    assert row["input_manifest"]["schema"] == "analysis/schemas/input/module_input.schema.json"
    assert row["input_manifest_path_relative"] == "analysis_results/enrichment-mock-task/module_input.json"
    assert row["artifact_counts"]["tables"] == 1
    assert row["artifact_counts"]["logs"] == 2
    assert row["artifact_manifest"]["tables"][0]["package_relative_path"] == "tables/mock_summary.tsv"
    assert row["artifact_manifest"]["tables"][0]["exists"] is True
    assert row["artifact_manifest"]["reports"][0]["package_relative_path"] == "reports/README_mock.md"
    assert {item["artifact_type"] for item in row["artifact_manifest"]["logs"]} == {"analysis_worker_log", "analysis_worker_invocation_manifest"}
    package_gate_text = "\n".join(str(item) for item in state["standard_package_gate_rows"])
    assert "Standard package catalog source" in package_gate_text
    assert "Standard package validation" in package_gate_text
    assert "Standard package artifact manifest" in package_gate_text
    assert "Standard package input manifest" in package_gate_text
    assert "worker_invocation.input_manifest diagnostics" in package_gate_text
    assert all(row["status"] == "passed" for row in state["standard_package_gate_rows"])
    assert state["developer_diagnostics"]["standard_analysis_package_catalog"]["package_count"] == 1
    assert state["developer_diagnostics"]["standard_package_gate_rows"] == state["standard_package_gate_rows"]
    result_row = next(item for item in state["result_rows"] if item["result_id"] == "analysis-package-enrichment-mock-task")
    assert result_row["semantics"] == "testing level"
    assert result_row["standard_package_status"] == "registered"
    assert result_row["standard_package_validation_status"] == "passed"
    assert result_row["standard_package_path"] == "analysis_results/enrichment-mock-task"
    assert result_row["standard_package_artifacts"] == "tables=1; plots=0; reports=1; logs=2"
    assert _action(state, "report_ready_export")["enabled"] is False
    assert _file_set(tmp_path) == before


def test_analysis_center_state_surfaces_standard_package_artifact_gate_blockers(tmp_path: Path) -> None:
    result = run_analysis_module_task(tmp_path, _module_input(tmp_path))
    package_dir = Path(result["result_package_dir"])
    result_path = package_dir / "result.json"
    result_json = json.loads(result_path.read_text(encoding="utf-8"))
    result_json["tables"] = [{"artifact_type": "missing_table", "path": "tables/missing.tsv"}]
    result_path.write_text(json.dumps(result_json, indent=2), encoding="utf-8")

    state = build_analysis_center_state(tmp_path)
    rows = {row["gate"]: row for row in state["standard_package_gate_rows"]}

    assert rows["Standard package validation"]["status"] == "blocked"
    assert "declared_artifact_tables_0_file_missing" in rows["Standard package validation"]["blockers"]
    assert rows["Standard package artifact manifest"]["status"] == "blocked"
    assert "declared_artifact_tables_0_file_missing" in rows["Standard package artifact manifest"]["blockers"]
    assert any("declared_artifact_tables_0_file_missing" in item for item in state["top_blockers"])


def test_analysis_center_state_surfaces_standard_package_input_manifest_gate_blockers(tmp_path: Path) -> None:
    result = run_analysis_module_task(tmp_path, _module_input(tmp_path))
    package_dir = Path(result["result_package_dir"])
    input_path = package_dir / "module_input.json"
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    payload["task_id"] = "wrong-task"
    input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    state = build_analysis_center_state(tmp_path)
    rows = {row["gate"]: row for row in state["standard_package_gate_rows"]}

    assert rows["Standard package validation"]["status"] == "blocked"
    assert "module_input_manifest_task_id_mismatch" in rows["Standard package validation"]["blockers"]
    assert rows["Standard package input manifest"]["status"] == "blocked"
    assert "module_input_manifest_task_id_mismatch" in rows["Standard package input manifest"]["blockers"]
    assert any("module_input_manifest_task_id_mismatch" in item for item in state["top_blockers"])


def test_analysis_center_state_blocks_standard_package_paths_outside_project_root(tmp_path: Path) -> None:
    result = run_analysis_module_task(tmp_path, _module_input(tmp_path))
    package_dir = Path(result["result_package_dir"])
    outside_project_package = tmp_path.parent / f"{tmp_path.name}-outside-standard-package"
    if outside_project_package.exists():
        shutil.rmtree(outside_project_package)
    shutil.copytree(package_dir, outside_project_package)
    registry = load_registry(tmp_path)
    entry = registry["results"][0]
    entry["output_artifacts"] = [
        {
            "artifact_type": "standard_result_package",
            "path": str(outside_project_package.resolve()),
            "schema": "biomedpilot.analysis.result_package.v1",
        }
    ]
    save_registry(tmp_path, [entry])

    state = build_analysis_center_state(tmp_path)
    rows = {row["gate"]: row for row in state["standard_package_gate_rows"]}
    package_row = state["standard_analysis_packages"]["rows"][0]
    result_row = next(item for item in state["result_rows"] if item["result_id"] == "analysis-package-enrichment-mock-task")

    assert state["standard_analysis_packages"]["status"] == "blocked"
    assert rows["Standard package validation"]["status"] == "blocked"
    assert rows["Standard package artifact manifest"]["status"] == "blocked"
    assert "standard_result_package_path_outside_project_root" in rows["Standard package validation"]["blockers"]
    assert package_row["artifact_manifest"]["source_policy"] == "standard_result_package_not_read"
    assert package_row["artifact_counts"] == {"tables": 0, "plots": 0, "reports": 0, "logs": 0}
    assert result_row["standard_package_status"] == "registered"
    assert result_row["standard_package_validation_status"] == "blocked"
    assert result_row["standard_package_artifacts"] == "tables=0; plots=0; reports=0; logs=0"
    assert any("standard_result_package_path_outside_project_root" in item for item in state["top_blockers"])


def test_analysis_center_state_blocks_direct_cli_standard_worker_packages(tmp_path: Path) -> None:
    result = run_analysis_module_task(tmp_path, _module_input(tmp_path))
    package_dir = Path(result["result_package_dir"])
    invocation_path = package_dir / "logs" / "worker_invocation.json"
    invocation = json.loads(invocation_path.read_text(encoding="utf-8"))
    invocation["worker_backend"] = "rscript"
    invocation["worker_boundary"] = {
        "boundary_type": "standard_r_worker",
        "task_system_invocation": "standard_worker_direct_cli",
        "migration_status": "standard_worker_direct_cli_contract",
    }
    invocation_path.write_text(json.dumps(invocation, indent=2), encoding="utf-8")

    state = build_analysis_center_state(tmp_path)
    rows = {row["gate"]: row for row in state["standard_package_gate_rows"]}
    package_row = state["standard_analysis_packages"]["rows"][0]

    assert state["standard_analysis_packages"]["status"] == "blocked"
    assert rows["Standard package validation"]["status"] == "blocked"
    assert package_row["worker_boundary_type"] == "standard_r_worker"
    assert package_row["worker_migration_status"] == "standard_worker_direct_cli_contract"
    assert "standard_r_worker_package_not_task_center_registered:standard_worker_direct_cli" in rows["Standard package validation"]["blockers"]
    assert any(
        "standard_r_worker_package_not_task_center_registered:standard_worker_direct_cli" in item
        for item in state["top_blockers"]
    )


def test_result_rows_show_missing_standard_package_for_non_package_results(tmp_path: Path) -> None:
    register_result(
        tmp_path,
        ResultIndexEntry(
            result_id="legacy-result",
            task_run_id="task",
            task_type="deg",
            result_semantics="testing_level",
            validation_status="passed",
        ),
    )

    state = build_analysis_center_state(tmp_path)
    result_row = next(item for item in state["result_rows"] if item["result_id"] == "legacy-result")

    assert result_row["standard_package_status"] == "missing_standard_result_package"
    assert result_row["standard_package_validation_status"] == "missing"
    assert result_row["standard_package_path"] == ""
    assert result_row["standard_package_artifacts"] == "None"


def test_dependency_rows_are_detect_only_and_include_formal_blockers() -> None:
    rows = build_dependency_rows(
        deg_dependency={
            "status": "blocked",
            "packages": {
                "numpy": {"available": True, "version": "1"},
                "pandas": {"available": True, "version": "2"},
                "scipy": {"available": False, "version": ""},
                "statsmodels": {"available": False, "version": ""},
            },
            "r_backend": {"packages": {"R": "not_checked", "limma": "not_checked", "DESeq2": "not_checked", "edgeR": "not_checked"}},
        },
        survival_dependency={"status": "preflight_only", "python_lifelines": {"available": False, "version": ""}, "blockers": ["lifelines_missing_formal_survival_disabled"]},
        enrichment_backend_gate={
            "status": "passed",
            "rscript": {"available": True, "version": "R 4.4.2"},
            "packages": {
                "clusterProfiler": {"available": True, "importable": True, "version": "4.14.6"},
                "fgsea": {"available": True, "importable": True, "version": "1.32.4"},
                "ReactomePA": {"available": False, "importable": False, "version": ""},
                "msigdbr": {"available": False, "importable": False, "version": ""},
            },
            "packaging_policy": "external_runtime_not_bundled",
            "blockers": [],
            "warnings": ["external_detection_global_status_blocked_by_unselected_capabilities"],
        },
    )

    text = "\n".join(str(row) for row in rows)
    assert "missing_python_package:scipy" in text
    assert "missing_python_package:statsmodels" in text
    assert "lifelines_missing_formal_survival_disabled" in text
    assert "clusterProfiler" in text
    assert "Reactome/MSigDB blockers do not stop selected core ORA/GSEA capabilities." in text
    assert "no install action" in text
    assert "required_in_packaged_app_for_formal_deg" in text


def test_legacy_asset_pipeline_state_is_review_only_and_does_not_upgrade_inputs(tmp_path: Path) -> None:
    adapter_dir = tmp_path / "acquisition" / "legacy_adapter_manifests"
    adapter_dir.mkdir(parents=True)
    (adapter_dir / "geo.json").write_text(json.dumps({"adapter_id": "geo", "source": "geo"}), encoding="utf-8")
    candidate_path = tmp_path / "standardized_data" / "asset_candidates" / "legacy_acquisition_asset_candidates.json"
    candidate_path.parent.mkdir(parents=True)
    candidate_path.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.legacy_standardized_asset_candidate_bundle.v1",
                "status": "candidate_only",
                "candidate_count": 1,
                "warnings": ["candidate_only_not_repository_asset"],
                "blockers": [],
                "downstream_contract": {
                    "writes_analysis_input_repository": False,
                    "writes_result_index": False,
                    "ready_for_formal_analysis": False,
                },
            }
        ),
        encoding="utf-8",
    )
    selection_path = tmp_path / "standardized_data" / "asset_candidates" / "legacy_asset_selection_manifest.json"
    selection_path.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.legacy_asset_selection_manifest.v1",
                "status": "selection_recorded_preflight_only",
                "confirmed_by_user": True,
                "selected_assets": {"expression": {"asset_id": "expr"}},
                "validation": {
                    "status": "passed_with_downstream_blockers",
                    "selection_blockers": [],
                    "downstream_blockers": ["missing_group_design_selection"],
                    "warnings": ["selected_legacy_asset_is_not_analysis_ready_until_downstream_gates_pass"],
                },
                "formal_analysis_ready": False,
                "result_semantics": "not_a_result",
                "report_ready_eligible": False,
            }
        ),
        encoding="utf-8",
    )
    before = _file_set(tmp_path)

    state = build_analysis_center_state(tmp_path)

    pipeline = state["legacy_asset_pipeline"]
    assert pipeline["status"] == "blocked"
    assert pipeline["artifact_count"] == 3
    assert pipeline["formal_analysis_enabled"] is False
    assert pipeline["writes_analysis_input_repository"] is False
    assert pipeline["writes_result_index"] is False
    assert pipeline["report_ready_eligible"] is False
    assert "missing_group_design_selection" in pipeline["blockers"]
    assert "B8 resolver" in pipeline["boundary_message"]
    operations = {item["operation_id"]: item for item in pipeline["operations"]}
    assert operations["legacy_build_candidates"]["enabled"] is True
    assert operations["legacy_materialize_candidates"]["enabled"] is True
    assert operations["legacy_merge_repository_manifest"]["enabled"] is False
    assert operations["legacy_confirm_asset_selection"]["enabled"] is False
    review = _action(state, "legacy_asset_pipeline_review")
    assert review["enabled"] is True
    assert review["button_behavior"] == "enabled_review_only_no_formal_execution"
    assert _action(state, "legacy_build_candidates")["button_behavior"] == "controlled_standardization_artifact_write_no_formal_execution"
    assert _file_set(tmp_path) == before


def _action(state: dict[str, object], action_id: str) -> dict[str, object]:
    return next(row for row in state["action_rows"] if row["action_id"] == action_id)  # type: ignore[index]


def _file_set(root: Path) -> set[str]:
    return {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()}


def _asset(asset_id: str, asset_type: str, repository: str, path: Path, *, value_type: str = "", gene_id_type: str = "symbol") -> dict[str, object]:
    return {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "asset_role": "expression_matrix" if "expression" in asset_type or "count" in asset_type else asset_type,
        "repository": repository,
        "path": str(path),
        "file_path": str(path),
        "validation_status": "passed",
        "analysis_ready": True,
        "expression_value_type": value_type,
        "gene_id_type": gene_id_type,
    }


def _module_input(tmp_path: Path, *, module_id: str = "enrichment") -> dict[str, object]:
    return {
        "schema_version": "biomedpilot.analysis.module_input.v1",
        "module_id": module_id,
        "mode": "mock",
        "task_id": f"{module_id}-mock-task",
        "project_id": tmp_path.name,
        "inputs": {
            "input_package_id": "input-package-001",
            "source_dataset_id": "dataset-001",
        },
        "parameters": {"comparison": "case_vs_control"},
        "runtime": {"random_seed": 7, "requested_environment": "app-dev"},
    }


def _write_standardized_state(root: Path, assets: list[dict[str, object]], *, default_expression: str) -> None:
    selection = {"expression": {"asset_id": default_expression, "selection_state": "user_confirmed"}}
    payload = {
        "schema_version": "biomedpilot.repository_manifest.v1",
        "assets": assets,
        "default_asset_selection": selection,
        "source_state": {"source_state_hash": "source-1"},
    }
    registry = {"schema_version": "biomedpilot.standardized_assets_registry.v2", "assets": assets, "default_asset_selection": selection}
    repo_path = root / "standardized_data" / "repositories" / "repository_manifest.json"
    registry_path = root / "manifests" / "standardized_assets_registry.json"
    repo_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    repo_path.write_text(json.dumps(payload), encoding="utf-8")
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
