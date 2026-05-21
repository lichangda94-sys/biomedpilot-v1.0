# UI Current Information Architecture Audit - 2026-05-19

## 1. 审计结论

本文件记录当前 `dev/ui-shell` / `2ab72e7` 下软件真实 UI 信息架构。它描述的是当前用户打开软件后实际能看到、能点击、能进入的结构，不是理想结构，也不以历史阶段报告作为可用证明。

当前结论：

- 软件启动后首先进入 UI-01 登录页。
- 登录后进入 UI-02 全局工作台 / 模块选择页。
- 当前真实全局导航只有 5 个入口：`Dashboard`、`生信分析`、`Meta 分析`、`设置中心`、`测试入口`。
- Dashboard 上真实可点击模块入口是：`生信分析模块`、`Meta 分析模块`。
- 生信分析模块有完整页面 stack，可真实挂载 UI-03 到 UI-13 及一个中文数据集检索页，但整体仍是 Developer Preview / testing / preflight 语义，不是正式生信 pipeline。
- Meta 分析模块在 UIShell 中是 shell-only，只保留入口壳、项目状态和开发线边界说明，不是完整 Meta runtime。
- 设置中心和测试模式可进入，但设置中心多数内容是 placeholder settings，不是完整配置系统。
- 当前没有发现因 import error 导致的用户可见页面 runtime blocked；上一轮 `deg_executor_preflight` 缺失 blocker 已修复。发布级 `.app` 仍因未签名不满足 ReleaseBuild，但这不是 UI 页面 runtime blocker。

## 2. 审计依据

当前工作区：

```text
/Users/changdali/Developer/biomedpilot v1.0/UIShell
```

当前分支与 HEAD：

```text
branch=dev/ui-shell
HEAD=2ab72e7
```

主要依据：

- `docs/ui/BioMedPilot_UI_Design_Constitution_v2_20260519.md`
- `docs/ui/UI_Freeze_Consolidation_Baseline_20260519.md`
- `docs/biomedpilot_ui_design_standard.md`
- `app/shell/main_window.py`
- `app/shell/sidebar.py`
- `app/shell/module_selection.py`
- `app/bioinformatics/workspace.py`
- `app/bioinformatics/project_home.py`
- `app/bioinformatics/workflow_pages.py`
- `app/meta_analysis/workspace.py`
- offscreen 运行时实例化结果

运行时抽取命令：

```bash
QT_QPA_PLATFORM=offscreen python3 - <<'PY'
from PySide6.QtWidgets import QApplication
from app.shell.main_window import MainWindow
from app.shell.sidebar import COMMON_SIDEBAR_ITEMS
from app.bioinformatics.workspace import BioinformaticsWorkspaceWidget
from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget

app = QApplication.instance() or QApplication([])
window = MainWindow()
bio = BioinformaticsWorkspaceWidget()
meta = MetaAnalysisWorkspaceWidget()
print([f"{i.key}:{i.label}" for i in COMMON_SIDEBAR_ITEMS])
print(window.current_workspace_key())
print([bio._stack.widget(i).objectName() for i in range(bio._stack.count())])
print(meta.page_keys())
PY
```

## 3. 用户打开软件后能看到什么

### 3.1 启动后的第一屏

当前第一屏是登录页，`MainWindow.current_workspace_key()` 返回：

```text
login
```

用户能看到：

- `BioMedPilot / 医研智析`
- `0.1.0-internal-beta / Developer Preview / 本地测试版`
- 本地测试登录表单
- 品牌说明
- 生信分析 / Meta 分析 / 科研报告生成能力标签
- 账号等级、订阅服务、VIP 服务、License 状态占位

真实交互：

- 用户名和密码非空即可进入本地测试 session。
- 注册账号、忘记密码、订阅/VIP/License 是占位，不是真实账号或支付系统。

### 3.2 登录后的第二屏

登录后 `MainWindow.current_workspace_key()` 返回：

```text
dashboard
```

用户能看到 UI-02 模块选择页：

- `生信分析模块`
- `Meta 分析模块`
- 最近项目区域
- 本地测试信息
- 本地环境状态摘要
- 图标资源摘要
- 设置入口预留按钮
- 退出登录按钮

