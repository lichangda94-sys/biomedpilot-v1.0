# UI Cross-Branch Runtime IA Audit - 2026-05-19

## 1. 审计结论

本审计只使用当前 worktree、当前 HEAD、运行时实例化和本次测试结果作为事实证据；历史阶段报告只作为参考，不作为当前可运行证明。

结论：

- `dev/ui-shell` 是当前 UI Freeze / shell 基线：可见全局导航为 `Dashboard`、`生信分析`、`Meta 分析`、`设置中心`、`测试模式`，没有 LabTools 入口，也没有 `app.labtools` 代码。
- `dev/integration` 已经真实接入 LabTools：Dashboard、侧边栏、`MainWindow` stack、`show_labtools()` 和 `LabToolsWorkspaceWidget` 都存在；LabTools 页面为完整集成态。
- `stable/mainline` 已经接入过 LabTools，但只是最小稳定承接：仅 `image_analysis` / ImageJ-Fiji 外部引擎边界页，不是完整 LabTools 工作台。
- `ReleaseBuild` 源码 worktree 包含与 `dev/integration` 同级的完整 LabTools UI，source smoke 和测试通过；但本次按要求未打包、未验证 `.app`，所以不能把 packaged app 作为当前证据。
- 本地 `dev/labtools` 存在，但不是统一桌面 App worktree；它是独立 `labtools` Python package，提供计算、试剂模板和 Western Blot 后端能力，不提供 `app/`、全局导航或 Qt shell。
- 当前目标 UI 架构应把 LabTools 定位为一级科研模块，但接回 `dev/ui-shell` 时应先接“入口 + 基础 shell + 状态边界”，不要把所有历史/测试/计划页面一次性提升为主导航。

## 2. 审计对象与 HEAD

| 审计对象 | 本地路径 | 实际分支 | HEAD | Worktree 状态 |
|---|---|---|---|---|
| `dev/ui-shell` | `/Users/changdali/Developer/biomedpilot v1.0/UIShell` | `dev/ui-shell` | `3849fa700ce724dd79fd3f56d9f281b8a0a24a46` | clean |
| `dev/integration` | `/Users/changdali/Developer/biomedpilot v1.0/Integration` | `dev/integration` | `49c855f871e79572974d3e24e7dda083548eddc4` | clean |
| `stable/mainline` | `/Users/changdali/Developer/biomedpilot v1.0/MainLine` | `stable/mainline` | `21e1a0f22b3fc06f658e114a33f9469a36c16b71` | clean |
| `ReleaseBuild` | `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild` | `dev/release-internal-test` | `639abf8f2b66e1226c0f199a8b3cd68403fd3ae5` | dirty before audit: untracked `docs/release/ReleaseBuild_handoff_report_20260513.md`; left untouched |
| `dev/labtools` | `/Users/changdali/Developer/biomedpilot v1.0/LabTools` | `dev/labtools` | `42d6b0fd503e6c73652863042c1d9c9a8113601b` | clean |

Branch discovery command:

```bash
git worktree list --porcelain
```

Per-worktree HEAD/status command:

```bash
git status --short --branch && git rev-parse HEAD && git branch --show-current
```

## 3. 运行命令与测试结果

| 审计对象 | 命令 | 结果 |
|---|---|---|
| `dev/ui-shell` | `python3 -m app.main --smoke-test` | passed: `workspace_entries=2`, `bioinformatics_features=5`, `meta_analysis_features=9`, no `labtools_features` |
| `dev/ui-shell` | `QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/ui/test_sidebar.py tests/ui/test_module_selection.py -rs` | passed: `14 passed in 2.33s` |
| `dev/ui-shell` | LabTools-specific tests | skipped: branch has no `app/labtools` and no LabTools nav contract |
| `dev/integration` | `python3 -m app.main --smoke-test` | passed: `workspace_entries=3`, `labtools_features=5` |
| `dev/integration` | `QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/ui/test_sidebar.py tests/ui/test_module_selection.py tests/ui/test_labtools_status_semantics.py tests/labtools -rs` | passed: `294 passed in 4.55s` |
| `stable/mainline` | `python3 -m app.main --smoke-test` | passed: `workspace_entries=3`, `labtools_features=1` |
| `stable/mainline` | `QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/ui/test_sidebar.py tests/ui/test_module_selection.py tests/labtools -rs` | passed: `20 passed in 2.93s` |
| `ReleaseBuild` | `python3 -m app.main --smoke-test` | passed: `workspace_entries=3`, `labtools_features=5` |
| `ReleaseBuild` | `QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/ui/test_sidebar.py tests/ui/test_module_selection.py tests/ui/test_labtools_status_semantics.py tests/labtools -rs` | passed: `294 passed in 4.53s` |
| `ReleaseBuild` | `.app` package launch / rebuild | skipped: user explicitly要求“不打包”；本审计不把旧包或 dist 目录作为当前可运行证据 |
| `dev/labtools` | `python3 -m labtools --smoke-test` | passed: package smoke test passed, version `0.1.0` |
| `dev/labtools` | `python3 -m pytest -q -rs` | passed: `145 passed in 0.19s` |
| `dev/labtools` | Qt shell / global nav test | skipped: this worktree has no `app/` directory and no desktop shell |

