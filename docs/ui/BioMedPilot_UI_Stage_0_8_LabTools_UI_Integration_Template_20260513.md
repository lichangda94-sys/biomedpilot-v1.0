# BioMedPilot UI Stage 0.8：LabTools UI 接入规范与工具型页面模板

日期：2026-05-13

## 1. 本阶段工作范围

本阶段承接 UI Stage 0.1-0.7，只在 MainLine 内为未来 LabTools / 实验工具模块建立 UI 接入规范和工具型页面模板。

实际工作：

- 审计 MainLine Shell 是否已有 LabTools 入口或预留入口。
- 审计 shared UI helper 是否足以支持工具型页面。
- 新增跨模块通用的工具型页面 card QSS helper。
- 更新 shared UI helper 测试。
- 新增本 Stage 0.8 报告。

未做的事：

- 未创建 `app/labtools/`、`app/lab_tools/` 或 `app/lab/`。
- 未开发 LabTools 业务页面、计算器、图像分析或实验记录功能。
- 未修改 LabTools 独立 worktree。
- 未修改 Bioinformatics 或 Meta UI。
- 未新增业务数据 schema。

## 2. 开始前 git status 结论

开始前确认当前目录为：

```text
/Users/changdali/Developer/biomedpilot v1.0/MainLine
```

开始前执行：

```text
git status --short
```

结论：MainLine 工作树 clean，未发现未预期 tracked 或 untracked change。

## 3. 是否发现 MainLine 中已有 LabTools 入口或预留入口

未发现 MainLine 中已有 LabTools 入口或预留业务代码。

审计结果：

- `app/` 下不存在 `app/labtools/`、`app/lab_tools/` 或 `app/lab/`。
- `app/shell/module_selection.py` 当前只提供 Bioinformatics 和 Meta Analysis 两张模块入口卡。
- `app/shell/main_window.py` 当前只创建 Bioinformatics、Meta Analysis、设置中心和测试模式页面。
- `SidebarWidget` 当前没有 LabTools 导航入口。

结论：本阶段不强行创建 LabTools 入口。未来 LabTools 进入 MainLine 前，应先在 LabTools 独立 worktree 完成模块开发与测试，再通过 Integration 或等效验证流程接入 MainLine Shell。

## 4. LabTools 未来接入 Shell 的 UI 原则

LabTools 必须作为 BioMedPilot Shell 内模块接入，不得形成第三套独立视觉体系。

原则：

- 使用 MainLine Shell 作为全局入口。
- 使用统一总色板：`#12324A`、`#1BAE9F`、`#F5F7F9`、`#FFFFFF`。
- 使用 shared UI tokens、status badge、button role 和 card helper。
- 不自建独立主色、独立导航、独立窗口框架或独立按钮体系。
- 实验工具结果必须标记为计算辅助、记录辅助或测量辅助，不得伪装成 Bioinformatics 结果、Meta Analysis 结果、临床结论或投稿级结论。
- LabTools 产物不得污染 Bioinformatics 或 Meta project manifest。

## 5. 工具型页面标准结构

未来 LabTools 单工具页面应采用以下结构：

1. 工具标题区：工具名称、一句话用途说明、Developer Preview / 本地测试版标记。
2. 状态摘要区：草稿、输入不完整、可计算、结果已生成、需复核、错误。
3. 输入区：参数字段、单位、默认值、必填/可选说明。
4. 主操作区：一个 primary action，例如“计算”“生成”“保存方案”。
5. 结果区：结果摘要、详细结果、表格或图表。
6. 次操作区：重置、导入、导出、复制、查看详情。
7. 开发者诊断区：默认折叠，用于 raw 参数、schema、internal id、debug info。

工具型页面不使用流程型“下一步”作为默认核心结构。只有当某个工具确实属于多步实验记录流程时，才允许出现 Primary Next。

## 6. 输入区 UI 规范

输入区必须：

- 使用统一 section card 或 `tool_input_card_qss()`。
- 参数字段分组清晰，每组不超过用户一次可理解的输入范围。
- 单位必须明确，例如 mL、uL、ng/uL、cells/mL、Ct、cycle、mm、pixel。
- 默认值必须标注来源，例如“系统默认”“来自上次记录”“用户手动输入”。
- 不把内部参数名直接暴露给普通用户，例如 `raw_value`、`internal_id`、`schema_key`。
- 对必填项、范围错误、单位缺失使用 warning / error 状态，不使用技术异常堆栈。

## 7. 参数区 UI 规范

参数区必须：

- 使用 `parameter_group_card_qss()` 或等效 shared card helper。
- 按输入语义分组，例如“样本信息”“试剂浓度”“目标体积”“仪器参数”。
- 保持中文友好，必要英文缩写只保留科研常用缩写。
- 不在主界面显示 raw JSON、schema、内部字段名、临时文件路径。
- 图像分析类工具必须把算法名、阈值、预处理、分割参数、软件版本和人工复核要求放入诊断区或报告审计，而不是混在普通输入标题中。

## 8. 主操作 / 次操作 / 危险操作按钮规则

主操作：

- 同一操作区最多一个 primary action。
- 常见文案为“计算”“生成”“保存方案”。
- 主操作必须代表当前页面最自然的用户下一步。

次操作：

- 使用 secondary / quiet。
- 常见文案为“重置”“导入”“导出”“复制”“查看详情”“刷新状态”。
- 不能与主操作视觉竞争。

危险操作：

- 使用 danger helper。
- 常见文案为“清空”“删除”“覆盖”。
- 必须明确影响范围，不得只靠颜色表达风险。

