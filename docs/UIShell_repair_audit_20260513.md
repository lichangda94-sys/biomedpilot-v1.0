# UIShell Repair Audit - 2026-05-13

## 1. Executive Decision

结论：`dev/ui-shell` 不建议继续作为独立长期开发分支，也不得作为 Integration Preview 或 ReleaseBuild 来源。

当前分支仍可作为只读参考和 scoped patch 取材来源，但不应 wholesale merge。后续建议以 `stable/mainline` 为新基线，重建一个极小的 UIShell scoped patch，只保留登录、主窗口、模块选择、侧边栏、设置页、测试模式、统一 UI token/helper 等纯壳层改动。

本轮仅做了一个 P0 级最小修复：当 Bioinformatics 业务页依赖缺失时，`BioinformaticsWorkspaceWidget` 返回可被 `MainWindow` 挂载的占位 QWidget，避免整个桌面壳实例化失败。未恢复 `app/bioinformatics/deg_executor_preflight.py`，未扩大到 Bioinformatics 业务逻辑。

## 2. Worktree State

审计 worktree：

```text
/Users/changdali/Developer/biomedpilot v1.0/UIShell
```

当前分支：

```text
dev/ui-shell
```

当前 HEAD：

```text
391c882 docs: add workspace codex guide
```

审计开始时 dirty status：

```text
## dev/ui-shell
?? docs/UIShell_handoff_report_20260513.md
```

说明：`docs/UIShell_handoff_report_20260513.md` 是审计开始前已存在的未跟踪文件，本轮未纳入修复范围。

与 `stable/mainline` 的分叉：

```text
merge-base: 67e5b138ae38
git rev-list --left-right --count stable/mainline...HEAD: 30 1
```

解释：`dev/ui-shell` 落后 `stable/mainline` 30 个提交，仅领先 1 个提交。领先提交为 `391c882 docs: add workspace codex guide`，内容是 UIShell worktree 指南，不是可合入的运行时代码。

## 3. Verification

修复前验证：

```text
git diff --check
pass

python3 -m app.main --smoke-test
pass

QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
6 failed, 40 passed, 87 skipped
```

修复前失败根因：

```text
TypeError: BioinformaticsWorkspaceWidget() takes no arguments
```

触发链路：

1. `app/shell/main_window.py` 在 `MainWindow.__init__` 中执行 `BioinformaticsWorkspaceWidget(on_back=self.show_dashboard)`。
2. `app/bioinformatics/workspace.py` 的宽泛 import fallback 吞掉了 `app.bioinformatics.workflow_pages` 导入异常。
3. 真正缺失依赖是 `ModuleNotFoundError: No module named 'app.bioinformatics.deg_executor_preflight'`。
4. fallback class 是 `pass`，既不接受 `on_back`，也不是 QWidget，导致 `MainWindow()` 构造阻塞。

修复后验证：

```text
git diff --check
pass

python3 -m app.main --smoke-test
pass

QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
46 passed, 87 skipped
```

补充 skip 原因：

```text
tests/ui/test_bioinformatics_workflow_pages.py: PySide6 UI runtime unavailable: No module named 'app.bioinformatics.deg_executor_preflight'
```

判定：MainWindow 实例化 P0 已修复；Bioinformatics workflow UI 的业务页测试仍因缺失 `deg_executor_preflight` 被整体 skip。这不是 UIShell 纯壳层可接受的 Integration 条件。

## 4. P0 Blockers

已修复：

- `MainWindow()` 被 Bioinformatics workspace fallback 阻塞。
- 修复方式：拆分 Qt import 与 Bioinformatics 业务页 import。Qt 可用但业务页依赖缺失时，返回 `bioinformaticsWorkspaceUnavailable` 占位 QWidget，保证登录、Dashboard、模块导航、设置页、Meta 最小入口等壳层测试继续运行。
- 文件：`app/bioinformatics/workspace.py`。
- 范围：只修壳层实例化降级，不恢复 DEG preflight 服务，不改变真实 Bioinformatics 业务流程。

仍存在：

- `app.bioinformatics.workflow_pages` 仍直接依赖缺失的 `app.bioinformatics.deg_executor_preflight`。
- `tests/ui/test_bioinformatics_workflow_pages.py` 的 87 个测试仍被 skip。
- 当前分支落后 MainLine 30 个提交，缺失 MainLine 的 workspace 初始化恢复、shared UI helper、UI governance、Meta active runtime、vocabulary/package 资源等后续基线内容。
- 分支仍混入 Bioinformatics UI/service integration 内容，且这些内容不应作为 UIShell scoped merge 的一部分。

## 5. Pure UIShell Content

可保留或作为 MainLine scoped patch 参考的内容：

- `CODEX.md` 中对 UIShell 职责边界的说明：桌面壳、登录页、主窗口、模块选择、侧边栏、状态/设置、主题色、按钮语义样式、开发者诊断折叠区。
- `app/shell/main_window.py`、`app/shell/login.py`、`app/shell/module_selection.py`、`app/shell/sidebar.py`、`app/shell/status_panel.py` 中与登录、导航、设置、测试模式相关的壳层行为。
- `tests/ui/test_login_page.py`、`tests/ui/test_module_selection.py`、`tests/ui/test_app_identity.py`、`tests/ui/test_sidebar.py`、`tests/ui/test_app_theme.py` 中仍通过的 shell 测试意图。
- 本轮 P0 降级修复的思路：业务模块不可导入时，不应阻塞桌面壳实例化。

