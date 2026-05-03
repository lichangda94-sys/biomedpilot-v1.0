# UI-13 设置与本地 AI 检索助手页报告

## 本阶段做了什么
- 新增 `BioinformaticsSettingsAndLocalAIWidget`。
- 展示本地 Python、project-local `.venv`、依赖、package manifest、默认项目设置、本地 AI 检索助手状态。
- 中文研究问题只生成规则型占位检索词。
- 接入已有 `app/bioinformatics/adapters/legacy_geo.py` 的 GEO legacy 环境检查能力，提供只读检查按钮和输出摘要。

## 修改文件
- `app/bioinformatics/workflow_pages.py`
- `app/bioinformatics/workspace.py`
- `app/ui_style_tokens.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

## 当前行为
- 无 Ollama 时显示“未检测到本地 AI 服务，当前可使用规则占位模式”。
- 检测到 Ollama 命令时仍将 Translator / Media 模型标记为占位。
- AI 使用边界提示固定显示：仅用于翻译、关键词扩展和检索辅助，不参与统计分析，不生成科研结论，不替代人工判断。
- 点击“运行 GEO 环境检查”会执行本地 legacy GEO 工具 `--check`，显示命令、退出码、stdout/stderr 摘要和中文状态。
- GEO 环境检查只验证本地工具环境，不下载 GEO 数据，不运行数据处理。

## 当前边界
- 不调用外部网络。
- 不让本地 AI 参与统计分析结论。
- 不实现真实订阅或账号权限。
- 不把 legacy GEO 环境检查等同于自动下载能力。

## 测试结果
- 已覆盖页面实例化、AI 状态占位、中文输入生成规则型关键词和使用边界提示。
- 已新增 GEO legacy 环境检查 UI 接入测试，mock 外部进程返回，确认检查输出和“不下载数据”边界提示存在。
- 局部回归：`QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_login_page.py tests/ui/test_bioinformatics_workflow_pages.py -q`，29 passed。
