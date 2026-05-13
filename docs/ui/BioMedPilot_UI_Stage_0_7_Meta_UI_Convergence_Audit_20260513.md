# BioMedPilot UI Stage 0.7：Meta UI 独立视觉体系收敛审计与低风险迁移

日期：2026-05-13

## 1. 本阶段工作范围

本阶段承接 UI Stage 0.1-0.6，只在 MainLine 工作树内执行 Meta UI 独立视觉体系风险审计和低风险迁移。

实际范围：

- MainLine `app/meta_analysis/workspace.py`
- MainLine `app/meta_analysis/project_workspace.py` 的只读审计
- `tests/meta_analysis/test_mainline_meta_contract.py`
- 本 Stage 0.7 审计报告

未做的事：

- 未进入或修改 Meta 独立 worktree。
- 未进入或修改 Bioinformatics 独立 worktree。
- 未修改 Bioinformatics UI。
- 未创建 LabTools 代码。
- 未开发 Meta Analysis 新功能。
- 未修改检索、导入、去重、筛选、全文、提取、质量评价、统计、报告服务逻辑。
- 未改变 Meta manifest / JSON / data schema。

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

## 3. 审计的 Meta 页面或区域

MainLine 当前 `app/meta_analysis` 只包含最小 Meta 入口和项目契约层：

- `app/meta_analysis/workspace.py`
  - Meta 主线入口壳
  - 项目首页占位页
  - 项目契约占位页
  - 功能开发线占位页
  - 项目绑定状态展示
- `app/meta_analysis/project_workspace.py`
  - Meta 项目 manifest / config 创建与读取
  - 无 QWidget UI，本阶段只做技术字段暴露风险审计

MainLine 当前不存在完整 PICO/PICOS/PECO、检索策略、文献导入、文献库、去重、筛选、全文、提取、质量评价、统计或报告 UI 页面。本阶段不虚构这些页面已实现，只记录未来合入风险。

## 4. Meta 是否存在独立视觉体系风险

存在 P1 风险，但当前 MainLine 风险集中在最小入口壳，尚未形成完整独立 UI。

审计发现：

- `workspace.py` 过去直接使用内联标题字号，例如 `font-size: 22px; font-weight: 700;` 和 `font-size: 18px; font-weight: 700;`。
- 返回按钮使用默认 QPushButton，没有统一 `buttonRole`。
- 主状态文本直接显示完整项目目录和 manifest 相关语义。
- 页面卡片、导航列表、边界提示没有接入 shared UI helper。
- 普通主界面可见 `mainline`、`dev/meta-analysis`、`manifest contract` 等开发线和技术契约文案。

本阶段已将这些入口层问题做低风险收敛。完整 Meta workflow 尚未在 MainLine 实现；后续从 Meta 独立 worktree 合入前仍需单独审计 PICO、检索、文献库、去重、筛选、全文、提取、质评、统计和报告页面，防止带入独立视觉体系。

## 5. Meta 按钮层级审计结论

MainLine 当前 Meta 入口只有返回按钮和新增的开发者诊断折叠按钮，没有 PICO 草稿、检索策略生成、文献导入、去重、筛选等业务按钮。

审计结论：

- “返回模块首页”应作为 navigation back，而不是默认按钮。
- “展开开发者诊断”应为 secondary / diagnostic，不应成为主流程按钮。
- 当前 MainLine Meta 入口没有多个 primary action 竞争。
- 未来完整 Meta 页面合入时，“确认研究问题”“生成检索策略”“导入文献”“执行去重”“继续筛选”等必须遵循同一页面最多一个 primary action / primary next 的规则。

实际迁移：

- `metaBackButton` 设置 `buttonRole = navigation_back`，样式使用 `button_qss("navigation_back")`。
- `metaDeveloperDiagnosticsToggle` 设置 `buttonRole = secondary`，样式使用 `button_qss("secondary")`。

## 6. Meta 状态标签审计结论

当前 MainLine Meta 状态主要来自项目绑定状态：

- 未绑定项目。
- 已绑定 Meta 项目。
- 当前目录不是有效 Meta 项目。
- 项目 manifest 中的 `status`，当前常见值为 `created`。

审计发现：

- 过去状态以普通文本显示，且混入完整路径。
- `created` 这类内部状态不适合作为普通用户主文案直接展示。

实际迁移：

- 未绑定项目使用 `status_badge_qss("not_ready")`。
- 已绑定但状态为 `created` 时，主界面显示“草稿”，使用 `status_badge_qss("draft")`。
- 无效目录使用 `status_badge_qss("warning")`。
- 内部原始 `status` 保留在开发者诊断区，不改变真实数据结构。

## 7. Meta 技术字段暴露审计结论

MainLine Meta 入口此前在主状态文本中直接显示：

- full local path / project root
- manifest 读取状态
- `created` 等内部状态
- `dev/meta-analysis` 开发线文本
- `manifest contract` 技术表述

本阶段已按 UI 总规范收敛：

- 普通主界面只显示“当前 Meta 项目：项目名 · 草稿 / 已就绪”等用户可理解状态。
- 完整项目目录、manifest path、config path、workflow_stage、内部 status、contract_version、开发线名称进入开发者诊断折叠区。
- 普通主界面文案将 `dev/meta-analysis` 改为“独立开发线”，将 `manifest contract` 改为“项目结构契约”。

## 8. 实际迁移或调整的 UI 样式

修改 `app/meta_analysis/workspace.py`：

