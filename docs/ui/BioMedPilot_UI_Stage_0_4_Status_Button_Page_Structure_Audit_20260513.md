# BioMedPilot UI Stage 0.4：状态标签、按钮层级与页面结构规范化审计

日期：2026-05-13
范围：MainLine `app/shell`、`app/bioinformatics`、MainLine `app/meta_analysis` 最小入口、未来 LabTools 接入原则、`app/shared/ui`

## 1. 本阶段审计范围

本阶段承接 UI Stage 0.1、0.2、0.3，目标是审计并初步统一跨模块最容易分裂的交互基础层：

- 状态标签：Ready、Not Ready、Warning、Error、Draft、Confirmed、Running、Completed、Pending、Saved、Ignored、Added to download list、Analysis-ready、Developer Preview、Testing-level。
- 按钮层级：主操作、次操作、返回/下一步、详情、危险或撤销、草稿确认、开发者诊断。
- 页面结构：流程型页面、工具型页面、数据列表型页面。
- 技术字段折叠：asset id、manifest path、raw path、schema、run id、internal JSON、validation_status、materialize、registry entry、debug log。

本阶段只在 MainLine 工作树内操作。Meta Analysis 只做审计记录，不修改代码。MainLine 当前不存在 `app/labtools/`，未创建 LabTools 业务代码。

## 2. 当前状态标签一致性结论

### 现状

Stage 0.2 已建立 `BioMedPilotStatusStyle` 和 `BioMedPilotStatusColors`，覆盖 `ready`、`not_ready`、`warning`、`error`、`draft`、`confirmed`、`running`、`completed`、`testing`、`blocked`。Stage 0.4 在此基础上补充了常见别名：

- `pending` -> 未就绪
- `saved` -> 已确认
- `ignored` -> 草稿
- `added` / `added_to_download_list` -> 已确认
- `analysis_ready` -> 已就绪
- `developer_preview` / `testing_level` -> 测试中

### 问题

- Shell 仍有 Developer Preview、本地测试、图标资源状态等普通文本状态，尚未完全 badge 化。
- Bioinformatics 项目首页和 workflow 已有局部状态对象，如 `bioProjectStatusLabel`、`readinessStatusBadge`、`bioStepBadge`，但普通入口页此前只使用普通 QLabel。
- Bioinformatics workflow 中 “可运行 / 暂不可运行 / 待确认 / 已生成 / 未生成 / 预检已生成 / dry-run” 语义较多，后续需要映射到统一状态族。
- MainLine Meta 最小入口仍把项目状态、目录、manifest 读取失败等内容放在普通文本中，且会显示完整目录路径。
- 开发者诊断状态和研究人员主状态尚未完全分离。

### Stage 0.4 处理

本阶段新增 `status_badge_qss(status)`，并在两个 Bioinformatics 入口页做低风险试点：

- `geo_import_page.py`
  - 功能状态使用 `testing` badge。
  - 初始导入状态使用 `pending` badge。
  - 草稿生成使用 `draft` badge。
  - GEO/GSE 检索完成使用 `completed` badge。
  - 失败使用 `error` badge。
  - 登记完成使用 `saved` badge。
- `local_expression_import_page.py`
  - 功能状态使用 `testing` badge。
  - 初始导入状态使用 `pending` badge。
  - 成功且无 warning 使用 `completed` badge。
  - 成功但有 warning 使用 `warning` badge。
  - 失败使用 `error` badge。

## 3. 当前按钮层级一致性结论

### 现状

Shell 登录页、模块选择页和 Bioinformatics 项目首页主要依赖 `app/ui_style_tokens.py` 的 QSS。Bioinformatics workflow 已有 `_button()` 和 `buttonRole`，其中包括 `primary_next`、`primary_action`、`secondary`、`back`、`danger` 等局部语义。

主要问题：

- Bioinformatics 分析任务中心仍存在多个主操作竞争，例如配置、生成任务、校验、创建任务、运行 DEG preflight 等。
- 普通入口页此前按钮视觉不分层，`生成检索草稿`、`检索 GEO/GSE`、`登记首条结果为数据来源`、`下一步` 都是默认 QPushButton。
- “登记 / 添加 / 加入 / 保存 / 确认 / 创建任务记录 / 加入报告” 等动词在相似语境中并不完全一致。
- 危险类动作如删除、清空、忽略目前很多仍是 secondary 风格，只通过文案表达风险。
- 详情类动作“查看详情 / 展开技术详情 / 技术信息 / 展开开发者诊断”文案尚需统一。

### Stage 0.4 处理

本阶段新增 shared button helper：

- `primary_button_qss()`
- `secondary_button_qss()`
- `quiet_button_qss()`
- `danger_button_qss()`
- `navigation_button_qss()`
- `button_qss(role)`

