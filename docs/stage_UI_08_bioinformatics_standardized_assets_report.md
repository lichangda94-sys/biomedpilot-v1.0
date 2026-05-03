# UI-08 生信标准化资产页报告

## 本阶段做了什么
- 新增 `BioinformaticsStandardizedAssetsWidget`。
- 新增 `app/bioinformatics/project_standardization.py` 薄服务层。
- 生成 `manifests/standardized_assets_registry.json` 和 `standardized_data/analysis_ready_assets/analysis_ready_manifest.json`。

## 修改文件
- `app/bioinformatics/project_standardization.py`
- `app/bioinformatics/workflow_pages.py`
- `app/bioinformatics/workspace.py`
- `tests/bioinformatics/test_workflow_adapters.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

## 当前边界
- 当前为资产注册和轻量校验，不等于正式 biological normalization。
- 不运行分析，不伪造 analysis-ready 结果。

## 测试结果
- 已覆盖无资产空状态、registry 表格、warning 展示和继续信号。
- 全量回归：`QT_QPA_PLATFORM=offscreen python3 -m pytest`，92 passed。
- 入口 smoke：`QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`，通过。
