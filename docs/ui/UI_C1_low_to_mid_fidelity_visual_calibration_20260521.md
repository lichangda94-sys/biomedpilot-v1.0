# UI-C1 Low-to-Mid Fidelity Visual Calibration

Date: 2026-05-21

Status: completed implementation checkpoint

Goal: calibrate the existing low-fidelity PySide shell toward the first batch of local UI concept images while preserving semantic keys, page keys, module keys, status keys, Developer Preview boundaries and Result / Report / Export gating.

## 1. Concept Image Inputs

Local concept folder:

`/Users/changdali/Desktop/UI/界面示意图`

Referenced images:

- `App图标.png`
- `IMG-01 Welcome : 欢迎页.png`
- `IMG-02 Dashboard : 工作台首页.png`
- `IMG-03 Settings : 设置中心.png`
- `IMG-04 LabTools : 实验工具首页.png`
- `IMG-05 Bioinformatics 首页.png`
- `IMG-06 Meta Question & Type.png`
- `IMG-07 Bio Data Source.png`
- `IMG-08 Bio Data Check & Preparation.png`
- `IMG-09 Meta Search Strategy.png`
- `IMG-10 Bio Result & Report.png`
- `IMG-11 Bio Group & Design.png`
- `IMG-12 Meta Full-text Management.png`
- `IMG-13 Meta Extraction Form Design.png`

## 2. Implemented Calibration

| area | implemented |
|---|---|
| Dashboard | Removed the bottom status/support explanation panel. Dashboard now keeps three module cards plus a recent projects table. |
| LabTools | Home now shows only the three primary entries: General Calculator, Reagent Preparation and Experiment Modules. Removed visible boundary/explanation blocks and removed the five experiment categories as homepage large cards. |
| Bioinformatics | Target shell now presents a user-facing 7-step workflow overview, 2 auxiliary entries and quick access buttons. Removed visible Architecture Boundaries / resolver-first / preflight-first / result-schema-first copy from the user shell. |
| Bio Result & Report | Result / Report / Export shared shell remains adopted under Bioinformatics, uses `module.bioinformatics`, preserves step 6 `result_report` highlight when navigating to results and does not introduce Meta/PubMed/screening context. |
| Meta Analysis | Target IA copy is user-facing; full-text/extraction shell now includes only `全文管理`, `提取表设计`, `提取完成核查`, `历史记录` tabs. |
| Meta Extraction Form Design | Added type-specific Binary Outcome Meta field structure and a disabled `确认本次提取` action that semantically represents advancing to the extraction stage. |
| Tests | Updated focused UI tests away from removed developer-boundary text assertions and toward concept-aligned structure plus semantic/status properties. |

## 3. Preserved Boundaries

- `semanticKey`, `pageKey`, `moduleKey`, `statusKey` and `statusSemanticKey` remain in the shell surfaces.
- Developer Preview / 本地测试版 remains visible.
- `shell_only`, `testing`, `planned`, `draft`, `blocked` and preflight/report gating semantics remain in properties and shared panels.
- Result / Report / Export exports remain gated; no formal report-ready package is enabled.

## 4. Not Implemented

- No formal DEG / GSEA / survival / clinical association execution.
- No fake results, fake plots, fake p-values, fake DEG tables or fake report-ready package.
- No full i18n, no language switch and no report template rewrite.
- No active icon or asset replacement.
- No App icon, Finder icon, Info.plist icon binding, LaunchServices, packaging or desktop `.app` overwrite.
- No business calculation or analysis logic rewrite.

## 5. Commands and Results

| command | result |
|---|---|
| `find /Users/changdali/Desktop/UI/界面示意图 -maxdepth 2 -type f \| sort` | Confirmed all UI-C1 concept image files. |
| `git status --short` | Clean before UI-C1 edits. |
| `python3 -m pytest -q tests/ui/test_module_selection.py tests/ui/test_labtools_shell.py tests/ui/test_bioinformatics_ia_shell.py tests/ui/test_meta_analysis_ia_shell.py` | Passed; `36 passed in 6.11s`. |
| `python3 -m app.main --smoke-test` | Passed; source smoke reported `pyside6_available=True`. |
| `python3 -m pytest -q tests/ui tests/shared/test_semantic_keys.py tests/shared/test_result_report_export_shell.py` | Passed; `180 passed in 21.07s`. |
| `git diff --check` | Passed. |
| `git diff --cached --check` | Passed after staging. |
