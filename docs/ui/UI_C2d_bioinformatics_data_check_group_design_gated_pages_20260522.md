# UI-C2d Bioinformatics Data Check + Group Design Gated Pages

## 1. Scope

This stage implemented gated PySide UI for Bioinformatics step 3 and step 4:
- Data Check & Preparation / 数据检查与准备.
- Group & Design / 分组与设计.

The work only adds gated page structure, readiness/status display, design draft surfaces, and focused tests.

## 2. Strict Boundary

Not enabled:
- Formal DEG executor.
- ORA / GSEA executor.
- KM / log-rank / Cox / survival executor.
- Any analysis executor run.
- Fake expression matrix.
- Fake DEG table.
- Fake plot.
- Report generation.
- Export.
- GEO / TCGA / GTEx download or real local import.
- Packaged app, App icon, Finder icon, `.icns`, `Info.plist`, LaunchServices, signing, or desktop entry work.

## 3. Data Check & Preparation

Added a gated readiness card to the Data Check page with:

| check | status semantics |
|---|---|
| expression matrix integrity | missing / passed |
| sample annotation completeness | missing / passed |
| clinical data completeness | warning / passed |
| gene annotation mapping | ready_for_preflight / warning |
| batch/platform consistency | ready_for_preflight / warning |
| missing rate check | ready_for_preflight / warning |
| outlier sample detection | blocked / warning |

The page now shows a `bioinformaticsDataCheckStatusChip` with blocked, missing, or `analysis.status.preflight_only` semantics.

The readiness summary explicitly states:
- Data Check only evaluates preflight eligibility.
- No fake matrix, result, plot, report, or export is generated.
- It does not display a formal quality score.

Save/report behavior:
- `Save Report - file picker required` is disabled.
- Copy check summary is allowed and clipboard-only.
- Standardization report export is downgraded to disabled / file-picker-required and does not write a report file.

## 4. Group & Design

Added a gated design draft card with:

| surface | content |
|---|---|
| group setup | Tumor, Normal, optional unused group |
| comparison setup | Tumor_vs_Normal draft or current comparison draft |
| covariate settings | Age, Gender, Smoking History, Stage |
| design summary | preflight eligibility wording, not formal analysis |
| Run Preflight | disabled / gated preview |

The page keeps existing group/comparison editing compatibility but labels actions as draft/gated and keeps `formalActionEnabled=false`.

`ready_for_preflight` remains a preflight boundary and is not upgraded to `formal_computed_result`.

## 5. Gate Semantics

| area | C2d state |
|---|---|
| Data Check readiness | preflight eligibility only |
| Group Design | design draft / comparison draft |
| Covariates | draft only, no model execution |
| Result semantic | no formal computed result |
| Report status | not report-ready |
| Export gate | disabled missing report-ready |

## 6. Tests Added

Added:
- `tests/ui/test_bioinformatics_data_check_group_design_gated_pages.py`

Focused coverage:
- Data Check page opens and includes the required readiness checks.
- Save Report is disabled/gated.
- Data Check does not create fake results.
- Standardization report export is disabled and does not write a report.
- Group & Design page shows groups, comparison, covariates, design summary.
- Run Preflight is disabled/gated and not a formal run.
- Result/report/export gates remain disabled.

## 7. Verification

Commands run before final commit:

| command | result |
|---|---|
| `python3 -m py_compile app/bioinformatics/workflow_pages.py tests/ui/test_bioinformatics_data_check_group_design_gated_pages.py` | passed |
| `python3 -m pytest -q tests/ui/test_bioinformatics_data_check_group_design_gated_pages.py` | 4 passed |
| `python3 -m pytest -q tests/ui/test_bioinformatics_gate_shell.py` | 5 passed |
| `python3 -m pytest -q tests/ui/test_bioinformatics_project_home.py tests/ui/test_bioinformatics_workflow_pages.py` | 99 passed |
| `python3 -m pytest -q tests/ui/test_bioinformatics_ia_shell.py` | 9 passed |
| `python3 -m app.main --smoke-test` | passed |
| `git diff --check` | passed |
| `git diff --cached --check` | passed |

## 8. Business Logic Statement

This stage modifies active Bioinformatics UI shell code and focused UI tests, but does not modify Bioinformatics executor business logic.

No formal analysis, report, export, packaging, signing, App icon, Finder icon, `.icns`, `Info.plist`, LaunchServices, or desktop app replacement work was performed.
