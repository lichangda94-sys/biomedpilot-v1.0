# UI-06 生信数据识别页报告

## 本阶段做了什么
- 新增 `BioinformaticsRecognitionWidget`。
- 新增 `app/bioinformatics/project_recognition.py` 薄服务层，优先包装 legacy GEO detector；普通项目文件使用轻量文件名规则生成识别报告。
- 报告写入 `logs/recognition/recognition_report.json`。

## 修改文件
- `app/bioinformatics/project_recognition.py`
- `app/bioinformatics/workflow_pages.py`
- `app/bioinformatics/workspace.py`
- `tests/bioinformatics/test_workflow_adapters.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

## 中文映射
- expression_matrix：表达矩阵
- normalized_expression_matrix：标准化表达矩阵
- raw_count_matrix：原始计数矩阵
- sample_metadata：样本注释
- clinical_metadata：临床信息
- gene_annotation：基因注释
- platform_annotation：平台注释
- comparison_config：分组比较配置
- gmt_gene_set：GMT 基因集
- unknown：未知文件

## 当前边界
- 不重写正式识别算法。
- unknown 文件不强行分类。
- 不执行标准化或分析。
- 不默认删除 `raw_data` 中的原始导入文件。
- 不把识别可信度解释为数据质量或科研可信度。

## 本次 UI 优化

- 表格列名从 `置信度` 改为 `识别可信度`。
- 识别可信度显示为百分比，例如 `0.7` 显示为 `70%`，缺失时显示 `未记录`。
- 识别可信度说明：软件根据文件内容推断文件类型的可信程度；它不是数据质量评分，也不是科研可信度评分。
- 文件大小改为人类可读格式，例如 `5763709` bytes 显示为 `5.5 MB`；原始 bytes 保留在 tooltip / 技术详情中。
- 长路径在表格中压缩显示，tooltip 保留完整路径。

## 刷新、重新识别与清理旧结果

- `刷新报告`：只重新读取 `logs/recognition/recognition_report.json` 并刷新当前显示；不重新扫描文件，不删除旧记录，不改变项目文件。
- `重新识别`：调用现有 recognition backend 重新扫描当前项目数据目录并重新生成报告；不会删除 `raw_data` 中的历史导入副本。
- `清理旧识别结果`：只清理旧 recognition report / `recognized_data` 路由结果；默认不删除 `raw_data/local_import` 中的原始导入文件，也不删除用户选择的本地源文件。
- 清理操作需要确认，确认文案说明“此操作只清理旧识别结果，不会删除原始数据文件”。

## 重复文件策略

- UI 会根据文件名和文件大小检测疑似重复导入文件；来自不同 `acq-*` 目录的同名同大小文件会被标记。
- 显示提示：`检测到可能重复导入的文件。`
- 增加筛选：`显示全部文件`、`仅显示当前有效数据来源`、`隐藏疑似重复文件`。
- 不静默删除重复文件；删除重复导入文件应放到后续“数据来源管理 / 清理导入记录”功能中。
- 如果无法判断当前有效数据来源，UI 会提示当前版本会扫描项目 `raw_data` 中所有已登记文件，因此历史导入副本也可能显示。

## 测试结果
- 已覆盖无报告空状态、mock 文件识别、中文映射、warning 展示和继续信号。
- 已新增 UI-06 专项测试：识别可信度百分比、文件大小 KB/MB/GB、长路径 tooltip、刷新不调用 backend、重新识别调用 backend、清理旧结果不删除 raw_data、疑似重复标记、隐藏重复筛选、技术详情默认折叠。
- 局部回归：`QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q`，23 passed。
- 前序 UI 回归：`QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_login_page.py tests/ui/test_module_selection.py tests/ui/test_bioinformatics_project_home.py tests/ui/test_bioinformatics_workflow_pages.py -q`，52 passed。
- 全量回归：`QT_QPA_PLATFORM=offscreen python3 -m pytest -q`，126 passed。
- 入口 smoke：`QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`，通过。