运行时结构抽取命令：

```bash
QT_QPA_PLATFORM=offscreen python3 - <<'PY'
# Imports COMMON_SIDEBAR_ITEMS, build_dashboard_model, MainWindow, and app.labtools.workspace when present.
# Instantiates MainWindow and LabToolsWorkspaceWidget offscreen.
# Prints visible/sidebar model items, main stack pages, dashboard features, LabTools page_keys, buttons, and status labels.
PY
```

## 4. 各分支真实全局导航

这里区分两类证据：

- “导航模型”：`COMMON_SIDEBAR_ITEMS` 中声明的 key/label。
- “真实可见侧边栏”：`SidebarWidget` 当前实际渲染的按钮。

| 审计对象 | 导航模型 | 真实可见侧边栏 | LabTools 是否可见 |
|---|---|---|---|
| `dev/ui-shell` | `dashboard`, `bioinformatics`, `meta_analysis`, `settings`, `testing` | `Dashboard`, `生信分析`, `Meta 分析`, `设置中心`, `测试模式` | 否 |
| `dev/integration` | `dashboard`, `bioinformatics`, `meta_analysis`, `labtools`, `project_center`, `data_center`, `task_center`, `report_center`, `settings`, `environment`, `testing`, `packaging` | `Dashboard`, `生信分析`, `Meta 分析`, `实验工具`, `设置中心`, `测试模式` | 是 |
| `stable/mainline` | `dashboard`, `bioinformatics`, `meta_analysis`, `labtools`, `project_center`, `data_center`, `task_center`, `report_center`, `settings`, `environment`, `testing`, `packaging` | `Dashboard`, `生信分析`, `Meta 分析`, `LabTools`, `设置中心`, `测试模式` | 是 |
| `ReleaseBuild` | `dashboard`, `bioinformatics`, `meta_analysis`, `labtools`, `project_center`, `data_center`, `task_center`, `report_center`, `settings`, `environment`, `testing`, `packaging` | `Dashboard`, `生信分析`, `Meta 分析`, `实验工具`, `设置中心`, `测试模式` | 是 |
| `dev/labtools` | 无 | 无 | 不适用：独立 package，没有桌面 shell |

判断：

- `project_center`、`data_center`、`task_center`、`report_center`、`environment`、`packaging` 在 integration/mainline/ReleaseBuild 的导航模型中存在，但不是真实渲染的全局侧边栏入口；这些应视为 planned / hidden / technical-detail candidates，不能按当前主导航统计。
- 真实用户登录后可见的主导航应以 `SidebarWidget` 渲染按钮为准，而不是仅以 `COMMON_SIDEBAR_ITEMS` 统计。

## 5. LabTools 挂载状态对照

| 审计对象 | 代码存在 | Dashboard feature | MainWindow stack | `show_labtools` | LabTools page_keys | 判定 |
|---|---:|---:|---:|---:|---|---|
| `dev/ui-shell` | 否 | 否 | 否 | 否 | 无 | 未挂载 |
| `dev/integration` | 是 | `5` | 是，`LabToolsWorkspaceWidget` | 是 | `home`, `general_calculators`, `imagej_fiji`, `reagent_records`, `cell_experiments`, `western_blot`, `pcr_qpcr`, `elisa_absorbance` | 完整集成态 |
| `stable/mainline` | 是 | `1` | 是，`LabToolsWorkspaceWidget` | 是 | `image_analysis` | 最小承接态 |
| `ReleaseBuild` | 是 | `5` | 是，`LabToolsWorkspaceWidget` | 是 | `home`, `general_calculators`, `imagej_fiji`, `reagent_records`, `cell_experiments`, `western_blot`, `pcr_qpcr`, `elisa_absorbance` | 源码完整集成态；包验证 skipped |
| `dev/labtools` | 是，独立 `labtools/` package | 不适用 | 不适用 | 不适用 | 不适用 | 后端 package，不是桌面 UI 挂载 |

