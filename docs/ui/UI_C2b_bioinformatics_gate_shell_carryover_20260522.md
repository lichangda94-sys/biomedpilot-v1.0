# UI-C2b Bioinformatics Gate Shell Carry-over

## 1. Scope

This stage implements a scoped, read-only Bioinformatics state/action/result/report gate shell in UIShell. It follows UI-C2a planning and keeps formal analysis execution out of scope.

No packaged app was run. No App icon, Finder icon, `.icns`, iconset, `Info.plist`, LaunchServices, `dist/**`, or desktop entry was touched.

## 2. Carried Over / Reused Gate Shell Content

Added a small UIShell-local gate preview layer under `app/bioinformatics/analysis_ui/`:

- `state.py`: read-only `build_analysis_center_state(project_root)` for page state, action rows, result gate, report gate, export gate, and dependency rows.
- `action_rules.py`: action gate matrix with formal action rows disabled.
- `labels.py`: status/action labels for UI display.
- `__init__.py`: exports the state/action builder.

This is not a wholesale carry-over of `dev/bioinformatics`. It intentionally avoids formal executor imports and avoids helpers that materialize result indexes, reports, plots, or export packages.

## 3. UI Shell Integration

Integrated gate preview into existing Bioinformatics UI surfaces:

- Project Home: shows workflow gate summary and export gate state.
- Analysis Tasks: shows an action gate matrix for DEG, ORA/GSEA, KM/log-rank, Cox, report, and export gates.
- Result & Report: shows result/report/export gate preview and keeps add-to-report disabled.
- Report Export: shows export gate preview and keeps report generation/export disabled.

The target IA remains the 7-step main flow:

1. Project Home / 项目首页
2. Data Source / 数据来源
3. Data Check & Preparation / 数据检查与准备
4. Group & Design / 分组与分析设计
5. Analysis Tasks / 分析任务
6. Result & Report / 结果与报告
7. Report Export / 报告导出

## 4. Formal Executors Not Connected

The following executors/capabilities were not carried over and were not connected to normal UI actions:

| Capability | Current UI-C2b state | Reason |
| --- | --- | --- |
| formal DEG | disabled / blocked_until_carryover | Requires scoped carry-over of dependency, parameter, confirmation, result schema, result registry gates |
| ORA | disabled / blocked_until_backend | Current UIShell ORA runner is not a product-ready formal gate stack |
| GSEA | hidden_until_ready | Formal GSEA remains unavailable until rank metric validation and formal executor gates exist |
| KM / log-rank | disabled / blocked_until_carryover | Survival/clinical result writing requires separate scoped audit |
| Cox | disabled / blocked_until_carryover | Clinical interpretation and result registry gates require separate scoped audit |
| report-ready package | disabled_missing_report_ready | Report-ready gate and package execution not enabled |
| export package | disabled_missing_report_ready | Requires report-ready package and file picker/export adapter |

## 5. Buttons Downgraded To Disabled / Gated

| UI surface | Previous/high-risk entry | UI-C2b state |
| --- | --- | --- |
| Analysis Tasks | `运行 GEO 差异分析` | Replaced by disabled `运行 GEO 差异分析 - 开发诊断禁用`; `formalActionEnabled=false` |
| Result & Report | `加入报告` | Disabled add-to-report boundary; no report mutation |
| Report Viewer / Export | `生成 / 刷新项目报告` | Disabled report-generation button; no report-ready package generation |
| Report Viewer / Export | `导出 DOCX`, `导出 HTML` | Disabled export buttons; `exportGate=disabled_missing_report_ready` |

Existing backend methods were not removed or rewritten because old workflow tests call them directly. The normal visible UI entry points are now disabled/gated.

## 6. Result / Report / Export Boundary

Result & Report and Report Export remain separate gate surfaces:

- Result & Report displays result gate preview and keeps fake results/plots disabled.
- Report Export displays export gate preview and keeps export disabled.
- Imported, testing, and preflight entries are not upgraded to `formal_computed_result`.
- Existing `formal_computed_result` entries, if present in a project index, can only be represented as read-only state; UI-C2b does not generate new formal result entries.

## 7. Files Changed

Created:

- `app/bioinformatics/analysis_ui/__init__.py`
- `app/bioinformatics/analysis_ui/action_rules.py`
- `app/bioinformatics/analysis_ui/labels.py`
- `app/bioinformatics/analysis_ui/state.py`
- `tests/ui/test_bioinformatics_gate_shell.py`
- `docs/ui/UI_C2b_bioinformatics_gate_shell_carryover_20260522.md`

Modified:

- `app/bioinformatics/project_home.py`
- `app/bioinformatics/workflow_pages.py`

No `app/bioinformatics` executor logic was modified.

## 8. Validation

| Command | Result |
| --- | --- |
| `git status --short` | Showed only UI-C2b scoped files before staging |
| `git diff --stat` | Showed scoped changes in Bioinformatics UI shell and new gate shell files |
| `git diff --check` | Passed |
| `python3 -m py_compile app/bioinformatics/analysis_ui/__init__.py app/bioinformatics/analysis_ui/labels.py app/bioinformatics/analysis_ui/action_rules.py app/bioinformatics/analysis_ui/state.py app/bioinformatics/project_home.py app/bioinformatics/workflow_pages.py tests/ui/test_bioinformatics_gate_shell.py` | Passed |
| `python3 -m pytest -q tests/ui/test_bioinformatics_gate_shell.py` | Passed, 5 tests |
| `python3 -m pytest -q tests/ui/test_bioinformatics_ia_shell.py` | Passed, 9 tests |
| `python3 -m pytest -q tests/ui/test_bioinformatics_workflow_pages.py` | Passed, 87 tests |
| `python3 -m pytest -q tests/shared/test_result_report_export_shell.py` | Passed, 5 tests |
| `python3 -m app.main --smoke-test` | Passed |

## 9. Remaining Boundaries

Current UI-C2b still cannot enable:

- formal DEG
- ORA/GSEA
- survival/KM/log-rank
- Cox
- fake formal tables
- fake plots
- formal report generation
- report-ready package
- export

The next safe stage is a visual/layout implementation over this gate shell or a separate scoped carry-over audit for formal DEG gates. Formal executors should still not be connected until the corresponding state/action/result/report gates and tests are carried over as a distinct stage.
