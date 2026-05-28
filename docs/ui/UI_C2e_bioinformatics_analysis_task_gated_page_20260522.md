# UI-C2e Bioinformatics Analysis Tasks + DEG Preflight Review Page

## 1. Scope

This stage implemented the gated UI for Bioinformatics step 5:
- Analysis Tasks / 分析任务.
- Task gate matrix.
- DEG parameter review.
- DEG preflight checklist.
- Disabled/gated analysis actions.

The implementation is UI shell and gate review only.

## 2. Strict Boundary

Not enabled:
- Formal DEG executor.
- ORA / GSEA executor.
- KM / log-rank / Cox / survival executor.
- Any real analysis run from the normal UI.
- DEG result table generation.
- Volcano, heatmap, enrichment, survival, or clinical plots.
- Report generation.
- Export.
- `preflight` states upgrading to `formal_computed_result`.
- Packaged app, App icon, Finder icon, `.icns`, `Info.plist`, LaunchServices, signing, or desktop entry work.

Existing direct internal methods for historical tests remain in place, but the normal Analysis Tasks visible buttons are disabled/gated.

## 3. Analysis Task Matrix

The page now displays a gated matrix for:

| task | UI state | dependency | blocked action |
|---|---|---|---|
| DEG | preflight / parameter review | expression matrix + group design | formal DEG executor |
| ORA | planned / disabled | requires DEG result | ORA executor |
| GSEA | planned / disabled | requires DEG result + GMT | GSEA executor |
| KM / log-rank | planned / disabled | requires survival audit | KM/log-rank executor |
| Cox | planned / disabled | requires clinical/survival audit | Cox executor |
| Clinical Association | audit required / disabled | requires clinical variable audit | clinical association executor |

## 4. DEG Parameter Review

The DEG review table shows:
- comparison, defaulting safely to `Tumor_vs_Normal` if no comparison exists.
- input matrix state as registered / preflight-ready or registered / gated.
- method policy as preview/planned policy, not an enabled formal executor.
- FDR threshold.
- log2FC threshold.
- low-expression filter.
- normalization review.
- missing value handling review.
- batch handling review.
- dependency snapshot preview.

Method policy wording explicitly distinguishes preview/planned executor policy from current enabled backend status.

## 5. Preflight Checklist

The preflight checklist includes:
- input matrix exists.
- sample metadata complete.
- group design valid.
- comparison valid.
- sample name matching.
- minimal group size.
- dependency status.
- output plan / result schema.

The checklist is marked with `resultSemanticKey=preflight_only` and `formalActionEnabled=false`.

## 6. Disabled Actions

The following visible actions are disabled/gated:

| button | behavior |
|---|---|
| Run Preflight - gated preview | `disabled_preflight_preview` |
| Run Formal DEG - disabled | `disabled_formal_executor` |
| Generate Plot - disabled | `disabled_no_result` |
| Add to Report - disabled | `disabled_report_draft` |
| Export Result - disabled | `disabled_export_gate` |
| 配置 DEG 任务 | disabled task plan preview |
| 生成 DEG 分析任务记录 | disabled task record preview |
| 生成并校验 DEG 输入 | disabled preflight preview |
| 创建任务 | disabled task creation preview |

The legacy `运行 GEO 差异分析 - 开发诊断禁用` button remains disabled and marked `developer_diagnostics_only`.

## 7. Result / Report / Export Semantics

C2e does not create:
- result artifacts.
- formal computed results.
- DEG tables.
- plots.
- report drafts/packages.
- export packages.

The result/report/export gates remain disabled until a future report-ready package exists.

## 8. Tests Added

Added:
- `tests/ui/test_bioinformatics_analysis_tasks_gated_page.py`

Focused coverage:
- Analysis Tasks page opens.
- DEG / ORA / GSEA / KM / Cox / Clinical Association task matrix is present.
- DEG parameter review and preflight checklist are present and preflight-only.
- Formal DEG, plot, report, and export actions are disabled.
- Existing old preflight button is disabled in the normal UI.
- Preflight states do not create formal result/report/export artifacts.

## 9. Verification

Commands run before final commit:

| command | result |
|---|---|
| `python3 -m py_compile app/bioinformatics/workflow_pages.py tests/ui/test_bioinformatics_analysis_tasks_gated_page.py` | passed |
| `python3 -m pytest -q tests/ui/test_bioinformatics_analysis_tasks_gated_page.py` | 4 passed |
| `python3 -m pytest -q tests/ui/test_bioinformatics_gate_shell.py` | 5 passed |
| `python3 -m pytest -q tests/ui/test_bioinformatics_data_check_group_design_gated_pages.py` | 4 passed |
| `python3 -m pytest -q tests/ui/test_bioinformatics_project_home.py tests/ui/test_bioinformatics_workflow_pages.py` | 99 passed |
| `python3 -m pytest -q tests/ui/test_bioinformatics_ia_shell.py` | 9 passed |
| `python3 -m app.main --smoke-test` | passed |
| `git diff --check` | passed |
| `git diff --cached --check` | passed |

## 10. Business Logic Statement

This stage modifies active Bioinformatics UI shell code and focused UI tests, but does not modify Bioinformatics executor business logic.

No formal analysis, report, export, packaging, signing, App icon, Finder icon, `.icns`, `Info.plist`, LaunchServices, or desktop app replacement work was performed.
