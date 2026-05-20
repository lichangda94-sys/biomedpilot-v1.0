# Bioinformatics Stage B1C：标准化页用户化记录

日期：2026-05-13

工作区：`/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

说明：任务要求读取的 Bioinformatics 本地 `docs/handoff/Global_Development_Manual.md` 与 `docs/architecture/*20260513.md` 当前仍不存在；本阶段延续 B1/B1A/B1B 的处理方式，读取并遵循 `01_ProjectControl/Global_Development_Manual.md`、`MainLine/docs/architecture/BioMedPilot_v1_overall_architecture_20260513.md`、`MainLine/docs/architecture/BioMedPilot_v1_code_structure_20260513.md` 作为当前权威副本。未发现本任务与总开发手册冲突。

## 1. 改造前主要问题

`BioinformaticsStandardizedAssetsWidget` 原主界面以“标准化资产”注册表为中心，用户首先看到的是资产表字段：

- `asset_type`
- `file_path`
- `source_file`
- `materialize 策略`
- `validation 状态`
- `warning`
- `analysis-ready`

这些字段更适合开发者排查，不适合作为数据识别之后的用户主步骤。页面标题、按钮和下一步也偏向“资产注册 / 工作流总控”，容易让用户误解为标准化阶段需要理解 manifest、schema、资产路径或 workflow orchestration。

## 2. 当前主界面展示的用户状态

标准化页标题已收敛为“数据标准化”，主界面按用户路径展示以下区域：

1. 当前输入数据
   - 数据来源文件名或文件数量。
   - 识别状态和识别时间。
   - 识别内容摘要。

2. 分析输入状态
   - 表达矩阵状态：是否识别到表达矩阵 / 原始计数矩阵 / 标准化表达矩阵；样本数和基因数当前标记为待后续校验确认，不伪造统计。
   - 样本信息状态：是否识别到样本、表型、临床或生存信息。
   - 分组与比较设计状态：是否已有确认的比较设计，或是否存在候选分组待确认。

3. 默认资产与下一步
   - 用中文名称说明当前默认使用的数据。
   - 下一步建议根据项目状态切换：返回数据识别、生成标准化数据、确认分组与比较设计、继续到分析任务中心。

4. 用户化资产表
   - 表头改为“数据内容 / 当前状态 / 用于后续分析 / 说明”。
   - 表格不再显示原始路径、manifest、schema、asset id 或内部 registry 字段。

5. 流程按钮
   - `生成标准化数据`
   - `确认分组与比较设计`
   - `刷新状态`
   - `继续到分析任务中心`

标准化页继续按钮的工作区导航已从“生信工作流总控”改为“分析任务中心”。工作流总控页面仍保留，可继续用于开发者预览和内部流程检查，但不再作为标准化页用户主线的显式下一步。

## 3. 已移入开发者诊断的技术字段

以下技术信息仍保留，但放入“开发者诊断”折叠区：

- standardized assets registry
- analysis-ready manifest
- data processing task plan
- readiness details
- recognition report
- registry path
- manifest path
- data processing task plan path
- raw source path / route path
- internal asset type
- validation status
- warnings
- schema version

开发者诊断区同时保留“打开 standardized_data 文件夹”入口。主界面不直接展示该路径。

## 4. 重复信息处理

已减少：

- 主表不再重复列出资产 registry 与默认资产。
- user summary 不再在主界面重复列出注册资产、analysis-ready、warning。
- 标准化页下一步不再把 workflow orchestration 显示成额外主步骤。

保留：

- “开发者诊断”仍保留完整 registry / manifest / readiness / recognition 内容，便于排查标准化资产注册、选择 manifest 和 warnings。
- “分析任务中心”仍显示 Developer Preview 标识，因为真实分析执行能力仍需后续阶段治理。

## 5. 当前仍未完全用户化的内容

- 表达矩阵样本数、基因数目前只在已有服务能提供时才应展示；本阶段未新增矩阵解析或真实统计，因此主界面标记为“待后续校验确认”。
- 分组确认入口当前返回数据准备状态页，由既有分组/比较设计能力承接；本阶段未新增独立分组设计页面。
- 标准化服务仍是资产注册与轻量校验，不等于正式 normalization；本阶段未改服务层或 manifest schema。
- Bioinformatics 本地总手册和架构文档副本缺失仍需项目层确认是否同步。

## 6. 留给后续阶段

后续分析任务中心和结果页优化建议：

- 将“分析任务中心”进一步用户化，区分可运行、待补输入、preview/testing-level 的任务。
- 为表达矩阵补充可靠样本数、基因数和矩阵维度校验展示。
- 为分组与比较设计提供更直接的确认入口，而不是依赖返回数据准备状态页。
- 结果页继续坚持不展示假 DEG、假火山图、假富集结果，只展示真实执行产物或明确的 testing-level 状态。

## 7. 测试结果

已执行：

- `python3 -m app.main --smoke-test`：通过。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`：215 passed。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：138 passed。

新增/更新测试：

- 更新 `test_recognition_readiness_standardization_pages`，断言标准化页状态使用“标准化数据”。
- 新增 `test_standardization_page_userized_surface_hides_technical_fields`，覆盖：
  - 用户化流程按钮存在。
  - 表达矩阵、样本信息、分组与比较设计、下一步建议状态存在。
  - 主表不显示 raw path、materialize、validation_status、analysis-ready、manifest、schema。
  - 开发者诊断区保持隐藏，并保留 registry / manifest / raw path 等排查信息。

## 8. 风险和人工确认事项

- 本阶段未修改 manifest schema、标准化服务层、readiness、workflow orchestrator 或真实分析执行逻辑。
- 未新增 DEG 执行器，未生成假 DEG、假火山图、假富集结果。
- 未修改 Meta、Vocabulary、LabTools、AI、UIShell、Integration、ReleaseBuild 等其他 worktree。
- 需要项目层后续确认是否将总开发手册和架构文档同步到 Bioinformatics worktree 指定路径，或正式改为引用 `01_ProjectControl` / `MainLine` 权威副本。