真实可点击模块：

| 入口 | 当前行为 | 真实状态 |
|---|---|---|
| 进入生信分析模块 | 进入 Bioinformatics workspace | Current runtime UI / Developer Preview |
| 进入 Meta 分析模块 | 进入 Meta shell workspace | Shell-only |
| 退出登录 | 返回登录页并清空 session | Current runtime UI |

不可作为真实模块入口的可见项：

| 可见项 | 当前状态 | 说明 |
|---|---|---|
| 设置入口（预留） | Disabled placeholder | Dashboard 内按钮禁用；真实设置入口在侧边栏 |
| 最近项目占位 | Placeholder / lightweight | 可显示最近项目，但不是完整 Project Center |
| 订阅 / VIP 服务 | Placeholder | 不实现真实订阅或支付 |

## 4. 当前全局导航是什么

当前全局导航模型来自 `COMMON_SIDEBAR_ITEMS`，真实值为：

```text
Dashboard
生信分析
Meta 分析
设置中心
测试入口
```

侧边栏真实渲染按钮：

```text
Dashboard
生信分析
Meta 分析
设置中心
测试模式
```

说明：

- `测试入口` 是导航模型标签，实际渲染为 `测试模式`。
- Project Center、Data Center、Task Center、Report Center、Environment、Packaging、LabTools、External Engines 当前不在全局主导航。
- 这些中心页不应进入主导航，直到它们形成真实用户工作流。

## 5. 当前真实可运行页面

### 5.1 Shell 层页面

| 页面 | object / key | 当前状态 | 用户可见路径 |
|---|---|---|---|
| 登录页 | `loginPage` | Current runtime UI | 应用启动第一屏 |
| 全局工作台 / 模块选择 | `moduleSelectionPage` | Current runtime UI | 登录后默认页 |
| Shell 侧边栏 | `SidebarWidget` | Current runtime UI | 登录后 shell 页面左侧 |
| 设置中心 | internal settings page | Current runtime UI / Placeholder settings | 侧边栏 `设置中心` |
| 测试模式 | internal testing page | Current runtime UI | 侧边栏 `测试模式` |

### 5.2 Bioinformatics 模块页面

当前 `BioinformaticsWorkspaceWidget` 能真实实例化并挂载以下页面：

| 顺序 | 页面 | objectName | 当前状态 |
|---:|---|---|---|
| 1 | 生信项目首页 | `bioinformaticsProjectHomePage` | Current runtime UI |
| 2 | 数据来源与登记 | `bioinformaticsDataSourcePage` | Current runtime UI / testing |
| 3 | 中文研究问题检索 | `bioinformaticsChineseDatasetSearchPage` | Current runtime UI / testing / network-dependent |
| 4 | 数据获取状态 | `bioinformaticsAcquisitionStatusPage` | Current runtime UI but should be developer diagnostic / merge target |
| 5 | 数据识别 | `bioinformaticsRecognitionPage` | Current runtime UI / testing |
| 6 | 数据准备状态 | `bioinformaticsReadinessDashboardPage` | Current runtime UI / preflight |
| 7 | 数据准备与标准化 | `bioinformaticsStandardizedAssetsPage` | Current runtime UI / asset registry, not formal normalization |
| 8 | 分组与比较设计 | `bioinformaticsGroupComparisonDesignPage` | Current runtime UI / manual confirmation |
| 9 | 工作流总控 | `bioinformaticsWorkflowStatusPage` | Current runtime UI / orchestration summary |
| 10 | 分析任务中心 | `bioinformaticsAnalysisTaskCenterPage` | Current runtime UI / task plan and preflight |
| 11 | 结果浏览 | `bioinformaticsResultsBrowserPage` | Current runtime UI / imported/testing result browser |
| 12 | 项目报告 | `bioinformaticsReportViewerPage` | Current runtime UI / draft Markdown report |
| 13 | 设置与本地 AI | `bioinformaticsSettingsLocalAIPage` | Current runtime UI / settings + local AI boundary |

关键边界：

