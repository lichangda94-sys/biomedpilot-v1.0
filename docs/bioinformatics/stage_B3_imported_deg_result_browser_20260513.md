# Bioinformatics Stage B3 Imported DEG 专门浏览与用户结果详情页

日期：2026-05-13

## 1. 本阶段完成内容

本阶段新增 imported DEG 专门浏览能力，用于查看用户已经导入的外部差异分析结果，避免用户误以为 BioMedPilot 重新计算了 DEG。

新增内容：

- 新增 `app/bioinformatics/imported_deg_results.py`。
- 新增 “导入结果浏览” 页面。
- 分析任务中心新增入口：“查看已导入差异分析结果”。
- 结果浏览页新增入口：“导入结果浏览”。
- 工作区导航栈新增 imported DEG 专门页。
- imported DEG 可标记为报告候选，但仍保留 `result_semantics = imported result`。

## 2. imported DEG 与软件重新计算 DEG 的边界

本阶段的 imported DEG 语义为：

- 用户导入 / 外部分析结果。
- 导入表格中的已有差异分析结果。
- 不是 BioMedPilot 重新计算。
- 可以浏览和进入报告草稿，但必须保留导入标签。

本阶段明确不做：

- 不接入真实 DEG 执行器。
- 不生成 DEG result table。
- 不生成火山图、热图、富集结果或 GSEA 结果。
- 不把 imported DEG 标记为 `real computed result`。
- 不把 imported DEG 作为 B2 preflight 重新计算输入。

B2 preflight 边界保持不变：

- 仍只生成 `analysis/deg/preflight/deg_preflight_manifest.json`。
- 仍标记 `input_preflight_only_not_deg_result`、`execution = not_run`、`not_a_result = true`。
- imported DEG 只会触发“导入差异结果不能作为重新计算 DEG 输入”的提示。

## 3. 用户可见页面变化

### 分析任务中心

新增次级入口：

- “查看已导入差异分析结果”

该入口只打开 imported DEG 浏览页，不运行 DEG。

### 结果浏览页

新增次级入口：

- “导入结果浏览”

结果列表继续区分 imported result、testing-level、dry-run、configured-not-run、real computed result。

### 导入结果浏览页

主界面显示：

- 当前是否存在已导入 DEG 结果。
- 结果名称。
- 来源说明：用户导入 / 外部分析结果。
- 状态：可浏览 / 格式待确认 / 缺少文件。
- 是否可用于报告：是 / 否 / 需确认。
- 主要列识别：gene、logFC / log2FC、p value、padj / FDR。
- 上调 / 下调 / 不显著数量；仅在主要列可可靠识别时基于预览行计算，否则显示待确认。
- 下一步建议。

详情区显示：

- 表格预览，限制行数。
- 关键列映射状态。
- 阈值草稿：`|log2FC| >= 1` 且 `p value/FDR <= 0.05`。
- 用户备注展示区；不参与内部计算字段。
- 明确说明这是外部导入结果，不代表 BioMedPilot 重新计算。

开发者诊断默认折叠，保留：

- raw path。
- result index raw object。
- schema version。
- internal semantic boundary。
- preview rows 和 column mapping raw payload。

## 4. 未完成内容

以下内容不属于 B3，留给后续阶段：

- 真实 DEG 执行器接入。
- DEG 正式结果详情页。
- 火山图、热图、富集、GSEA 等派生结果。
- 大文件分页、排序、过滤和列映射交互编辑。
- 多 imported DEG 结果的逐项选择操作。
- 报告模板更细粒度用户化。
- Integration / MainLine 合并验证。

## 5. 测试结果

已运行：

- `python3 -m app.main --smoke-test`：通过。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`：219 passed。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：146 passed。
- `git diff --check`：通过。

新增或更新测试覆盖：

- imported DEG 浏览服务可识别 gene、logFC、p value、FDR 等主要列。
- imported DEG 可计算预览行中的上调 / 下调 / 不显著数量。
- imported DEG 可标记为报告候选，但仍为 imported result。
- imported DEG 不被 B2 preflight 当作重新计算输入。
- 不生成 fake DEG result、volcano、enrichment。
- UI 入口文案为“查看已导入差异分析结果”和“导入结果浏览”，不使用“运行 DEG”或“生成 DEG 结果”。
- 主界面隐藏 raw path / manifest / schema version 等技术字段。
- 开发者诊断保留必要技术信息。
- 工作区导航可进入 imported DEG 浏览页。

## 6. 风险和需要人工确认事项

- 当前上调 / 下调 / 不显著数量仅基于预览行和识别到的列计算，用于导入结果浏览确认，不代表 BioMedPilot 正式统计输出。
- 列映射是启发式识别；复杂列名、多个 contrast、宽表或多组结果仍需后续列映射 UI。
- “标记为报告候选”只是将 imported result 写入现有 result index，保留导入语义，不代表正式计算完成。
- imported DEG 详情页当前默认展示第一个导入结果；多结果选择和逐项操作留给后续阶段。

## 7. 其他 worktree

本阶段仅修改 Bioinformatics 独立 worktree 内文件。

未触碰、未提交、未回滚：

- MainLine
- Meta
- LabTools
- Integration
- Vocabulary
- UIShell
- AI
- ReleaseBuild
