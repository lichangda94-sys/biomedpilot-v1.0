# UI-07 生信 Ready 数据准备状态页报告

## 本阶段做了什么
- 新增 `BioinformaticsReadinessDashboardWidget`。
- 新增 `app/bioinformatics/project_readiness.py` 薄服务层。
- 从 recognition report 生成 `logs/readiness/readiness_report.json` 和 `manifests/analysis_capability_matrix.json`。

## 修改文件
- `app/bioinformatics/project_readiness.py`
- `app/bioinformatics/workflow_pages.py`
- `app/bioinformatics/workspace.py`
- `tests/bioinformatics/test_workflow_adapters.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

## 状态映射
- not_ready：尚未准备好
- partially_ready：部分准备就绪
- ready：已准备好
- ready_with_warnings：已准备好，但存在警告
- unavailable：暂不可运行

## 当前边界
- 不伪造 Ready 状态。
- 不隐藏 TCGA + GTEx 未批次校正警告。
- 不运行分析。

## 测试结果
- 已覆盖无报告空状态、Ready 运行、capability matrix 中文展示、缺失输入和 warning。
- 全量回归：`QT_QPA_PLATFORM=offscreen python3 -m pytest`，92 passed。
- 入口 smoke：`QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`，通过。

## 本次交互优化
- 将原先占用较多垂直空间的 Ready 状态大区块改为紧凑状态条，只展示当前状态和关键警告标签。
- 将分析能力表格提升为页面主体，保留“分析 / 是否可运行 / 已有输入 / 缺失输入 / 警告 / 下一步建议”。
- 新增“补充缺失信息”入口，避免用户在缺少关键输入时只能跳过或返回前序页面。

## 补充缺失信息能力
- 样本信息：支持选择本地文件、手动输入、生成 TSV 模板。
- 临床信息：支持选择本地文件、手动输入、生成 TSV 模板。
- 表达矩阵：支持选择本地文件，不支持手动录入完整表达矩阵。
- 补充文件会通过现有数据登记服务写入当前项目；手动输入会保存为项目内 TSV 文件。
- 补充完成后可点击“保存并重新检查”，页面会重新运行数据识别和 Ready 检查，并刷新状态条与分析能力表格。

## 技术详情处理
- 原始 readiness report、analysis capability matrix 和底层 JSON 继续保留在“展开技术详情”中。
- 技术详情默认折叠，普通用户主界面不直接暴露底层字段。

## 当前测试结果
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q`，26 passed。
