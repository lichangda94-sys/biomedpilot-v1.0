# LabTools Tool Logic Retrospective Audit Report

日期：2026-05-14

## Stage

LabTools Tool Logic Retrospective Audit - 使用逻辑与结果语义回顾审计。

## Worktree

- Worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- Branch：`dev/labtools`
- Starting commit：`8d9c7d3 docs(labtools): add tool logic audit report`
- Scope：只做审计、文档和必要测试检查；不新增工具、不新增算法、不扩展 UI 功能。

## Entry Checks

已按阶段要求检查：

- `git status --short`：clean，无未提交业务代码。
- `git branch --show-current`：`dev/labtools`。
- `git log --oneline -15`：最近 15 个提交均处于 LabTools 相关开发线，HEAD 为 `8d9c7d3 docs(labtools): add tool logic audit report`。

未执行回退、覆盖或 push。

## Documents Reviewed

- `CODEX.md`
- `README.md`
- `docs/labtools_current_handoff.md`
- `docs/labtools_schema_index.md`
- `docs/labtools_tool_logic_audit.md`
- `docs/stage_labtools_*.md`
- `reports/LabTools_handoff_report_20260513.md`

## Audit Method

本次审计把阶段报告和当前代码逐项对照，重点检查：

- 用户从首页、计算器、配方、图像定量、实验模板进入工具后的操作逻辑是否与当前能力匹配。
- 计算结果、ROI 结果、recipe draft、experiment draft 的用户语义是否保持辅助、草稿、manual-review、testing-level。
- 未实现能力是否仍保持 placeholder / `algorithm_not_available`，未生成 fake 结果。
- 写盘行为是否只发生在用户选择目录或 JSON 路径后，且保留 no-overwrite、失败可见和 schema version。
- 是否出现网络、AI Gateway、本地模型、ImageJ/Fiji、OpenCV、scikit-image 或跨模块持久化路径。

新增 `docs/labtools_tool_logic_audit.md` 作为长期回顾审计索引，阶段报告保留本轮命令、结果和交接状态。

## Findings

No blocking findings.

### 1. Tool Entry And Status Semantics

Pass. `labtools_features()` 和 LabTools 首页把四类入口标为：

- 实验计算器：本地辅助计算草稿。
- 试剂与配方：本地草稿。
- 图像定量：manual-review MVP。
- 实验模板：草稿中心，不是完整 ELN。

这与 handoff、schema index 和 L6E/L7B 报告一致。

### 2. Calculator Result Semantics

Pass. 计算器服务层和 UI 继续输出本地辅助计算草稿，包含人工复核提示，不写 CSV/manifest/项目文件，不保存历史。L7A 的复制结果只写 clipboard，invalid 输入不启用 copyable text。

### 3. Recipe Draft Flow

Pass. 用户配方仍需草稿确认后进入内存 store；本地 JSON 保存只保存用户确认配方。保存/载入文案和 payload 都保留 SOP/SDS/浓度/pH/储存条件/有效期/危险性人工核对提示。`recipe_id` 冲突导入仍 clone 为 imported copy，不覆盖现有用户配方。

### 4. Source Draft And Network Boundary

Pass. 外部来源流程只支持手动来源卡片和人工摘录草稿，`network_enabled` 请求被拒绝，UI 的网络检索按钮只显示未启用提示。未发现 HTTP client、AI Gateway 或本地模型调用。

### 5. Image Analysis Semantics

Pass. 当前真实图像能力仍限于：

- fluorescence manual ROI grayscale metrics。
- wound manual ROI + user threshold area estimation。

cell counting、densitometry / grayscale / ink-value 仍保持 `algorithm_not_available` 占位，不生成细胞数、WB/凝胶灰度或 fake 定量值。

### 6. ROI Export And Persistence Semantics

Pass. ROI export package 仍只在调用方提供用户选择目录后写入 JSON manifest、CSV summary、Markdown fragment 和 ROI overlay PNG。Manifest 固定 `labtools_roi_export_manifest.v1`，Markdown fragment 不包含原图绝对路径，导出结果保持 manual-review / semi-quantitative / auxiliary 语义。

### 7. Experiment Template Drafts

Pass. 实验模板仍为本地结构化记录草稿，保存/载入只处理 `labtools_experiment_record_draft_store.v1` JSON，未升级为完整 ELN、正式报告、签名、权限或合规审计。

## Non-Blocking Notes

- 图像导出成功 UI 会显示用户选择的导出目录和生成文件绝对路径，这是本地 UI 反馈；schema index 已明确这些路径不属于公开报告正文。
- `create_fluorescence_audit_records()` 和 `create_wound_healing_audit_records()` 的 audit details 内包含 `source_path`，当前只在内存审计记录中使用；如果未来写入持久审计日志，需要重新审查本地路径暴露边界。
- 本次未新增回归测试，因为现有 L6D/L6E/L7A/L7B 覆盖已经直接命中本阶段审计点；本阶段只补齐审计文档。

## Validation

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`：159 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：169 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q`：18 passed
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`：passed，输出包含 `workspace_entries=3`、`labtools_features=4`
- `python3 -m compileall app/labtools`：passed

## Stage Result

本阶段没有发现需要立即修改代码的使用逻辑或结果语义缺陷。当前 LabTools 仍应保持 Developer Preview / internal beta / local testing 定位；后续若启用自动图像算法、网络/AI、数据库、正式报告或完整 ELN，必须作为单独阶段重新设计边界和测试。