但这些内容大多不应从当前分支直接合入。MainLine 已经有更近的 UI token/helper 和 shell 初始化修复提交，应以 MainLine 当前实现为准重新挑选。

## 6. Bioinformatics Content That Should Not Stay In UIShell

以下内容属于 Bioinformatics 业务或业务 UI 集成，不应留在 UIShell scoped patch 中：

- `app/bioinformatics/workflow_pages.py` 中的数据来源、GEO 中文检索、识别、ready 检查、标准化、分组比较、分析任务中心、结果浏览、报告草稿、设置与本地 AI 页面。
- `app/bioinformatics/project_readiness.py`、`app/bioinformatics/project_analysis_tasks.py`、`app/bioinformatics/analysis_task_runs.py`、`app/bioinformatics/project_standardization.py`、`app/bioinformatics/reports/project_report_builder.py` 等 workflow/service 改动。
- `app/bioinformatics/pages/*` 中具体业务页面样式和行为调整。
- `tests/bioinformatics/*` 以及 `tests/ui/test_bioinformatics_workflow_pages.py` 的业务流程断言。
- `docs/bioinformatics_*`、`docs/stage_bio_*`、`docs/stage_UI_03` 至后续 Bioinformatics workflow 阶段报告。

这些内容可以进入 Bioinformatics 专属分支审计，但不应作为 UIShell 分支继续承载。

## 7. Replaced By MainLine

已被 MainLine 替代或应以 MainLine 为准的内容：

- MainLine 提交 `f295672 fix(mainline): restore bioinformatics workspace initialization` 已恢复 `app/bioinformatics/deg_executor_preflight.py`，解决 Bioinformatics workspace 初始化缺失依赖的主线版本。
- MainLine 提交 `d981a9e`、`b8409ec`、`6e2cfbb`、`8045864` 已引入 shared UI token/theme/helper，并迁移 shell 与部分 Bioinformatics 页面样式。
- MainLine 提交 `1dceec0`、`4e5c4ac` 已收敛 Bioinformatics flow/task/result/report 页面样式。
- MainLine 后续 Meta active runtime、UI governance、desktop launcher、packaging/vocabulary 相关文档和资源均不在当前 UIShell HEAD 中。

因此，当前 UIShell 中的 inline QSS、旧 token、旧阶段报告路径、旧测试断言不应作为权威来源。

## 8. Deprecated Or Not Recommended

建议废弃：

- 以 `dev/ui-shell` 整分支作为 Integration Preview 或 ReleaseBuild 输入。
- 将当前分支中的 Bioinformatics workflow 页面和 service 改动随 UIShell 一起合入。
- 以当前分支的 `app/ui_style_tokens.py` 旧 token 字典覆盖 MainLine shared UI helper。
- 以当前分支的 Meta 最小/旧 shell contract 覆盖 MainLine active runtime。
- 以当前分支的历史阶段报告作为当前测试通过证明。

## 9. Minimal Repair Route

建议路线：

1. 保留本轮 P0 降级修复或在 MainLine 中采用等价策略：业务模块导入失败不能阻塞 shell。
2. 在 `stable/mainline` 上新建 scoped UIShell 分支，不从 `dev/ui-shell` wholesale merge。
3. 只挑选纯壳层 patch：登录、主窗口、模块选择、侧边栏、设置页、测试模式、shared UI token/helper、开发者诊断折叠策略。
4. 明确排除 Bioinformatics 业务逻辑、Meta 业务逻辑、LabTools、ReleaseBuild、packaging 和大词表资产。
5. 对 Bioinformatics workflow 内容另开业务分支处理，先恢复或重建 `deg_executor_preflight` 边界，再跑有效测试。
6. 只有在 `tests/ui` 有效通过、业务测试不再因缺失模块 skip、跨模块污染清理完成后，才重新评估 Integration Preview readiness。

## 10. Integration Decision

当前结论仍为：

```text
UIShell = NO-BLOCKED
```

理由：

- `dev/ui-shell` 落后 MainLine 30 个提交。
- 当前分支只领先 1 个 docs 提交，没有足够独立运行时代码价值。
- MainWindow P0 已在本分支内最小修复，但 Bioinformatics workflow UI tests 仍因缺失业务依赖被 skip。
- 分支仍混入 Bioinformatics UI/service integration，不是纯 UIShell patch。
- 大量内容已被 MainLine 替代，直接合入会回退 MainLine 的 shared UI helper、Meta/runtime、vocabulary/package 等基线。

明确限制：UIShell 当前仍不得进入 Integration Preview。除非后续 `tests/ui` 全部有效通过，且 Bioinformatics/Meta/LabTools/ReleaseBuild 等跨模块污染被清理，否则不得作为 Integration Preview 或 ReleaseBuild 来源。
