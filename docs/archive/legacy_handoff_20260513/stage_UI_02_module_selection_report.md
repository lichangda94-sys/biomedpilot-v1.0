# UI-02 Module Selection Page Report

## 本阶段做了什么

- 新增 `ModuleSelectionWidget`，作为登录成功后的正式统一模块入口页面。
- 页面顶部展示 `BioMedPilot / 医研智析`、当前用户、`0.1.0-internal-beta`、`Developer Preview / 本地测试版`。
- 页面中央展示两个同等重要的大型模块卡片：生信分析模块和 Meta 分析模块。
- 页面右侧展示本地测试信息，包括账号等级、license 状态、订阅/VIP 预留、设置入口占位、本地环境状态和退出登录。
- 最近项目保留为占位/轻量展示，后续可继续接入项目中心。

## 修改了哪些文件

- `app/ui_style_tokens.py`
- `app/shell/login.py`
- `app/shell/module_selection.py`
- `app/shell/main_window.py`
- `tests/ui/test_module_selection.py`
- `docs/stage_UI_02_module_selection_report.md`

## 模块选择首页如何接收 LocalSession

- UI-01 登录成功后，`MainWindow._complete_login()` 保存内存中的 `LocalSession`。
- `MainWindow._build_dashboard_page()` 创建 `ModuleSelectionWidget` 时通过 `session=self._session` 传入当前 session。
- `ModuleSelectionWidget.set_session()` 负责把 `username`、`tier`、`license_status` 显示到页面。
- 当 session 为空时，页面使用安全默认文案 `未登录本地测试用户`，不会崩溃。

## 生信模块和 Meta 模块的跳转方式

- `进入生信分析` 按钮触发 `open_bioinformatics_requested` 信号，并由 `MainWindow.show_bioinformatics()` 进入现有生信工作区。
- `进入 Meta 分析` 按钮触发 `open_meta_analysis_requested` 信号，并由 `MainWindow.show_meta_analysis()` 进入现有 Meta 工作区。
- 本阶段没有改动任何生信或 Meta 后端分析逻辑。

## 当前占位功能

- 最近项目：当前展示最近项目或暂无项目占位。
- 设置入口：当前为禁用的占位按钮，保留后续接入设置中心。
- 订阅 / VIP 服务：显示 `预留功能`，未实现真实订阅或支付。
- 本地环境状态：展示基础 Python/PySide6 状态，并保留后续设置中心详情入口。

## 测试结果

- 已新增模块选择页 UI 构造、session 展示、模块进入回调、退出登录回调和主窗口退出登录测试。
- 已运行 `QT_QPA_PLATFORM=offscreen python3 -m pytest`。
- 结果：`70 passed`。
