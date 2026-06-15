# BioMedPilot R Analysis Architecture Gate Report

Generated: `2026-06-15T03:06:24+00:00`

Worktree: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

## 1. 当前是否符合目标模式

| Field | Value |
| --- | --- |
| Gate status | `passed` |
| Architecture status | `partial_with_p1_gaps` |
| Schema validation | `passed` |
| Full analysis activation gate | `blocked` |
| Require full ready | `False` |

Current interpretation: the architecture gate proves the current source has no P0 blocker and the report contract is schema-valid. It does not prove full analysis readiness while the full activation gate remains blocked.

## 2. PASS / WARN / FAIL 总表

| Requirements | PASS | WARN | FAIL | Other |
| --- | ---: | ---: | ---: | ---: |
| 20 | 12 | 8 | 0 | 0 |

### Runtime Boundary Scan Evidence

| Scan | Status | Scope | Hit Count | Policy |
| --- | --- | --- | --- | --- |
| Runtime package install | passed | app, analysis, scripts, config | 0 | runtime_package_install_and_resource_download_forbidden_in_active_app_analysis_scripts_config |
| Runtime resource download | passed | app, analysis, scripts, config | 0 | runtime_package_install_and_resource_download_forbidden_in_active_app_analysis_scripts_config |
| Default app-dev heavy dependency | passed | requirements.txt, pyproject.toml, docker/Dockerfile.app-dev, renv/renv.app.lock | 0 | heavy_full_analysis_dependencies_excluded_from_default_app_dev_surface |

### Module Interface Matrix

| Metric | Count | Detail |
| --- | --- | --- |
| Passed modules | 10 |  |
| Blocked modules | 0 | {} |

| Module | Status | Modes | Mock Fixture | Environment |
| --- | --- | --- | --- | --- |
| deg | passed | mock=True; lite=True; full=False | passed | r-bio-core->r-bio-full |
| survival | passed | mock=True; lite=True; full=True | passed | r-bio-core->r-bio-full |
| univariate | passed | mock=True; lite=True; full=False | passed | r-bio-core->r-bio-full |
| multivariate | passed | mock=True; lite=True; full=False | passed | r-bio-core->r-bio-full |
| enrichment | passed | mock=True; lite=True; full=False | passed | r-bio-core->r-bio-full |
| immune_infiltration | passed | mock=True; lite=True; full=False | passed | r-bio-core->r-bio-full |
| correlation | passed | mock=True; lite=True; full=False | passed | r-bio-core->r-bio-full |
| spatial_transcriptomics | passed | mock=True; lite=True; full=False | passed | r-bio-core->r-spatial-full |
| docking | passed | mock=True; lite=True; full=False | passed | r-bio-core->r-chem-full |
| molecular_dynamics | passed | mock=True; lite=True; full=False | passed | r-bio-core->r-chem-gpu |

### Module Mode Readiness Matrix

| Metric | Count | Detail |
| --- | --- | --- |
| Passed modules | 1 |  |
| Partial modules | 9 | {"module_full_mode_blocked:correlation": 1, "module_full_mode_blocked:deg": 1, "module_full_mode_blocked:docking": 1, "module_full_mode_blocked:enrichment": 1, "module_full_mode_blocked:immune_infiltration": 1, "module_full_mode_blocked:molecular_dynamics": 1, "module_full_mode_blocked:multivariate": 1, "module_full_mode_blocked:spatial_transcriptomics": 1, "module_full_mode_blocked:univariate": 1, "module_full_mode_declared_blocker:correlation:full_r_worker_container_not_available": 1, "module_full_mode_declared_blocker:deg:full_r_worker_container_not_available": 1, "module_full_mode_declared_blocker:docking:r_chem_full_container_not_available": 1, "module_full_mode_declared_blocker:enrichment:full_resource_manifest_and_container_not_available": 1, "module_full_mode_declared_blocker:immune_infiltration:full_r_worker_container_not_available": 1, "module_full_mode_declared_blocker:molecular_dynamics:r_chem_gpu_container_not_available": 1, "module_full_mode_declared_blocker:multivariate:full_r_worker_container_not_available": 1, "module_full_mode_declared_blocker:spatial_transcriptomics:r_spatial_full_container_not_available": 1, "module_full_mode_declared_blocker:univariate:full_r_worker_container_not_available": 1} |
| Blocked modules | 0 | {} |

| Module | Status | Mock | Lite | Full | Next |
| --- | --- | --- | --- | --- | --- |
| deg | partial | passed | passed; r-bio-core | blocked; r-bio-full; full_r_worker_container_not_available | declare_scoped_full_mode_only_after_environment_and_resource_locks |
| survival | passed | passed | passed; r-bio-core | passed; r-bio-full;  | no_action_migration_evidence_passed |
| univariate | partial | passed | passed; r-bio-core | blocked; r-bio-full; full_r_worker_container_not_available | declare_scoped_full_mode_only_after_environment_and_resource_locks |
| multivariate | partial | passed | passed; r-bio-core | blocked; r-bio-full; full_r_worker_container_not_available | declare_scoped_full_mode_only_after_environment_and_resource_locks |
| enrichment | partial | passed | passed; r-bio-core | blocked; r-bio-full; full_resource_manifest_and_container_not_available | declare_scoped_full_mode_only_after_environment_and_resource_locks |
| immune_infiltration | partial | passed | passed; r-bio-core | blocked; r-bio-full; full_r_worker_container_not_available | declare_scoped_full_mode_only_after_environment_and_resource_locks |
| correlation | partial | passed | passed; r-bio-core | blocked; r-bio-full; full_r_worker_container_not_available | declare_scoped_full_mode_only_after_environment_and_resource_locks |
| spatial_transcriptomics | partial | passed | passed; r-bio-core | blocked; r-spatial-full; r_spatial_full_container_not_available | declare_scoped_full_mode_only_after_environment_and_resource_locks |
| docking | partial | passed | passed; r-bio-core | blocked; r-chem-full; r_chem_full_container_not_available | declare_scoped_full_mode_only_after_environment_and_resource_locks |
| molecular_dynamics | partial | passed | passed; r-bio-core | blocked; r-chem-gpu; r_chem_gpu_container_not_available | declare_scoped_full_mode_only_after_environment_and_resource_locks |

