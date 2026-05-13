# Stage AA2: Tester Walkthrough & Workspace Readability Polish

## 本阶段目标

在不新增大功能的前提下，把 Stage AA1 已完成的 Import diagnostics、Recent Import Batches、Attachment Registry、Duplicate Merge Preview、PRISMA trace 和 audit export 整理成测试人员能理解、能操作、能记录问题的 testing 级说明、page state 文案和测试文档。

Meta Analysis 仍为 Developer Preview / testing，不是 production。

## 修改页面

- `app/meta_analysis/pages/literature_import_page.py`
  - Import page state 增加 panel help、testing limitations 和 warning severity counts。
- `app/meta_analysis/pages/duplicate_review_page.py`
  - Duplicate Review page state 增加 panel help、testing limitations 和 merge preview warning severity。
- `app/meta_analysis/pages/attachment_page.py`
  - Attachment page state 增加 panel help、testing limitations 和 attachment warning severity。
- `app/meta_analysis/pages/reporting_page.py`
  - Reporting page state / PRISMA trace state 增加 panel help、testing limitations 和 source/audit warning severity。
- `app/meta_analysis/pages/audit_log_page.py`
  - Audit page state 增加 panel help 和 testing limitations。

## 新增文案/说明

每个相关 page state 均补充：

- 当前面板显示什么
- 输入来自哪里
- 输出写到哪里
- warning 的含义
- 下一步建议
- testing 限制

重点说明：

- Diagnostics 是 testing 级质量检查，不自动修复导入文件。
- Merge preview 是 reviewer 辅助，不替代人工判断。
- Attachment 只支持手动 link / copy / ignore 状态，不自动下载 PDF。
- Reporting 继续区分 test summary、formal Markdown、HTML/DOCX testing report，正式 PDF 和 PRISMA diagram 未开放。
- Audit log 是只读追踪摘要，不替代 Task Center。

## Warning Severity 分类

新增 `app/meta_analysis/pages/warning_severity.py`。

支持四类 severity：

- `blocker`
- `major`
- `minor`
- `info`

当前覆盖：

- Import diagnostics
  - missing title / failed record：blocker
  - missing author / year、invalid DOI/year、duplicate identifier：major
  - missing DOI / PMID、empty abstract：minor
- Attachment
  - missing source file：blocker
  - registry missing、broken paths：major
  - missing full-text：minor
  - no automatic PDF / OCR：info
- Merge preview
  - no records / missing preview：blocker
  - field conflict：major
  - low confidence：minor
- PRISMA trace
  - missing source reference：major
  - missing audit events：minor
  - formal PRISMA diagram not implemented：info

这是轻量 helper，不是复杂规则引擎。

## 新增 Tester Walkthrough

新增：

- `docs/user_testing/meta_literature_workspace_walkthrough.md`

内容包括：

- 如何导入 RIS / NBIB / CSV
- 如何查看 Import diagnostics
- 如何理解缺 title / author / year / DOI / PMID
- 如何查看 Recent Import Batches
- 如何查看 Duplicate Merge Preview
- 如何检查 Attachment Registry
- 如何导出 Missing Full-text Report
- 如何查看 PRISMA Source References
- 如何导出 review log
- 哪些 warning 可以接受
- 哪些 warning 需要记录为 blocker / major

## 新增 Tester Checklist

新增：

- `docs/user_testing/meta_literature_workspace_checklist.md`

表格字段：

- 测试项
- 操作步骤
- 预期结果
- 失败时记录内容
- 严重程度建议

## 已知限制更新

更新：

- `docs/user_testing/known_limitations.md`

新增说明：

- diagnostics 是 testing 级质量检查
- merge preview 是辅助，不替代 reviewer 判断
- attachment 不自动下载 PDF
- 不做 OCR
- 不做机构全文访问
- 正式 PRISMA diagram 未实现

## 测试结果

- `python3 -m compileall -q .`：通过
- `python3 -m pytest -q`：336 passed
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m compileall -q .`：通过
- `'/Users/changdali/Documents/model9/.venv/bin/python' -m pytest -q`：336 passed
- `'/Users/changdali/Documents/model9/.venv/bin/python' scripts/run_tests.py`：336 passed
- `python3 -m app.main --smoke-test`：通过

## 下一步建议

Stage AA3 可以继续做轻量桌面可读性检查：把 walkthrough 中的测试步骤映射到 workspace 中的面板顺序，增加 sample input 的固定说明和 tester issue template。仍建议避免修改 shell 架构或 packaging。
