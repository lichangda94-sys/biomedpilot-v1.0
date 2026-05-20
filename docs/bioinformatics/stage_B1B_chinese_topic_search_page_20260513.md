# Bioinformatics Stage B1B 中文研究主题检索独立页扩容记录

日期：2026-05-13

## 1. 当前结构

本阶段只扩容 Bioinformatics 的中文研究主题检索独立页及其直接 UI 状态，涉及：

- `app/bioinformatics/workflow_pages.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

页面当前结构：

1. 中文研究主题输入
   - 标题为“中文研究主题检索”。
   - 输入区标题为“中文研究主题输入”。
   - placeholder 为“例如：甲状腺癌 脂质代谢 免疫浸润”。
   - 说明限定为生成 GEO / TCGA / GTEx 数据检索草稿，确认后再进入候选数据选择。

2. Query draft（草稿 / 待确认）
   - 新增独立草稿概览区，显示 GEO、TCGA、GTEx 的草稿摘要。
   - 保留各数据库分区内可展开的草稿文本框，用户可查看、复制和确认草稿。

3. 检索状态
   - 显示 query draft 状态。
   - 显示 GEO / TCGA / GTEx 分区候选数量。
   - 显示已保存候选数量。
   - 显示加入下载列表数量。
   - 显示下一步建议。

4. 数据库分区结果
   - `GEO/GSE`
   - `TCGA/GDC`
   - `GTEx`

5. 开发者诊断
   - 原“高级信息”收敛为“开发者诊断”。
   - 映射日志默认折叠。

## 2. Query draft 区

当前 query draft 仍复用既有 `BioinformaticsSourceRouter` 和 `QueryUnderstandingLayer`：

- 默认不联网生成草稿。
- 本地模型只有在既有配置启用时才通过既有接口参与。
- 草稿状态标记为“已生成，待用户确认”。
- 用户确认草稿不会执行真实数据库检索。

本阶段没有新增 AI Gateway 底层逻辑，没有绕过 AI Gateway，没有保存 raw prompt / raw response。

## 3. GEO / TCGA / GTEx 分区结果

GEO / GSE：

- 保留在线检索按钮，但只使用既有 `GeoSearchAdapter` 入口。
- 候选表显示 GSE 编号、标题、样本数、数据类型/平台、分析潜力和资产状态。
- 候选操作统一为“查看详情 / 保存 / 忽略 / 加入下载列表”。

TCGA / GDC：

- 当前主要是项目候选和下载清单级能力。
- 候选卡片显示项目代码、中文名称、英文名称、数据库、推荐原因、可用数据和适用说明。
- 不伪造表达矩阵或临床文件已下载。

GTEx：

- 当前主要是组织参考候选和下载清单级能力。
- 候选卡片显示组织名称、中文名称、英文名称、数据库、推荐原因、可用数据和适用说明。
- 保持 GTEx 是正常组织参考的用户提示，不伪造本地表达矩阵。

## 4. 候选操作处理

查看详情：

- GEO 进入现有 `GeoDatasetDetailPanel`，显示英文标题、英文原始信息、中文翻译草稿、样本结构与下载建议、数据资产状态。
- TCGA / GTEx 进入当前分区详情面板，显示用户可理解的项目/组织说明、样本数、数据类型、资产状态、下载建议和风险提示。

保存：

- 进入现有项目数据来源体系。
- 通过现有 acquisition record 保存为 planned source。
- 不改变 project manifest schema。

忽略：

- 只从当前候选展示中移除。
- 不删除真实数据。
- 不写入项目数据来源。

加入下载列表：

- GEO 使用既有下载任务创建路径；默认不会执行真实下载。
- TCGA / GTEx 使用既有下载清单创建能力。
- 下载列表状态继续汇入现有 acquisition / 待处理数据来源体系。

## 5. Testing-level 能力

仍属于 Developer Preview / testing-level 的内容：

- 中文 query draft 是检索草稿，不是正式检索策略。
- TCGA / GTEx 当前主要是本地映射或下载清单级入口。
- GEO 在线检索和下载仍依赖既有用户显式操作，不在本阶段自动执行。
- 中文简介仍是草稿，需人工确认。

## 6. 后续阶段留项

- 将 GEO、TCGA、GTEx 的详情体验进一步统一。
- TCGA / GTEx 真实数据文件下载和用户文件选择仍需独立阶段处理。
- 下载列表可进一步做成跨入口统一管理器。
- 标准化页用户化继续留给 B1C。

## 7. 技术字段暴露

主界面未新增 raw prompt、raw response、internal candidate id、manifest path、audit id、raw source path 等技术字段。

仍保留的技术信息：

- 映射日志在“开发者诊断”折叠区内。
- GEO 数据资产状态仍显示用户化状态文本，不直接显示 manifest path。

## 8. 测试结果

已执行：

- `python3 -m app.main --smoke-test`：PASS
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`：215 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：137 passed

本阶段新增/更新测试覆盖：

- 中文主题检索页标题、输入 placeholder 和 query draft 区。
- 页面只保留 GEO / TCGA / GTEx 分区，不出现 PubMed、PICO 或 Meta 主入口。
- 候选操作按钮“查看详情 / 保存 / 忽略 / 加入下载列表”。
- 忽略候选只影响当前候选展示，不写入项目数据来源。
- 数据选择页进入中文主题检索导航仍保持可用。

## 9. 风险和人工确认事项

未发现与总开发手册冲突的实现事项。

当前风险：

- “加入下载列表”对 GEO 是 download task / pending source 层级，不代表已经下载表达矩阵。
- TCGA / GTEx 仍是下载清单级能力，不代表数据文件已落地。
- Bioinformatics 本地 `docs/handoff/Global_Development_Manual.md` 与 `docs/architecture/*20260513.md` 仍不存在；本阶段继续读取 `01_ProjectControl` 和 `MainLine` 中的权威副本。
