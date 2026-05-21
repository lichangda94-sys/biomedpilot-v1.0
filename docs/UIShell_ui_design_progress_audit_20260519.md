# UIShell UI Design Progress Audit - 2026-05-19

## 1. 审计结论

当前 `dev/ui-shell` 可以作为 BioMedPilot 桌面壳层的设计与测试参考，但不应直接视为完整可交付 UI，也不应作为 Integration Preview 或 ReleaseBuild 来源。

核心判断：

- Shell 层可运行：登录页、模块选择页、主窗口、侧边栏、设置中心、测试模式入口仍能被 `MainWindow` 挂载，offscreen UI 测试通过。
- 生信 UI 设计沉淀较完整：仓库中已有 UI-03 到 UI-13 的页面代码、阶段报告、集成矩阵和部分后端接入说明。
- 生信工作流当前运行时不可用：`app.bioinformatics.workflow_pages` 导入失败，缺失 `app.bioinformatics.deg_executor_preflight`，导致 87 个生信 workflow UI 测试被 skip；实际桌面壳会降级到 `bioinformaticsWorkspaceUnavailable` 占位页。
- Meta 模块在本工作区是壳层合同，不是完整 Meta runtime：当前 UI 只展示项目壳、主线边界和 `dev/meta-analysis` 开发线说明。
- 打包入口可生成本地 `.app` launcher，`--smoke-test` 和 LaunchServices `open -W -n` 形态可退出，但 bundle 未签名，且仍不是独立安装器。

当前总体状态：`UIShell = Shell 可用，Bioinformatics workflow UI blocked，Meta 为 shell-only，Packaging 为 local launcher testing`。

## 2. 审计范围

工作区：

```text
/Users/changdali/Developer/biomedpilot v1.0/UIShell
```

分支与版本：

```text
branch=dev/ui-shell
HEAD=db4e27b
date=2026-05-19
```

重点检查范围：

- `README.md`
- `CODEX.md`
- `pyproject.toml`
- `app/main.py`
- `app/ui_theme.py`
- `app/ui_style_tokens.py`
- `app/shell/*`
- `app/bioinformatics/workspace.py`
- `app/bioinformatics/project_home.py`
- `app/bioinformatics/workflow_pages.py`
- `app/meta_analysis/workspace.py`
- `app/shared/feature_availability.py`
- `docs/biomedpilot_ui_design_standard.md`
- `docs/bioinformatics_ui_integration_matrix.md`
- `docs/stage_UI_01_*` 到 `docs/stage_UI_13_*`
- `tests/ui/*`
- `scripts/package_app.py`

## 3. 验证结果

### 3.1 启动 smoke

命令：

```bash
python3 -m app.main --smoke-test
```

结果：通过。

关键输出：

```text
BioMedPilot / 医研智析
app_version=0.1.0-internal-beta
app_channel=Developer Preview / testing
launch_mode=source
app_root=/Users/changdali/Developer/biomedpilot v1.0/UIShell
git_head=db4e27b
workspace_entries=2
bioinformatics_features=5
meta_analysis_features=9
pyside6_available=True
```

注意：本机没有 `python` 命令，README 中的 `python -m app.main` 在当前环境不可直接执行，应使用 `python3`。

### 3.2 UI / packaging 相关测试

命令：

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/ui tests/test_unified_entry.py tests/test_app_version_entry.py tests/test_versioned_packaged_entry.py tests/test_package_app.py
```

结果：

```text
53 passed, 87 skipped
```

补充查看 `tests/ui -rs` 后，87 个 skip 的共同原因是：

```text
PySide6 UI runtime unavailable: No module named 'app.bioinformatics.deg_executor_preflight'
```

因此，这组结果不能证明 UI-04 到 UI-13 当前可运行，只能证明 shell 与非生信 workflow 的测试仍可通过。

### 3.3 生信 workflow import

命令：

```bash
python3 - <<'PY'
try:
    import app.bioinformatics.workflow_pages as workflow_pages
except Exception as exc:
    print(f"workflow_pages_import=failed:{exc.__class__.__name__}:{exc}")
else:
    print("workflow_pages_import=ok")
