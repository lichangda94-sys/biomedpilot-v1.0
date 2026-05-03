# UI-01 Login Page Report

## 本阶段做了什么

- 新增 `BioMedPilotLoginWidget`，作为软件打开后的第一个页面。
- 页面采用中文友好入口，左侧展示 BioMedPilot / 医研智析 品牌、能力标签和 `0.1.0-internal-beta / Developer Preview / 本地测试版` 标记。
- 右侧新增本地测试登录卡片，包含用户名、密码、进入按钮、注册账号占位、忘记密码占位、账号等级和订阅/VIP 预留状态。
- 登录成功后创建内存中的本地 session 状态，并进入现有模块选择首页 Dashboard。
- 新增 active `app/ui_style_tokens.py`，复用 legacy UI token 的颜色和间距方向，避免在登录页中散落重复样式常量。
- 按统一 UI 规范移除登录页底部无意义图标展示行；登录页只保留品牌信息、登录表单、版本状态和账号/订阅/VIP/License 占位。

## 修改了哪些文件

- `app/ui_style_tokens.py`
- `app/shell/login.py`
- `app/shell/main_window.py`
- `tests/ui/test_login_page.py`
- `docs/stage_UI_01_login_page_report.md`

## 当前登录边界

- 当前只支持本地测试登录。
- 用户名和密码均非空时允许登录。
- 用户名或密码为空时显示中文提示：`请输入用户名和密码。`
- 登录成功后生成的 session 包含 `username`、`role`、`tier`、`license_status`、`login_time`。
- 密码只用于本地非空校验，不进入 session，不写入文件，登录成功后清空密码输入框。
- 当前不实现真实账号系统、支付、订阅或云端认证。

## 后续预留点

- 账号系统：可在 `BioMedPilotLoginWidget.attempt_login()` 外接认证服务，并保持 UI 输入边界不变。
- 订阅/VIP：当前以静态状态显示 `预留功能`，后续可由 license/profile 状态驱动。
- License：当前 session 的 `license_status` 为 `local_testing`，后续可替换为本地 license 文件或企业授权校验结果。
- 用户角色：当前 `role` 固定为 `local_test_user`，后续可扩展为 developer、tester、standard、admin 等角色。

## 测试结果

- 已新增 UI 构造与登录边界测试。
- 已更新测试确认登录页不再渲染 `loginDockLabel` / `loginDockIcon`。
- 已运行 `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_login_page.py tests/ui/test_bioinformatics_workflow_pages.py -q`。
- 结果：`29 passed`。
