# BioMedPilot UI Stage 0.6：Bioinformatics 分析任务中心与结果/报告页 UI 风险收敛审计

日期：2026-05-13

## 1. 本阶段工作范围

本阶段仅在 MainLine 工作树内执行，范围限定为 Bioinformatics 分析任务中心、结果浏览、项目报告相关 UI 的审计与低风险收敛。

本阶段不开发新分析功能，不修改分析执行逻辑，不修改 result manager、report builder、analysis task center 服务层逻辑，不修改 manifest / JSON / data schema，不修改 Meta Analysis UI，不创建 LabTools 代码。

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

## 3. 审计页面与区域

本阶段审计并低风险调整了以下区域：

- `app/bioinformatics/workflow_pages.py`
  - `BioinformaticsAnalysisTaskCenterWidget`
  - `BioinformaticsResultsBrowserWidget`
  - `BioinformaticsReportViewerWidget`
  - `_analysis_task_run_row`
- `tests/ui/test_bioinformatics_workflow_pages.py`
  - 分析任务中心按钮层级断言
  - 结果页诊断折叠断言
  - 报告页诊断折叠断言
  - 任务历史主界面不暴露 asset id 的断言

## 4. 分析任务中心主操作竞争审计结论

Stage 0.5 后遗留的 P1 风险仍集中在分析任务中心：同一操作区内同时存在“配置 DEG 任务”“生成 DEG 分析任务记录”“生成并校验 DEG 输入”“创建任务”“运行 GEO 差异分析”等多个视觉上接近主按钮的操作。

这会导致普通用户无法判断当前阶段最推荐的下一步，也会把测试级或开发者预览操作与正式流程操作混在同一视觉层级。

本阶段将“创建 DEG 配置草稿”保留为分析任务中心当前最明确的主操作，其余操作降级为 secondary action。流程导航“继续：结果浏览”标记为 `primary_next`。

## 5. 实际调整的按钮视觉层级

分析任务中心：

- “刷新任务中心”调整为“刷新状态”，secondary。
- “去确认分组”调整为“确认分组”，secondary。
- “配置 DEG 任务”调整为“创建 DEG 配置草稿”，`primary_action`。
- “生成 DEG 分析任务记录”调整为“生成任务记录”，secondary。
- “生成并校验 DEG 输入”调整为“校验 DEG 输入”，secondary。
- “创建任务”调整为“创建通用任务”，secondary。
- “运行 GEO 差异分析”保留行为，降级为 secondary。
- “查看任务记录详情”调整为“查看详情”，secondary。
- “继续：结果浏览”标记为 `primary_next`。

结果浏览：

- “刷新结果”保持 secondary。
- “打开结果文件夹”保持 secondary。
- 原主界面“打开参数 JSON”移入开发者诊断区，并改为“打开结果索引”。
- 原主界面“加入报告”占位操作移入开发者诊断区，并改为“加入报告（占位）”。
- 增加流程导航“继续到项目报告”，`primary_next`。

项目报告：

- “生成 / 刷新项目报告”标记为 `primary_action`。
- “打开报告文件”“打开报告文件夹”“导出 DOCX”“导出 HTML”均标记为 secondary。

## 6. 是否改变按钮行为

未改变按钮业务行为。

本阶段只调整按钮文案、按钮角色属性与视觉层级。分析任务创建、DEG 草稿生成、预检、运行入口、结果刷新、报告生成、文件打开等底层行为未被修改。

## 7. 结果页技术字段暴露审计结论

结果浏览页此前在主表格中直接显示结果文件路径，并在主操作区提供“打开参数 JSON”。这些内容对普通用户不构成主要决策信息，且会把 result index / manifest / full path 等技术字段暴露到主界面。

本阶段将结果表格中的“路径”列改为“可打开”列，只展示“可打开 / 未记录”这类用户可理解状态。完整路径、result index、manifest 和原始 JSON 默认进入开发者诊断折叠区。