PY
```

结果：

```text
workflow_pages_import=failed:ModuleNotFoundError:No module named 'app.bioinformatics.deg_executor_preflight'
```

这是真正的 UI workflow blocker。

### 3.4 本地打包 smoke

命令：

```bash
python3 scripts/package_app.py --smoke-test
```

结果：通过。

关键输出：

```text
launch_mode=packaged-local-python
app_path=/Users/changdali/Developer/biomedpilot v1.0/UIShell/dist/BioMedPilot.app
standalone=false
network_downloads=false
```

### 3.5 LaunchServices / bundle 元数据

命令：

```bash
open -W -n dist/BioMedPilot.app --args --smoke-test
plutil -p dist/BioMedPilot.app/Contents/Info.plist
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

结果：

- `open -W -n ... --args --smoke-test`：返回码 0。
- `CFBundleExecutable=BioMedPilot`，可执行名无空格。
- `CFBundleDisplayName=BioMedPilot / 医研智析`。
- `codesign` 失败：`code object is not signed at all`。

结论：本地 launcher 形态可 smoke，但不满足签名/发布级打包要求。

## 4. UI 设计进程分层状态

### 4.1 Shell 层

状态：可用。

已完成内容：

- UI-01 登录页：本地测试登录、错误提示、版本标记、账号/VIP/License 占位。
- UI-02 模块选择页：生信与 Meta 双模块入口、当前用户、版本、Developer Preview 标记、本地环境摘要。
- 主窗口：登录后进入 shell stack，支持 Dashboard、生信、Meta、设置、测试模式。
- 侧边栏：基础导航可用。
- 设置页：展示图标资源状态、默认配置占位和本地设置项。
- 测试模式页：可生成测试反馈模板。

主要证据：

- `app/shell/login.py`
- `app/shell/module_selection.py`
- `app/shell/main_window.py`
- `app/shell/sidebar.py`
- `tests/ui/test_login_page.py`
- `tests/ui/test_module_selection.py`

当前问题：

- 设置中心仍是占位型页面，没有真实配置保存。
- 侧边栏公共导航项定义里包含项目中心、数据中心、任务中心、报告中心、环境检查、打包入口，但实际 `SidebarWidget` 只渲染 Dashboard、生信、Meta、设置、测试模式，导航模型和可见 UI 不一致。

### 4.2 视觉规范与资源

状态：部分完成。

已完成内容：

- `docs/biomedpilot_ui_design_standard.md` 已定义产品定位、颜色、页面原则、术语替换、技术详情折叠、测试规范和禁止事项。
- `app/ui_style_tokens.py` 提供统一颜色、间距、控件高度、圆角、字号 token。
- `app/ui_theme.py` 强制 light theme，避免继承系统 dark mode。
- app icon、登录页、模块选择、UI-03 项目首页图标已大量生成并接入。

图标资源状态：

```text
total=45
generated=35
connected=33
generated_waiting=2
pending=10
```

未完成内容：

- UI-04 到 UI-13 的生信工作流图标组仍为 `待生成`。
- `app/ui_theme.py` 全局 highlight 使用 `#2563EB`，与设计标准中的 deep navy / teal 主色存在轻微漂移。
- Shell 中仍有部分 inline stylesheet，与 token 化方向不完全一致。

### 4.3 生信 UI-03 到 UI-13

状态：设计与代码沉淀存在，但当前运行时 blocked。

已沉淀内容：

- UI-03：项目首页，创建/打开项目，生成 `project_manifest.json` 与 `project_config.json`。
- UI-04：数据来源与登记，三入口设计：本地数据导入、GSE 编号检索、中文研究问题检索。
- UI-05：数据获取状态页，历史上作为独立页实现；最新设计规范要求普通流程并入 UI-04。
- UI-06：数据识别。
- UI-07：Ready 数据准备状态。
- UI-08：标准化资产。
- UI-09：工作流总控。
- UI-10：分析任务中心。
- UI-11：结果浏览。
- UI-12：报告查看。
- UI-13：设置与本地 AI 检索助手。

主要证据：