### Environment Artifact Matrix

| Metric | Count | Detail |
| --- | --- | --- |
| Passed environments | 3 |  |
| Partial environments | 3 | {"analysis_environment_renv_lock_not_restored:r-chem-full:scaffold_only_not_restored": 1, "analysis_environment_renv_lock_not_restored:r-chem-gpu:scaffold_only_not_restored": 1, "analysis_environment_renv_lock_not_restored:r-spatial-full:scaffold_only_not_restored": 1, "dockerfiles_exist_but_full_image_builds_not_proven": 3, "environment_docker_image_build_not_proven:r-chem-full": 1, "environment_docker_image_build_not_proven:r-chem-gpu": 1, "environment_docker_image_build_not_proven:r-spatial-full": 1, "environment_renv_lock_scaffold_only_not_restored:r-chem-full": 1, "environment_renv_lock_scaffold_only_not_restored:r-chem-gpu": 1, "environment_renv_lock_scaffold_only_not_restored:r-spatial-full": 1, "full_environment_locks_are_scaffold_only_not_restored": 3} |
| Blocked environments | 0 | {} |

| Environment | Status | Class | Dockerfile | renv | Allowed Modules |
| --- | --- | --- | --- | --- | --- |
| app-dev | passed | app-dev | present; docker/Dockerfile.app-dev | present; scaffold_only_not_restored; packages=0 |  |
| r-bio-core | passed | lite | present; docker/Dockerfile.r-bio-core | present; scaffold_only_not_restored; packages=0 | deg, survival, univariate, multivariate, enrichment, immune_infiltration, correlation, spatial_transcriptomics, docking, molecular_dynamics |
| r-bio-full | passed | full | present; docker/Dockerfile.r-bio-full | present; restored; packages=39 | deg, survival, univariate, multivariate, enrichment, immune_infiltration, correlation |
| r-spatial-full | partial | full | present; docker/Dockerfile.r-spatial-full | present; scaffold_only_not_restored; packages=0 | spatial_transcriptomics |
| r-chem-full | partial | full | present; docker/Dockerfile.r-chem-full | present; scaffold_only_not_restored; packages=0 | docking |
| r-chem-gpu | partial | full | present; docker/Dockerfile.r-chem-gpu | present; scaffold_only_not_restored; packages=0 | molecular_dynamics |

### r-bio-full External Evidence Validation

| Field | Value |
| --- | --- |
| environment_id | r-bio-full |
| validation_status | passed |
| evidence_source | docker_hub |
| evidence_root | /Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/external_analysis_environments/r-bio-full |
| registry_preflight_status | passed |
| docker_build_status | built |
| docker_evidence_status | present |
| renv_evidence_status | present |
| r_session_info_status | present |
| package_inventory_status | present |
| hash_validation_status | passed |
| full_gate_next_stage_allowed | True |

| Blockers |
| --- |
| none |

### Resource Artifact Matrix

