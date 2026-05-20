# Bioinformatics Stage B1E：结果浏览页与项目报告页用户化记录

日期：2026-05-13

工作区：`/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

说明：本阶段遵循 `01_ProjectControl/Global_Development_Manual.md`。Bioinformatics 本地 `docs/handoff/Global_Development_Manual.md` 与 `docs/architecture/*20260513.md` 仍不存在；本阶段继续沿用 B1-B1D 的处理方式，读取 `01_ProjectControl` 与 `MainLine` 中的权威副本。未发现本任务与总开发手册冲突。

## 1. 结果浏览页改造前主要问题

结果浏览页原主界面直接展示 result index 视角：

- 分析类型 raw key。
- 文件类型。
- 创建时间。
- raw path / file path。
- status 原文。
- warning。
- 结果详情 JSON。

这些信息适合开发者排查，不适合普通用户判断“这个结果来自哪里、是否能打开、是否能进入报告、是否只是测试记录”。

## 2. 项目报告页改造前主要问题

项目报告页原主界面直接展示 Markdown 原文和 report manifest JSON。由于 report builder 当前会收集项目路径、输入文件、manifest 和 warnings，直接显示原文容易把 raw path、schema、manifest path 等技术信息放入普通用户视图。

此外，页面只显示“生成 / 刷新项目报告”和导出 placeholder，没有明确说明：

- 哪些内容是报告草稿。
- 哪些结果是 imported result。
- 哪些结果只是 testing-level。
- 哪些任务只是 configured-not-run 或 dry-run。
- 当前报告不是生产级、临床级或投稿级输出。

## 3. 当前主界面如何展示结果来源和状态

结果浏览页现在显示：

1. 当前结果状态
   - 可查看结果数量。
   - 导入结果数量。
   - 测试级结果数量。
   - dry-run 数量。
   - 配置草稿数量。

2. 报告适用性
   - 哪些结果可进入报告草稿。
   - 是否必须保留导入 / 测试级 / 真实计算标签。
   - 如果只有配置草稿或 dry-run，则提示不适合生成结果报告。

3. 用户化结果表
   - 结果名称。
   - 结果类型。
   - 来源说明。
   - 当前状态。
   - 是否可打开。
   - 是否可进入报告。
   - 下一步 / 注意事项。

4. 开发者诊断
   - 原始 result index、display entries、task records、warnings 和路径信息保留在折叠区。

项目报告页现在显示：

1. 报告草稿状态
   - 是否已生成 Markdown 报告草稿。
   - PDF / DOCX / HTML 是否仍为 testing placeholder。

2. 结果语义摘要
   - 导入结果、测试级结果、dry-run、配置草稿、真实计算结果的数量。

3. 报告部分表
   - 项目信息。
   - 数据来源。
   - 数据识别。
   - 数据标准化。
   - 分组与比较设计。
   - 分析任务状态。
   - 已有结果。
   - 报告草稿。

4. 用户摘要预览
   - 只展示用户可理解的草稿说明。
   - Markdown 原文、manifest 和 raw result index 移入开发者诊断。

## 4. 结果语义区分方式

- imported result：显示为“导入表格中的已有差异分析结果，不是本软件重新计算”。
- testing-level：显示为“测试级 / 开发者预览结果，不等于正式科研结果”。
- dry-run：显示为“流程记录 / dry-run，未执行真实分析”。
- configured-not-run：显示为“已配置，尚未运行”。
- real computed result：只有 result index 明确提供 `real computed result` 或等价语义时才显示；当前阶段没有新增真实计算结果。

本阶段未新增真实 DEG 执行器，未生成假 DEG、假火山图、假富集结果，也未把 dry-run、testing-level 或 imported result 写成真实计算结果。

## 5. 移入开发者诊断的技术字段

以下内容不再直接出现在用户主界面，保留在“开发者诊断”折叠区：

- result index raw key
- result manager path
- report manifest
- report manifest path
- raw Markdown 原文
- raw JSON
- schema version
- task id
- task record path
- raw result path / file path
- internal status / execution key

## 6. 当前仍未完全用户化的内容

- report builder 核心逻辑未改，Markdown 原文仍可能包含技术信息，因此本阶段把 Markdown 原文放入开发者诊断，主界面只展示用户摘要。
- imported DEG 如果只存在于识别报告中，结果浏览页可作为导入结果展示；report builder 仍主要依赖 result index 生成正式 Markdown 表格。
- 结果浏览页仍没有专门的 imported DEG 表格预览器，只提供来源和状态层面的浏览。
- PDF / DOCX / HTML 导出仍是 testing placeholder。

## 7. 留给后续阶段

后续 DEG 配置页、真实 preflight 或 Integration 阶段应处理：

- 独立 DEG 配置页和强输入校验。
- imported DEG 的专门浏览和字段解释。
- 真实 preflight 与真实 executor 的边界设计。
- 结果页对真实计算结果、导入结果、测试级结果的更细粒度筛选。
- 报告 builder 的用户版 Markdown 模板，避免 raw path 和 manifest 信息进入用户报告。
- Integration 阶段验证结果语义在 MainLine / ReleaseBuild 中保持一致。

## 8. 测试结果

已执行：

- `python3 -m app.main --smoke-test`：通过。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`：215 passed。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：143 passed。

新增/更新测试：

- 结果浏览页用户化标题、结果来源和语义文案。
- imported DEG 不被描述为本软件重新计算。
- dry-run / testing-level 不被描述为真实结果。
- 结果浏览页主界面不直接暴露 raw path、schema、task id、raw key。
- 项目报告页明确 draft / imported / testing-level / dry-run / configured-not-run 语义。
- 报告页主界面不直接暴露 manifest、schema、raw path。
- 开发者诊断区仍保留 result index、report manifest、raw path 和 schema version。

## 9. 风险和人工确认事项

- 本阶段未修改 project manifest schema，未重写 result service 或 report builder 核心逻辑。
- 未删除 result index、report manifest、task record 或 imported DEG 相关能力。
- 未修改 shared vocabulary、AI Gateway、Meta、Vocabulary、LabTools、AI、UIShell、Integration、ReleaseBuild、MainLine 等其他 worktree。
- 需要人工确认后续是否把 report builder 改成用户版模板，或继续保留当前技术 Markdown 并通过 UI 摘要屏蔽技术细节。

## 10. 其他 worktree 状态

提交前检查到 LabTools 和 Meta 存在未提交改动；这些改动不是本阶段产生，本阶段未修改其业务文件，也未纳入提交。Integration 在最终检查时为干净状态。

其他 worktree 状态将在最终提交汇报中再次记录。
