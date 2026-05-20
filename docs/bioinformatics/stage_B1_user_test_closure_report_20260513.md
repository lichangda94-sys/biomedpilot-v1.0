# Bioinformatics Stage B1F：用户可测试闭环总验收与阶段报告

日期：2026-05-13

工作区：`/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

## 0. 前置读取与边界

已读取：

- `/Users/changdali/Developer/biomedpilot v1.0/README_总说明.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/CODEX.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/docs/bioinformatics/stage_B1_user_test_entry_audit_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/docs/bioinformatics/stage_B1A_data_selection_convergence_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/docs/bioinformatics/stage_B1B_chinese_topic_search_page_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/docs/bioinformatics/stage_B1C_standardization_page_userization_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/docs/bioinformatics/stage_B1D_analysis_task_center_userization_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/docs/bioinformatics/stage_B1E_results_report_userization_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/迁移报告_20260513.md`

用户指定的以下 Bioinformatics 本地路径仍不存在：

- `docs/handoff/Global_Development_Manual.md`
- `docs/architecture/BioMedPilot_v1_overall_architecture_20260513.md`
- `docs/architecture/BioMedPilot_v1_code_structure_20260513.md`

本阶段按 B1-B1E 既有记录继续读取并遵循：

- `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/architecture/BioMedPilot_v1_overall_architecture_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/architecture/BioMedPilot_v1_code_structure_20260513.md`

未发现本任务与总开发手册冲突。本阶段为验收与报告阶段，未新增功能，未修改其他 worktree，未打包 internal beta，未执行 git push。

## 1. B1 总结论

Bioinformatics 当前已经具备模块 worktree 内部用户测试的基础闭环：

项目首页 -> 数据选择 -> 本地数据导入 / GSE 编号检索 / 中文研究主题检索 -> 数据识别 -> 数据标准化 -> 分析任务中心 -> 结果浏览 -> 项目报告草稿。

该闭环适合内部用户测试“入口是否清楚、状态是否可理解、哪些步骤阻断、哪些结果语义不可误读”。它不代表已经进入 Integration 或 ReleaseBuild，也不代表具备正式 DEG、火山图、富集或投稿级报告能力。

验收判断：

- 当前用户能清楚理解每一步的作用：基本可以。数据选择、中文主题检索、标准化、分析任务、结果和报告页已经完成主要用户化；Ready 检查和生信工作流总控仍偏工程视图。
- 当前用户能从数据选择进入识别、标准化、分析任务、结果、报告：可以。标准化页已直接进入分析任务中心，结果和报告页有空态与语义提示。
- 已达到内部测试可用的页面：项目首页、数据选择、本地数据导入、GSE 编号检索、中文研究主题检索、数据识别、数据标准化、分析任务中心、结果浏览、项目报告草稿。
- 仍是 Developer Preview / testing-level 的页面或能力：中文 query draft、TCGA/GTEx 下载清单、标准化资产注册、分析任务配置草稿、测试级 GEO 差异结果、结果浏览、报告草稿、导出 DOCX/HTML/PDF。
- 仍依赖开发者诊断的内容：recognition report、standardized assets registry、readiness/capability matrix、task records、result index、report manifest、raw paths、schema version、warnings。
- 明显技术字段暴露：主线页面已大幅收敛，普通主界面不应再直接展示大量 manifest、schema、raw path、asset id、task id；但开发者诊断折叠区仍保留这些内容。
- imported result / testing-level / dry-run 误写成真实结果的风险：主界面已加语义区分，风险降低；后续 report builder 模板仍需继续用户化，避免 Markdown 原文引入技术语义混淆。
- PubMed 或 Meta 内容混入 Bioinformatics 的风险：当前 B1 主线未引入 PubMed、PICO、Meta 文献检索入口。
- 真实 DEG 与配置草稿混淆风险：当前 UI 已明确“配置草稿 / 未执行真实分析”和“测试级 / 开发者预览”，但后续若新增 DEG 配置页或 executor，必须重新做边界审计。

## 2. 各阶段完成内容

### B1：入口审计

- 审计项目首页、数据选择、中文主题检索、数据识别、标准化、分析任务中心、结果浏览、项目报告。
- 明确主线阻塞点：标准化页、分析任务中心、结果和报告页偏开发者调试视图。
- 定义 B1A/B1B/B1C 后续拆分。

### B1A：数据选择页收敛

- 数据选择页组织为三类入口：本地数据导入、GSE 编号检索、中文研究主题检索。
- 增加当前数据选择状态摘要：已保存数据来源、下载列表/待处理、可进入识别数量、下一步建议。
- 明确中文主题检索入口不是 PubMed 文献检索。

### B1B：中文研究主题检索独立页扩容

- 中文主题页形成工作台结构：中文主题输入、query draft、GEO/TCGA/GTEx 分区结果、候选操作、开发者诊断。
- 明确 query draft 是草稿 / 待确认，默认不联网，不伪装成真实 AI 完成或正式检索策略。
- GEO 候选支持查看详情、保存、忽略、加入下载列表；TCGA/GTEx 保持下载清单级能力，不伪造落地数据。

### B1C：标准化页用户化

- 标准化页主界面改为当前输入数据、分析输入状态、默认资产与下一步、用户化资产表。
- 隐藏 asset type、file path、source file、manifest、schema 等技术字段到开发者诊断。
- 标准化页继续按钮改为进入分析任务中心，工作流总控不再作为用户主线显式下一步。

### B1D：分析任务中心用户化

- 分析任务中心改为“当前分析条件”、用户化任务表和开发者诊断。
- 任务表按差异表达、富集、GSEA、相关性、生存、临床变量关联、TCGA+GTEx、结果浏览与报告展示可配置性、缺失输入和下一步。
- 区分可配置 DEG、缺分组、imported DEG、配置草稿、testing-level 结果。
- 测试级 GEO 差异结果生成入口移入开发者诊断。

### B1E：结果浏览页与项目报告页用户化

- 结果浏览页按结果来源、语义、可打开性、可进入报告和下一步显示。
- 项目报告页改为报告草稿状态、结果语义摘要、报告部分表和用户摘要预览。
- Markdown 原文、result index、report manifest、raw paths、schema version 移入开发者诊断。
- 明确 imported result、testing-level、dry-run、configured-not-run、real computed result 的 UI 语义。

## 3. 当前用户可测试闭环

建议内部用户测试主路径：

1. 项目首页：创建或打开 Bioinformatics 项目。
2. 数据选择：查看本地数据导入、GSE 编号检索、中文研究主题检索三类入口。
3. 本地数据导入：导入表达矩阵、样本信息、临床表或已下载数据。
4. GSE 编号检索：输入 GSE 编号，查看详情并加入项目数据来源体系。
5. 中文研究主题检索：输入中文主题，生成 GEO/TCGA/GTEx query draft，查看候选并保存或加入下载列表。
6. 数据识别：选择可识别数据，查看文件类型、分组线索和下一步。
7. 数据标准化：生成标准化数据，确认表达矩阵、样本信息、分组设计、默认资产和下一步。
8. 分析任务中心：查看哪些分析可配置，哪些缺输入，创建配置草稿但不误解为真实分析。
9. 结果浏览：查看 imported/testing/dry-run/configured-not-run 等结果语义，确认是否可用于报告草稿。
10. 项目报告：生成或查看报告草稿，确认报告内容不写成正式科研结论。

## 4. 当前仍未完成或 testing-level 的内容

- 真实 DEG 执行器未接入。
- 真实火山图未生成。
- 真实富集分析结果未生成。
- 中文主题检索 query draft 默认不联网，在线能力只限既有入口和用户显式操作。
- TCGA / GTEx 真实文件下载仍未完整接入，当前多为候选和下载清单级。
- 标准化仍是资产注册和轻量校验，不等于正式 biological normalization。
- DEG 仍缺独立配置页和强输入校验页。
- imported DEG 尚无专门结果详情页。
- report builder 仍需用户版模板治理。
- 当前结果和报告不能作为正式科研结论、临床结论或投稿级材料。

## 5. 明确禁止误报的能力

当前不得对用户声称：

- 已接入真实 DEG 执行器。
- 已生成真实火山图。
- 已生成真实富集结果。
- 中文主题检索 query draft 是正式联网检索或正式 AI 完成结果。
- TCGA / GTEx 文件已经完整下载并可直接分析。
- dry-run、testing-level、configured-not-run 或 imported result 是本软件真实计算结果。
- 当前报告草稿可作为正式科研结论、临床级、投稿级或 production-ready 输出。

## 6. 当前可进入内部测试的页面

可进入内部测试：

- 项目首页。
- 数据选择页。
- 本地数据导入。
- GSE 编号检索和 GEO 详情。
- 中文研究主题检索。
- 数据识别。
- 数据标准化。
- 分析任务中心。
- 结果浏览。
- 项目报告草稿。

内部测试时应保留 Developer Preview / testing-level 标记，不做正式结论宣传。

## 7. 当前需要开发者诊断保留的内容

继续保留在开发者诊断折叠区、manifest、日志或阶段报告中：

- recognition report。
- acquisition records / download handoff。
- standardized assets registry。
- analysis-ready manifest。
- readiness details / capability matrix。
- task records。
- result index / result manager。
- report manifest。
- raw paths / route paths。
- schema version。
- warnings / raw JSON。

这些内容对排查仍必要，但不应进入普通用户主界面。

## 8. 结果语义规则

- `imported result`：外部导入结果，例如导入表格中的已有差异分析结果；必须说明不是本软件重新计算。
- `testing-level`：开发者预览或内部测试级结果；可用于内部测试和报告草稿，但不得写成正式科研结果。
- `dry-run`：流程记录或预演；未执行真实分析，不能作为结果。
- `configured-not-run`：已配置任务或草稿，但尚未运行；不能作为结果。
- `real computed result`：只有未来真实 executor 明确产出且通过校验后才能使用；当前 B1 闭环不提供此类结果。

## 9. 后续建议阶段

建议后续阶段：

- B2：独立 DEG 配置页与 preflight 输入校验。重点是表达矩阵、样本 ID、分组设计、case/control、缺失值和最小样本数校验。
- B3：imported DEG 专门浏览与用户版结果详情。重点是导入来源、字段识别、可视化预览和是否可进入报告。
- B4：报告模板用户化。重点是从 report builder 层避免 raw path、manifest、schema 进入用户版 Markdown。
- B5：Integration 合并验证。重点是跨 MainLine / Bioinformatics / ReleaseBuild 的入口、测试、结果语义和模块边界验证。
- B6：真实执行器接入前审计。若准备接入 limma / DESeq2 / edgeR 或富集/GSEA executor，必须单独做执行器、输入输出、统计假设、错误处理和安全计划。

## 10. 风险和需要人工确认事项

- Bioinformatics 本地 `docs/handoff` 与 `docs/architecture` 指定副本仍不存在；需要确认是否同步权威副本，或正式记录使用 `01_ProjectControl` / `MainLine` 权威副本。
- B1 闭环可进入模块内部用户测试，但尚未进入 Integration，不能作为 ReleaseBuild 包来源。
- 结果和报告语义已在 UI 层收敛，但 report builder 模板仍需后续治理。
- 真实 DEG、富集、火山图、TCGA/GTEx 完整下载均需独立阶段，不应混入 B1 closure。

## 11. 验收命令结果

已执行：

- `python3 -m app.main --smoke-test`：通过。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`：215 passed。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：143 passed。
- `git diff --check`：通过。
- `git status --short --branch`：Bioinformatics 仅有本阶段新增报告，提交后应恢复干净。

