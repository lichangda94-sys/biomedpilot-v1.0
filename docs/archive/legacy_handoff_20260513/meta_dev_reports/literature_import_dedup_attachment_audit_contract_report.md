# Literature Import, Dedup, Attachment, And Audit Contract Report

## 本轮目标

加固 Meta Analysis 文献导入、字段标准化、导入诊断、去重、附件、审计日志和 PRISMA 来源追溯契约。所有能力仍为 Developer Preview / testing。

## 实际完成

- 新增 literature schema registry、field sanitizer、import options、import diagnostics。
- 扩展 legacy 文献模型，兼容旧字段并支持 creators、authors_text、first_author、publication_type、date、publication_title、clinical_trials_ids、external_key。
- 强化 DOI / PMID / title / year / journal / creators / publication type 标准化。
- 强化 duplicate detection：PMID、DOI、ClinicalTrials ID exact；title / first author / year / journal suspected。
- 扩展 duplicate group 新旧字段兼容，并新增 merge preview。
- 新增 Attachment service，支持 ignore / link / copy，不支持自动下载 PDF。
- FullTextService 通过 Attachment service 写入 PDF 附件，同时保持 fulltext_registry 兼容。
- 新增 Meta audit log：`audit/audit_log.jsonl`。
- PRISMA summary 继续从 artifacts 汇总，并补充 source references / audit references。
- 更新用户测试 Feature Availability 和 Known Limitations。

## 新增数据 / 输出

- `literature/import_diagnostics/<batch_id>_import_diagnostics.json`
- `literature/import_diagnostics/<batch_id>_import_warnings.csv`
- `attachments/attachment_registry.json`
- `reports/missing_fulltext_report.csv`
- `audit/audit_log.jsonl`

## Data Center / Task Center

- Data Center 新增或登记：`attachment_registry`、`missing_fulltext_report`。
- Task Center 新增：`attachment_link`、`attachment_copy`、`attachment_validate`、`missing_fulltext_report_export`。
- 既有类型 `literature_records`、`duplicate_candidate_groups`、`deduplicated_literature`、`fulltext_registry`、`screening_decisions`、`meta_analysis_report` 保持兼容。

## 测试

- 新增 `tests/meta_analysis/test_literature_contract_hardening.py`。
- 覆盖 schema、sanitizer、normalizer、diagnostics、audit events、duplicate merge preview、attachment/fulltext、PRISMA source references、report audit。
- 完整 `tests/meta_analysis` 当前通过。

## 已知限制

- 仍不是 production import wizard。
- RIS profile 为 testing 级兼容，不保证覆盖所有 Zotero / EndNote 变体。
- Merge preview 已有字段优先级，但完整批量合并 UI 尚未实现。
- Attachment service 不下载外部文件，不处理机构登录或版权受限 PDF。
- PRISMA 来源可追溯增强，但 full-text workflow 仍不是生产级完整流程。

## 下一步建议

- 将 diagnostics 和 Recent Import Batches 做成更清晰的 UI 面板。
- 为 Zotero / EndNote RIS 增加更多真实 fixture。
- 将 Attachment registry 接入正式 Full-text / Quality 页面。
- 将 audit log 纳入 reproducibility package 完整性检查。
