# Bioinformatics L3 UI Path Map

Date: 2026-05-29

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Branch: `dev/bioinformatics`

Scope: Phase 2 single-point L3 proof for Bioinformatics only.

Meta Analysis was not modified or tested in this phase.

## Selected Path

Selected path: controlled formal DEG.

Reason: Phase 1 identified controlled formal DEG as the closest Bioinformatics L3 candidate because the current code already has standardized input resolution, DEG-ready gates, dependency detection, parameter confirmation, formal runner, result index v2, result review, plot artifact generation, and report-ready package gates.

## Current UI Chain

| Step | Current UI entry | Handler | Service / contract | Output |
| --- | --- | --- | --- | --- |
| Project input state | Existing Bioinformatics project with standardized repository assets | `BioinformaticsAnalysisTaskCenterWidget.refresh_project` | `resolve_analysis_inputs`, `build_analysis_center_state` | Resolver package rows, DEG gate rows, disabled/enabled reasons |
| Parameter confirmation | Button: `确认 formal DEG 参数` | `confirm_formal_deg_parameters` | `save_deg_parameter_confirmation` | `manifests/formal_deg_parameter_confirmation.json`, task-run/output plan |
| Formal DEG run | Button: `运行两组 controlled DEG` | `run_formal_controlled_deg_task` | `run_formal_controlled_deg` | Formal DEG TSV, run log, result index v2 entry |
| Result review | Results browser | `BioinformaticsResultsBrowserWidget.refresh_results` | `build_formal_deg_result_review` | Result table rows, summary, provenance |
| Table export | Button/API: `导出 DEG CSV` / `导出 DEG TSV` | `export_formal_deg_review_csv`, `export_formal_deg_review_tsv` | `export_formal_deg_review_table` | CSV/TSV export under `results/exports/formal_deg_review/` |
| Plot artifact | Button: `生成 formal DEG plot artifact` | `generate_formal_deg_plot_artifact` | `create_formal_deg_plot_artifact` | Real SVG plot artifact under `plots/formal_deg/<result_id>/`, registered in result index |
| Report package | Button: `生成 formal DEG report-ready package` | `generate_formal_deg_report_ready_package` | `create_formal_deg_report_ready_package` | Formal DEG section-only report package |

## Real Input Used For Proof

The focused proof uses real project files in a temporary Bioinformatics project:

```text
input/deg_l3_count_matrix.tsv
input/deg_l3_sample_metadata.tsv
input/deg_l3_group_design.json
standardized_data/repositories/repository_manifest.json
manifests/standardized_assets_registry.json
```

The expression matrix is a real small raw-count matrix with three genes and six samples. It is not a mock result table and is not a hard-coded DEG output. The DEG result table is produced by the formal DEG runner after the current UI confirms parameters and clicks the run button.

## Gate Behavior Proven

| Gate | Evidence |
| --- | --- |
| Resolver package | Current UI reads standardized repository/registry through resolver state. |
| Parameter confirmation | Current UI button writes `formal_deg_parameter_confirmation.json`. |
| Dependency gate | Current environment uses detect-first Python DEG dependencies; no install action is used. |
| Formal run | Current UI button calls formal controlled DEG runner. |
| Result semantics | Result index entry is `formal_computed_result`. |
| Plot semantics | Plot artifact inherits `formal_computed_result` from the source result. |
| Report boundary | Report package is formal DEG section-only; GSEA and survival remain disabled. |
| Clinical boundary | UI guard text and report boundaries keep the result as statistical analysis only. |

## Boundaries

This is a single-point Bioinformatics L3 proof for controlled formal DEG. It does not claim:

- all Bioinformatics analysis types are L3 complete;
- GEO/TCGA/GTEx full upstream acquisition is part of this proof;
- ORA/GSEA/survival/clinical/risk-score are L3 complete;
- clinical, diagnostic, prognostic, treatment, or public-release production-grade conclusions are supported.

## Verification Test

```text
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_l3_formal_deg_loop.py -q
1 passed
```
