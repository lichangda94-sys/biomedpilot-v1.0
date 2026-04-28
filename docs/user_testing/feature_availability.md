# Feature Availability

Status meanings:

- `已开放`: available for this testing round.
- `测试中`: legacy capability exists, but the unified shell connection is still being tested.
- `待接入`: visible so testers know the planned workflow, but not ready for real use.
- `暂未开放`: do not test in this round.

| 模块 | 功能 | 状态 | 说明 | 下一步 |
| --- | --- | --- | --- | --- |
| Shared | 项目中心 | 已开放 | 支持 JSON 持久化项目记录和最近项目读取。 | 增加项目搜索和归档。 |
| Shared | 测试模式 | 已开放 | 提供测试说明和反馈模板生成。 | 增加反馈包导出。 |
| 生信分析 | 数据检索 / 导入 | 测试中 | 支持生成 GEO 查询计划和 GSE accession 导入记录；当前不自动下载 NCBI 数据。 | 接入受控在线检索、候选列表和下载步骤。 |
| 生信分析 | 数据下载 | 测试中 | 读取 GEO 查询计划并生成下载计划；当前不实际下载 NCBI 数据。 | 在用户确认后接入 legacy GEO 下载执行。 |
| 生信分析 | 数据资产识别 | 测试中 | 读取 GEO 下载计划并扫描本地目标目录，不联网、不下载。 | 接入真实下载产物后的表达矩阵、样本注释和平台注释识别。 |
| 生信分析 | 数据清洗 | 测试中 | 读取资产识别结果并生成清洗预检计划；当前不执行矩阵标准化。 | 接入受控矩阵清洗、标准化结果预览和输出登记。 |
| 生信分析 | 样本分组 | 测试中 | 读取数据清洗计划并生成样本分组预检；当前不自动推断病例/对照分组。 | 接入样本注释表预览、分组编辑和保存。 |
| 生信分析 | 差异表达分析 | 测试中 | 读取样本分组计划并检查表达矩阵、样本注释和病例/对照分组；当前不运行正式差异统计。 | 接入参数配置、统计引擎选择和受控 DEG runner。 |
| 生信分析 | 富集分析 | 测试中 | 读取差异表达分析预检并检查 DEG 结果或基因列表；当前不下载数据库、不运行 GO / KEGG / GSEA。 | 接入基因列表确认、数据库版本选择和受控富集 runner。 |
| 生信分析 | 相关性分析 | 测试中 | 读取数据清洗计划并检查表达矩阵与样本注释；当前不计算相关系数、不生成相关性图。 | 接入目标基因/表型选择、相关方法设置和图表输出。 |
| 生信分析 | 生存分析 | 暂未开放 | 暂未开放。 | 定义临床数据契约。 |
| 生信分析 | 报告导出 | 待接入 | 统一报告入口占位。 | 接入 Report Center。 |
| Meta 分析 | 文献导入 | 测试中 | 支持 NBIB / RIS / CSV 文件导入，并登记任务与数据资产。 | 继续接入 Prepare for Screening 和 Duplicate Review。 |
| Meta 分析 | 去重准备 | 测试中 | 读取 Literature Import 输出并生成标准化筛选准备记录。 | 继续接入 Duplicate Review。 |
| Meta 分析 | Duplicate Review | 测试中 | 读取筛选准备记录并生成重复候选组摘要，当前不执行人工合并。 | 接入人工确认 UI 和合并决策保存。 |
| Meta 分析 | Screening | 测试中 | 读取 Prepare/Duplicate 输出并生成标题摘要筛选队列，支持最小 include/exclude/maybe 决策保存。 | 扩展为逐条文献判读界面和排除理由字典。 |
| Meta 分析 | Extraction | 测试中 | 读取 Screening 队列并为 included 文献生成数据提取池，正式人工提取表单尚未开放。 | 接入 PICO 字段、结局数据和来源页码的人工提取表单。 |
| Meta 分析 | Analysis | 测试中 | 读取 Extraction 输出并执行 Analysis 预检；当前不运行正式 Meta 统计。 | 接入 outcome 提取表单、分析计划和统计 runner。 |
| Meta 分析 | Reporting | 测试中 | 读取 Analysis 预检输出并导出测试版 Markdown 摘要；正式报告和图表包尚未开放。 | 接入森林图、漏斗图、结果表和正式报告模板。 |
