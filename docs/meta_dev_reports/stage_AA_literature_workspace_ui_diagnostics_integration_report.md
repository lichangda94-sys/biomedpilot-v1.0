# Stage AA: Literature Workspace UI & Diagnostics Integration Report

## 本阶段目标

把 literature schema、import diagnostics、attachment registry、merge preview 和 audit log 能力接入 Meta Analysis workspace 的轻 UI 与 page state。所有能力仍为 Developer Preview / testing。

## 实际完成内容

- Literature Import page state 增加 diagnostics summary、warning list、failed records preview、diagnostics / warnings export path。
- Literature Import 页面导入成功后显示 diagnostics、warning list、failed preview 和导出路径。
- Workspace 已有 Recent Import Batches 读取能力，本阶段增加 page state 覆盖。
- 新增 Full-text / Attachment page state 和轻 UI，显示 attachment_registry、missing_fulltext_report、link/copy/ignore 模式、附件状态摘要。
- Duplicate Review page state 增加 merge preview、canonical candidate、match reasons、field conflicts。
- Duplicate Review 轻 UI 渲染 merge preview、field_sources、provenance_sources 和 warnings。
- 新增 Audit Log page state 和轻 UI，显示 audit/audit_log.jsonl 路径、事件总数、事件类型计数和 recent events。
- Meta workspace 增加 Attachment 和 Audit Log 轻量入口。

## 修改/新增文件

- `app/meta_analysis/pages/literature_import_page.py`
- `app/meta_analysis/pages/duplicate_review_page.py`
- `app/meta_analysis/pages/attachment_page.py`
- `app/meta_analysis/pages/audit_log_page.py`
- `app/meta_analysis/workspace.py`
- `tests/meta_analysis/test_stage_aa_literature_workspace_ui_diagnostics.py`

## Data Center / Task Center

- 未新增 Data Center 类型。
- 未新增 Task Center 类型。
- 保持上一阶段已有 `attachment_registry`、`missing_fulltext_report`、Attachment task 类型和既有 literature / dedup / fulltext 登记兼容。

## 新增测试

- Import page state diagnostics / warnings / failed preview / recent batches。
- Attachment page state registry、missing full-text report、link/copy/ignore 状态。
- Duplicate Review page state merge preview、canonical candidate、match reasons、field conflicts。
- Audit Log page state event counts、recent events、missing-log empty state。

## 测试结果

- `python3 -m pytest -q tests/meta_analysis`: 183 passed。
- 完整验证命令结果见最终汇报。

## 当前仍为 testing 的功能

- 文献导入 diagnostics 与 warning 展示。
- Attachment registry 和 missing full-text report。
- Duplicate merge preview 和 conflict 展示。
- Audit log 只读 summary。

## 已知限制

- Attachment 页面是轻量 testing 入口，不是完整 full-text management UI。
- Merge preview 已显示冲突和来源，但批量合并 UI 仍未实现。
- Audit log 页面只读，不提供筛选、导出或审计编辑。
- 不支持自动 PDF 下载、OCR 或正式 PubMed 检索 UI。

## 下一阶段建议

- 将 diagnostics / audit log 纳入 reproducibility package UI 检查。
- 增加真实 Zotero / EndNote RIS fixture 的 diagnostics 展示验证。
- 将 Attachment registry 与 Full-text screening / Quality 页面做更清晰的用户流程连接。
