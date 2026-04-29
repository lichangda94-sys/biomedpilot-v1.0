# Stage AA1: Literature Workspace Diagnostics Panels

## 本阶段目标

把现有 literature import diagnostics、recent import batches、attachment registry、missing full-text report 和 duplicate merge preview 能力接入 Meta Analysis 的 testing 级轻 UI / page state，方便测试人员检查文献导入质量、附件状态和重复文献合并依据。

当前 Meta Analysis 仍为 Developer Preview / testing，不是 production。

## 新增/修改页面

- `app/meta_analysis/pages/literature_import_page.py`
  - 继续提供 Import diagnostics summary、warning table、failed records preview 和 diagnostics / warnings export path。
- `app/meta_analysis/workspace.py`
  - Recent Import Batches 增强显示 `batch_id` 和 linked literature record count。
- `app/meta_analysis/pages/attachment_page.py`
  - Attachment Registry panel 增加 registry 缺失 warning、linked / copied / ignored / missing counts。
- `app/meta_analysis/pages/duplicate_review_page.py`
  - Duplicate Merge Preview panel 增加 canonical candidate、match reasons 和字段冲突摘要。

## Diagnostics 展示字段

- `warning_count`
- `failed_record_count`
- `missing_title_count`
- `missing_author_count`
- `missing_year_count`
- `missing_doi_count`
- `missing_pmid_count`
- `empty_abstract_count`
- `invalid_doi_count`
- `invalid_year_count`
- `diagnostics_path`
- `import_warnings.csv` path
- failed record examples
- parse warning examples

缺 diagnostics 文件时返回 missing warning 和默认 0 值，不崩溃。

## Recent Import Batches 展示字段

- `batch_id`
- `source_database`
- `source_format`
- `status`
- `created_at`
- raw / parsed / normalized / failed / warning counts
- `duplicate_candidate_count`
- `linked_literature_record_count`
- diagnostics path / summary

无导入批次时显示 empty state。

## Attachment Registry 展示字段

- `attachment_registry_path`
- registry missing warning
- `missing_fulltext_report_path`
- attachment count
- PDF attachment count
- linked / copied / ignored / missing counts
- broken path count
- per-attachment `record_id`、`file_name`、`attachment_type`、`file_exists`

不支持也不执行自动 PDF 下载、OCR、机构登录或版权受限下载。

## Merge Preview 展示字段

- duplicate group count
- exact / suspected duplicate group count
- group `record_ids`
- match reasons
- confidence
- canonical candidate
- merge preview availability
- merge field sources
- provenance sources
- field conflict summary:
  - title
  - creators/authors
  - year/date
  - journal/publication_title
  - DOI
  - PMID
  - clinical_trials_ids

旧 dedup decision (`keep_first` / `keep_second` / `skip`) 继续兼容。

## 新增测试

- `tests/meta_analysis/test_stage_aa1_literature_workspace_diagnostics_panels.py`
  - import diagnostics panel state
  - missing diagnostics non-crashing behavior
  - recent import batches empty state
  - recent import linked literature record count
  - attachment registry summary
  - missing full-text report path
  - missing attachment registry warning
  - duplicate merge preview field conflict summary
  - old dedup decision compatibility

## 已知限制

- 本阶段只做轻 UI / page state，不做完整交互式批量合并。
- Attachment panel 只展示 link / copy / ignore 状态，不做自动 PDF 获取。
- Merge preview 只展示合并依据，不自动写入正式 records。
- PRISMA 图仍未实现，本阶段不生成正式 PRISMA diagram。

## 测试结果

- `python3 -m compileall -q .`：通过
- `python3 -m pytest -q`：332 passed
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`：通过
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`：332 passed
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`：332 passed
- `python3 -m app.main --smoke-test`：通过

## 下一步建议

Stage AA2 可以继续把 Import / Duplicate / Attachment 面板接入更清晰的桌面布局，增加测试人员可读的 walkthrough 文档，并在不改变 shell 架构的前提下整理每个 panel 的空状态和错误提示。
