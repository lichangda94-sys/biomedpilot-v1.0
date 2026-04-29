# Meta Literature Workspace Checklist

当前清单适用于 Developer Preview / testing。请不要将任何测试结果解释为 production-ready。

| 测试项 | 操作步骤 | 预期结果 | 失败时记录内容 | 严重程度建议 |
| --- | --- | --- | --- | --- |
| RIS 导入 | 在 Literature Import 选择 RIS 文件并点击 Import | 生成 ImportBatch summary、diagnostics path、warnings CSV path | 文件路径、错误 message、是否生成 batch | blocker |
| NBIB 导入 | 选择 NBIB 文件并点击 Import | PMID、title、authors、journal 等关键字段可解析 | 失败记录示例、缺失字段统计 | blocker |
| CSV 导入 | 选择 CSV 文件并点击 Import | CSV 记录进入 literature records，并生成 diagnostics | CSV 表头、失败行、diagnostics path | major |
| Import diagnostics | 导入后查看 diagnostics cards | 显示 missing title / author / year / DOI / PMID 与 invalid DOI/year | diagnostics JSON 内容、页面显示内容 | major |
| 缺 diagnostics | 删除或指定缺失 diagnostics path 后刷新状态 | 页面显示 warning 和默认值，不崩溃 | 缺失路径、页面 warning | major |
| Recent Import Batches | 查看 workspace 顶部 dashboard | 显示 batch_id、format、counts、duplicate_candidate_count、linked record count | batch JSON、显示缺失字段 | minor |
| Duplicate groups | 打开 Duplicate Review 并载入 duplicate groups | 显示 exact / suspected groups、record_ids、reason、confidence | duplicate_groups JSON、错误 message | major |
| Merge preview | 查看单个重复组 preview | 显示 canonical candidate、field sources、field conflicts | group_id、preview warning、字段冲突 | major |
| Reviewer decision | 选择 keep_both / mark_not_duplicate / exclude_duplicate / merge | 写入 dedup decision 和 audit event | decision 文件、audit log、错误 message | major |
| Attachment registry | 打开 Attachment 页面并刷新项目目录 | 显示 attachment_registry path、PDF/link/copy/ignore/missing counts | registry path、broken row | major |
| Broken attachment path | 使用失效附件路径刷新状态 | 显示 broken path warning，不崩溃 | record_id、file_path、warning | major |
| Missing full-text report | 点击导出 missing_fulltext_report.csv | 生成 reports/missing_fulltext_report.csv | 输出路径、CSV 内容 | minor |
| PRISMA source references | 在 Reporting 页面生成 PRISMA summary | 显示 source references 和 missing source warnings | source_type、missing path | major |
| Review log export | 在 Audit Log 页面导出 JSONL / CSV | 生成 reports/review_log.jsonl 和 review_log.csv | 输出路径、event count | minor |
| Audit log missing | 空项目刷新 Audit Log | 显示空状态和 warning，不崩溃 | 项目路径、页面 warning | minor |
| Testing status | 检查 Import / Duplicate / Attachment / Reporting / Audit 页面 | 页面明确显示 testing / Developer Preview | 截图、页面标题 | major |
| No PDF automation | 检查 Attachment 页面说明 | 页面说明不自动下载 PDF、不做 OCR、不做机构访问 | 页面文案缺失位置 | major |
| No PRISMA diagram claim | 检查 Reporting 页面和 docs | 明确正式 PRISMA diagram 未实现 | 页面或文档中的误导描述 | major |
