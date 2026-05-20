# Bioinformatics Stage B2 DEG 配置页与 preflight 输入校验设计

日期：2026-05-13

## 1. DEG 配置页结构

本阶段新增独立页面“DEG 配置与 preflight 输入校验”，并从“分析任务中心”的主按钮“进入差异分析配置”进入。

页面主界面包含：

- 当前分析输入：表达矩阵、count matrix、normalized matrix、样本信息、imported DEG 排除提示、样本列数量。
- 当前比较设计：case/control 或用户确认比较、每组样本数、样本名匹配状态。
- DEG 配置草稿：method、log2FC、p value、FDR；明确 DESeq2 / edgeR / limma 仍为待接入状态。
- preflight 检查表：检查项、状态、用户可理解说明。
- 下一步建议：返回标准化、确认分组、生成 preflight、回到分析任务中心。
- 开发者诊断：保留 manifest path、asset/raw path、raw JSON、internal check id 等技术细节。

主界面文案明确：

- “仅配置 / 仅校验 / 未运行真实差异分析”
- “preflight passed 不等于 real computed result”
- “输入校验记录，不是 DEG 结果，也不会进入正式结果页”

## 2. preflight 已完成检查项

新增 `app/bioinformatics/deg_task_plan.py`，只负责输入校验和 preflight manifest 物化，不执行 DEG。

当前已检查：

- count matrix 或可用表达矩阵是否存在。
- 表达矩阵样本列是否可识别。
- sample metadata 是否存在，或能否由已确认分组构建。
- group design 是否已确认。
- comparison design 是否合法。
- case/control 是否非空且不同。
- case/control 至少各有 1 个样本；少于 2 个样本给出 warning。
- 样本名是否在表达矩阵和分组中匹配。
- 表达矩阵预览是否明显为数值矩阵。
- imported DEG 是否被误用为重新计算输入。

preflight status 当前使用：

- `passed`：没有 blocker 和 warning。
- `warning`：无 blocker，但有人工确认风险。
- `blocked`：缺少关键输入或输入不合法。
- `draft`：页面尚未生成 preflight 时的 UI 状态。

## 3. preflight 未完成检查项

本阶段没有做真实执行器级 preflight，以下内容留给真实 DEG 执行器接入前审计：

- DESeq2 / edgeR / limma 对输入矩阵类型的严格方法匹配。
- batch / covariate / paired design 等复杂设计合法性。
- count matrix 是否满足整数计数、低表达过滤、库大小等正式统计要求。
- 多比较设计批量运行规则。
- gene id 注释版本、重复 gene id 处理、平台探针映射策略。
- 大矩阵性能、内存和临时文件边界。
- R / Bioconductor 环境与版本锁定。

## 4. preflight 产物和边界

允许产物：

- `analysis/deg/preflight/deg_preflight_manifest.json`

该文件记录：

- 输入摘要。
- 比较设计摘要。
- checks、blockers、warnings。
- 配置草稿。
- `semantic_boundary = input_preflight_only_not_deg_result`
- `execution = not_run`
- `not_a_result = true`

禁止产物未生成：

- DEG result table。
- volcano plot。
- heatmap。
- enrichment result。
- formal report conclusion。

preflight manifest 不写入 result index，不作为 completed analysis，不进入正式结果页。

## 5. 为什么本阶段不执行真实 DEG

B2 的目标是建立用户可理解的配置页和运行前输入边界。真实 DEG 需要额外审计统计方法、输入矩阵类型、分组设计、样本匹配、R/Bioconductor 环境、结果语义和报告边界。本阶段如果接入真实执行器，会超过用户入口收敛和 preflight 设计范围，也会增加把测试记录误写成正式科研结果的风险。

## 6. 如何避免 fake result

本阶段采取以下边界：

- 不生成 DEG 表。
- 不生成火山图、热图或富集结果。
- 不把 `passed` 写成真实完成。
- 不写 result index。
- 不把 imported DEG 当作重新计算输入。
- UI 主界面持续显示“仅配置 / 仅校验 / 未运行真实差异分析”。

## 7. 与 B1 分析任务中心、结果页、报告页的关系

- B1D 分析任务中心现在将差异表达入口导向 B2 独立配置页。
- B1E 结果浏览页和报告页仍只处理 imported result、testing-level、dry-run、configured-not-run、real computed result 的展示语义。
- B2 preflight manifest 不进入结果浏览页作为分析结果。
- 后续真实执行器接入前，需要再定义 task run 与 result index 的正式写入规则。

## 8. 后续真实执行器接入前审计

建议后续阶段先做：

- DEG executor preflight v2：方法级输入规则和 R 环境审计。
- 独立 DEG task run schema 审计：区分 preflight、queued、running、failed、completed。
- 结果语义审计：只有真实执行器完成后才能写入 `real computed result`。
- imported DEG 专门浏览：继续防止导入结果被误认成本软件计算结果。
- Integration 合并验证：进入 MainLine / Integration 前统一检查页面导航、result index、report manifest 边界。

## 9. 测试结果

本阶段已运行：

- `python3 -m app.main --smoke-test`：通过。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`：217 passed。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：145 passed。

新增或更新测试覆盖：

- DEG 配置页可初始化。
- 缺分组时显示 preflight blocker。
- imported DEG 不被当作重新计算输入。
- preflight passed / blocked 语义不等于真实分析。
- preflight 不生成 DEG 结果文件。
- 主界面不直接暴露 raw path / manifest 等典型技术字段。
- 开发者诊断保留技术信息。
- 工作区导航可进入独立 DEG 配置页。

## 10. 其他 worktree 状态

本阶段开始前只检查并记录其他 worktree 状态，未修改、未提交、未回滚其他 worktree。

- Meta：干净。
- MainLine：干净。
- Integration：干净。
- Vocabulary：干净。
- UIShell：干净。
- AI：干净。
- ReleaseBuild：干净。
- LabTools：任务说明中已知存在未提交改动，非本阶段产生；本任务未触碰、未提交、未回滚。最终复查时 `dev/labtools` 显示 clean，若这些改动由其他流程清理或提交，不属于本阶段操作。

## 11. 风险和需要人工确认事项

- 当前 preflight 是轻量输入校验，不代表统计方法适配完成。
- 样本数最低要求当前按“各组至少 1 个样本为 blocker 边界、少于 2 个样本为 warning”处理；真实 DEG 前需由统计方案确认正式阈值。
- 对 CSV/TSV/GZ 矩阵做轻量预览，不做完整矩阵扫描。
- imported DEG 识别依赖现有识别规则，后续 imported DEG 专门浏览阶段仍需继续强化。
- 真实 DEG 执行器、结果页正式写入、报告结论生成均未接入。
