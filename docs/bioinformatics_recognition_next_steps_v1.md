# Bioinformatics Recognition Next Steps v1

## 功能目标

Stage 2.8 在数据识别完成后提供统一的“下一步建议”和流程状态提示。目标是让用户知道当前识别 run 是否会被后续标准化使用、哪些任务可以直接进入、哪些任务需要确认、哪些路径不建议使用。

该阶段只收敛 view model 和 UI 文案，不新增识别算法、DEG 算法、富集算法或绘图引擎。

## Next Step 判定规则

下一步建议由 `app/bioinformatics/recognition_next_steps.py` 生成。输入包括：

- recognition run metadata
- recognition report files
- `content_blocks`
- `recognized_data/current.json` 指向状态
- standardized assets registry 状态
- species / species_group
- imported DEG availability
- group config availability

输出包括：

- `primary_action`
- `secondary_actions`
- `direct_available`
- `needs_confirmation`
- `not_recommended`
- `current_status`

## Current / History / Legacy 状态

状态文案：

- 当前使用中：该识别记录将作为数据标准化的输入。
- 历史记录：该识别记录当前不会被标准化模块使用。
- 旧版识别记录：由旧版项目结构导入。
- 本次识别结果，尚未设为当前输入：仅用于只读详情或临时报告视图。
- 当前识别输入已失效：`current.json` 指向的 run 已不存在。

查看详情本身是只读操作，不会修改 `current.json`。只有点击“设为当前标准化输入”才会更新当前 run。

## 数据资产对应推荐路径

| 数据资产 | 可直接进行 | 需要确认 |
| --- | --- | --- |
| count matrix | 数据标准化、count 矩阵标准化 | 重新差异表达分析前确认分组；样本 QC 前确认分组和批次 |
| FPKM / TPM matrix | 表达热图、样本相关性、候选基因表达查看 | 不建议作为 DESeq2/edgeR 式重新 DEG 输入 |
| imported DEG result table | DEG 浏览、DEG 筛选、火山图输入、富集分析输入 | 富集前选择阈值和 gene list |
| gene annotation | gene annotation 浏览、protein-coding 筛选、报告注释 | 需要确认 gene ID 转换策略时再补配置 |
| unknown table | 返回数据导入、查看详情、导出报告 | 重新检查文件格式或手动配置 |

## Mouse / Human 推荐差异

Mouse 数据：

- 显示“小鼠数据，不推荐人类队列整合”。
- 可推荐动物模型分析、机制探索、方法验证。
- 不推荐默认接入 TCGA/GTEx 人类对照。

Human 数据：

- 不显示 mouse 限制文案。
- 是否进入 TCGA/GTEx 仍由后续任务中心根据资产和项目配置判断。

## UI 文案规范

主界面使用短文案：

- 当前使用中
- 历史记录
- 继续数据标准化
- 设为当前标准化输入
- 进入分析任务中心
- 查看已有 DEG 结果
- 需要确认分组
- 小鼠数据，不推荐人类队列整合
- 未选择当前识别结果

主界面避免显示：

- `current.json`
- `content_blocks`
- `semantic_type`
- `standardized_assets_registry`
- `ready_with_group_confirmation`

这些字段仍可放入技术详情或 JSON 附录。

## 页面收敛

数据识别页：

- 本次识别结果下方显示“下一步建议”。
- 历史详情也复用同一套 next-step view model。
- 非 current 历史 run 的主按钮是“设为当前标准化输入”。

标准化页：

- 顶部显示当前标准化输入来源。
- 没有 `current.json` 时提示用户先完成识别或选择历史 run。
- `current.json` 指向失效 run 时提示重新识别或选择历史记录。

分析任务中心：

- 任务表增加“来源与状态”列。
- 用户能看到任务来源于 count matrix、FPKM matrix、已有 DEG 或 gene annotation。

结果浏览：

- imported DEG 结果顶部显示“当前结果来源：导入表格中的已有差异分析结果”。
- 显示 comparison 数量、物种和可用路径。
- 默认选择第一个完整 comparison。

## 当前限制

- 下一步建议只生成导航和文案，不执行分析。
- “查看已有 DEG 结果”依赖标准化资产中已有 `deg_result_table`。
- 火山图和真实富集分析仍由后续阶段实现。
- 对未持久化的临时识别报告，仅支持详情和导出，不保证可设为 current run。

## 后续计划

- 将 next-step action 与任务中心 capability 详情做双向跳转。
- 在 DEG 结果浏览中记录来自识别页的默认 comparison 选择。
- 在报告中加入 next-step action 审计记录。
