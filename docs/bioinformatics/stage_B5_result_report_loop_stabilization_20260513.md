# Bioinformatics Stage B5 Result and Report Loop Stabilization Audit

日期：2026-05-13

## 1. 当前 HEAD

- 审计起点分支：`dev/bioinformatics`
- 审计起点 HEAD：`aff8ba5 Implement imported DEG report loop`
- 工作目录：`/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`
- 本阶段范围：Bioinformatics 结果与报告闭环稳定化审计和小修复。

## 2. 审计范围

本阶段检查并小修复：

- imported DEG 服务、列识别、异常输入处理、manifest 生成和 result index 注册。
- result index 旧格式、空索引、缺失索引兼容性。
- 结果中心、imported DEG detail 页面、报告页主界面语义和技术字段隔离。
- `project_analysis_report.md` 和 `project_report_manifest.json` 的语义声明、报告措辞和 raw path 脱敏。
- B2 DEG preflight manifest 语义，确认仍为 input preflight only，不写作科学结果。

本阶段未做：

- 未实现真实 DEG executor。
- 未接入 limma、DESeq2、edgeR。
- 未新增火山图、热图、富集分析或网络检索。
- 未修改 Meta、LabTools、UIShell、MainLine、ReleaseBuild 或桌面启动入口。

## 3. 发现的问题

- imported DEG 在列名齐全但数据不可解析时，可能进入 `ready`，例如只有表头、非数值 logFC、非数值 p value。这会让异常输入过早成为报告候选。
- imported DEG 对中文列名支持不足，例如 `基因`、`log2倍数变化`、`P值`、`校正P值` 不能稳定自动映射。
- report builder 的 real computed result 语义策略里保留了未来真实计算完成态措辞，不适合当前未接入真实计算器的阶段。
- report builder 会把 result index 中的缺失文件 warning 写入 Markdown，原 warning 可能包含绝对路径。
- 异常 imported DEG 覆盖不足，缺少空文件、只有表头、缺关键列、重复 gene、非数值列、GZ、XLSX、中文列名等测试。

## 4. 修复内容

- 收紧 imported DEG `ready` 条件：
  - 必须识别 gene、logFC/log2FC、p value 或 adjusted p value。
  - 必须至少有可解析的数值行。
  - 出现重复 gene symbol 或非数值 logFC / p value / padj 时进入 `needs_confirmation`，不生成 report candidate manifest。
- 增强 imported DEG 异常摘要：
  - 写入 `skipped_non_numeric_rows`、`duplicate_gene_count` 和 warning codes。
  - 缺关键列时返回用户可理解的 missing column message。
- 增强列识别：
  - 支持中文列名 `基因`、`log2倍数变化`、`P值`、`校正P值`。
  - 分隔符识别覆盖 CSV、TSV、TXT、GZ 常见输入。
  - 保留无新增依赖的 XLSX 读取路径。
- 修复报告语义：
  - `real computed result` 策略改为“当前未开放；本阶段不生成真实计算结论”。
  - Markdown 报告继续明确 preflight-only、imported result、testing-level、dry-run / configured-not-run 的安全措辞。
- 修复报告 raw path 风险：
  - 缺失结果文件 warning 在报告中脱敏为“结果文件缺失，请在开发者诊断中查看路径。”
  - 数据来源字段进入 Markdown 前做用户文本脱敏。
- 补充测试：
  - imported DEG 异常输入不会生成 `report_candidate=true`。
  - 旧 result index、空 result index、无 result index 均可生成安全报告草稿。
  - 缺失文件路径不会进入 Markdown 报告。

## 5. 未修复但记录的问题

- imported DEG 的手动列映射目前是服务层持久化能力，尚未提供完整交互式列映射编辑 UI。
- duplicate gene symbol 当前保守处理为 `needs_confirmation`，后续如需自动合并或保留重复项，需要单独产品决策。
- 报告页主界面现在展示中文 Markdown 草稿预览；开发者诊断仍保留 raw Markdown、report payload、manifest 和 result index，用于排查。
- result index 仍是兼容型混合索引，未来真实 executor 接入前需要单独审计正式 schema。

## 6. 测试结果

已运行 targeted tests：

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics/test_imported_deg_results.py tests/bioinformatics/test_project_report_builder.py -q
```

结果：`12 passed`

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q
```

结果：`82 passed`

完整测试已运行：

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`：`229 passed`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：`146 passed`
- `python3 -m app.main --smoke-test`：通过
- `git diff --check`：通过
- `python3 scripts/package_app.py`：通过，未提交 dist 产物

## 7. 是否建议进入桌面手动测试

建议进入桌面手动测试。

建议手动覆盖：

- 无结果、只有 preflight、只有 imported DEG、异常 imported DEG、旧 result index、缺失结果文件。
- 报告页刷新、复制报告摘要、打开报告文件夹。
- 主界面确认不显示 raw absolute path、schema id、manifest full path 或 raw JSON。

## 8. 是否建议进入真实 DEG executor pre-audit

建议在桌面手动测试通过后进入真实 DEG executor pre-audit。

进入前仍需单独审计：

- count matrix / TPM / FPKM / log expression 输入类型。
- sample metadata 和 case/control 最低样本数。
- batch / covariate / paired design。
- limma / DESeq2 / edgeR 输入条件。
- result index schema、error manifest、报告中真实计算结果与导入结果的区分。

## 9. 下一阶段建议

- Stage B6：真实 DEG executor pre-audit，只审计不写执行器。
- Stage B7：在安全窄场景下实现真实 DEG executor，优先 count matrix、明确 sample metadata、case/control 两组。
- Stage B8：再考虑火山图、热图、富集分析；不要和真实 DEG executor 首版合并推进。