## 6. LabTools 页面、入口与功能状态

### 6.1 `dev/integration` 与 `ReleaseBuild`

当前完整 LabTools 工作台页面：

| page_key | 页面 | 当前状态 |
|---|---|---|
| `home` | LabTools / 实验工具首页 | current runtime / testing summary |
| `general_calculators` | 通用试剂制备 / 计算器 | current runtime / testing |
| `imagej_fiji` | 外部 ImageJ/Fiji 引擎设置 | current runtime / technical settings |
| `reagent_records` | 试剂记录入口 | shell/placeholder-style module page |
| `cell_experiments` | 细胞实验工具 | planned / 未启用 |
| `western_blot` | Western Blot 工作台 | current runtime / testing；样品准备、BCA、上样计算、配胶与 Lane 布局、流程记录可见 |
| `pcr_qpcr` | PCR/qPCR 工具 | planned / 未启用 |
| `elisa_absorbance` | ELISA/吸光度工具 | planned / 未启用 |

功能边界：

- `通用试剂制备`：本地换算、模板管理和制备清单生成处于 testing；不提供内置配方库，不替代 SOP。
- `Western Blot 工具`：流程工作台和多项计算/记录入口处于 testing；结果与灰度分析仍有 placeholder/testing 边界，不应表达为自动图像结论。
- `PCR/qPCR`、`ELISA/吸光度`、`细胞实验工具`：入口存在，但状态为 planned / 未启用，不应进入主用户工作流。
- ImageJ/Fiji 是外部引擎配置和检查能力，不是内置生产级图像分析算法。

### 6.2 `stable/mainline`

当前 LabTools 页面只有：

| page_key | 页面 | 当前状态 |
|---|---|---|
| `image_analysis` | 图像能力边界 / ImageJ-Fiji 本机引擎检测 | current runtime / testing boundary |

功能边界：

- 只声明并检测 ImageJ/Fiji 外部引擎状态。
- 不启用 WB/gel 真实分析、agarose gel、自动 ROI、细胞计数、条带识别、pathology workflow 或生产级真实图像算法。
- 这是稳定分支上的最小承接，不代表完整 LabTools 已稳定。

### 6.3 `dev/labtools`

本地 `dev/labtools` 不是 UI shell，而是独立 package。当前可运行能力来自 package smoke 和 145 个后端测试：

| package area | 当前状态 |
|---|---|
| `labtools.calculators` | current backend package：浓度、稀释、solution preparation、cell seeding、qPCR mix、formula solver、单位换算、计算记录 |
| `labtools.reagent_templates` | current backend package：试剂模板、配制计算、制备记录、存储 |
| `labtools.western_blot` | current backend package：BCA、protein loading、WB loading、SDS-PAGE gel templates、记录导出 |
| `labtools.pcr_qpcr` | public package surface；主要复用 calculator 能力 |
| `labtools.cell_culture` | public package surface；主要复用 cell seeding 能力 |
| `labtools.elisa` | public package surface；包入口存在，但 UI/runtime 未在此 worktree 提供 |

它可以作为 LabTools 功能真实状态的模块分支证据，但不能作为全局导航、Qt 页面、桌面 runtime 的证据。

## 7. 为什么 `dev/ui-shell` 当前未显示 LabTools

原因是结构性未接入，不是隐藏按钮或 runtime blocked：

- `app/labtools` 模块不存在；导入 `app.labtools.workspace` 报 `ModuleNotFoundError("No module named 'app.labtools'")`。
- `app/shell/main_window.py` 未导入 `LabToolsWorkspaceWidget`。
- `MainWindow` stack 只有 `ModuleSelectionWidget`、`BioinformaticsWorkspaceWidget`、`MetaAnalysisWorkspaceWidget`、settings page、testing page。
- `MainWindow` 没有 `show_labtools()`。
- `COMMON_SIDEBAR_ITEMS` 没有 `labtools`。
- `ModuleSelectionWidget` 没有 LabTools card / LabTools button。
- `build_dashboard_model()` 没有 `labtools_features`。

