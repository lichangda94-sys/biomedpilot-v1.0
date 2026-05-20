# Bioinformatics Stage B1A 数据选择页收敛记录

日期：2026-05-13

## 1. 本阶段修改范围

本阶段只修改 Bioinformatics 数据选择页及其直接 UI 测试：

- `app/bioinformatics/workflow_pages.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

未修改 project manifest schema，未新增真实外部 API 调用，未新增 DEG 执行器，未生成假 DEG、火山图或富集结果，未接入 PubMed 或文献检索，未改动 AI Gateway、shared vocabulary、Meta 或其他 worktree。

说明：任务要求读取的 Bioinformatics 本地 `docs/handoff/Global_Development_Manual.md` 与 `docs/architecture/*20260513.md` 当前不存在；本阶段按 B1 审计记录读取了 `01_ProjectControl/Global_Development_Manual.md`、`MainLine/docs/architecture/BioMedPilot_v1_overall_architecture_20260513.md`、`MainLine/docs/architecture/BioMedPilot_v1_code_structure_20260513.md` 作为当前权威副本。

## 2. 三类入口组织方式

数据选择页现在按主线显示三块入口：

1. 本地数据导入
   - 主按钮统一为“选择本地文件或文件夹”。
   - 说明收敛为“用于导入表达矩阵、样本信息、临床表或已下载数据。”
   - 主界面不显示 manifest、schema、asset id 等技术字段。

2. GSE 编号检索
   - 输入框示例改为 `GSE60235`。
   - 主按钮统一为“检索”。
   - 仍复用现有 GSE 摘要、详情、添加到项目数据来源的能力，不重写底层检索服务。

3. 中文研究主题检索
   - 入口按钮保持并明确为“进入中文主题检索”。
   - 说明限定为面向 GEO / TCGA / GTEx 的生信数据检索辅助。
   - 数据选择页未新增 PubMed 文献检索入口。

## 3. 下载列表和当前选择状态

页面新增“当前数据选择状态”摘要，显示：

- 已保存数据来源数量。
- 下载列表 / 待处理数量。
- 可进入数据识别数量。
- 下一步建议。

原“待处理数据集”列表标题收敛为“下载列表 / 待处理数据来源”。当前仍复用现有表格，支持查看详情、下载所选、删除所选和进入数据识别；本阶段没有开发完整下载管理器。

下一步提示规则：

- 无项目时：提示先创建或打开项目。
- 无数据来源时：提示先导入本地数据，或检索 GSE / 中文研究主题。
- 有待下载或待确认数据时：提示先完成下载或确认数据来源。
- 有可识别数据时：提示可以进入数据识别。

## 4. 留给 B1B

B1B 继续处理中文研究主题检索独立页：

- 中文问题输入后的英文 query draft。
- GEO / TCGA / GTEx query draft 分区。
- 用户编辑与确认。
- 更大的分区结果展示区。
- 数据集详情页中的保存、忽略、加入下载列表路径。

## 5. 留给 B1C

B1C 继续处理标准化页用户化：

- 隐藏 asset id、raw path、manifest、schema 等技术字段。
- 强调表达矩阵、样本信息、分组设计、默认资产和下一步。
- 将必要技术细节保留在开发者诊断折叠区。

## 6. 仍偏技术化字段

本阶段未全面清理后续页面。数据选择页中，来源详情和技术明细仍保留在默认折叠的诊断区域；下载列表表格仍有“数据状态”“可用内容”“需要补充”等状态列，但这些是用户判断下一步所需字段，不直接暴露 manifest/schema/raw path/asset id。

## 7. 测试结果

已新增/更新 UI 测试覆盖：

- 数据选择页三类入口文案存在。
- 中文主题检索入口文案为“进入中文主题检索”。
- 数据选择页不出现 PubMed 入口文本。
- GSE 输入示例为 `GSE60235`，主按钮为“检索”。
- 当前数据选择状态摘要可初始化，并随本地数据导入更新。

完整验收结果见本阶段提交汇报。

## 8. 风险和人工确认事项

未发现与总开发手册冲突的实现事项。当前风险是下载列表仍是轻量状态摘要和复用表格，不是完整下载管理器；这是本阶段明确允许的范围，后续可在 B1B 或后续下载管理任务中继续收敛。
