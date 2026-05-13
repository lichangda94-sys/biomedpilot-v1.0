# Stage AB3: Production-like Literature Import Wizard

## 本阶段目标

在不重写 parser 的前提下，把现有 NBIB / RIS / CSV 导入、diagnostics、Recent Import Batches 和 Stage 6 最小导入面板包装为 testing / Developer Preview 级 step-based Literature Import Wizard。该阶段只做本地文件导入向导，不做真实数据库自动检索，不做 production 声明。

## Continuity audit

正式项目根目录：

- `/Users/changdali/Documents/BioMedPilot`

当前 git 状态审计：

- 分支：`codex/biomedpilot-root`
- 基线 HEAD：`a1a789c feat(meta): add protocol research question module`
- 未跟踪：`test_inputs/`，本阶段未触碰、未提交

审计的正式项目模块：

- `app/meta_analysis/pages/literature_import_page.py`
- `app/meta_analysis/services/literature_batch_import_service.py`
- `app/meta_analysis/services/literature_import_service.py`
- `app/meta_analysis/workspace.py`
- `app/meta_analysis/pages/workflow_dashboard_page.py`
- `tests/meta_analysis/test_stage_6_literature_import_panel.py`
- `tests/meta_analysis/test_stage_aa_literature_workspace_ui_diagnostics.py`
- `docs/meta_dev_reports/*`
- `docs/user_testing/*`

正式项目已有相关能力：

- `LiteratureBatchImportService` 已能调用 legacy batch service 执行 RIS / NBIB / CSV 导入。
- `LiteratureBatchImportSummary` 已返回 raw / parsed / normalized / failed / warning / duplicate counts。
- `LiteratureImportPageState` 已能展示 diagnostics cards、warning table、failed preview、diagnostics path 和 warnings CSV path。
- `recent_import_batch_summaries()` 已能读取 Recent Import Batches。
- Zotero RIS、EndNote RIS、PubMed NBIB 和异常 RIS fixtures 已有回归测试。

## Legacy capability audit

审计的 legacy 目录：

- `/Users/changdali/Documents/model9`
- `/Users/changdali/Documents/New project 2`
- `/Users/changdali/Documents/New project`

发现的 legacy 相关能力：

- `model9/literature/batch_service.py`
- `model9/literature/adapters.py`
- `New project 2/app/meta_analysis/legacy/app_meta/ui/literature_import_page.py`
- `New project 2/app/meta_analysis/legacy/tests/test_import_batch_service.py`

Legacy 能力判断：

- 当前 BioMedPilot 已通过 `LiteratureBatchImportService` 适配并复用 legacy batch import / parser 能力。
- legacy PySide literature import page 是 CSV-first demo UI，NBIB/RIS 是 placeholder，不接入当前 diagnostics、audit、manifest 或 workspace page state。

迁移结论：

- 未直接迁移 legacy UI。
- 继续复用正式项目中已封装的 legacy batch import adapter。

## Capabilities reused

- 复用 `LiteratureBatchImportService.execute_import()`。
- 复用 `LiteratureBatchImportRequest` / `LiteratureBatchImportSummary`。
- 复用 `import_diagnostics_visual_summary()`。
- 复用现有 diagnostics JSON / warnings CSV 输出。
- 复用现有 `LiteratureImportPage` 文件选择器入口和 Stage 6 导入控件。

## New behavior added

在 `app/meta_analysis/pages/literature_import_page.py` 新增 step-based wizard page state：

- `LiteratureImportWizardFilePreview`
- `LiteratureImportWizardState`
- `LiteratureImportWizardExecutionResult`
- `initial_literature_import_wizard_state()`
- `preview_literature_import_files(...)`
- `execute_literature_import_wizard(...)`

向导步骤：

- `source_selection`
- `file_selection`
- `import_preview`
- `import_diagnostics`
- `duplicate_review_handoff`

向导能力：

- file-picker-first 状态说明。
- 支持多文件输入的 page-state 模型。
- 支持 RIS / NBIB / CSV auto-detect。
- 支持 unsupported / missing file 预览错误。
- 支持导入前 record count preview。
- 支持按路径稳定排序后逐个调用现有 batch import service。
- 导入成功后暴露 diagnostics export paths、warnings CSV paths、warning table 和下一步 `Review duplicates`。

## Data Center / Task Center / audit / manifest / lineage impact

- 本阶段不新增 Data Center 类型。
- 本阶段不新增 Task Center 类型。
- 本阶段不新增 audit event 类型。
- 本阶段不新增 canonical manifest 路径。
- Literature import artifacts、diagnostics 和 import batches 继续由现有 batch import / diagnostics 链路生成。

## Tests added

新增：

- `tests/meta_analysis/test_stage_ab3_literature_import_wizard.py`

覆盖：

- wizard initial state 是 file-picker-first。
- 空输入返回用户可读错误，不崩溃。
- unsupported 文件在执行前被拒绝。
- RIS / NBIB / CSV preview 自动识别格式。
- 单文件导入后显示 diagnostics / warnings CSV / Review duplicates。
- 多文件导入按路径稳定排序并生成多个 batch。

Focused test result：

- `python3 -m compileall -q app/meta_analysis/pages/literature_import_page.py tests/meta_analysis/test_stage_ab3_literature_import_wizard.py`：通过
- `python3 -m pytest -q tests/meta_analysis/test_stage_ab3_literature_import_wizard.py tests/meta_analysis/test_stage_6_literature_import_panel.py`：10 passed

## Tests run and results

- `python3 -m compileall -q .`：通过
- `python3 -m pytest -q`：351 passed
- `python3 scripts/run_tests.py`：351 passed
- `python3 -m app.main --smoke-test`：通过，输出 `workspace_entries=2`、`bioinformatics_features=11`、`meta_analysis_features=7`、`pyside6_available=True`
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`：通过
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`：351 passed
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`：351 passed

## Remaining testing limitations

- 向导仍是 Developer Preview / testing，不是 production import wizard。
- 当前 PySide 页面仍是轻量文件选择器表单；wizard 主要以 page state / tests 形式加固。
- 多文件导入逐个执行，不做跨文件自动合并。
- 不自动修复原始 RIS / NBIB / CSV。
- 不执行真实 PubMed / Web of Science / CNKI / WanFang 在线检索。
- 不支持自动 PDF 下载、OCR、机构全文访问。

## Next-stage recommendation

进入 Stage AB4：Zotero-style Literature Table。

建议复用当前 literature records、diagnostics、duplicate risk、screening/fulltext/extraction status 和 duplicate merge preview，先做只读文献表格和颜色/标签状态，不自动删除或合并文献。