因此，`dev/ui-shell` 当前未显示 LabTools 的直接原因是分支基线未包含 LabTools shell 与模块代码；不是因为 LabTools 页面运行失败。

## 8. Integration Preview / MainLine / ReleaseBuild 是否接入过 LabTools

| 问题 | 事实结论 |
|---|---|
| Integration Preview 是否接入过 LabTools | 是。`dev/integration` 当前 runtime 已挂载完整 LabTools，source smoke 和 294 个目标测试通过。 |
| MainLine 是否接入过 LabTools | 是，但只接入最小 `image_analysis` 边界页；不能证明完整 LabTools 已稳定。 |
| ReleaseBuild 是否包含 LabTools | 是，源码 worktree 当前包含完整 LabTools UI，source smoke 和 294 个目标测试通过。 |
| ReleaseBuild 是否只是旧包或滞后包 | 不能简单判为“只是旧包”。源码运行态与 integration 的 LabTools 页面集一致；但本次没有验证 `.app` 包，所以 packaged state 是 skipped/unknown。 |

## 9. Current Runtime / Historical Asset / Shell-only / Runtime Blocked

### 9.1 Current runtime

| 范围 | 页面 / 模块 |
|---|---|
| `dev/ui-shell` | 登录页、Dashboard、Bioinformatics workspace、设置中心、测试模式、Meta shell |
| `dev/integration` | 登录页、Dashboard、Bioinformatics workspace、Meta workflow pages、LabTools full workspace、设置中心、测试模式 |
| `stable/mainline` | 登录页、Dashboard、Bioinformatics workspace、Meta workflow pages、LabTools image boundary page、设置中心、测试模式 |
| `ReleaseBuild` | source runtime 同 `dev/integration`；packaged runtime 未验证 |
| `dev/labtools` | standalone package backend：calculators、reagent templates、western blot helpers |

### 9.2 Historical UI asset

| 范围 | 说明 |
|---|---|
| 历史阶段报告 | `docs/stage_*`、handoff、repair、rectification、roadmap 等只能作为历史参考 |
| legacy sources | `app/*/legacy/`、archive/snapshot 类内容不进入主导航事实 |
| ReleaseBuild dist | 本次未运行 packaged app；dist 中旧包不能替代当前 runtime 验证 |

### 9.3 Shell-only / placeholder / planned

| 范围 | 页面 / 入口 | 建议 |
|---|---|---|
| integration/mainline/ReleaseBuild navigation model | `project_center`, `data_center`, `task_center`, `report_center`, `environment`, `packaging` | 目前不是可见主导航；保持隐藏或降级到技术详情 |
| `dev/ui-shell` Meta | `workflow_home`, `project_contract`, `dev_branch` | shell-only；不应表现为完整 Meta runtime |
| LabTools full workspace | `pcr_qpcr`, `elisa_absorbance`, 部分 `cell_experiments` | placeholder / planned；保留在 LabTools 内部状态区，不上升为主流程 |
| LabTools external engines | `imagej_fiji` | 技术设置；应归入外部引擎/技术详情，不应抢占普通用户主流程 |

### 9.4 Runtime blocked

本次审计未发现目标分支中可见主入口存在 import-level runtime blocker：

- `dev/ui-shell` 的 LabTools 不是 blocked，而是 not mounted / not present。
- `dev/integration`、`stable/mainline`、`ReleaseBuild` 的 source smoke 均通过。
- `dev/labtools` package smoke 和测试通过。
- `ReleaseBuild` packaged `.app` 状态为 skipped/unknown，不归类为 runtime blocked。

## 10. 哪些页面应该合并、隐藏、降级为技术详情