禁止：

- 不允许多个主按钮并列竞争。
- 不允许把“写入 manifest”“创建 registry entry”“保存 raw payload”等技术动作作为普通用户主按钮。

## 9. 结果区 UI 规范

结果区必须：

- 使用 `result_summary_card_qss()` 展示最重要的结果摘要。
- 没有结果时使用 `empty_result_card_qss()` 或等效空状态卡。
- 结果摘要优先，详细表格其次。
- 图表或表格必须有标题、单位、来源说明。
- 可导出内容必须明确格式，例如 CSV、TSV、PNG、PDF、Markdown。
- 工具结果必须标记为计算辅助 / 记录辅助 / 测量辅助。
- 不把 raw JSON、临时文件路径、internal id、debug log 放在主界面。

## 10. 开发者诊断区规范

开发者诊断区默认折叠。

允许包含：

- 参数原始值。
- 计算日志。
- schema。
- internal id。
- raw JSON。
- debug info。
- 图像分析算法参数、阈值、软件版本。
- 输入 provenance。

不允许：

- 不作为普通用户主路径。
- 不把诊断内容伪装成生产级功能。
- 不把未验证算法输出描述为临床判断或正式科研结论。

## 11. 哪些 shared UI helper 已足够复用

未来 LabTools 可直接复用：

- `page_title_qss()`
- `helper_text_qss()`
- `warning_text_qss()`
- `error_text_qss()`
- `status_badge_qss()`
- `button_qss()`
- `primary_button_qss()`
- `secondary_button_qss()`
- `quiet_button_qss()`
- `danger_button_qss()`
- `section_card_qss()`
- `diagnostic_card_qss()`
- `surface_card_qss()`

这些 helper 已覆盖标题、辅助说明、状态标签、按钮层级、普通卡片和诊断卡片。

## 12. 是否新增 shared UI helper

是。

本阶段新增跨模块通用 helper：

- `tool_input_card_qss(selector="QFrame")`
- `parameter_group_card_qss(selector="QFrame")`
- `result_summary_card_qss(selector="QFrame")`
- `empty_result_card_qss(selector="QFrame")`

这些 helper 位于 `app/shared/ui/theme.py`，并通过 `app/shared/ui/__init__.py` 导出。它们为纯 QSS 字符串 helper，不依赖 Qt，不导入业务模块，不绑定 LabTools 业务，不改变任何业务含义。

## 13. 是否创建 LabTools 业务代码

未创建 LabTools 业务代码。

本阶段没有新增 `app/labtools/`，没有实现任何实验工具计算功能，没有创建 LabTools 页面、模型、schema、manifest 或服务层。

## 14. 是否修改 Bioinformatics / Meta UI

未修改 Bioinformatics UI。

未修改 Meta Analysis UI。

## 15. 是否触碰独立 worktree

未触碰 LabTools 独立 worktree。

未触碰 Bioinformatics 独立 worktree。

未触碰 Meta 独立 worktree。

## 16. 后续 UI Stage 建议

建议后续 UI Stage：

1. 建立跨模块 `DeveloperDetails` 组件或 helper，减少 Bioinformatics、Meta、未来 LabTools 页面重复实现诊断折叠区。
2. 为 Shell 模块选择页设计 LabTools 入口卡规范，但不要在业务未集成前创建可点击完整入口。
3. 在 LabTools 独立 worktree 中先按工具型页面模板完成一个最小只读 UI 骨架，再经 Integration 验证后进入 MainLine。
4. 为工具型页面增加 UI lint 或测试规则：禁止直接硬编码主色、禁止多个 primary action、禁止主界面显示 raw JSON / internal id / temp path。
5. 图像分析类工具进入 UI 前，先定义“测量辅助 / 人工复核”状态标签和算法参数诊断规范。

## 17. P0 / P1 / P2 / P3 风险分级

P0：

- 如果未来 LabTools 绕过 MainLine Shell，自建独立主色、导航和窗口结构，会破坏 UI Governance 权威。
- 如果 LabTools 结果写入 Bioinformatics 或 Meta project manifest，会造成跨模块污染。

P1：

- 如果 LabTools 工具页堆叠多个“计算 / 生成 / 保存 / 导出”主按钮，会形成与 Bioinformatics 和 Meta 不一致的按钮体系。
- 如果图像分析或实验计算结果不标记为辅助 / testing-level / 需人工复核，容易被误解为正式科研或临床结论。
- 如果主界面显示 raw JSON、schema、internal id、临时路径、debug log，会重复早期 Bioinformatics / Meta 技术字段暴露问题。

P2：

- shared UI helper 目前仍是 QSS 字符串层，尚未形成 QWidget 组件层。
- 工具型页面尚无真实 MainLine 页面试点；未来第一个 LabTools 页面接入时需要视觉回归。
- 空状态、结果摘要和参数分组的细节仍需结合真实工具校准。

P3：

- MainLine 当前没有 LabTools 入口，这是正确边界；不属于当前缺陷。
- LabTools 独立 worktree 的现有能力不在本阶段审计范围，后续需在 LabTools 任务中单独评估。

## 18. 测试结果

本阶段已执行以下验证：

- `git diff --check`：通过。
- `python3 -m app.main --smoke-test`：通过。
- `python3 -m pytest tests/ui/test_shared_ui_theme.py -q`：7 passed。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：144 passed。
- `git diff --cached --check`：提交前执行并通过。

## 19. 是否未执行 git push

未执行 `git push`。
