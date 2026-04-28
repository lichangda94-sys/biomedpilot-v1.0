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
| 生信分析 | 数据检索 / 导入 | 测试中 | GEO 检索/导入能力来自 legacy GEO 工具，当前先暴露状态入口。 | 将 legacy GEO GUI 操作嵌入统一工作台。 |
| 生信分析 | 数据下载 | 测试中 | legacy GEO 下载流程已保留。 | 增加受控下载按钮和结果目录登记。 |
| 生信分析 | 数据资产识别 | 测试中 | geo_processing 资产识别能力已保留。 | 接入统一 Data Center。 |
| 生信分析 | 数据清洗 | 测试中 | legacy GEO/本地数据处理能力已保留。 | 增加输入检查和标准化结果预览。 |
| 生信分析 | 样本分组 | 待接入 | 工作台占位，真实项目数据接入后开放。 | 接入样本注释和分组编辑。 |
| 生信分析 | 差异表达分析 | 待接入 | 当前测试版暂未开放正式统计执行。 | 完成参数检查和 runner adapter。 |
| 生信分析 | 富集分析 | 暂未开放 | 暂未开放。 | 等待差异分析结果接入。 |
| 生信分析 | 相关性分析 | 暂未开放 | 暂未开放。 | 定义输入数据契约。 |
| 生信分析 | 生存分析 | 暂未开放 | 暂未开放。 | 定义临床数据契约。 |
| 生信分析 | 报告导出 | 待接入 | 统一报告入口占位。 | 接入 Report Center。 |
| Meta 分析 | 文献导入 | 测试中 | 支持 NBIB / RIS / CSV 文件导入，并登记任务与数据资产。 | 继续接入 Prepare for Screening 和 Duplicate Review。 |
| Meta 分析 | 去重准备 | 测试中 | 读取 Literature Import 输出并生成标准化筛选准备记录。 | 继续接入 Duplicate Review。 |
| Meta 分析 | Duplicate Review | 测试中 | 读取筛选准备记录并生成重复候选组摘要，当前不执行人工合并。 | 接入人工确认 UI 和合并决策保存。 |
| Meta 分析 | Screening | 测试中 | Screening service 已保留。 | 接入标题摘要筛选队列。 |
| Meta 分析 | Extraction | 测试中 | Extraction service 已保留。 | 接入提取表单和保存。 |
| Meta 分析 | Analysis | 待接入 | 当前测试版暂未开放完整 Meta 统计执行。 | 接入分析计划和统计 runner。 |
| Meta 分析 | Reporting | 测试中 | Reporting service 已保留。 | 接入报告导出按钮和历史记录。 |
