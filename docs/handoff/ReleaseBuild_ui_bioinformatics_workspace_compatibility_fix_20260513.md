# ReleaseBuild UI / Bioinformatics Workspace Compatibility Fix

日期：2026-05-13

工作区：`/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`

分支：`dev/release-internal-test`

## 1. 初始失败现象

ReleaseBuild `tests/ui -q` 初始复现结果：

- `6 failed, 40 passed, 87 skipped`
- 共同错误：`TypeError: BioinformaticsWorkspaceWidget() takes no arguments`

失败测试：

- `tests/ui/test_app_identity.py::test_main_window_uses_app_icon`
- `tests/ui/test_login_page.py::test_main_window_starts_at_login_and_enters_dashboard`
- `tests/ui/test_login_page.py::test_settings_page_displays_icon_asset_details`
- `tests/ui/test_module_selection.py::test_main_window_logout_returns_to_login_and_clears_session`
- `tests/ui/test_module_selection.py::test_main_window_module_buttons_enter_existing_workspaces`
- `tests/ui/test_module_selection.py::test_main_window_open_meta_project_binds_workspace_project_dir`

失败栈指向 `app/shell/main_window.py`：

- Shell 初始化调用：`BioinformaticsWorkspaceWidget(on_back=self.show_dashboard)`
- 失败时实际被调用的类签名：`()`

## 2. 根因判断

ReleaseBuild `app/bioinformatics/workspace.py` 中真实 Qt workspace 的构造签名已经是：

```python
BioinformaticsWorkspaceWidget(on_back: Callable[[], None] | None = None)
```

但该文件原先用一个宽泛 `except Exception` 包住 Qt 和 Bioinformatics workflow 依赖导入。ReleaseBuild 缺失 `app/bioinformatics/deg_executor_preflight.py`，导致 `app.bioinformatics.workflow_pages` 顶层导入失败：

```text
ModuleNotFoundError: No module named 'app.bioinformatics.deg_executor_preflight'
```

导入失败被 `workspace.py` 的 fallback 吞掉后，运行时暴露的是底部无 `__init__` 参数的 fallback `BioinformaticsWorkspaceWidget`，从而在 Shell 传入 `on_back` 时触发 `takes no arguments`。

该问题属于 ReleaseBuild / UIShell / Bioinformatics workspace 初始化兼容问题，不是 Vocabulary 词库问题。

## 3. MainLine 对比

MainLine 已有等价可用状态：

- MainLine `app/bioinformatics/workspace.py` 的真实 workspace 签名接受 `on_back`。
- MainLine 存在 `app/bioinformatics/deg_executor_preflight.py`。
- MainLine `app/bioinformatics/reports/project_report_builder.py` 已能读取 DEG preflight manifest，并在报告草稿中展示 `DEG 输入准备状态`。

本次只按 ReleaseBuild 当前失败面同步最小 scoped patch，没有整分支 merge MainLine、Integration 或 Vocabulary。

## 4. 修改文件

- `app/bioinformatics/deg_executor_preflight.py`
  - 从 MainLine scoped 同步缺失的 DEG 输入 preflight helper。
  - 只生成本地 preflight manifest / warnings / comparisons TSV。
  - 明确不执行真实 DEG 差异分析。
- `app/bioinformatics/workspace.py`
  - 将 fallback 限制为 Qt 导入不可用时才触发，避免 Bioinformatics 内部导入错误遮蔽真实 workspace。
  - fallback `BioinformaticsWorkspaceWidget` 增加 `on_back` 兼容参数。
- `app/bioinformatics/reports/project_report_builder.py`
  - 同步 MainLine 的最小 preflight 报告草稿汇总。
  - 只读取本地 manifest 并显示输入准备状态，继续标注 preflight 不代表真实 DEG 完成。
- `tests/ui/test_module_selection.py`
  - 增加 `BioinformaticsWorkspaceWidget(on_back=...)` 构造兼容回归测试。
- `docs/handoff/ReleaseBuild_ui_bioinformatics_workspace_compatibility_fix_20260513.md`
  - 本修复报告。

## 5. 边界声明

- 修改 Vocabulary baseline：否。
- 修改 `data/medical_terms/`：否。
- 修改 `scripts/package_app.py` 词库资源复制策略：否。
- 修改 `medical_terms_index.sqlite` 策略：否。
- 修改 shared vocabulary query intelligence 行为：否。
- 修改 Bioinformatics 业务分析流程：否；仅补齐 UI workflow 已引用的本地 preflight helper 和报告草稿读取。
- 修改 Meta Analysis 流程：否。
- 修改 AI Gateway 行为：否。
- 执行真实网络访问：否。
- 调用 Ollama 或外部 AI：否。
- 删除文件：否。
- 引入外部依赖：否。
- 整分支合并：否。

## 6. 测试结果

已执行：

```bash
git status --short --branch
git diff --check
python3 -m app.main --smoke-test
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m pytest tests/shared -q
python3 -m pytest tests/bioinformatics -q
python3 -m pytest tests/meta_analysis -q
python3 -m pytest tests/test_package_app.py -q
QT_QPA_PLATFORM=offscreen python3 scripts/package_app.py --output-dir /tmp/biomedpilot-ui-bio-compat-package --smoke-test
```

结果：

- `git diff --check`：通过。
- `python3 -m app.main --smoke-test`：通过。
- `tests/ui -q`：`134 passed in 8.82s`。
- `tests/shared -q`：`225 passed in 26.71s`。
- `tests/bioinformatics -q`：`264 passed in 3.54s`。
- `tests/meta_analysis -q`：`3 passed in 0.47s`。
- `tests/test_package_app.py -q`：`2 passed in 1.80s`。
- package smoke：通过，`network_downloads=false`。

## 7. 遗留问题

- 本次未改变 SQLite optional derived resource 策略；`medical_terms_index.sqlite` 仍不是运行硬依赖。
- 本次未处理 Meta confirmed / user edited 治理状态。
- 本次未处理 Bioinformatics TCGA / GTEx / tissue fallback 去重。
- 本次未启用真实 Bioinformatics executor。

## 8. Internal Beta Package Rebuild 建议

建议进入 internal beta package rebuild。

理由：

- ReleaseBuild `tests/ui` 已从 V0.4 的 6 个失败恢复为全绿。
- Vocabulary baseline 未被修改。
- shared / bioinformatics / meta 回归通过。
- packaging resource presence 相关 pytest 和 package smoke 通过。
- package smoke 仍显示 `network_downloads=false`，未引入真实网络或外部 AI 行为。
