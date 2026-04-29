# Meta Literature Workspace Walkthrough

BioMedPilot / 医研智析的 Meta Literature Workspace 目前是 Developer Preview / testing。它用于测试文献导入质量、重复文献依据、附件登记、PRISMA source trace 和 audit log，不应被当作 production 审稿流程。

## 1. 导入 RIS / NBIB / CSV

1. 打开 Meta Analysis workspace。
2. 在 Literature Import 页面选择 `.ris`、`.nbib` 或 `.csv` 文件。
3. 选择或输入格式；不确定时使用 `auto`。
4. 填写 `source_database`，例如 PubMed、Zotero、EndNote 或 CSV。
5. 如有检索日期和检索式，填写 `search_date` 与 `search_strategy`。
6. 保持 `dedup_mode=detect_only` 或按测试任务选择。
7. 点击 Import。

导入成功后，页面会显示 ImportBatch summary、diagnostics path、warnings CSV path 和下一步 `Review duplicates`。

## 2. 查看 Import diagnostics

Import diagnostics 面板显示：

- raw / parsed / normalized / failed record count
- warning count
- missing title / author / year / DOI / PMID
- invalid DOI / year
- empty abstract
- failed record examples
- import warnings CSV path

如果 diagnostics 文件不存在，页面会显示 warning 和 0 值，不应崩溃。

## 3. 如何理解缺字段 warning

| Warning | 含义 | 建议严重程度 |
| --- | --- | --- |
| missing title | 文献无法稳定识别，可能影响筛选和去重 | blocker |
| failed record | 单条记录解析失败 | blocker |
| missing author | 作者缺失会影响去重、引用和 PRISMA 追踪 | major |
| missing year | 年份缺失会影响去重和报告 | major |
| invalid DOI / year | 标准化失败，需要检查原始文件 | major |
| missing DOI / PMID | 可继续测试，但 identifier 去重能力下降 | minor |
| empty abstract | 标题摘要筛选信息不足 | minor |

## 4. 查看 Recent Import Batches

Workspace 顶部的 Meta Literature Import Quality Dashboard 会显示最近导入批次：

- batch_id
- source database / source format
- status
- created_at
- raw / parsed / normalized / failed / warning count
- duplicate_candidate_count
- linked_literature_record_count
- diagnostics path / summary

没有导入批次时显示 empty state。

## 5. 查看 Duplicate Merge Preview

Duplicate Review 页面用于查看重复候选组和 merge preview。

重点检查：

- duplicate group 总数
- exact / suspected duplicate group 数量
- record_ids
- match reasons
- confidence
- canonical candidate
- field conflict summary
- merge preview field sources

字段冲突重点包括 title、creators/authors、year/date、journal/publication_title、DOI、PMID 和 clinical_trials_ids。

Merge preview 只是辅助，不会替代 reviewer 判断，也不会自动批量合并。

## 6. 检查 Attachment Registry

Full-text / Attachment 页面显示：

- `attachments/attachment_registry.json`
- PDF 附件数
- link / copy / ignore / missing 数量
- broken path 数量
- per-record file name、attachment type、file_exists
- `reports/missing_fulltext_report.csv`

附件路径失效时应显示 warning，不应崩溃。

## 7. 导出 Missing Full-text Report

在 Attachment 页面点击导出 missing full-text report。输出路径为：

`project_dir/reports/missing_fulltext_report.csv`

该报告只记录当前哪些 record 缺 full-text PDF。软件不会自动下载 PDF，不做 OCR，不做机构全文访问。

## 8. 查看 PRISMA Source References

Reporting 页面可生成 PRISMA summary，并显示 source references。

检查内容：

- ImportBatch source
- DuplicateReviewDecision source
- ScreeningRecord source
- FulltextStatus source
- ExtractionRecord source
- AnalysisInput source

缺 source 时显示 warning，报告继续生成并标记 missing。

## 9. 导出 Review Log

Audit Log 页面可导出：

- `project_dir/reports/review_log.jsonl`
- `project_dir/reports/review_log.csv`

Review log 用于测试记录和追踪，不替代 Task Center。

## 10. 可以接受的 warning

通常可继续测试但需要记录：

- missing DOI / PMID
- empty abstract
- missing full-text report 尚未生成
- 部分 audit events 尚未出现
- full-text workflow incomplete

## 11. 需要记录为 blocker / major 的 warning

记录为 blocker：

- missing title
- failed record
- merge preview 不可读取但用户需要做 merge
- 附件源文件不存在且任务要求绑定 PDF

记录为 major：

- missing author / year
- invalid DOI / year
- duplicate identifier conflict
- attachment_registry 缺失但测试任务要求检查附件
- broken attachment paths
- PRISMA source reference 缺失

## 12. 当前 testing 限制

- Diagnostics 是 testing 级质量检查，不会自动修复文件。
- Merge preview 是辅助，不替代 reviewer 判断。
- Attachment 不自动下载 PDF。
- 不做 OCR。
- 不做机构全文访问。
- 不生成正式 PRISMA diagram。
- 所有输出仍需测试人员复核。