- `app/bioinformatics/workspace.py`
- `app/bioinformatics/project_home.py`
- `app/bioinformatics/workflow_pages.py`
- `docs/stage_UI_03_bioinformatics_project_home_report.md`
- `docs/stage_UI_04_bioinformatics_data_source_report.md`
- `docs/stage_UI_05_bioinformatics_acquisition_status_report.md`
- `docs/stage_UI_06_bioinformatics_recognition_report.md`
- `docs/stage_UI_07_bioinformatics_readiness_dashboard_report.md`
- `docs/stage_UI_08_bioinformatics_standardized_assets_report.md`
- `docs/stage_UI_09_bioinformatics_workflow_status_report.md`
- `docs/stage_UI_10_bioinformatics_analysis_task_center_report.md`
- `docs/stage_UI_11_bioinformatics_results_browser_report.md`
- `docs/stage_UI_12_bioinformatics_report_viewer_report.md`
- `docs/stage_UI_13_bioinformatics_settings_local_ai_report.md`
- `docs/bioinformatics_ui_integration_matrix.md`

当前 blocker：

```text
No module named 'app.bioinformatics.deg_executor_preflight'
```

影响：

- `app.bioinformatics.workflow_pages` 不能导入。
- `BioinformaticsWorkspaceWidget` 在当前运行时走 fallback。
- UI-04 到 UI-13 的真实页面不会进入当前桌面运行路径。
- `tests/ui/test_bioinformatics_workflow_pages.py` 的 87 个测试被 skip。

设计一致性问题：

- `docs/biomedpilot_ui_design_standard.md` 要求 UI-03 移除底部 `继续：数据来源选择` 和 `打开项目文件夹`；当前 `app/bioinformatics/project_home.py` 中仍有 `继续：选择数据来源`、`打开项目文件夹`、`查看项目结构` 等摘要区操作。
- 设计标准要求 UI-05 不再作为普通用户独立页面；当前 workspace 仍创建 `BioinformaticsAcquisitionStatusWidget` 并保留 `show_acquisition_status()`。虽然普通主流程未必暴露它，但代码结构仍保留独立页。
- 技术术语多数已被折叠或转换，但仍需在真实页面恢复后做一次界面文本巡检，重点检查 `manifest`、`source_type`、`plan_only`、`acquisition` 是否泄漏到普通主界面。

### 4.4 Meta 模块

状态：shell-only。

当前实现：

- `app/meta_analysis/workspace.py` 只提供 Meta 分析模块入口、项目壳、主线合同和开发线说明。
- 页面明确提示完整 PICO、检索、筛选、提取、统计和报告功能在 `dev/meta-analysis` 开发。
- `FeatureAvailability` 中记录了多个 Meta testing 功能，但当前 UIShell 工作区的 Meta UI 不是这些功能的完整运行入口。

风险：

- 模块选择页文案提到中文 18 步 workflow 与多项 testing 能力，容易让测试者误以为当前 UIShell 已经接入完整 Meta runtime。建议在 UI-02 或 Meta 入口页同步强调“当前工作区为入口壳，不是完整 Meta 功能线”。

### 4.5 后端接入边界

状态：测试级接入，不能宣传为正式科研分析。

根据 `docs/bioinformatics_ui_integration_matrix.md`，以下能力已有不同程度接入：

- 项目创建/打开。
- 本地数据导入登记。
- GSE 编号登记。
- GEO 元数据检索尝试。
- 中文主题检索词生成。
- 数据识别。
- Ready 检查。
- 标准化资产。
- 工作流总控。
- 分析任务记录创建。
- 结果索引读取。
- Markdown 项目报告生成。

必须保留的边界：

- 不伪造真实 GEO 下载。
- 不伪造 TCGA / GTEx 网络获取。
- 不运行正式统计分析。
- 不把 preview task 或 dry-run runner 描述为正式生信分析。
- AI 只能作为检索词、翻译、摘要辅助，不能生成统计结论。
- PDF/DOCX 正式报告未开放。

## 5. 主要风险清单

### P0 - 生信 workflow 页面导入失败

证据：

```text
ModuleNotFoundError: No module named 'app.bioinformatics.deg_executor_preflight'
```

影响：

- 当前生信 UI-04 到 UI-13 不在真实运行路径中。
- 87 个生信 workflow UI 测试被 skip。
- shell smoke 通过不能证明生信工作流可用。

建议：

- 恢复或重建 `app/bioinformatics/deg_executor_preflight.py`。
- 重新运行 `QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/ui/test_bioinformatics_workflow_pages.py`。
- 只有该文件不再被整体 skip，才重新评估 UI-04 到 UI-13 进度。

