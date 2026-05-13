# LabTools L6C Experiment Templates And Record Drafts Report

日期：2026-05-13

## 1. Stage

- Stage name：LabTools L6C - lightweight experiment templates and record drafts
- Worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- Branch：`dev/labtools`
- Starting commit：`bbaa221 Add LabTools recipe draft persistence`
- Ending commit：最终交接记录

## 2. Scope

本阶段将“实验模板”从占位页升级为轻量结构化草稿中心。目标是提供常见 wet-lab 实验记录草稿结构，而不是完整 ELN 或正式 SOP。

## 3. Implemented Features

- 新增 `app/labtools/experiment_templates` 服务层：
  - `ExperimentTemplate`。
  - `ExperimentRecordDraft`。
  - `ExperimentTemplateLibrary`。
  - `create_record_draft()`。
  - `draft_markdown_preview()`。
- 内置 5 个模板：
  - qPCR 实验计划模板。
  - Western blot 实验计划模板。
  - 细胞实验接种计划模板。
  - Scratch assay 记录模板。
  - 免疫荧光图像记录模板。
- 草稿字段：
  - 实验目的。
  - 样本分组。
  - 试剂/材料。
  - 关键参数。
  - 输出文件/记录。
  - 备注。
  - 人工复核提示。
- 草稿 schema：`labtools_experiment_template_draft.v1`。
- 草稿状态：`draft_manual_review_required`。
- UI：
  - 新增 `LabToolsTemplateWidget`。
  - 首页“实验模板”入口改为可进入。
  - Workspace page key 从 `pending` 更新为 `templates`。
  - 可选择模板、预填字段、生成 Markdown 预览。

## 4. Explicit Non-goals

- 未实现完整 ELN。
- 未实现权限、签名、审计合规或团队协作。
- 未实现自动保存或数据库。
- 未实现正式实验报告系统。
- 未实现网络、AI、本地模型或自动实验设计。
- 未新增图像算法、自动 ROI、自动细胞计数、WB/凝胶灰度。
- 未修改 Bioinformatics、Meta Analysis、ReleaseBuild、Integration、MainLine。

## 5. Safety And Semantics

- 所有模板和记录均为本地结构化草稿。
- 使用前必须人工核对实验室 SOP、伦理/安全要求、试剂说明书和实验设计。
- Scratch assay 和免疫荧光模板只记录 manual-review 工作流，不自动判断迁移效果、细胞数量或荧光结论。
- Western blot 模板不做条带灰度、归一化或图像解释。
- qPCR 模板不自动设计 primer，不解释 Ct 为正式结论。

## 6. Persistence Status

- 本阶段不自动保存。
- 不写数据库。
- 不写 manifest。
- 不导出 JSON/CSV。
- UI 仅生成内存中的结构化 draft 和 Markdown 预览。

## 7. Dependency Changes

- 未新增第三方依赖。
- 仅使用 Python 标准库 dataclass、datetime、uuid。

## 8. Validation

已运行：

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q
```

结果：通过，`142 passed in 0.63s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

结果：通过，`147 passed in 9.47s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q
```

结果：通过，`18 passed in 2.46s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
```

结果：通过，输出包含 `workspace_entries=3`、`labtools_features=4`。

```bash
python3 -m compileall app/labtools
```

结果：通过。

```bash
git diff --check
```

结果：通过。

提交前还需运行：

- `git diff --cached --check`

## 9. Known Limitations

- 当前模板字段为本地草稿结构，不支持用户自定义模板。
- 不保存草稿历史。
- 不提供完整 ELN、签名、权限、审计合规或团队协作。
- 不做自动分析、自动设计或正式结论。

## 10. Next Recommended Stage

- L6C.1：实验模板草稿 JSON 保存/导出 schema，但仍保持 lightweight draft，不做完整 ELN。
- L6B.1：recipe JSON schema 文档化、导入冲突策略和版本展示。

## 11. Git Status After Commit

- 待提交后回填最终状态。