| Metric | Count | Detail |
| --- | --- | --- |
| Locked resources | 1 | evidence_entries=0 |
| Blocked full resources | 11 | {"resource_cache_path_not_prepared:autodock_vina_tool": 1, "resource_cache_path_not_prepared:cellchatdb_full": 1, "resource_cache_path_not_prepared:docking_template_bundle": 1, "resource_cache_path_not_prepared:go_full": 1, "resource_cache_path_not_prepared:gromacs_tool": 1, "resource_cache_path_not_prepared:kegg_full": 1, "resource_cache_path_not_prepared:md_forcefield_template_bundle": 1, "resource_cache_path_not_prepared:msigdb_full": 1, "resource_cache_path_not_prepared:orgdb_human_full": 1, "resource_cache_path_not_prepared:reactome_full": 1, "resource_cache_path_not_prepared:spatial_reference_full": 1, "resource_full_lock_not_ready:autodock_vina_tool": 1, "resource_full_lock_not_ready:cellchatdb_full": 1, "resource_full_lock_not_ready:docking_template_bundle": 1, "resource_full_lock_not_ready:go_full": 1, "resource_full_lock_not_ready:gromacs_tool": 1, "resource_full_lock_not_ready:kegg_full": 1, "resource_full_lock_not_ready:md_forcefield_template_bundle": 1, "resource_full_lock_not_ready:msigdb_full": 1, "resource_full_lock_not_ready:orgdb_human_full": 1, "resource_full_lock_not_ready:reactome_full": 1, "resource_full_lock_not_ready:spatial_reference_full": 1, "resource_lock_evidence_missing:autodock_vina_tool": 1, "resource_lock_evidence_missing:cellchatdb_full": 1, "resource_lock_evidence_missing:docking_template_bundle": 1, "resource_lock_evidence_missing:go_full": 1, "resource_lock_evidence_missing:gromacs_tool": 1, "resource_lock_evidence_missing:kegg_full": 1, "resource_lock_evidence_missing:md_forcefield_template_bundle": 1, "resource_lock_evidence_missing:msigdb_full": 1, "resource_lock_evidence_missing:orgdb_human_full": 1, "resource_lock_evidence_missing:reactome_full": 1, "resource_lock_evidence_missing:spatial_reference_full": 1, "resource_lock_evidence_registry_entry_missing:autodock_vina_tool": 1, "resource_lock_evidence_registry_entry_missing:cellchatdb_full": 1, "resource_lock_evidence_registry_entry_missing:docking_template_bundle": 1, "resource_lock_evidence_registry_entry_missing:go_full": 1, "resource_lock_evidence_registry_entry_missing:gromacs_tool": 1, "resource_lock_evidence_registry_entry_missing:kegg_full": 1, "resource_lock_evidence_registry_entry_missing:md_forcefield_template_bundle": 1, "resource_lock_evidence_registry_entry_missing:msigdb_full": 1, "resource_lock_evidence_registry_entry_missing:orgdb_human_full": 1, "resource_lock_evidence_registry_entry_missing:reactome_full": 1, "resource_lock_evidence_registry_entry_missing:spatial_reference_full": 1, "resource_placeholder_field:autodock_vina_tool:hash": 1, "resource_placeholder_field:autodock_vina_tool:license": 1, "resource_placeholder_field:autodock_vina_tool:version": 1, "resource_placeholder_field:cellchatdb_full:hash": 1, "resource_placeholder_field:cellchatdb_full:license": 1, "resource_placeholder_field:cellchatdb_full:version": 1, "resource_placeholder_field:docking_template_bundle:hash": 1, "resource_placeholder_field:docking_template_bundle:license": 1, "resource_placeholder_field:docking_template_bundle:version": 1, "resource_placeholder_field:go_full:hash": 1, "resource_placeholder_field:go_full:license": 1, "resource_placeholder_field:go_full:version": 1, "resource_placeholder_field:gromacs_tool:hash": 1, "resource_placeholder_field:gromacs_tool:license": 1, "resource_placeholder_field:gromacs_tool:version": 1, "resource_placeholder_field:kegg_full:hash": 1, "resource_placeholder_field:kegg_full:license": 1, "resource_placeholder_field:kegg_full:version": 1, "resource_placeholder_field:md_forcefield_template_bundle:hash": 1, "resource_placeholder_field:md_forcefield_template_bundle:license": 1, "resource_placeholder_field:md_forcefield_template_bundle:version": 1, "resource_placeholder_field:msigdb_full:hash": 1, "resource_placeholder_field:msigdb_full:license": 1, "resource_placeholder_field:msigdb_full:version": 1, "resource_placeholder_field:orgdb_human_full:hash": 1, "resource_placeholder_field:orgdb_human_full:license": 1, "resource_placeholder_field:orgdb_human_full:version": 1, "resource_placeholder_field:reactome_full:hash": 1, "resource_placeholder_field:reactome_full:license": 1, "resource_placeholder_field:reactome_full:version": 1, "resource_placeholder_field:spatial_reference_full:hash": 1, "resource_placeholder_field:spatial_reference_full:license": 1, "resource_placeholder_field:spatial_reference_full:version": 1} |
| Failed resources | 0 | {} |

| Resource | Status | Family | Version | Hash | License | Evidence | Modules |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mock_fixture_builtin_v1 | passed | mock_fixture | declared | declared | declared | present | survival, univariate, multivariate, enrichment, immune_infiltration, spatial_transcriptomics, docking, molecular_dynamics |
| reactome_full | partial | pathway_database | placeholder | placeholder | placeholder | missing | enrichment |
| msigdb_full | partial | gene_set_database | placeholder | placeholder | placeholder | missing | enrichment |
| go_full | partial | ontology_database | placeholder | placeholder | placeholder | missing | enrichment, immune_infiltration |
| kegg_full | partial | pathway_database | placeholder | placeholder | placeholder | missing | enrichment |
| orgdb_human_full | partial | organism_annotation_database | placeholder | placeholder | placeholder | missing | enrichment, immune_infiltration |
| spatial_reference_full | partial | spatial_reference | placeholder | placeholder | placeholder | missing | spatial_transcriptomics |
| cellchatdb_full | partial | cell_communication_database | placeholder | placeholder | placeholder | missing | spatial_transcriptomics |
| autodock_vina_tool | partial | external_scientific_tool | placeholder | placeholder | placeholder | missing | docking |
| docking_template_bundle | partial | docking_template | placeholder | placeholder | placeholder | missing | docking |
| gromacs_tool | partial | external_scientific_tool | placeholder | placeholder | placeholder | missing | molecular_dynamics |
| md_forcefield_template_bundle | partial | md_template | placeholder | placeholder | placeholder | missing | molecular_dynamics |

### Standard Worker Entrypoint Matrix

| Metric | Count | Detail |
| --- | --- | --- |
| Passed entrypoint contracts | 6 | lite_modules=['deg', 'survival', 'univariate', 'multivariate', 'enrichment', 'immune_infiltration', 'correlation', 'spatial_transcriptomics', 'docking', 'molecular_dynamics'] |
| Partial entrypoint contracts | 0 | {} |
| Blocked entrypoint contracts | 0 | {} |