- `bioinformaticsAnalysisTaskCenterPage` 可以生成 DEG task plan、dry-run task run 和 executor preflight，但不运行正式 DEG。
- `bioinformaticsReportViewerPage` 生成的是报告草稿，不是发表级报告。
- 结果浏览必须区分 imported DEG、analysis task run、completed result，不得把 dry-run 写成真实结果。

### 5.3 Meta Analysis 模块页面

当前 `MetaAnalysisWorkspaceWidget.page_keys()` 为：

```text
workflow_home
project_contract
dev_branch
```

对应页面：

| 页面 | page_key | 当前状态 |
|---|---|---|
| Meta 项目首页 | `workflow_home` | Shell-only |
| 项目契约 | `project_contract` | Shell-only / minimal contract |
| 功能开发线 | `dev_branch` | Shell-only / reference to `dev/meta-analysis` |

关键边界：

- 当前 UIShell 不承载完整 Meta workflow。
- PICO、检索、筛选、全文、提取、质量评价、统计和报告不应在 UIShell 中表现为完整 runtime。
- Meta 历史开发报告只能作为 historical UI asset / reference。

## 6. 哪些页面是 Historical UI Asset

以下内容是历史 UI 资产或历史证据，不能单独证明当前页面可运行：

| 资产 | 分类 | 处理 |
|---|---|---|
| `docs/stage_UI_01_login_page_report.md` 到 `docs/stage_UI_13_bioinformatics_settings_local_ai_report.md` | Historical UI asset | 只作为阶段记录；必须以当前 HEAD 运行和测试为准 |
| `docs/UIShell_handoff_report_20260513.md` | Historical audit / handoff | 只作历史参考 |
| `docs/UIShell_repair_audit_20260513.md` | Historical repair audit | P0 blocker 信息已被后续修复替代 |
| `docs/meta_dev_reports/*` | Meta historical development reports | 不等于 UIShell 当前 Meta runtime |
| `archive/legacy_sources/*` | Legacy source snapshot | 不进入当前用户主流程 |
| UI-04 到 UI-13 待生成图标组 | Historical/planned visual assets | 页面结构和 runtime 稳定后再处理 |

规则：

- 历史阶段报告中的 `passed` 数量不等于当前 HEAD 通过。
- 页面类存在不等于当前 workspace 挂载。
- 图标存在不等于功能完成。

## 7. 哪些页面是 Shell-only

| 页面 / 模块 | 当前状态 | 原因 |
|---|---|---|
| Meta 分析模块整体 | Shell-only | UIShell 只保留入口、项目壳、主线边界说明 |
| `metaMainlinePage_workflow_home` | Shell-only | 只展示项目绑定和状态摘要 |
| `metaMainlinePage_project_contract` | Shell-only / minimal contract | 只说明最小 manifest contract |
| `metaMainlinePage_dev_branch` | Shell-only / reference | 指向完整 Meta workflow 的开发线 |

当前不是 shell-only 的部分：

- Bioinformatics workspace 当前可真实挂载，不再是 fallback shell。
- Settings 和 Testing 是简化 runtime 页面，不是完整系统，但也不是 shell-only。

## 8. 哪些页面是 Runtime Blocked

当前用户可见 UI 页面中未发现 import error 级 runtime blocked。

上一轮已修复：

| 曾经 blocked 页面 | 旧 blocker | 当前状态 |
|---|---|---|
| Bioinformatics UI-04 到 UI-13 | 缺失 `app.bioinformatics.deg_executor_preflight` 导致 workflow tests 整体 skip | 已修复；页面可 import 并被 workspace stack 挂载 |

仍需区分的非页面 blocker：

| 项 | 状态 | 说明 |
|---|---|---|
| signed `.app` / ReleaseBuild | Release-level blocked | 本地 launcher 可 smoke，但未签名，不是 standalone |
| 完整 Meta runtime | Not in this workspace | 在 UIShell 中是 shell-only，不算 runtime blocked 页面 |
| LabTools | Not in UIShell navigation | 当前 UIShell 未接入，不算 runtime blocked 页面 |