| 页面 / 入口 | 当前问题 | 处理建议 |
|---|---|---|
| LabTools `imagej_fiji` | 外部引擎配置属于技术前置条件，不是普通任务页 | 降级为 LabTools 内部“外部引擎设置”或全局 External Engines 技术详情 |
| LabTools `reagent_records` 与 `general_calculators` | 试剂制备、模板、记录属于同一用户任务链 | 合并为“试剂与配制”工作区，内部用 tabs/sections 区分计算、模板、记录 |
| LabTools `pcr_qpcr` | planned / 未启用 | 隐藏或保留在 LabTools 内部 planned 列表，不放主操作区 |
| LabTools `elisa_absorbance` | planned / 未启用 | 隐藏或保留在 LabTools 内部 planned 列表，不放主操作区 |
| LabTools `cell_experiments` | 入口状态与真实功能不一致，部分文案为未启用 | 不进入主流程；待形成记录/计算闭环后再上升 |
| integration/mainline navigation model 的 `project_center` 等中心入口 | model 存在但侧边栏不渲染，用户无法直接进入 | 不作为主导航；先收敛到 Dashboard 最近项目、模块内任务中心或开发者诊断 |
| `packaging` | 不是普通用户功能 | 隐藏或开发者诊断，不进入主导航 |
| `environment` | 更像技术诊断 | 降级为设置中心 / 外部引擎 / 开发者诊断 |

## 11. 与 UI 宪法冲突点

| 冲突点 | 影响 | 建议 |
|---|---|---|
| integration/mainline/ReleaseBuild 的导航模型声明了多个未渲染中心入口 | 导航事实不清，容易把 model 当真实 UI | 文档和代码命名应区分 `declared/planned` 与 `visible/runtime` |
| 完整 LabTools 工作台中 planned 页面与 testing 页面同级展示 | 用户可能误以为 PCR/qPCR、ELISA、细胞实验已进入可用主流程 | planned 页面移到“后续工具”或隐藏，主区只展示 testing/current runtime |
| ImageJ/Fiji 配置作为 LabTools page_key 与任务页同级 | 技术依赖抢占用户任务层级 | 降级为外部引擎设置入口 |
| `stable/mainline` 有 LabTools nav 但只有图像边界页 | 稳定承接范围容易被误读 | 在 UI 和审计中明确“最小 LabTools 承接，不代表完整工作台稳定” |
| `ReleaseBuild` 源码完整但包未验证 | 若把 dist/历史包当证据会误导发布状态 | packaged state 必须单独验证；本次按要求 skipped |

## 12. LabTools 在目标 UI 架构中的定位

建议定位：

- LabTools 是一级科研模块，与 Bioinformatics、Meta Analysis 并列。
- 主入口名称建议统一为 `实验工具 / LabTools`，避免 mainline 的纯英文 `LabTools` 与 integration/release 的中文 `实验工具` 分裂。
- `dev/ui-shell` 应接回 LabTools 入口和基础 shell，但接回范围应小而明确：
  - Dashboard card / sidebar item / `MainWindow.show_labtools()`
  - `LabToolsWorkspaceWidget` 基础容器
  - 只展示 current runtime/testing 的试剂配制与 Western Blot 核心入口
  - planned 页面默认隐藏或放入“后续工具”
  - 外部引擎配置降级为技术详情
- 接回时应以 `dev/integration` 的运行态挂载作为综合证据，以 `dev/labtools` 的 package 测试作为后端能力证据，不直接照搬历史阶段报告。

结论性建议：需要将 LabTools 入口和基础 shell 接回 `dev/ui-shell`，但不建议把完整 integration 页面集原样作为主导航一次性合入。先接一级入口与最小工作台，再按 UI 宪法收敛页面层级和状态文案。

## 13. 目标 UI 架构事实来源优先级

后续判断目标 UI 架构时，事实来源优先级应固定为：

1. 当前运行时验证
2. `dev/integration` 综合状态
3. 对应模块分支真实功能状态，例如 `dev/labtools`
4. `dev/ui-shell` 的壳层设计基线
5. `stable/mainline` 稳定承接状态
6. `ReleaseBuild` 打包状态
7. 历史阶段报告，仅作参考

执行规则：

- 页面存在、报告存在、图标存在，都不能替代当前运行时验证。
- `dev/integration` 可证明“已综合接入”，但不能自动证明“稳定发布”。
- `dev/labtools` 可证明后端 package 能力，但不能自动证明桌面 UI 已挂载。
- `dev/ui-shell` 是壳层设计基线，不是所有模块功能真实状态的上限。
- `ReleaseBuild` 只有在实际 packaged app 运行验证后，才能作为发布态证据。
