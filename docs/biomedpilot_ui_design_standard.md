# BioMedPilot / 医研智析 UI Design Standard

## 定位

BioMedPilot 是专业医学科研桌面软件，不是网页后台，也不是图标展示页。UI 必须保持简洁、克制、专业、低噪音。所有页面只展示当前步骤真正需要的信息和操作。

## 统一视觉规范

- 使用 premium macOS desktop software aesthetic。
- 主色保持：deep navy `#12324A`、teal `#1BAE9F`、white `#FFFFFF`、light gray `#F5F7F9`。
- 使用白色圆角卡片、轻阴影、浅灰边框。
- 保留 `Developer Preview`、`本地测试版`、`0.1.0-internal-beta` 标记。
- 不使用无意义装饰图标、图标展示行、营销式插画或长说明文本。

## 统一页面原则

- 当前页面只做当前步骤的核心任务。
- 每页必须让用户知道：我现在在哪一步、我要做什么、下一步去哪里。
- 主按钮只能表达当前最重要动作。
- 次要信息放到折叠区、tooltip、设置页或技术详情中。
- 普通用户界面不暴露 `acquisition`、`handoff`、`manifest`、`artifact`、`backend`、`source_type`、`plan_only` 等开发者术语。

## 用户化术语

| 技术术语 | 普通用户界面用语 |
|---|---|
| acquisition plan | 数据获取计划 |
| acquisition record | 数据登记记录 |
| standardization handoff | 下一步交接清单 |
| reference | 引用原始位置 |
| copy | 已复制到项目文件夹 |
| plan_only | 已登记编号，等待数据获取 |
| manifest | 技术详情中的项目清单，不在普通页面直接展示 |

## 登录页规范

- 删除底部无意义图标展示行。
- 登录页只保留品牌信息、登录表单、版本状态、账号 / 订阅 / VIP / License 占位。
- 不新增装饰内容。

## 项目页规范

- UI-03 只负责创建项目或确认已有项目。
- 左侧“创建新项目”说明文字必须精简。
- 右侧项目验证状态要醒目。
- “打开项目”按钮改为“确认并继续”或“确认使用该项目”。
- 删除底部“继续：数据来源选择”和“打开项目文件夹”按钮。
- 创建或确认项目成功后，自动进入 UI-04“数据来源与登记”。

## 数据来源页规范

- UI-04 命名为“数据来源与登记”。
- 只保留三个主入口：本地数据导入、GSE 编号检索、中文研究主题检索。
- GEO Series Matrix、TCGA 本地数据、GTEx 本地数据不再单独拆成主卡片，统一归入“本地数据导入”说明。
- 本地导入主界面只显示一个按钮：“选择本地数据”。内部可以再选择文件或文件夹。
- GSE 编号入口按钮为“检索数据集”，普通界面不写 plan。
- 中文主题入口按钮为“检索相关数据集”，不单独显示本地 AI 助手卡片。
- 原 UI-05 acquisition status 不再作为普通用户独立页面，其内容合并到 UI-04 的登记状态区域或技术详情。
- UI-04 完成登记后，主按钮为“继续：数据识别”。

## 功能接入规范

- 已经实现的后端功能必须接入 UI，不做纯静态占位。
- 当前应检查并接入：`project_workspace`、`project_workspace_binding`、`project_recognition`、`project_readiness`、`project_standardization`、`project_workflow_orchestrator`、`project_analysis_tasks`、result manager、`project_report_builder`。
- 未实现的功能要明确标记为当前版本未实现，不伪装。
- 不伪造 GEO 下载、TCGA / GTEx 网络获取、中文检索结果、统计分析结果或报告内容。
- 不把 preview runner 说成正式统计分析。
- 本地 AI 只能用于检索词辅助，不参与统计结论。

## 技术详情规范

- 技术详情默认折叠。
- 可显示 manifest、acquisition plan、record、handoff、workflow state、result index、raw JSON、debug logs。
- 普通用户主界面不直接显示这些技术术语。

## 测试规范

每次 UI 修改必须新增或更新测试，至少覆盖：

- 页面可 offscreen 实例化。
- 核心按钮存在。
- 主流程信号或回调正常。
- 空状态不崩溃。
- 错误状态不崩溃。
- 已实现后端功能能被真实调用。
- 未实现功能有中文说明。
- Developer Preview 标记仍存在。
- 前序 UI 测试继续通过。
- 现有测试继续通过。

## 文档规范

- 每个 UI 阶段必须更新对应 stage report。
- 持续维护 `docs/biomedpilot_ui_design_standard.md`。
- 持续维护 `docs/bioinformatics_ui_integration_matrix.md`。

## 禁止事项

- 不改动 Meta 模块，除非任务明确要求。
- 不删除 `Developer Preview` / `internal beta` 标记。
- 不新增真实支付、订阅、线上账号。
- 不删除或回退已有未跟踪业务文件。
- 不用整张参考图当背景。
- 不把设计稿里的装饰图标区做进真实产品界面。