### P1 - UI-03 与最新设计规范存在回流

证据：

- 设计规范要求 UI-03 移除底部继续和打开文件夹按钮。
- 当前代码仍有 `继续：选择数据来源`、`打开项目文件夹`、`查看项目结构`。

建议：

- 在恢复生信 workflow import 后，按规范重新收敛 UI-03：创建/确认成功自动进入 UI-04，摘要区保持只读，技术/文件夹类操作放入折叠技术详情或调试入口。

### P1 - UI-05 独立页面仍保留

证据：

- `BioinformaticsWorkspaceWidget` 仍实例化 `BioinformaticsAcquisitionStatusWidget`。
- `show_acquisition_status()` 仍存在。

建议：

- 若 UI-05 仅为技术状态页，应从普通导航路径移除，并合并到 UI-04 登记状态和技术详情。
- 若仍需保留，应明确标记为开发者诊断页面，避免普通用户流程多一站。

### P1 - 历史阶段报告与当前 HEAD 状态不一致

证据：

- 阶段报告中记录过 UI workflow 测试全量通过。
- 当前 HEAD 下同一测试文件因缺失模块被整体 skip。

建议：

- 后续阶段报告必须写入当前 HEAD、命令和 skip/fail 原因。
- 不再引用旧报告中的 passed 数量作为当前可运行证据。

### P2 - 图标资源未覆盖完整生信工作流

证据：

```text
pending=10
```

待生成组包括 UI-04 到 UI-13。

建议：

- 待 workflow import 恢复后，再按实际页面信息架构生成 UI-04 到 UI-13 图标；不要在页面不可运行时先做视觉资源完工声明。

### P2 - 打包未签名

证据：

```text
dist/BioMedPilot.app: code object is not signed at all
```

建议：

- 本地测试可以继续使用 launcher。
- Integration Preview 或 ReleaseBuild 前需要加入签名、LaunchServices 日志、`-psn_*` 参数处理和 Apple Silicon 架构检查。

### P2 - 文档命令与当前环境不完全一致

证据：

- README 使用 `python -m app.main`。
- 当前环境 `python` 命令不存在，`python3` 可用。

建议：

- README 的运行命令补充 `python3` 版本，或说明使用项目虚拟环境中的 Python。

## 6. 建议下一阶段顺序

1. 恢复生信 workflow import blocker：补齐或迁移 `app.bioinformatics.deg_executor_preflight`。
2. 让 `tests/ui/test_bioinformatics_workflow_pages.py` 从 skip 变为有效执行。
3. 按 `docs/biomedpilot_ui_design_standard.md` 重审 UI-03、UI-04、UI-05 的普通用户路径。
4. 对 UI-04 到 UI-13 做一次真实界面文本巡检，清理普通界面的技术术语泄漏。
5. 补齐 UI-04 到 UI-13 图标资源，并更新 `app.app_identity` 图标状态。
6. 更新阶段报告，明确当前 HEAD、验证命令、passed/skipped/fail 状态。
7. 若目标包含桌面交付，再补签名、LaunchServices、`-psn_*` 和架构检查。

## 7. 当前可交付判断

| 范围 | 当前判断 | 说明 |
|---|---|---|
| Shell 视觉与导航 | 可继续迭代 | 登录、模块选择、主窗口、设置/测试入口可用 |
| 生信 UI 设计稿/页面代码参考 | 可参考 | UI-03 到 UI-13 代码和文档存在 |
| 生信 UI 运行时 | 不可验收 | workflow import blocker 导致 fallback |
| Meta UI | shell-only | 不是完整 Meta runtime |
| 本地 `.app` launcher | testing 可用 | smoke 与 LaunchServices 形态可退出 |
| 发布级 `.app` | 不可发布 | 未签名，不是 standalone |
| Integration Preview | 不建议进入 | 生信 workflow 测试无效，当前证据不足 |

## 8. 审计中执行的命令

```bash
pwd
git status --short --branch
git rev-parse --short HEAD
python3 -m app.main --smoke-test
QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/ui tests/test_unified_entry.py tests/test_app_version_entry.py tests/test_versioned_packaged_entry.py tests/test_package_app.py
QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/ui -rs
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
plutil -p dist/BioMedPilot.app/Contents/Info.plist
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```