## 12. 其他 worktree 状态

开始前按用户要求仅检查并记录以下 worktree 状态，未修改、清理、提交或回滚：

- Meta：干净。
- LabTools：干净。
- MainLine：干净。
- Integration：干净。
- Vocabulary：干净。
- UIShell：干净。
- AI：干净。
- ReleaseBuild：干净。

提交前再次检查：

- Meta：干净。
- LabTools：存在未提交改动：`pyproject.toml`、`requirements.txt`，以及未跟踪目录 `app/labtools/image_analysis/fluorescence/`。
- MainLine：存在未提交改动：`app/shared/ui/__init__.py`、`app/shared/ui/theme.py`、`tests/ui/test_shared_ui_theme.py`，以及未跟踪文档 `docs/ui/BioMedPilot_UI_Stage_0_8_LabTools_UI_Integration_Template_20260513.md`。
- Integration：干净。
- Vocabulary：干净。
- UIShell：干净。
- AI：干净。
- ReleaseBuild：干净。

LabTools 和 MainLine 的未提交改动不是本阶段产生，本阶段未修改、清理、提交或回滚它们。若后续这些 worktree 仍有未提交改动，应按其各自任务来源处理，不归属于本 B1F 阶段。

## 13. B1F 执行说明

本阶段只创建总验收报告，没有新增功能代码，没有修改 UI 逻辑，没有新增真实分析、外部 API、manifest schema 或跨模块改动。