## 8. 报告页技术字段暴露审计结论

项目报告页此前直接在主界面展示 report manifest JSON。该内容对普通用户不是报告阅读所需信息，应归入开发者诊断。

本阶段将报告 manifest 默认折叠到“开发者诊断”区，主界面保留报告状态、可报告内容摘要和 Markdown 草稿预览。

## 9. 实际移动或折叠的技术字段

分析任务中心：

- 任务记录原始 JSON 默认折叠到“开发者诊断”。
- run id 不再显示在任务历史主表格。
- source asset id 不再显示在任务历史主表格，改为“1 个输入资产”等摘要。
- 创建任务、创建 DEG 草稿、生成 DEG 任务记录后的状态提示不再直接暴露 task id / run id。

结果浏览：

- full local path 不再显示在结果主表格。
- result index 入口移入“开发者诊断”。
- 结果 raw JSON 详情默认折叠。

项目报告：

- report manifest 默认折叠到“开发者诊断”。
- 报告预览区增加“报告预览（草稿）”提示，避免把 Developer Preview 报告伪装为正式出版结果。

## 10. 是否新增或扩展 shared UI helper

未新增或扩展 shared UI helper。

本阶段复用既有 `_button` role 机制、card / muted / text preview 基础 helper，以及 Stage 0.3 / 0.4 已建立的 shared UI tokens 与按钮角色样式。

## 11. 是否修改业务逻辑

未修改业务逻辑。

未修改分析执行逻辑、结果索引结构、报告生成逻辑、manifest / JSON / data schema、AI Gateway、词库、下载、识别、标准化或分析服务层逻辑。

## 12. 是否触碰 Bioinformatics / Meta 独立 worktree

未触碰 Bioinformatics 独立 worktree。

未触碰 Meta 独立 worktree。

## 13. 是否修改 Meta UI

未修改 Meta Analysis UI。

## 14. 是否创建 LabTools 代码

未创建 LabTools UI 或业务代码。

## 15. 仍需后续阶段处理的问题

- 结果浏览页仍有部分结果详情 raw JSON，仅已默认折叠；后续可进一步拆分为用户摘要与开发者详情。
- 分析任务中心的任务能力摘要仍包含较多流程诊断信息，后续可拆为普通摘要和开发者诊断。
- 报告页 DOCX / HTML 导出仍是 testing placeholder，应在后续正式功能阶段明确产品状态与禁用/启用规则。
- Bioinformatics 其他轻量页仍可能存在 path、schema、registry entry 等技术字段，需要在后续阶段继续按页面审计。
- 后续可考虑为“开发者诊断折叠区”建立跨模块统一组件，减少页面内重复写法。

## 16. P0 / P1 / P2 / P3 风险分级

P0：未发现会破坏 UI 总规范权威或主线 Shell 权威的问题。

P1：

- 分析任务中心此前多个主按钮竞争，本阶段已做低风险收敛；仍需后续继续区分正式流程操作与 testing-level 操作。
- 结果/报告页此前直接暴露 full path、result index、manifest、raw JSON，本阶段已默认折叠核心区域；其他页面仍需继续排查。

P2：

- 任务能力摘要、结果详情、报告 manifest 的开发者内容仍存在，但已折叠；后续可使用统一组件。
- 报告导出占位操作需要在正式功能阶段调整为明确禁用态或完整实现态。

P3：

- 任务历史表格目前用“任务记录”作为 run id 的用户态占位文案，后续可根据正式任务命名体系优化。
- “可打开 / 未记录”可进一步替换为统一状态 badge。

## 17. 测试结果

本阶段已执行以下验证：

- `git diff --check`：通过。
- `python3 -m app.main --smoke-test`：通过。
- `python3 -m pytest tests/ui/test_shared_ui_theme.py -q`：6 passed。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：143 passed。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`：264 passed。
- `git diff --cached --check`：提交前执行并通过。

## 18. 是否未执行 git push

未执行 `git push`。
