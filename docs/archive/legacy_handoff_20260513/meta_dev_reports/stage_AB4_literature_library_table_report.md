# Stage AB4: Zotero-style Literature Table

## 本阶段目标

新增 testing / Developer Preview 级只读 Literature Library page state，把导入文献、重复风险、筛选状态、全文状态和提取状态汇总为用户能理解的 Zotero-style 文献表格。该阶段不做批量编辑、不自动删除、不自动合并。

## Continuity audit

正式项目根目录：

- `/Users/changdali/Documents/BioMedPilot`

当前 git 状态审计：

- 分支：`codex/biomedpilot-root`
- 基线 HEAD：`842a9d6 feat(meta): add literature import wizard`
- 未跟踪：`test_inputs/`，本阶段未触碰、未提交

审计的正式项目模块：

- `app/meta_analysis/pages/literature_import_page.py`
- `app/meta_analysis/pages/duplicate_review_page.py`
- `app/meta_analysis/pages/workflow_dashboard_page.py`
- `app/meta_analysis/workspace.py`
- `app/meta_analysis/services/dedup_decision_service.py`
- `app/meta_analysis/services/duplicate_review_service.py`
- `tests/meta_analysis/*duplicate*`
- `tests/meta_analysis/test_stage_ab3_literature_import_wizard.py`
- `docs/meta_dev_reports/*`

正式项目已有相关能力：

- 已有 Literature Import Wizard 和 diagnostics。
- 已有 duplicate groups、merge preview、duplicate decisions。
- 已有 screening/fulltext/extraction artifacts。
- 尚无统一只读文献库表格 page state。

## Legacy capability audit

审计的 legacy 目录：

- `/Users/changdali/Documents/model9`
- `/Users/changdali/Documents/New project 2`
- `/Users/changdali/Documents/New project`

发现的 legacy 相关能力：

- `model9/app_meta/ui/literature_import_page.py`
- `New project 2/app/meta_analysis/legacy/app_meta/ui/literature_import_page.py`

Legacy 能力判断：

- legacy 页面有 Imported records 表格和 Import Quality 卡片，但主要面向 demo/CSV 状态，不读取当前 BioMedPilot project_dir、duplicate groups、screening/fulltext/extraction artifacts。

迁移结论：

- 未迁移 legacy UI。
- 本阶段采用当前正式项目 artifact/page-state 架构重新接入只读文献表格。

## Capabilities reused

- 复用当前 literature artifacts：`literature/literature_records.json`、`literature_import/*_records.json`。
- 复用 duplicate groups 结构，兼容新旧字段：`group_id` / `duplicate_group_id`，`record_ids` / `candidate_record_ids`，`reason` / `match_reason`。
- 复用 screening/fulltext/extraction artifacts 中的 record-level 状态。
- 复用 current workspace，把 `LiteratureLibraryPage` 接在 Literature Import 后。

## New files

- `app/meta_analysis/pages/literature_library_page.py`
- `tests/meta_analysis/test_stage_ab4_literature_library_table.py`

## Modified files

- `app/meta_analysis/workspace.py`

## New behavior added

新增只读 page state：

- `LiteratureLibraryRow`
- `LiteratureLibraryState`
- `initial_literature_library_state`
- `literature_library_state_from_project`
- `LiteratureLibraryPage`

表格字段：

- internal record ID
- title
- authors
- first author
- corresponding author
- journal
- year / publication date
- DOI
- PMID
- publication type
- abstract availability
- source database
- source file
- import batch
- duplicate risk
- screening status
- full-text status
- extraction status

Duplicate risk 标签：

- 红色：`high_duplicate_risk`
- 黄色：`probable_duplicate / conflicting identifier`
- 灰色：`possible_duplicate`
- 绿色：`no_obvious_duplicate_risk`

重要说明：

- 绿色只表示未发现明显重复风险，不代表文献可信、不代表质量高。
- 本页面只读，不自动删除、不自动合并、不改变 workflow 状态。

## Data Center / Task Center / audit / manifest / lineage impact

- 本阶段不新增 Data Center 类型。
- 本阶段不新增 Task Center 类型。
- 本阶段不写 audit log。
- 本阶段不新增 canonical manifest 路径。
- 本阶段只读取现有 artifacts 并生成 UI/page-state 状态。

## Tests added

新增：

- `tests/meta_analysis/test_stage_ab4_literature_library_table.py`

覆盖：

- 空项目 no-crash empty state。
- 文献记录字段映射：title、authors、first author、corresponding author、journal、DOI/PMID、abstract。
- screening/fulltext/extraction status 汇总。
- exact/suspected duplicate risk 标签和颜色。
- 绿色标签不包含 trusted/可信含义。
- legacy `literature_import/*_records.json` shape 兼容读取。

Focused test result：

- `python3 -m compileall -q app/meta_analysis/pages/literature_library_page.py app/meta_analysis/workspace.py tests/meta_analysis/test_stage_ab4_literature_library_table.py`：通过
- `python3 -m pytest -q tests/meta_analysis/test_stage_ab4_literature_library_table.py`：5 passed

## Tests run and results

- `python3 -m compileall -q .`：通过
- `python3 -m pytest -q`：356 passed
- `python3 scripts/run_tests.py`：356 passed
- `python3 -m app.main --smoke-test`：通过，输出 `workspace_entries=2`、`bioinformatics_features=11`、`meta_analysis_features=7`、`pyside6_available=True`
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`：通过
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`：356 passed
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`：356 passed

## Remaining testing limitations

- 文献表格当前是只读 page state / lightweight page，不是完整 Zotero 替代品。
- 不支持批量编辑、批量删除或批量合并。
- duplicate risk 来自当前 duplicate groups artifact，不代表文献质量判断。
- 绿色标签不是可信文献声明。

## Next-stage recommendation

进入 Stage AB5：Inclusion / Exclusion Criteria Builder。

建议新增 criteria models/service/page state，写入 `criteria/inclusion_criteria.json`、`criteria/exclusion_criteria.json`、`criteria/criteria_summary.md`，并在 screening/full-text/PRISMA 中逐步引用 criteria reason。
