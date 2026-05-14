# LabTools Tool Logic Retrospective Audit

日期：2026-05-14

## 1. 审计定位

本文件是 LabTools 当前已开发工具的使用逻辑与结果语义回顾审计。审计目标是暂停新增功能，确认现有工具的用户流程、输出含义、未实现边界和写盘/网络/AI 边界是否彼此一致。

本审计不新增工具、不新增算法、不新增图像处理逻辑、不新增计算公式、不新增 persistence schema、不新增导出格式。

## 2. 审计范围

纳入审计的 LabTools 工具面：

- 实验计算器。
- 本地试剂与配方。
- 外部来源手动草稿。
- 图像定量 manual ROI MVP。
- 实验模板和记录草稿。
- 当前 persistence / export schema 文档。
- 当前 UI 语义回归测试。

明确不审计和不修改：

- Bioinformatics / Meta / ReleaseBuild / MainLine。
- `dist`、desktop app package、release bundle。
- 外部网络、AI Gateway、本地模型、ImageJ/Fiji、OpenCV、scikit-image。

## 3. 总体结论

当前 LabTools 的工具使用逻辑与结果语义整体一致。已实现能力在 UI、服务层、schema 文档和测试中均被描述为本地辅助、草稿、manual-review 或 Developer Preview / testing-level 输出；未实现能力保持 placeholder / `algorithm_not_available`，未发现 fake 结果路径。

当前允许写盘的能力仍集中在用户明确选择路径后的三个方向：

- ROI export package。
- 用户配方草稿 JSON。
- 实验记录草稿 JSON。

这些路径仍保持 schema version、no silent overwrite、取消/失败可见、不自动保存、不联网、不调用 AI 的边界。

## 4. 工具逻辑审计

### 4.1 实验计算器

当前能力：

- 浓度 / 分子量 / 摩尔浓度换算。
- C1V1 稀释。
- 溶液配制。
- 细胞接种。
- qPCR 配液。
- WB / SDS-PAGE 上样体积计算。
- 结果复制到 clipboard。

使用逻辑结论：

- 输入错误返回用户可读错误，不输出误导性有效结果。
- 有效结果显示公式、结果和人工复核提示。
- copyable text 只用于 clipboard，不形成历史记录、文件、manifest 或正式报告。
- WB/SDS-PAGE 仅为上样体积计算，不进入 WB/凝胶灰度或条带解释。

结果语义：

- 实验辅助计算草稿。
- 不替代实验 SOP、试剂说明书、安全操作规范、临床建议或诊断结论。

审计结果：Pass。

### 4.2 本地试剂与配方

当前能力：

- 内置本地参考配方。
- 配方体积缩放。
- stock-to-working dilution。
- 用户配方草稿确认。
- 用户确认配方 JSON 保存/载入。
- `recipe_id` 冲突导入为 imported copy。

使用逻辑结论：

- 用户配方必须先确认，再进入内存 store。
- 保存 JSON 只保存用户确认配方，不保存内置参考配方、网络内容或自动建议。
- 导入冲突不覆盖现有用户配方。
- 安全边界提示覆盖 SOP、SDS、试剂说明书、浓度、pH、储存条件、有效期和危险性。

结果语义：

- 本地配方草稿 / 参考草稿。
- 不是正式 SOP，不构成安全操作规范，不自动适配所有实验。

审计结果：Pass。

### 4.3 外部来源手动草稿

当前能力：

- 手动录入来源 URL、标题、摘要和摘录内容。
- 生成来源卡片和摘录草稿。
- 摘录草稿转用户配方草稿。
- 用户确认后进入用户配方 store。

使用逻辑结论：

- 网络检索按钮不访问网络，只显示未启用提示。
- `network_enabled` 请求被校验拒绝。
- 来源内容不会自动成为正式配方，必须经过草稿转换和用户确认。

结果语义：

- 手动来源草稿和人工摘录草稿。
- 不代表网页抓取、AI 摘录、外部标准配方或自动验证来源。

审计结果：Pass。

### 4.4 图像定量

当前真实能力：

