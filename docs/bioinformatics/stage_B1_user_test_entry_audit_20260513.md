# Bioinformatics Stage B1 用户可测试入口收敛审计

日期：2026-05-13

范围：`/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

## 0. 前置读取与边界

本阶段已读取：

- `/Users/changdali/Developer/biomedpilot v1.0/README_总说明.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/CODEX.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/handoff/MainLine_current_baseline_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/迁移报告_20260513.md`

用户指定的以下 Bioinformatics 内路径当前不存在：

- `docs/handoff/Global_Development_Manual.md`
- `docs/architecture/BioMedPilot_v1_overall_architecture_20260513.md`
- `docs/architecture/BioMedPilot_v1_code_structure_20260513.md`

已改读同一 v1.0 根目录内存在的权威副本作为约束：

- `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/architecture/BioMedPilot_v1_overall_architecture_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/architecture/BioMedPilot_v1_code_structure_20260513.md`

本阶段未发现与总开发手册冲突的任务要求。执行边界保持为 Bioinformatics worktree 内部；不修改 Meta、Vocabulary、LabTools、AI、UIShell、Integration、ReleaseBuild 或 MainLine。

## 1. 当前页面与流程现状

当前 `BioinformaticsWorkspaceWidget` 维护一个 `QStackedWidget` 页面栈，实际用户入口如下：

1. 项目首页：创建或打开生信项目。
2. 数据导入与检索：本地数据导入、GSE 编号检索、中文研究主题检索入口、待处理数据集。
3. 中文研究主题检索：独立页面，按 GEO/GSE、TCGA/GDC、GTEx 分页展示 query draft、候选和已选来源。
4. 数据识别：勾选待识别数据，运行识别并显示文件类型、分组预览和技术详情折叠区。
5. Ready 检查：数据准备检查，显示已识别输入、缺失输入、待办项和能力矩阵。
6. 标准化数据：生成标准化资产和 analysis-ready manifest。
7. 生信工作流总控：运行完整流程或单步流程，展示步骤状态。
8. 分析任务中心：展示任务模板、缺失输入、默认参数、创建任务，并保留 GEO 差异分析运行入口。
9. 结果浏览：读取结果索引，显示结果表。
10. 项目报告：基于结果索引生成 Markdown 项目报告。
11. 设置与本地 AI：独立设置页，不在主线自动进入。

从打开 Bioinformatics 到完成一次数据选择，当前实际路径有三类：

- 本地数据路径：项目首页 -> 数据导入与检索 -> 本地数据导入 -> 待处理数据集 -> 下一步：数据识别。
- GSE 编号路径：项目首页 -> 数据导入与检索 -> GSE 编号检索 -> GEO 数据集详情 -> 添加到项目 -> 待处理数据集；若仅 plan_only，不能进入识别，需下载元数据或导入实际文件。
- 中文主题路径：项目首页 -> 数据导入与检索 -> 中文研究主题检索 -> 生成草稿 -> 按 GEO/GSE、TCGA/GDC、GTEx 选择候选或创建下载清单 -> 回到同一待处理/已选来源体系；只有具备实际文件或已下载元数据的条目能进入识别。

## 2. 7 步主线判断

CODEX.md 定义主流程为：

项目首页 -> 数据选择 -> 数据识别 -> 数据标准化 -> 分析任务中心 -> 结果浏览 -> 项目报告

当前已经具备这些页面和主要状态门禁，但还没有完全形成用户感知上的 7 步直线：

- 项目首页：可直接内部测试。
- 数据选择：基本可测试，三个入口已清楚分层，待处理数据集成为汇合点。
- 数据识别：可直接内部测试，支持勾选来源、识别、分组预览。
- 数据标准化：可测试，但主界面仍暴露文件路径、source_file、materialize 策略、validation 状态、analysis-ready 等技术字段。
- 分析任务中心：可测试，但仍偏开发者视图，包含 task type 输入、默认参数 JSON、preview 字段，并存在真实 GEO 差异分析运行按钮。
- 结果浏览：可测试，但结果路径和参数 JSON 入口偏技术化。
- 项目报告：可测试，但报告 manifest 直接显示在主界面，DOCX/HTML 仍为 testing placeholder。

额外存在的 Ready 检查和生信工作流总控页在工程上有用，但对普通用户来说会打断 7 步主线。建议后续把它们吸收到“数据标准化”和“分析任务中心”的用户路径中，技术细节进入开发者诊断折叠区。

## 3. 数据入口分层

当前数据选择页已经只保留三个一级入口：

- 本地数据导入：表达矩阵、GEO Series Matrix、样本信息、临床表、注释文件。
- GSE 编号检索：已知 GEO accession 时直接检索数据集详情并添加到项目。
- 中文研究主题检索：进入独立页面，生成英文 query draft 和 GEO/TCGA/GTEx 分源候选。

本阶段小修后，中文入口命名统一为“中文研究主题检索”，按钮改为“进入中文主题检索”。这使入口名称与当前阶段描述一致。

## 4. 中文研究主题检索独立性

中文研究主题检索已经是独立页面，具备：

- 中文主题输入。
- GEO/GSE query draft。
- TCGA/GDC 项目草稿。
- GTEx 组织草稿。
- 用户确认草稿。
- GEO/GSE、TCGA/GDC、GTEx 三个分区 tab。
- GEO 数据集详情面板。
- GEO 已选数据集列表。
- TCGA/GDC 和 GTEx 推荐卡片。

不足：

- 页面使用 `max_width=1080`，结果区域可测试但仍偏紧凑；GEO 表格、详情面板和已选列表叠在同一个 tab 内，长结果时需要大量滚动。
- TCGA/GDC 和 GTEx 候选展示更接近“推荐卡片”，不是与 GEO 同等级的大结果区。
- “高级信息 / 映射日志”已经折叠，但仍在主页面占一段区域，后续可改为开发者诊断入口。

## 5. GEO / TCGA / GTEx 区分

当前区分较清楚：

- 数据模型中 `source` 使用 `geo`、`tcga_gdc`、`gtex`。
- UI tab 分为 `GEO/GSE`、`TCGA/GDC`、`GTEx`。
- GEO 候选使用 GSE 编号表格和 GEO 数据集详情。
- TCGA/GDC 使用项目代码、癌种/项目名称、样本类型、数据类型。
- GTEx 使用组织、样本数、表达类型，并提示 GTEx 是正常组织参考，不是肿瘤样本数据库。

仍需改进：

- 数据选择页的统一待处理数据集表中，TCGA/GDC 和 GTEx 当前主要表现为“中文检索”来源，用户需要进入详情或原 tab 才能看清来源差异。
- TCGA/GDC 和 GTEx 的“创建下载任务/下载清单”需要更明确标注为清单或准备动作，不应让用户误以为已经下载表达矩阵。

## 6. GSE 与中文主题检索的下载列表汇合

GSE 编号检索和中文主题检索中的 GEO 候选可以汇入同一类 GEO accession acquisition records，并在待处理数据集或已选 GEO 数据集中显示。

当前行为：

- GSE 编号检索保存 `geo_accession`，来源为 GSE 编号检索。
- 中文主题检索保存 `geo_accession`、`tcga_project`、`gtex_tissue`，来源为中文研究主题。
- `_current_project_dataset_entries` 会把本地、GEO、TCGA、GTEx 记录规范成统一的 `DatasetListEntry`。
- GEO 详情面板可从 GSE 编号入口和中文主题入口复用。

不足：

- 数据选择页和中文主题页各自有列表视图，概念上已经汇合，视觉上仍像两个列表。
- 非 GEO 的 TCGA/GDC、GTEx 目前是“创建下载清单”级别，尚未与“实际表达矩阵已下载”形成同等用户状态。

## 7. 数据集详情页判断能力

GEO 数据集详情页已经可以帮助用户判断：

- 基础信息。
- 英文原始信息。
- 中文翻译与提炼草稿。
- 样本结构与下载建议。
- 候选比较组。
- 数据资产状态。
- 添加到项目、忽略、从项目列表移除、下载补充文件。

不足：

- “数据资产状态”仍使用 asset / manifest 语义的间接结果，虽然文本已做用户化。
- “中文翻译与提炼”是 AI 草稿，已标记需人工确认，符合边界；后续应继续避免保存 raw prompt / raw response。
- TCGA/GDC 和 GTEx 详情目前主要是文本说明，不如 GEO 详情完整。

## 8. 标准化页技术字段暴露

标准化页当前仍暴露过多开发者字段：

- `asset_type`
- `file_path`
- `source_file`
- `materialize_strategy`
- `validation_status`
- `warning`
- `analysis-ready`
- hidden manifest 中的 `analysis-ready manifest`

这些字段不应直接进入普通用户主界面。用户主界面应优先显示：

- 是否已发现表达矩阵。
- 是否已发现样本信息。
- 是否已确认分组设计。
- 默认使用哪些资产。
- 哪些资产可进入分析任务中心。
- 下一步操作。

技术字段应进入“开发者诊断 / 技术详情”折叠区。

## 9. 可直接内部测试的页面

当前可直接内部测试：

- 项目首页。
- 数据导入与检索。
- 中文研究主题检索。
- 数据识别。
- Ready 检查。
- 标准化数据。
- 分析任务中心的任务模板/任务创建 preflight。
- 结果浏览。
- 项目报告 Markdown。

需要测试时保持 Developer Preview / testing-level 标记，不把 dry-run、preflight 或 imported result 描述为正式计算结果。

## 10. 仍偏开发者调试视图的页面

偏开发者调试视图：

- 生信工作流总控：stage key 输入、运行单个步骤、workflow report、输入/输出路径/warning 表格。
- 标准化数据：主表直接展示路径和 registry 字段。
- 分析任务中心：task type 输入、默认参数 JSON、preview 字段、真实 GEO 差异分析按钮。
- 结果浏览：打开参数 JSON、结果路径主表字段。
- 项目报告：manifest 主界面展示、DOCX/HTML placeholder。
- 设置与本地 AI：本地 AI 和 legacy GEO 环境检查不应混入普通用户数据选择主线。

## 11. 当前最小可测试闭环

建议当前 B1 最小可测试闭环定义为：

项目首页 -> 创建项目 -> 数据导入与检索 -> 本地表达矩阵导入 -> 待处理数据集勾选 -> 数据识别 -> Ready 检查 -> 标准化数据 -> 分析任务中心查看可运行/不可运行任务 -> 结果浏览空态 -> 项目报告空态/阻断提示。

补充可测试分支：

- GSE 编号检索 -> 查看 GEO 数据集详情 -> 添加到待处理数据集 -> 验证 plan_only 阻断进入识别。
- 中文研究主题检索 -> 生成草稿 -> 查看 GEO/TCGA/GTEx 分区候选 -> 选择候选或创建下载清单 -> 验证未下载数据时不能误入识别或结果。

不建议把真实 DEG、火山图、富集结果纳入 B1 验收闭环。

## 12. 当前阻塞点

阻塞点：

- 用户指定的 Global_Development_Manual 和两份架构文档不在 Bioinformatics worktree 指定路径下，后续应决定是否将权威副本同步到模块 worktree 或改为引用 `01_ProjectControl` / MainLine。
- 7 步用户主线中间插入 Ready 检查和生信工作流总控页，普通测试者会感知为 9 步以上。
- 标准化页和分析任务中心仍有较多技术字段。
- TCGA/GDC、GTEx 目前更像候选/清单准备，不是完整下载到识别闭环。
- 结果和报告页依赖已有结果索引；没有结果时只能测试空态和阻断提示。

## 13. 不应进入用户主界面的技术字段

以下字段应从普通用户主界面移出，保留到开发者诊断区、日志、manifest 或 handoff：

- `project_manifest.json`
- `project_config.json`
- `schema_version`
- `manifest_path`
- `registry_path`
- `analysis_ready_manifest`
- `asset_id`
- `asset_type`
- `source_file`
- `file_path`
- `raw_data_path`
- `route_path`
- `materialize_strategy`
- `validation_status`
- `recognition_report`
- `analysis_capability_matrix`
- `workflow_state`
- `stage key`
- `download_request_path`
- `download_receipt_path`
- `asset_manifest_path`
- raw path 绝对路径
- raw prompt / raw response

## 14. 本阶段小修

本阶段做了小范围、低风险 UI 文案修复：

- 将数据选择页入口“中文研究问题检索”统一为“中文研究主题检索”。
- 将中文检索独立页标题统一为“中文研究主题检索”。
- 将入口按钮“进入检索界面”改为“进入中文主题检索”。
- 同步更新对应 UI 测试断言。

未做大规模 UI 重构，未新增外部 API 调用，未新增真实 DEG 执行器，未修改 manifest schema，未修改 shared vocabulary 或 AI Gateway 逻辑，未改动其他 worktree。

## 15. 后续任务拆分建议

### B1A：数据选择页收敛

目标：把数据选择页做成用户进入识别前的唯一收敛点。

建议范围：

- 本地数据导入。
- GSE 编号检索。
- 中文研究主题检索入口。
- 下载列表入口。
- 下一步按钮。
- 统一待处理数据集表，让本地、GSE、中文主题来源在同一列表中清楚显示。
- 明确 plan_only、待下载、已下载、可进入识别四类状态。

不做：

- 不执行真实 DEG。
- 不新增 PubMed。
- 不改 manifest schema。

### B1B：中文研究主题检索独立页

目标：把中文主题检索变成一个足够大的、用户可编辑和确认的候选选择页。

建议范围：

- 中文问题输入。
- 英文 query draft。
- GEO / TCGA / GTEx query draft。
- 用户编辑与确认。
- 分区结果展示。
- 数据集详情。
- 保存 / 忽略 / 加入下载列表。
- GEO 结果区扩容；TCGA/GDC 和 GTEx 与 GEO 结果区保持同等层级。
- 高级映射日志改为开发者诊断折叠区。

不做：

- 不绕过 AI Gateway。
- 不保存 raw prompt / raw response。
- 不把 PubMed 或文献检索混入 Bioinformatics。

### B1C：标准化页用户化

目标：把标准化页从 registry/manifest 查看器改成用户理解的“分析输入准备”页。

建议范围：

- 隐藏 asset id、raw path、manifest、schema、registry、materialize_strategy 等技术字段。
- 强调表达矩阵、样本信息、分组设计、默认资产、下一步。
- 给每个分析任务显示“可运行 / 还缺什么 / 建议补充”。
- 开发者诊断折叠区保留技术细节。
- 将 Ready 检查与标准化页关系收敛，减少用户路径中的额外步骤。

不做：

- 不改变项目 manifest schema。
- 不生成假 DEG、假火山图、假富集结果。
- 不把 dry-run/preflight 标成真实结果。