并在两个 Bioinformatics 入口页做低风险视觉试点：

- `geo_import_page.py`
  - `检索 GEO/GSE` 使用 primary。
  - `生成检索草稿` 使用 secondary。
  - `登记首条结果为数据来源` 使用 secondary。
  - disabled `下一步：数据下载` 使用 navigation helper。
- `local_expression_import_page.py`
  - `导入表达矩阵` 使用 primary。
  - disabled 下一步按钮使用 navigation helper。

没有改变按钮行为、信号连接、服务调用或流程。

## 4. 当前页面结构一致性结论

### A. 流程型页面模板

适用：Bioinformatics、Meta Analysis。

推荐模板：

1. 页面标题。
2. 一句话说明。
3. 当前状态摘要。
4. 主内容区。
5. 右侧详情或底部详情。
6. 开发者诊断折叠区。
7. 下一步 / 返回。

现状：

- Bioinformatics 项目首页和 workflow 大页已接近该模板。
- Bioinformatics 普通 `pages/*_page.py` 是轻量垂直布局，有标题、说明、状态、输入、按钮、summary card、错误提示，但缺少统一的详情折叠区和主/次按钮规则。
- Meta mainline workspace 有 header、状态文本、左侧列表和右侧页面栈，但尚未接入 shared page header、status badge、button helper。

### B. 工具型页面模板

适用：未来 LabTools。

推荐模板：

1. 工具标题。
2. 输入区。
3. 计算 / 生成按钮。
4. 结果卡片。
5. 单位说明 / 使用提示。
6. 保存或导出。
7. 开发者诊断默认不展示。

LabTools 未来不得自建独立 Shell、独立主色或独立按钮体系。工具结果必须标记为计算辅助或记录辅助，不伪装成生信分析、Meta 分析、临床结论或正式报告。

### C. 数据列表型页面模板

适用：数据集、文献、候选结果。

推荐模板：

1. 筛选 / 搜索区。
2. 列表区。
3. 详情区。
4. 保存 / 忽略 / 加入队列。
5. 状态标签。

现状风险：

- Bioinformatics GEO/GSE 候选结果中“登记 / 下载 / 添加”语义需要统一。
- Meta 文献候选、去重、筛选页面未来合入时必须把 `preview_id`、`queue_path`、`decisions_path` 进入开发者详情。

## 5. Bioinformatics 发现的问题

P1：

- 分析任务中心仍像技术命令面板，多个主操作竞争。
- 结果浏览页仍暴露结果路径、参数 JSON、warning 技术列、run id 等字段。
- 标准化页面的资产表仍显示 asset id、validation_status、manifest 结构，虽然部分已有技术详情意识，但主界面还需进一步收敛。

P2：

- 普通 `pages/*_page.py` 多数仍保留默认 QPushButton、重复 summary card、title、error label QSS。
- `登记首条结果为数据来源`、`添加到项目`、`下载并添加`、`加入报告`、`保存默认资产选择` 等动词体系需要统一。
- `Ready`、`partially_ready`、`ready_with_warnings`、`unavailable`、`skipped_dry_run`、`configured_not_run` 等状态需要映射到 shared status family。

P3：

- legacy UI 保留旧按钮、状态和日志表达，不作为新 UI 参考，当前不重构。

## 6. Meta Analysis 发现的问题

本阶段没有修改 Meta Analysis UI 代码。

MainLine `app/meta_analysis/workspace.py` 当前问题：

- `Meta 分析模块` title 和 page heading 仍使用内联字号。
- `返回模块首页` 按钮未接入 shared button helper。
- 项目状态文本会显示 `summary.status`、项目根目录和 manifest 读取失败信息，普通主界面技术字段密度偏高。
- 左侧 `Meta 项目首页 / 项目契约 / 功能开发线` 是主线占位壳，可保留，但后续正式合入完整 Meta workflow 前必须重做状态 badge、按钮层级和开发者详情。

从 Stage 0.1 已记录的 dev/meta-analysis 风险继续有效：

- PICO、检索策略、文献库、去重、筛选页面状态多、按钮多，容易形成独立视觉体系。
- `Draft ID`、`preview_id`、`queue_path`、`decisions_path`、`manifest`、`run_count`、`schema` 等字段必须进入开发者详情。
- Meta 不得把紫色或 `#0F766E` 等局部色作为模块主色替代总色板。

## 7. LabTools 未来接入要求

MainLine 当前不存在 `app/labtools/`，本阶段未创建业务代码。

未来 LabTools 应遵守：