- fluorescence manual ROI grayscale metrics。
- wound manual ROI + user threshold area estimation。

当前占位能力：

- cell counting：`algorithm_not_available`。
- densitometry / grayscale / ink-value：`algorithm_not_available`。
- automatic ROI、batch processing、WB / gel grayscale：未实现。

使用逻辑结论：

- 图像分析只读取用户提供的单张本地图片，不上传、不联网。
- fluorescence 需要用户手动输入 signal/background ROI。
- wound 需要用户手动输入 analysis ROI、threshold 和 bright/dark mode。
- 细胞计数和灰度/墨值任务只生成占位结构，不生成定量结果。

结果语义：

- fluorescence：manual ROI grayscale measurement assistance。
- wound：manual ROI + user threshold semi-quantitative area estimation。
- 不构成自动图像算法结论、迁移效果判断、细胞识别、WB/凝胶灰度结论或临床解释。

审计结果：Pass。

### 4.5 ROI Export Package

当前能力：

- fluorescence manual ROI export package。
- wound manual ROI threshold export package。
- 每个 package 包含 JSON manifest、CSV summary、Markdown fragment、ROI overlay PNG。

使用逻辑结论：

- 只有用户点击导出并选择目录后才写盘。
- 文件名使用 no-overwrite 策略。
- 取消导出不写盘，失败显示用户可读错误并保留当前分析结果。
- Markdown fragment 不包含原图绝对路径。

结果语义：

- 本地导出包。
- manual-review / auxiliary / semi-quantitative。
- 不是正式报告、生产级报告、自动算法证明或临床诊断。

审计结果：Pass。

### 4.6 实验模板和记录草稿

当前能力：

- qPCR、WB、细胞接种、scratch assay、免疫荧光图像记录模板。
- 生成本地结构化记录草稿和 Markdown 预览。
- 用户选择路径后保存/载入实验记录草稿 JSON。

使用逻辑结论：

- 草稿状态固定为 `draft_manual_review_required`。
- 保存/载入只处理 `labtools_experiment_record_draft_store.v1`。
- 不做权限、签名、审计合规、团队协作、自动实验设计或正式报告。

结果语义：

- 本地结构化草稿。
- 不是完整 ELN、正式 SOP、临床建议或正式实验记录。

审计结果：Pass。

## 5. Schema 与写盘边界

当前 schema / JSON-compatible structures：

- `labtools_roi_export_manifest.v1`。
- `labtools_recipe_draft_store.v1`。
- `labtools_experiment_template_draft.v1`。
- `labtools_experiment_record_draft_store.v1`。
- `CalculationRecord` JSON-compatible dict。
- `Recipe` / `RecipeDraft` JSON-compatible dict。

本次审计未新增 schema，未修改 schema version，未新增导出格式。

写盘边界保持：

- no autosave。
- no database/history/background project storage。
- no network / AI / local model。
- no silent overwrite。
- user-visible cancel/failure states。
- schema version in saved JSON artifacts。
- draft/manual-review/auxiliary wording。

审计结果：Pass。

## 6. 残余风险与后续门槛

当前无 blocking finding。

非阻塞注意事项：

- ROI 导出成功 UI 会显示用户选择的导出目录和生成文件路径；这是本地 UI 反馈，不应复制进公开报告正文。
- 图像 audit record details 当前可包含 `source_path`，但现阶段仅作为内存审计记录使用；如未来持久化审计日志，需要重新审查本地路径泄露边界。
- 安全范围检查是关键词级边界检查，不是化学安全、伦理、安全或 SOP 审核引擎。

后续若要启用以下任一方向，必须单独立项并重新设计测试和安全边界：

- 自动 ROI。
- 自动细胞计数。
- WB / gel grayscale 或 densitometry。
- 批量图像处理或批量导出。
- 网络检索、网页抓取、AI Gateway、本地模型。
- 数据库、项目存储、自动保存、完整 ELN、正式报告。

## 7. 验证基线

本次回顾审计应保持以下验证命令通过：

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q`
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`
- `python3 -m compileall app/labtools`
- `git diff --check`
