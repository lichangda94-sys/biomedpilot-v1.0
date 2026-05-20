# Bioinformatics Stage B1D：分析任务中心用户化记录

日期：2026-05-13

工作区：`/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

说明：任务要求读取的 Bioinformatics 本地 `docs/handoff/Global_Development_Manual.md` 与 `docs/architecture/*20260513.md` 当前仍不存在；本阶段延续 B1/B1A/B1B/B1C 的处理方式，读取并遵循 `01_ProjectControl/Global_Development_Manual.md`、`MainLine/docs/architecture/BioMedPilot_v1_overall_architecture_20260513.md`、`MainLine/docs/architecture/BioMedPilot_v1_code_structure_20260513.md` 作为当前权威副本。未发现本任务与总开发手册冲突。

## 1. 改造前主要问题

分析任务中心原主界面偏 capability matrix / task record 调试视图：

- 主界面直接出现 `task type` 输入。
- 任务表直接显示 `available_inputs`、`missing_inputs`、`warning`、默认参数 JSON 和 `preview_status`。
- “运行 GEO 差异分析”作为主按钮出现，容易被误解为正式 DEG 执行入口。
- task record 和结果索引的原始 JSON 直接处于主页面可见区域。

这些信息适合开发者排查，不适合作为用户从“数据标准化”进入后的任务选择页面。

## 2. 当前主界面展示的用户任务状态

分析任务中心主界面现在按用户路径组织：

1. 当前分析条件
   - 核心输入是否满足差异表达分析。
   - 结果状态：暂无结果、已有配置草稿、已有导入结果、已有测试级结果。
   - 下一步建议：返回标准化、确认分组、创建配置草稿或进入结果浏览。

2. 主操作
   - `刷新任务状态`
   - `确认分组与比较设计`
   - `创建差异分析配置草稿`
   - `继续：结果浏览`

3. 用户化任务表
   - 表头为“分析任务 / 当前状态 / 需要输入 / 当前缺少 / 下一步”。
   - 覆盖差异表达分析、富集分析、GSEA、相关性分析、生存分析、临床变量关联、TCGA + GTEx 联合分析、结果浏览与报告。
   - 主表使用中文输入名称，不直接显示 capability matrix 原始 key。

4. 开发者诊断
   - 原始 task center、task records、result index、task type 输入和测试级 GEO 差异结果生成入口均移入折叠区。

## 3. DEG / imported DEG / dry-run / testing-level 区分

差异表达分析现在按以下方式区分：

- 可配置 DEG：当 capability matrix 判断已具备表达矩阵、样本信息和比较分组时，状态显示“可配置”，下一步为创建差异分析配置草稿。
- 缺分组：状态显示“需要确认分组”，下一步提示“请先确认分组与比较设计”。
- imported DEG：如果识别到导入的差异结果表，状态显示“已有导入结果”，下一步明确说明“当前为导入表格中的已有差异分析结果，不是本软件重新计算”。
- 配置草稿 / dry-run：`create_analysis_task` 仍只创建 task record，UI 状态显示“配置草稿”，并明确“未执行真实分析”。
- testing-level：既有 GEO 差异结果生成入口保留在开发者诊断区，状态和 result index 均标记为 testing-level，不再在主界面写成正式 DEG。

本阶段未新增真实 DEG 执行器，未生成假 DEG、假火山图、假富集结果，也未把 dry-run 或 imported result 写成真实计算结果。

## 4. 移入开发者诊断的技术字段

以下内容不再出现在用户主表，保留在“开发者诊断”折叠区：

- capability matrix raw key
- task type 原始枚举
- task record JSON
- task run / task record path
- result index raw JSON
- default parameters JSON
- preview status 原始字段
- available_inputs / missing_inputs 原始 key
- internal task id
- raw source/result path

开发者仍可通过诊断区创建指定任务记录或触发既有测试级 GEO 差异结果生成入口，用于内部验证。

## 5. 当前仍未完全用户化的内容

- 还没有独立的 DEG 配置页面；“创建差异分析配置草稿”当前仍落到 task record。
- 富集分析、GSEA、相关性、生存分析等仍是任务可执行性展示，未新增真实执行能力。
- 结果浏览页和项目报告页仍有技术字段暴露，已留给后续阶段。
- `deg_task_plan.py` 与 `analysis_task_runs.py` 在当前工作区不存在；实际任务中心能力集中在 `project_analysis_tasks.py`，结果索引集中在 `results/project_results.py`。

## 6. 留给后续结果页和项目报告页优化

- 结果浏览页应继续区分 imported result、testing-level、dry-run、real computed result。
- 项目报告页应避免把测试级或导入结果写成正式结论。
- 后续可新增独立 DEG 配置页，但必须先定义输入校验、结果语义、测试边界和人工确认点。
- 富集、GSEA、相关性和生存分析需要独立阶段治理，不能用假结果填充闭环。

## 7. 测试结果

已执行：

- `python3 -m app.main --smoke-test`：通过。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`：215 passed。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：141 passed。

新增/更新测试：

- 分析任务中心主界面用户化表头、任务文案和流程按钮。
- 主表不直接暴露 `differential_expression`、`analysis_capability_matrix`、manifest、task id 或 raw path。
- 开发者诊断区默认隐藏，并保留原始 task center 技术信息。
- imported DEG 不被呈现为本软件重新计算结果。
- 测试级 GEO 差异结果写入 result index 时标记 `testing-level`。
- 标准化页继续按钮仍能进入分析任务中心。

## 8. 风险和人工确认事项

- 本阶段未修改 manifest schema，未重写 analysis service 层，未删除 capability matrix、task plan、task record 或 result index 能力。
- 未修改 shared vocabulary、AI Gateway、Meta、Vocabulary、LabTools、AI、UIShell、Integration、ReleaseBuild 等其他 worktree。
- 既有测试级 GEO 差异结果生成入口仍存在，但已从主界面降级到开发者诊断区，并在 UI/result index 中标记 testing-level；是否保留该入口的长期产品形态需后续人工确认。
- 需要项目层后续确认是否将总开发手册和架构文档同步到 Bioinformatics worktree 指定路径，或正式改为引用 `01_ProjectControl` / `MainLine` 权威副本。