- 作为 Shell 内模块接入，不自建独立导航或主题。
- 默认采用工具型页面模板。
- 使用 shared UI tokens、status badge、button helper。
- 主按钮用于“计算 / 生成”，次按钮用于“复制 / 导出 / 保存记录”。
- 危险按钮用于“清空 / 删除记录”，必须使用 danger helper。
- 状态文案应使用“待输入 / 已计算 / 需复核 / 错误 / 已保存”，并映射到 shared status family。
- 技术细节、算法参数、图像处理阈值、OpenCV/ImageJ/Fiji 版本、输入 provenance 应进入开发者详情或报告审计，不默认展示在工具主界面。

## 8. 是否新增 Shared UI Helper

是。新增 helper 位于 `app/shared/ui/theme.py`，并通过 `app/shared/ui/__init__.py` 导出：

- `status_badge_qss(status)`
- `primary_button_qss()`
- `secondary_button_qss()`
- `quiet_button_qss()`
- `danger_button_qss()`
- `navigation_button_qss()`
- `button_qss(role)`
- `section_card_qss(selector="QFrame")`
- `diagnostic_card_qss(selector="QFrame")`

这些 helper 均为纯字符串 QSS，不导入 Qt，不导入业务模块，不改变业务语义。

## 9. 是否进行了低风险试点

是。

试点文件：

- `app/bioinformatics/pages/geo_import_page.py`
- `app/bioinformatics/pages/local_expression_import_page.py`

试点内容：

- 功能状态、等待状态、完成状态、warning 状态、error 状态使用 `status_badge_qss()`。
- 主操作和次操作按钮使用 shared button helper。
- disabled 下一步按钮使用 navigation helper。

未做的事：

- 未全量替换所有 Bioinformatics 页面。
- 未修改 workflow 业务逻辑。
- 未修改 Meta UI。
- 未创建 LabTools。
- 未改变任何数据结构、分析逻辑、下载、识别、标准化、任务或报告逻辑。

## 10. Stage 0.5 或后续处理

建议 Stage 0.5 处理：

1. 将 Bioinformatics 其余普通 `pages/*_page.py` 的按钮和状态标签迁移到 shared helper。
2. 在 Bioinformatics workflow 的 `_button()` 和 `_apply_button_semantics()` 中复用 shared button helper，避免维护两套按钮语义。
3. 增加 `DeveloperDetails` 或 `diagnostic_card_qss()` 的低风险试点，把路径、manifest、raw JSON、run id 等收敛到折叠区。
4. 审计分析任务中心，将多个 primary action 拆分为“主流程动作”和“开发者诊断动作”。
5. 审计结果浏览页，隐藏参数 JSON、路径、warning 技术列，主界面只保留研究人员可理解摘要。
6. Meta 合入前先做专门 UI 对齐阶段，不直接合入独立状态/按钮体系。
7. LabTools 接入前先提交工具型页面模板和 shared helper 使用测试。

## 11. P0 / P1 / P2 / P3 风险分级

### P0

- Meta 完整 workflow 如果带独立主题、独立按钮体系、独立状态标签直接合入 MainLine，会破坏 UI Governance 权威。
- LabTools 如果创建独立 Shell 或独立工具箱视觉体系，会破坏主线 Shell 权威。

### P1

- Bioinformatics 分析任务中心多个主按钮竞争，影响用户判断下一步。
- 结果浏览和报告相关页面仍暴露路径、JSON、run id、manifest 等技术字段。
- 统一 status badge 和 button helper 已建立，但多数页面尚未接入，存在继续分裂风险。

### P2

- 普通 Bioinformatics 子页面仍有默认按钮和重复 QSS。
- Shell 设置页、测试页、Meta 最小入口仍未接入 shared page structure helper。
- 状态别名映射刚建立，仍需结合实际页面逐步校准。

### P3

- legacy UI 仍保留旧视觉语言，只记录，不重构。
- MainLine Meta 最小入口的开发边界文案当前可保留，但正式功能合入前需重做。

## 12. 是否修改业务逻辑

没有。

本阶段只修改 shared UI helper、两个 Bioinformatics 入口页的视觉样式调用、UI helper 测试和本审计文档。没有修改服务调用、数据模型、分析流程、下载逻辑、识别逻辑、标准化逻辑、AI Gateway、词库、报告生成或 Meta / LabTools 业务代码。

## 13. 测试结果

已完成验证：

- `git diff --check`：通过
- `python3 -m pytest tests/ui/test_shared_ui_theme.py -q`：6 passed
- `python3 -m py_compile app/shared/ui/theme.py app/bioinformatics/pages/geo_import_page.py app/bioinformatics/pages/local_expression_import_page.py`：通过
- `python3 -m app.main --smoke-test`：通过
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：139 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`：264 passed

`git diff --cached --check` 在提交前执行。