| Contract | Status | Evidence | Lite Modules | Formal Pending | Boundary | Warnings |
| --- | --- | --- | --- | --- | --- | --- |
| standard_r_worker_cli_contract | passed | analysis/runners/run_module.R::cli_args |  |  | static_source_contract_check_no_worker_execution |  |
| standard_r_worker_package_output_contract | passed | analysis/runners/run_module.R::standard_package_writers |  |  | static_source_contract_check_no_worker_execution |  |
| standard_r_worker_lite_dispatch_contract | passed | analysis/runners/run_module.R::lite_dispatch | deg, survival, univariate, multivariate, enrichment, immune_infiltration, correlation, spatial_transcriptomics, docking, molecular_dynamics |  | lite_dispatch_only_full_mode_still_blocked_by_gate |  |
| standard_r_worker_main_backend_invocation_contract | passed | app/analysis_runtime/r_worker.py; app/analysis_runtime/task_bridge.py |  |  | main_backend_invokes_repo_owned_runner_no_module_private_r_outputs |  |
| standard_r_worker_no_runtime_acquisition | passed | analysis/runners/run_module.R |  |  | no_install_no_download_in_standard_worker_entrypoint |  |
| standard_r_worker_formal_migration_boundary | passed | analysis/registry/standard_worker_migration_evidence.json |  | deg, univariate, multivariate, enrichment, immune_infiltration, correlation, spatial_transcriptomics, docking, molecular_dynamics | entrypoint_contract_passed_formal_full_migration_tracked_by_standard_worker_migration_matrix |  |

### External Tool Adapter Isolation Matrix

| Metric | Count | Detail |
| --- | --- | --- |
| Passed adapters | 2 | {"full_mode_blocked_until_tool_or_resource_lock:autodock_vina_tool,docking_template_bundle": 1, "full_mode_blocked_until_tool_or_resource_lock:gromacs_tool,md_forcefield_template_bundle": 1, "lite_mode_writes_command_manifest_only_no_external_tool_execution": 2, "r_chem_full_container_not_available": 1, "r_chem_gpu_container_not_available": 1} |
| Blocked adapters | 0 | {} |

| Module | Status | Lite | Full | Resources | Policy |
| --- | --- | --- | --- | --- | --- |
| docking | passed | r-bio-core; not_executed_in_lite_mode | r-chem-full; supported=False | autodock_vina_tool, docking_template_bundle | R_adapter_calls_AutoDock_Vina_in_chem_environment_only |
| molecular_dynamics | passed | r-bio-core; not_executed_in_lite_mode | r-chem-gpu; supported=False | gromacs_tool, md_forcefield_template_bundle | R_adapter_calls_GROMACS_in_chem_gpu_environment_only |

### Task System Boundary Matrix

| Metric | Count | Detail |
| --- | --- | --- |
| Passed task-boundary modules | 10 | {"current_adapter_pending_standard_worker_migration:correlation": 1, "current_adapter_pending_standard_worker_migration:docking": 1, "current_adapter_pending_standard_worker_migration:enrichment": 1, "current_adapter_pending_standard_worker_migration:immune_infiltration": 1, "current_adapter_pending_standard_worker_migration:molecular_dynamics": 1, "current_adapter_pending_standard_worker_migration:multivariate": 1, "current_adapter_pending_standard_worker_migration:spatial_transcriptomics": 1, "current_adapter_pending_standard_worker_migration:univariate": 1, "formal_worker_migration_pending:correlation": 1, "formal_worker_migration_pending:deg": 1, "formal_worker_migration_pending:docking": 1, "formal_worker_migration_pending:enrichment": 1, "formal_worker_migration_pending:immune_infiltration": 1, "formal_worker_migration_pending:molecular_dynamics": 1, "formal_worker_migration_pending:multivariate": 1, "formal_worker_migration_pending:spatial_transcriptomics": 1, "formal_worker_migration_pending:univariate": 1, "legacy_sidecar_boundary_transitional:deg": 1, "legacy_sidecar_boundary_transitional:survival": 1} |
| Blocked task-boundary modules | 0 | {} |

| Module | Status | Result Task Types | Task Invocation | Worker Manifest | Formal Worker |
| --- | --- | --- | --- | --- | --- |
| deg | passed | deg, recomputed_deg, differential_expression | task_center_registered | True | pending_standard_worker_migration |
| survival | passed | survival, survival_km_logrank, cox_univariate, cox_multivariate | task_center_registered | True | migrated_to_isolated_standard_worker |
| univariate | passed | univariate, clinical_association | task_center_registered | True | pending_standard_worker_migration |
| multivariate | passed | multivariate | task_center_registered | True | pending_standard_worker_migration |
| enrichment | passed | enrichment, ora, gsea, gsea_preranked | task_center_registered | True | pending_standard_worker_migration |
| immune_infiltration | passed | immune_infiltration, immune_tme_scoring | task_center_registered | True | pending_standard_worker_migration |
| correlation | passed | correlation | task_center_registered | True | pending_standard_worker_migration |
| spatial_transcriptomics | passed | spatial_transcriptomics | task_center_registered | True | pending_standard_worker_migration |
| docking | passed | docking | task_center_registered | True | pending_standard_worker_migration |
| molecular_dynamics | passed | molecular_dynamics | task_center_registered | True | pending_standard_worker_migration |

### Lite Task Bridge Coverage Matrix

| Metric | Count | Detail |
| --- | --- | --- |
| Covered lite modules | 10 | tests/test_analysis_runtime_task_bridge.py |
| Blocked lite modules | 0 | {} |

