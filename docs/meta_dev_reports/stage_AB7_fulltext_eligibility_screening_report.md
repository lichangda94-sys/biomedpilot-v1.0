# Stage AB7: Full-text Eligibility Screening Report

## 本阶段目标

把现有 fulltext / attachment testing 能力包装成正式的 Full-text Eligibility Screening 阶段：从 title / abstract included 或 maybe 记录生成全文候选清单，支持人工记录全文状态、PDF link/copy、全文排除原因、全文排除报告和 final included studies。

当前状态仍为 Developer Preview / testing，不是 production。

## Continuity audit

审计了当前正式项目 `/Users/changdali/Documents/BioMedPilot`：

- `app/meta_analysis/services/fulltext_service.py`
- `app/meta_analysis/services/attachment_service.py`
- `app/meta_analysis/models/systematic_review.py`
- `app/meta_analysis/pages/attachment_page.py`
- `app/meta_analysis/pages/screening_page.py`
- `app/meta_analysis/pages/workflow_dashboard_page.py`
- `app/meta_analysis/services/project_contract_service.py`
- `app/meta_analysis/services/report_manifest_service.py`
- `tests/meta_analysis/test_systematic_review_workflow_completion.py`
- `tests/meta_analysis/test_stage_ab6_title_abstract_screening_ux.py`
- `docs/meta_dev_reports/stage_AB6_title_abstract_screening_ux_report.md`

确认 AB1 workflow dashboard、AB5 criteria hints、AB6 title / abstract screening UX 仍保留。

## Legacy capability audit

审计了只读 legacy 目录：

- `/Users/changdali/Documents/model9/fulltext/`
- `/Users/changdali/Documents/New project 2/app/meta_analysis/legacy/fulltext/`
- `/Users/changdali/Documents/New project/app/meta_analysis/legacy/fulltext/`（未发现优于当前正式项目的 fulltext eligibility 实现）

legacy 只包含较早的 `FullTextRecord` / `FullTextStore` / `FullTextService`，没有当前 BioMedPilot 的 attachment registry、audit log、Data Center、Task Center、manifest 或 workflow dashboard 集成。因此未迁移 legacy 代码。

## 已存在能力

- `FullTextService` 已支持：
  - `fulltext/fulltext_registry.json`
  - `fulltext/fulltext_screening_decisions.json`
  - `reports/full_text_exclusion_report.csv`
  - PDF link/copy 到 Attachment service
  - full-text availability status
  - full-text exclusion reasons
- `AttachmentService` 已支持：
  - `link_existing_files`
  - `copy_to_project_library`
  - `ignore_attachments`
  - `attachments/attachment_registry.json`
  - `reports/missing_fulltext_report.csv`
- AB6 已生成 title / abstract decisions page-state 和 artifacts。

## 复用能力

- 复用 `FullTextService` 作为兼容保存层。
- 复用 `AttachmentService` 处理 PDF link/copy，不直接写系统路径。
- 复用 `FULLTEXT_EXCLUSION_REASONS`。
- 复用 Data Center、Task Center、audit log、project contract manifest。
- 复用 workflow dashboard 状态推断机制。

## 新增行为

新增 `FullTextEligibilityService`：

- 从 `screening/title_abstract_decisions.json`、`screening/screening_decisions.json` 或 screening queue 生成全文候选。
- 候选仅来自 title / abstract `included`、`maybe` 或 `needs_review`。
- 支持 eligibility status：
  - `not_checked`
  - `available_online`
  - `local_pdf_linked`
  - `local_pdf_copied`
  - `missing_full_text`
  - `failed_to_access`
  - `manual_review_required`
  - `excluded_after_full_text_review`
  - `included_for_extraction`
- 保存：
  - `fulltext/fulltext_eligibility_decisions.json`
- 保留兼容：
  - `fulltext/fulltext_screening_decisions.json`
- 导出：
  - `fulltext/fulltext_exclusion_report.csv`
  - `reports/full_text_exclusion_report.csv`
  - `fulltext/final_included_studies.json`

新增 `FullTextEligibilityPageState`：

- 显示 candidate list。
- 显示 eligibility status options。
- 显示 exclusion reason options。
- 显示 output paths。
- 显示 warning 和 testing limitations。
- 空项目不崩溃。

## Data Center / Task Center / audit / manifest / lineage 影响

Data Center 新增或登记：

- `fulltext_eligibility_decisions`
- `fulltext_eligibility_exclusion_report`
- `final_included_studies`

Task Center：

- 继续复用既有 `fulltext_screening_decision`、`fulltext_attach`、`fulltext_exclusion_export`。
- 未新增 shared TaskType。

Audit log：

- 保存 eligibility decision 时写 `fulltext_status_changed`。
- 导出 final included studies 时写 `record_saved`。
- 导出 full-text eligibility exclusion report 时写 `report_exported`。

Manifest / lineage：

- 新增 canonical paths：
  - `fulltext/fulltext_eligibility_decisions.json`
  - `fulltext/fulltext_exclusion_report.csv`
  - `fulltext/final_included_studies.json`
- 新增 lineage：
  - fulltext eligibility decisions 追溯到 title / abstract decisions。
  - final included studies 追溯到 fulltext eligibility decisions。

Workflow dashboard：

- Full-text / Attachment step 现在识别 `fulltext_eligibility_decisions.json` 和 `final_included_studies.json`。
- 旧 `fulltext_registry.json` / `attachment_registry.json` 仍作为 fallback 兼容。

Report manifest：

- Full-text section 增加 eligibility decisions、eligibility exclusion report 和 final included studies 来源。

## 新增/修改文件

新增：

- `app/meta_analysis/services/fulltext_eligibility_service.py`
- `app/meta_analysis/pages/fulltext_eligibility_page.py`
- `tests/meta_analysis/test_stage_ab7_fulltext_eligibility_screening.py`
- `docs/meta_dev_reports/stage_AB7_fulltext_eligibility_screening_report.md`

修改：

- `app/meta_analysis/services/project_contract_service.py`
- `app/meta_analysis/pages/workflow_dashboard_page.py`
- `app/meta_analysis/services/report_manifest_service.py`
- `app/meta_analysis/workspace.py`

## 未迁移内容及原因

未迁移 legacy fulltext store/service，因为当前正式项目已经有更完整的 fulltext + attachment + audit + Data Center / Task Center 实现。直接迁移 legacy 会绕过当前主链和 manifest/audit 机制。

## 未实现内容

- 不自动下载 PDF。
- 不做 OCR。
- 不做机构代理登录或版权受限全文访问。
- 不做复杂批量全文筛选 UI。
- 不做正式 PRISMA diagram。
- 不把 final included studies 声明为 production 纳入清单。

## 测试结果

已运行：

- `python3 -m compileall -q .`：通过
- `python3 -m pytest -q tests/meta_analysis/test_stage_ab7_fulltext_eligibility_screening.py`：7 passed
- `python3 -m pytest -q`：373 passed
- `python3 scripts/run_tests.py`：373 passed
- `python3 -m app.main --smoke-test`：通过，`workspace_entries=2`、`bioinformatics_features=11`、`meta_analysis_features=7`
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`：通过
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`：373 passed
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`：373 passed

## 下一阶段建议

进入 Stage AB8：Extraction UI Simplification。建议继续复用已有 ExtractionRecord core、draft、validation、multi-outcome rows 和 completeness score，重点做 page-state 表格化、manual supplement log 和更清晰的字段错误定位，不重写 extraction schema。