## 9. 哪些页面是 Placeholder / Planned

| 页面 / 区域 | 当前状态 | 建议 |
|---|---|---|
| 登录页注册账号 | Placeholder | 保持 disabled / weak；不进入账号系统设计 |
| 登录页忘记密码 | Placeholder | 保持 disabled / weak |
| 登录页订阅/VIP/License | Placeholder | 保留本地测试状态，不暗示真实支付/授权 |
| Dashboard 设置入口（预留）按钮 | Placeholder / disabled | 不作为真实设置入口；真实设置通过侧边栏进入 |
| Dashboard 最近项目占位 | Placeholder / lightweight | 不升级为完整 Project Center，除非项目中心形成真实用户流程 |
| Shell 设置中心多数配置项 | Placeholder settings | 标明未保存真实配置 |
| Bioinformatics Settings & Local AI | Testing / placeholder hybrid | 保留 AI disabled/local/manual-review 语义 |
| UI-04 到 UI-13 图标资源 | Planned visual work | 在页面结构和 runtime 稳定后再生成 |
| LabTools 全局入口 | Planned / out of current UIShell | 不进入当前主导航 |
| External Engines 独立中心 | Planned | 先在 Settings 内弱化表达，未来有真实 workflow 再提升 |
| ReleaseBuild / signed package | Planned | 当前 local launcher 不是发布版 |

## 10. 哪些页面应该合并

| 当前页面 | 应合并到 | 理由 |
|---|---|---|
| `bioinformaticsAcquisitionStatusPage` / UI-05 数据获取状态 | UI-04 数据来源与登记 | 数据获取计划、登记记录、下一步交接清单是数据来源登记后的状态，不应让普通用户离开主任务 |
| Bioinformatics 工作流总控中的部分技术状态 | 各步骤页面的状态摘要 + 技术详情 | 避免用户为了理解当前状态跳转到技术中控页 |
| Settings 中图标资源状态与开发者明细 | 开发者诊断折叠区 | 普通用户设置页不应成为资产审计页 |
| Meta full workflow 说明 | Meta shell-only 边界说明 | 当前 UIShell 不承载完整 Meta runtime |
| Dashboard 最近项目占位与未来 Project Center | 当前 Dashboard 最近项目区域 | 不应新增 Project Center 主导航 |

## 11. 哪些页面应该隐藏

| 页面 / 入口 | 当前处理建议 | 原因 |
|---|---|---|
| Project Center 主导航 | 隐藏 | 目前不是独立可见全局用户工作流 |
| Data Center 主导航 | 隐藏 | 技术/数据管理未形成普通用户入口 |
| Task Center 主导航 | 隐藏 | 当前 task center 属于 Bioinformatics 内部步骤 |
| Report Center 主导航 | 隐藏 | 当前报告在 Bioinformatics report viewer 内处理 |
| Environment 主导航 | 隐藏 | 应在设置或开发者诊断中表达 |
| Packaging 主导航 | 隐藏 | 打包不是普通用户主流程 |
| LabTools 主导航 | 隐藏 | 当前 UIShell 未接入真实 LabTools runtime |
| External Engines 主导航 | 隐藏 | 当前应先归入 Settings / External Engine 区域 |
| Meta 完整 workflow 页面 | 隐藏于 UIShell | 当前只是 shell-only |

## 12. 哪些页面应该降级为技术详情

| 页面 / 区域 | 降级目标 | 原因 |
|---|---|---|
| UI-05 Acquisition Status | UI-04 技术详情 / Developer Diagnostic | `acquisition`、`plan`、`record`、`handoff` 属于技术状态 |
| Bioinformatics raw JSON / manifest 展示 | 折叠技术详情 | 普通用户不应以 JSON 理解流程 |
| Recognition history raw run detail | 技术详情 | 主界面只显示当前识别摘要和下一步 |
| Standardized asset registry detail | 技术详情 | 主界面应显示可用资产、缺失项、确认状态 |
| Workflow state raw report | 技术详情 | 主界面应显示步骤状态和阻塞项 |
| Analysis task run manifest | 技术详情 | 主界面应显示任务语义、输入准备、testing/preflight 边界 |
| Project report manifest / builder report | 技术详情 | 主界面应显示报告草稿和导出状态 |
| Settings icon asset detailed list | Developer Diagnostic | 普通设置页不应被图标槽位审计占据 |