| Module | Status | Fixture | Worker | Coverage Test | Contracts |
| --- | --- | --- | --- | --- | --- |
| deg | passed | present | rscript | test_all_registered_lite_modules_run_through_standard_r_worker_package_contract | TaskCenter completed task, standard_result_package validation passed, result_index registered testing_level result, worker_invocation boundary standard_r_worker, report_ready_eligible false, runtime/resource acquisition forbidden |
| survival | passed | present | rscript | test_all_registered_lite_modules_run_through_standard_r_worker_package_contract | TaskCenter completed task, standard_result_package validation passed, result_index registered testing_level result, worker_invocation boundary standard_r_worker, report_ready_eligible false, runtime/resource acquisition forbidden |
| univariate | passed | present | rscript | test_all_registered_lite_modules_run_through_standard_r_worker_package_contract | TaskCenter completed task, standard_result_package validation passed, result_index registered testing_level result, worker_invocation boundary standard_r_worker, report_ready_eligible false, runtime/resource acquisition forbidden |
| multivariate | passed | present | rscript | test_all_registered_lite_modules_run_through_standard_r_worker_package_contract | TaskCenter completed task, standard_result_package validation passed, result_index registered testing_level result, worker_invocation boundary standard_r_worker, report_ready_eligible false, runtime/resource acquisition forbidden |
| enrichment | passed | present | rscript | test_all_registered_lite_modules_run_through_standard_r_worker_package_contract | TaskCenter completed task, standard_result_package validation passed, result_index registered testing_level result, worker_invocation boundary standard_r_worker, report_ready_eligible false, runtime/resource acquisition forbidden |
| immune_infiltration | passed | present | rscript | test_all_registered_lite_modules_run_through_standard_r_worker_package_contract | TaskCenter completed task, standard_result_package validation passed, result_index registered testing_level result, worker_invocation boundary standard_r_worker, report_ready_eligible false, runtime/resource acquisition forbidden |
| correlation | passed | present | rscript | test_all_registered_lite_modules_run_through_standard_r_worker_package_contract | TaskCenter completed task, standard_result_package validation passed, result_index registered testing_level result, worker_invocation boundary standard_r_worker, report_ready_eligible false, runtime/resource acquisition forbidden |
| spatial_transcriptomics | passed | present | rscript | test_all_registered_lite_modules_run_through_standard_r_worker_package_contract | TaskCenter completed task, standard_result_package validation passed, result_index registered testing_level result, worker_invocation boundary standard_r_worker, report_ready_eligible false, runtime/resource acquisition forbidden |
| docking | passed | present | rscript | test_all_registered_lite_modules_run_through_standard_r_worker_package_contract | TaskCenter completed task, standard_result_package validation passed, result_index registered testing_level result, worker_invocation boundary standard_r_worker, report_ready_eligible false, runtime/resource acquisition forbidden |
| molecular_dynamics | passed | present | rscript | test_all_registered_lite_modules_run_through_standard_r_worker_package_contract | TaskCenter completed task, standard_result_package validation passed, result_index registered testing_level result, worker_invocation boundary standard_r_worker, report_ready_eligible false, runtime/resource acquisition forbidden |

### Legacy Sidecar Transition Matrix

| Metric | Count | Detail |
| --- | --- | --- |
| Passed sidecar boundary contracts | 6 | {"existing_controlled_python_and_r_contracts_pending_standard_worker_migration": 1, "existing_standard_worker_lite_contract_pending_full_migration": 2, "legacy_formal_execution_disabled_pending_full_standard_worker_migration": 1, "planned_external_tool_adapter_only": 2, "planned_not_current_runtime": 1, "r_native_lite_contract_exists_pending_full_environment_and_standard_worker_migration": 2, "survival_minimal_v1_formal_standard_worker_migrated": 1} |
| Partial sidecar transition contracts | 1 | {"legacy_sidecar_producer_transitional:deg": 1, "legacy_sidecar_producer_transitional:survival": 1} |
| Blocked sidecar boundary contracts | 0 | {} |
| Lite standard-worker replacement candidates | 0 |  |