- Header card 使用 `section_card_qss("QFrame#metaMainlineHeader")`。
- 页面标题使用 `page_title_qss()`。
- 副标题和页面说明使用 `helper_text_qss()`。
- 返回按钮使用 `button_qss("navigation_back")`。
- 开发者诊断折叠按钮使用 `button_qss("secondary")`。
- 开发者诊断卡片使用 `diagnostic_card_qss("QFrame#metaDeveloperDiagnosticsCard")`。
- 页面占位卡使用 `section_card_qss(...)`。
- 页面边界提示使用 `status_badge_qss("testing")`。
- 项目状态使用 `status_badge_qss(...)`。
- 导航列表使用 shared UI token 中的 surface、border、text、selected background 颜色。

修改 `tests/meta_analysis/test_mainline_meta_contract.py`：

- 验证 Meta 主状态不再显示完整项目路径或 `meta_project_manifest.json`。
- 验证项目状态显示为中文“草稿”并使用 draft badge。
- 验证完整路径和 manifest path 默认保留在隐藏的开发者诊断区。
- 验证标题、header、返回按钮和开发者诊断按钮使用 shared UI helper / button role。

## 9. 是否改变按钮行为

未改变按钮业务行为。

“返回模块首页”仍连接原有 `on_back` 回调；开发者诊断按钮只切换本页诊断卡片显示状态。没有改变 Meta workflow 状态机、项目绑定、项目创建或项目打开逻辑。

## 10. 是否移动技术字段到开发者诊断区

是。

本阶段移动或折叠到开发者诊断区的内容：

- `project_root`
- `manifest_path`
- `config_path`
- `workflow_stage`
- 内部 `status`
- `contract_version`
- `dev/meta-analysis` 开发线名称
- 无效目录下的 validation errors

主界面不再默认展示完整项目路径和 `meta_project_manifest.json`。

## 11. 是否新增或扩展 shared UI helper

未新增或扩展 shared UI helper。

本阶段复用已有 shared UI helper：

- `button_qss`
- `section_card_qss`
- `diagnostic_card_qss`
- `status_badge_qss`
- `page_title_qss`
- `card_title_qss`
- `helper_text_qss`

## 12. 是否修改 Meta 业务逻辑

未修改 Meta 业务逻辑。

未修改：

- Meta 项目 manifest / config schema。
- 项目创建、打开、验证逻辑。
- 检索、导入、去重、筛选、全文、提取、质量评价、统计、报告服务逻辑。
- active runtime 或 legacy bridge 架构。

## 13. 是否触碰 Meta / Bioinformatics 独立 worktree

未触碰 Meta 独立 worktree。

未触碰 Bioinformatics 独立 worktree。

## 14. 是否修改 Bioinformatics UI

未修改 Bioinformatics UI。

## 15. 是否创建 LabTools 代码

未创建 LabTools UI 或业务代码。

## 16. Active Runtime Legacy Bridge 相关风险

MainLine 当前 `app/meta_analysis` 未发现 active runtime legacy bridge 相关 UI 代码。本阶段仅记录该风险，不处理架构或集成问题。

未来若从 Meta 独立 worktree 合入完整流程，需专门审计：

- legacy bridge 是否把 raw adapter output、legacy path、transitional bridge detail 暴露到普通主界面。
- active runtime 依赖 legacy 的边界是否只在开发者诊断和架构文档中说明。
- legacy / adapter / bridge 状态不得伪装为生产级功能。

## 17. 仍需后续阶段处理的问题

- 完整 Meta workflow 不在 MainLine，本阶段无法审计真实 PICO、检索、文献库、去重、筛选、全文、提取、质评、统计、报告页面的全部按钮和状态。
- 后续 Meta 合入前必须对独立 worktree 页面做 UI token / helper 接入，避免带入独立主色、独立按钮体系和独立状态标签。
- 当前开发者诊断区仍为页面内局部实现，后续可抽取跨模块 `DeveloperDetails` 组件。
- Meta 项目契约占位页仍是最小壳，后续应在正式流程合入时补充用户可理解的项目状态摘要，而不是技术契约说明。
- 未来 PICO、检索策略、文献库、去重、筛选页面应统一使用“确认 / 保存 / 刷新 / 导出 / 查看详情 / 下一步”动词体系。

## 18. P0 / P1 / P2 / P3 风险分级

P0：

- 本阶段未发现需要停止的 P0 冲突。未修改模块边界，未将 Bioinformatics 能力混入 Meta，未创建 LabTools 代码。

P1：

- 完整 Meta workflow 若从独立 worktree 合入时继续使用独立色板、按钮体系、状态标签或技术字段主界面展示，会破坏 UI Governance 权威。
- Meta 当前 MainLine 最小入口此前暴露 full path / manifest 技术文案，本阶段已收敛，但未来完整页面仍需逐页治理。

P2：

- MainLine Meta 入口仍是占位壳，页面密度和流程导航尚不能代表完整 Meta 用户体验。
- 开发者诊断折叠区仍是局部实现，后续应组件化。
- Meta 状态映射目前只覆盖最小项目状态；Imported、Deduplicated、Screening pending、Included / Excluded、Strategy-only、Execution-ready 等需在完整页面合入时扩展。

P3：

- `meta_workspace_layout_state()` 仍保留 `project_dir` 作为内部状态输出，用于测试和 shell contract，不是普通主界面展示。
- `project_workspace.py` 仍在 manifest/config 中记录完整路径，这是数据契约需要，本阶段不修改 schema。

## 19. 测试结果

本阶段已执行以下验证：

- `git diff --check`：通过。
- `python3 -m app.main --smoke-test`：通过。
- `python3 -m pytest tests/ui/test_shared_ui_theme.py -q`：6 passed。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：143 passed。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q`：4 passed。
- `git diff --cached --check`：提交前执行并通过。

## 20. 是否未执行 git push

未执行 `git push`。