## 13. 哪些页面和 UI 宪法冲突

| 页面 / 区域 | 冲突点 | 处理建议 |
|---|---|---|
| UI-05 数据获取状态独立页 | 宪法要求技术状态页优先并入主任务页或降级为开发者诊断 | 合并到 UI-04 或隐藏为诊断 |
| Dashboard 设置入口（预留） | 可见但 disabled，容易与真实设置入口混淆 | 删除或改为状态说明；保留侧边栏设置中心 |
| 设置中心图标资源明细 | 开发者资产状态占据普通设置页 | 放入开发者诊断折叠区 |
| Bioinformatics 多个 `primaryButton` 同区并列区域 | 宪法要求主操作唯一、次操作克制 | 分阶段收敛按钮层级 |
| Meta 历史阶段报告 | 容易让人误以为 UIShell 已接入完整 Meta runtime | 全部标为 historical UI asset / reference |
| UI-04 到 UI-13 未来图标组 | 视觉资源先于稳定 IA 容易制造虚假成熟感 | 暂缓图标生成 |

## 14. 每个模块下有哪些页面

### 14.1 全局 Shell

```text
Login
Dashboard / Module Selection
Settings Center
Testing Mode
```

### 14.2 Bioinformatics

```text
Project Home
Data Source & Registration
Chinese Dataset Search
Acquisition Status
Recognition
Readiness Dashboard
Standardized Assets
Group Comparison Design
Workflow Status
Analysis Task Center
Results Browser
Report Viewer
Settings & Local AI
```

当前建议的用户主流程应收敛为：

```text
Project Home
→ Data Source & Registration
→ Recognition
→ Readiness Dashboard
→ Standardized Assets / Group Comparison Design
→ Analysis Task Center
→ Results Browser
→ Report Viewer
```

`Acquisition Status` 应并入 `Data Source & Registration` 或降级为技术详情。

### 14.3 Meta Analysis

```text
Meta Project Home
Project Contract
Development Branch Boundary
```

全部为 shell-only，不是完整 Meta runtime。

## 15. 当前 IA 的真实结构图

```text
App launch
└── Login / 本地测试登录
    └── Dashboard / 全局工作台
        ├── 生信分析模块
        │   └── Bioinformatics Workspace
        │       ├── Project Home
        │       ├── Data Source & Registration
        │       ├── Chinese Dataset Search
        │       ├── Acquisition Status (merge/downgrade target)
        │       ├── Recognition
        │       ├── Readiness Dashboard
        │       ├── Standardized Assets
        │       ├── Group Comparison Design
        │       ├── Workflow Status
        │       ├── Analysis Task Center
        │       ├── Results Browser
        │       ├── Report Viewer
        │       └── Settings & Local AI
        ├── Meta 分析模块
        │   └── Meta Shell Workspace
        │       ├── Meta Project Home (shell-only)
        │       ├── Project Contract (shell-only)
        │       └── Dev Branch Boundary (shell-only)
        ├── 设置中心
        │   └── Placeholder settings + icon/resource diagnostics
        └── 测试模式
            └── Tester guide / feedback template
```

## 16. 下一步 IA 收敛任务

建议按以下顺序处理，不新增主导航：

1. 将 UI-05 Acquisition Status 并入 UI-04，或从普通 stack 中隐藏为 Developer Diagnostic。
2. 将 Settings 中图标资源明细折叠到开发者诊断区，普通设置页只保留可理解的本地配置状态。
3. 收敛 Bioinformatics 页面中的多主按钮区域，确保每页只有一个最突出主操作。
4. 做一次普通用户界面文案巡检，清理 `manifest`、`acquisition`、`source_type`、`plan_only`、`registry`、`dry-run` 等技术术语泄漏。
5. 保持 Meta 在 UIShell 中 shell-only，直到完整 Meta runtime 在目标工作区通过有效测试。