| Contract | Status | Evidence | Transitional Modules | Replacement Candidates | Warnings |
| --- | --- | --- | --- | --- | --- |
| legacy_sidecar_writer_contract | passed | app/analysis_runtime/standard_package.py::write_legacy_service_adapter_invocation_manifest |  |  |  |
| catalog_task_center_guard | passed | app/analysis_runtime/package_catalog.py::_catalog_task_system_boundary_blockers |  |  |  |
| migration_evidence_forbids_sidecar | passed | app/analysis_runtime/architecture_status.py::_standard_worker_migration_evidence_template |  |  |  |
| registry_adapter_transition_scope | passed | analysis/registry/analysis_modules.json::modules[*].current_adapter_status | deg, survival |  |  |
| source_sidecar_producer_inventory | partial | app/bioinformatics/* standard package sidecar writers |  |  | legacy_sidecar_producer_transitional:deg, legacy_sidecar_producer_transitional:survival |
| legacy_sidecar_override_allowlist | passed | static scan: allow_legacy_sidecar_execution=True |  |  |  |
| sidecar_boundary_test_coverage | passed | tests/bioinformatics/test_formal_controlled_deg_runner.py, tests/bioinformatics/test_enrichment_r_adapter.py, and tests/bioinformatics/test_km_logrank_execution.py |  |  |  |

### Frontend Standard Package Consumption Matrix

| Metric | Count | Detail |
| --- | --- | --- |
| Passed consumers | 5 |  |
| Partial consumers | 0 | {} |
| Blocked consumers | 0 | {} |
| Migrated detail views | 3 | formal_deg_review_panel, formal_deg_plot_report_controls, immune_tme_scoring_page |
| Pending detail views | 0 |  |

| Consumer | Status | Surface | File | Policy |
| --- | --- | --- | --- | --- |
| catalog_source_policy | passed | build_standard_analysis_package_catalog | app/analysis_runtime/package_catalog.py | consume_result_index_registered_standard_result_packages_only |
| catalog_detail_policy | passed | build_standard_analysis_package_detail | app/analysis_runtime/package_catalog.py | consume_result_index_registered_standard_result_packages_only |
| analysis_center_state | passed | build_analysis_center_state | app/bioinformatics/analysis_ui/state.py | consume_result_index_registered_standard_result_packages_only |
| results_browser_tables | passed | BioinformaticsResultsBrowserWidget | app/bioinformatics/workflow_pages.py | consume_result_index_registered_standard_result_packages_only |
| detailed_result_views_migration | passed | module_specific_detailed_result_views | app/bioinformatics/workflow_pages.py and module-specific detail builders | transitional_legacy_detail_views_must_not_be_formal_readiness_evidence |

### Reproducibility Provenance Matrix

| Metric | Count | Detail |
| --- | --- | --- |
| Passed provenance contracts | 5 | fields=['schema_version', 'module_id', 'mode', 'task_id', 'created_at', 'input_hash', 'parameter_hash', 'random_seed', 'engine', 'runtime', 'command'] |
| Partial provenance contracts | 1 | {"legacy_sidecar_provenance_transitional:deg": 1, "legacy_sidecar_provenance_transitional:survival": 1} |
| Blocked provenance contracts | 0 | {} |

| Contract | Status | Evidence | Runtime Fields | Warnings |
| --- | --- | --- | --- | --- |
| provenance_payload_schema | passed | analysis/schemas/output/provenance.schema.json | r_version, bioconductor_version, package_versions, external_tool_versions |  |
| standard_package_validator_required_provenance | passed | app/analysis_runtime/standard_package.py::_passed_package_provenance_blockers |  |  |
| task_bridge_provenance_writer | passed | app/analysis_runtime/task_bridge.py::_write_standard_package |  |  |
| standard_r_worker_provenance_writer | passed | analysis/runners/run_module.R::write_provenance |  |  |
| worker_invocation_schema | passed | analysis/schemas/output/worker_invocation.schema.json |  |  |
| legacy_sidecar_provenance_boundary | partial | app/bioinformatics/* standard package sidecar writers and app/analysis_runtime/standard_package.py |  | legacy_sidecar_provenance_transitional:deg, legacy_sidecar_provenance_transitional:survival |

## 3. 最大的 5 个架构风险

| Priority | Risk ID | Source | Summary |
| --- | --- | --- | --- |
| P1 | full_analysis_environment_locks_not_restored | environment_readiness | Full analysis environments remain scaffold-only or lack restored lock evidence. |
| P1 | full_analysis_resource_locks_not_complete | resource_readiness | Full analysis resources/tools remain blocked until version/hash/license/cache evidence is complete. |
| P1 | formal_algorithms_not_universally_migrated_to_isolated_standard_worker | standard_worker_migration_matrix | Formal algorithms still have pending isolated standard-worker migration rows. |
| P2 | RARCH-09 | app/analysis_runtime/task_bridge.py | Main backend task-system invocation boundary |
| P2 | RARCH-16 | analysis/schemas/output/provenance.schema.json and standard package validator | Reproducibility provenance contract |

### Standard Worker Migration Evidence Coverage

| Metric | Count | Modules |
| --- | --- | --- |
| Expected evidence modules | 10 | deg, survival, univariate, multivariate, enrichment, immune_infiltration, correlation, spatial_transcriptomics, docking, molecular_dynamics |
| Passed evidence modules | 1 | survival |
| Blocked evidence modules | 0 |  |
| Missing evidence modules | 9 | deg, univariate, multivariate, enrichment, immune_infiltration, correlation, spatial_transcriptomics, docking, molecular_dynamics |

### Full Activation Module Matrix

| Metric | Count | Detail |
| --- | --- | --- |
| Eligible modules | 1 |  |
| Blocked modules | 9 | {"analysis_full_environment_lock_not_restored:r-chem-full": 1, "analysis_full_environment_lock_not_restored:r-chem-gpu": 1, "analysis_full_environment_lock_not_restored:r-spatial-full": 1, "analysis_resource_not_locked:autodock_vina_tool": 1, "analysis_resource_not_locked:cellchatdb_full": 1, "analysis_resource_not_locked:docking_template_bundle": 1, "analysis_resource_not_locked:go_full": 2, "analysis_resource_not_locked:gromacs_tool": 1, "analysis_resource_not_locked:kegg_full": 1, "analysis_resource_not_locked:md_forcefield_template_bundle": 1, "analysis_resource_not_locked:msigdb_full": 1, "analysis_resource_not_locked:orgdb_human_full": 2, "analysis_resource_not_locked:reactome_full": 1, "analysis_resource_not_locked:spatial_reference_full": 1, "full_mode_not_supported_in_registry": 9, "registry_evidence_entry_missing_or_blocked": 9} |

| Module | Environment | Resources | Worker | Blockers |
| --- | --- | --- | --- | --- |
| deg | r-bio-core->r-bio-full | not_required | pending_standard_worker_migration | full_mode_not_supported_in_registry, registry_evidence_entry_missing_or_blocked |
| survival | r-bio-core->r-bio-full | not_required | migrated_to_isolated_standard_worker |  |
| univariate | r-bio-core->r-bio-full | not_required | pending_standard_worker_migration | full_mode_not_supported_in_registry, registry_evidence_entry_missing_or_blocked |
| multivariate | r-bio-core->r-bio-full | not_required | pending_standard_worker_migration | full_mode_not_supported_in_registry, registry_evidence_entry_missing_or_blocked |
| enrichment | r-bio-core->r-bio-full | blocked | pending_standard_worker_migration | analysis_resource_not_locked:reactome_full, analysis_resource_not_locked:msigdb_full, analysis_resource_not_locked:go_full, analysis_resource_not_locked:kegg_full, analysis_resource_not_locked:orgdb_human_full, full_mode_not_supported_in_registry, registry_evidence_entry_missing_or_blocked |
| immune_infiltration | r-bio-core->r-bio-full | blocked | pending_standard_worker_migration | analysis_resource_not_locked:go_full, analysis_resource_not_locked:orgdb_human_full, full_mode_not_supported_in_registry, registry_evidence_entry_missing_or_blocked |
| correlation | r-bio-core->r-bio-full | not_required | pending_standard_worker_migration | full_mode_not_supported_in_registry, registry_evidence_entry_missing_or_blocked |
| spatial_transcriptomics | r-bio-core->r-spatial-full | blocked | pending_standard_worker_migration | analysis_full_environment_lock_not_restored:r-spatial-full, analysis_resource_not_locked:spatial_reference_full, analysis_resource_not_locked:cellchatdb_full, full_mode_not_supported_in_registry, registry_evidence_entry_missing_or_blocked |
| docking | r-bio-core->r-chem-full | blocked | pending_standard_worker_migration | analysis_full_environment_lock_not_restored:r-chem-full, analysis_resource_not_locked:autodock_vina_tool, analysis_resource_not_locked:docking_template_bundle, full_mode_not_supported_in_registry, registry_evidence_entry_missing_or_blocked |
| molecular_dynamics | r-bio-core->r-chem-gpu | blocked | pending_standard_worker_migration | analysis_full_environment_lock_not_restored:r-chem-gpu, analysis_resource_not_locked:gromacs_tool, analysis_resource_not_locked:md_forcefield_template_bundle, full_mode_not_supported_in_registry, registry_evidence_entry_missing_or_blocked |

### Survival Formal Migration Preflight

Survival now has scoped full/formal migration evidence for survival_minimal_v1. Global full-ready remains blocked while other environments, resources, and modules are incomplete.

| Evidence Area | Required Before Ready | Current Status |
| --- | --- | --- |
| standard_worker_evidence | registry-owned standard worker migration evidence entry for survival | survival_standard_worker_evidence_passed_scope_survival_minimal_v1_full_activation_still_blocked |
| result_package_evidence | passed full/formal package with result.json, provenance.json, tables, plots, reports, logs, and no result blockers | survival_full_formal_standard_package_passed_scope_survival_minimal_v1 |
| provenance_evidence | R/Bioconductor/package versions, input hash, parameter hash, random seed, command, and worker boundary metadata | survival_full_formal_provenance_passed_scope_survival_minimal_v1 |
| task_bridge_evidence | task-center registered full execution through the standard R worker boundary | migrated_to_isolated_standard_worker |
| frontend_package_catalog_evidence | result-index registered standard package consumed by package catalog/detail views, not module-private output | catalog_contract_exists_and_survival_full_package_registered_scope_survival_minimal_v1 |
| environment_evidence | r-bio-full restored renv lock and Docker build evidence | r_bio_full_environment_evidence_passed_scope_survival_minimal_v1_full_activation_still_blocked |
| forbidden_source_guard | mock, lite, blocked-full, legacy sidecar, module-private, copied, no-provenance, no-worker-invocation, and no-task-bridge sources are rejected | blocked_mock_lite_blocked_full_legacy_sidecar_forbidden |
| gate_evidence | default gate stays passed; require-full-ready remains blocked until every full environment/resource/module is ready | full_analysis_activation_blocked; require_full_ready_expected_exit_code_1; survival_scoped_migration_evidence_passed_global_full_ready_blocked |

## 4. P0/P1/P2/P3 问题清单

### P0

No rows reported.

### P1

| Issue ID | Source | Summary |
| --- | --- | --- |
| full_analysis_environment_locks_not_restored | environment_readiness | Full analysis environments remain scaffold-only or lack restored lock evidence. |
| full_analysis_resource_locks_not_complete | resource_readiness | Full analysis resources/tools remain blocked until version/hash/license/cache evidence is complete. |
| formal_algorithms_not_universally_migrated_to_isolated_standard_worker | standard_worker_migration_matrix | Formal algorithms still have pending isolated standard-worker migration rows. |

### P2

| Issue ID | Source | Summary |
| --- | --- | --- |
| RARCH-09 | app/analysis_runtime/task_bridge.py | Main backend task-system invocation boundary |
| RARCH-16 | analysis/schemas/output/provenance.schema.json and standard package validator | Reproducibility provenance contract |

### P3

| Issue ID | Source | Summary |
| --- | --- | --- |
| RARCH-04 | analysis/registry/analysis_modules.json::modules[*].modes | Mock / lite / full mode declarations |
| RARCH-12 | analysis/registry/analysis_environments.json | Dedicated environment split |
| RARCH-13 | renv/renv.*.lock | renv lock equivalent exists |
| RARCH-14 | docker/Dockerfile.r-* | Full analysis Docker image boundary |
| RARCH-15 | analysis/resources/manifest.json | Large resource version/source/hash/license/cache governance |
| RARCH-18 | analysis/modules/docking/module.json and analysis/modules/molecular_dynamics/module.json | Docking and molecular dynamics are external-tool adapters |

## 5. 涉及的文件路径

- `analysis/registry/analysis_environments.json`
- `analysis/registry/environment_lock_evidence.json`
- `renv/renv.bio-full.lock`
- `renv/renv.spatial-full.lock`
- `renv/renv.chem-full.lock`
- `analysis/schemas/output/environment_lock_evidence.schema.json`
- `analysis/schemas/output/environment_lock_evidence_registry.schema.json`
- `external_analysis_environments/`
- `docker/Dockerfile.r-bio-full`
- `docker/Dockerfile.r-spatial-full`
- `docker/Dockerfile.r-chem-full`
- `docker/Dockerfile.r-chem-gpu`
- `analysis/resources/manifest.json`
- `analysis/registry/resource_lock_evidence.json`
- `analysis/schemas/output/resource_lock_evidence.schema.json`
- `analysis/schemas/output/resource_lock_evidence_registry.schema.json`
- `analysis/resources/locks/`
- `external_analysis_resources/`
- `app/bioinformatics/`
- `analysis/registry/standard_worker_migration_evidence.json`
- `analysis/runners/run_module.R`
- `analysis/modules/`
- `analysis/schemas/input/module_input.schema.json`
- `analysis/schemas/output/standard_worker_migration_evidence.schema.json`
- `analysis/schemas/output/standard_worker_migration_evidence_registry.schema.json`
- `analysis/schemas/output/result_package.schema.json`

## 6. 最小可行整改路径

1. `restore_full_analysis_environment_locks`
2. `lock_full_analysis_resources`
3. `migrate_formal_algorithms_to_isolated_standard_worker`

## 7. 建议优先修改的文件

- `restore_full_analysis_environment_locks`
  - `analysis/registry/analysis_environments.json`
  - `analysis/registry/environment_lock_evidence.json`
  - `renv/renv.bio-full.lock`
  - `renv/renv.spatial-full.lock`
  - `renv/renv.chem-full.lock`
  - `analysis/schemas/output/environment_lock_evidence.schema.json`
  - `analysis/schemas/output/environment_lock_evidence_registry.schema.json`
  - `external_analysis_environments/`
  - ... 4 more files
- `lock_full_analysis_resources`
  - `analysis/resources/manifest.json`
  - `analysis/registry/resource_lock_evidence.json`
  - `analysis/schemas/output/resource_lock_evidence.schema.json`
  - `analysis/schemas/output/resource_lock_evidence_registry.schema.json`
  - `analysis/resources/locks/`
  - `external_analysis_resources/`
- `migrate_formal_algorithms_to_isolated_standard_worker`
  - `app/bioinformatics/`
  - `analysis/registry/standard_worker_migration_evidence.json`
  - `analysis/runners/run_module.R`
  - `analysis/modules/`
  - `analysis/schemas/input/module_input.schema.json`
  - `analysis/schemas/output/standard_worker_migration_evidence.schema.json`
  - `analysis/schemas/output/standard_worker_migration_evidence_registry.schema.json`
  - `analysis/schemas/output/result_package.schema.json`

## 8. 已完成的修改

- Architecture gate script exists and emits a schema-versioned JSON payload.
- The gate reports PASS/WARN/FAIL requirement rows, priority issues, top risks, and remediation guidance from one machine-readable source.
- Default gate policy remains read-only and does not execute workers, install R packages, or download resources.
- Architecture gate report schema validation is currently `passed`.
- Current P0 issue list is empty.
- Full analysis activation remains explicitly blocked rather than silently enabled.
- Legacy sidecar producer inventory verifies default execution gates for 3/3 remaining sidecar producers; transitional sidecars remain non-migration evidence.
- Survival has scoped survival_minimal_v1 full/formal standard-worker migration evidence; global full-ready remains blocked.
- Full/formal result package validation now rejects missing worker invocation, missing R session info, missing Docker/renv hashes, unregistered packages, and non-standard-worker or legacy sidecar evidence.
- Survival resource profile is documented as clinical_fixture_only; enrichment, spatial, docking, and molecular-dynamics resources remain global full-ready blockers.
- r-bio-full external evidence collection workflow is scaffolded as explicit manual tooling; default app-dev and default gate do not build Docker, restore renv, install R packages, or download resources.

## 9. 尚需人工决定的问题

| Item | Decision Required | Required Evidence | Scope |
| --- | --- | --- | --- |
| restore_full_analysis_environment_locks | detect-first external full environments only; default app-dev remains lightweight | full environment locks restored from controlled external analysis environments, each restored full environment lock has schema-valid environment_lock_evidence, Docker image build evidence captured outside default app-dev, validate_analysis_environment_registry.full_mode_ready becomes true |  |
| lock_full_analysis_resources | resource lock only; no runtime database fetch in user request flow | each full resource declares version, source, hash, license, and cache path, each locked full resource has schema-valid resource_lock_evidence, large resources are prelocked or explicitly imported before full mode, validate_analysis_resource_manifest.full_mode_ready becomes true |  |
| migrate_formal_algorithms_to_isolated_standard_worker | one module at a time; sidecar-only legacy adapter output is not full migration | selected formal module has registry-owned schema-valid standard worker migration evidence, validate_standard_worker_migration_evidence.status=passed, selected formal module has formal_worker_status=migrated_to_isolated_standard_worker, selected formal module executes through the task bridge and standard worker boundary, standard package includes result.json, provenance.json, tables, plots, reports, and logs, frontend consumes the standard package instead of module-private output paths | missing=9; passed=1; blocked=0; modules=deg, univariate, multivariate, enrichment, immune_infiltration, correlation, spatial_transcriptomics, docking, molecular_dynamics |
