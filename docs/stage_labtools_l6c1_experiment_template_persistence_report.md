# LabTools L6C.1 Experiment Template Draft Persistence Report

日期：2026-05-13

## 1. Stage

- Stage name：LabTools L6C.1 - experiment template draft JSON persistence
- Worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- Branch：`dev/labtools`
- Starting commit：`0c1866e Add LabTools experiment template drafts`
- Ending commit：最终交接记录

## 2. Scope

本阶段在 L6C 轻量实验模板和结构化记录草稿基础上，新增用户选择路径后的本地 JSON 保存/载入能力。目标是让模板草稿可复用、可审计，但仍保持 lightweight draft，不升级为完整 ELN。

## 3. Files Changed

- `app/labtools/experiment_templates/template_persistence.py`
- `app/labtools/experiment_templates/__init__.py`
- `app/labtools/ui/template_widgets.py`
- `tests/labtools/test_experiment_template_persistence.py`
- `tests/labtools/test_labtools_imports.py`
- `tests/ui/test_labtools_template_ui.py`
- `docs/labtools_current_handoff.md`
- `docs/stage_labtools_l6c1_experiment_template_persistence_report.md`

## 4. Implemented Features

- 新增 experiment record draft store JSON schema：`labtools_experiment_record_draft_store.v1`。
- 新增本地保存服务：
  - `save_experiment_draft_store()`。
  - 仅保存用户生成的 `ExperimentRecordDraft`。
  - 文件名 sanitize。
  - no-overwrite：同名文件自动使用 `_001` 等 suffix。
- 新增本地载入服务：
  - `load_experiment_draft_store()`。
  - 校验 JSON、schema、draft 列表、核心字段、草稿状态和人工复核提示。
  - 返回结构化 load result，不写入其它模块。
- 新增基础范围检查：
  - `evaluate_experiment_record_draft()`。
  - 常规草稿状态为 `manual_review_required`。
  - 人体/动物实验、病毒包装、临床诊断、治疗建议或高风险合成相关关键词会被阻断。
- UI 新增：
  - “保存记录草稿 JSON”按钮。
  - “载入记录草稿 JSON”按钮。
  - 取消保存/载入不写盘。
  - 保存/载入失败显示用户可读错误。

## 5. Schema

- Store schema：`labtools_experiment_record_draft_store.v1`。
- Source draft schema：`labtools_experiment_template_draft.v1`。
- Payload 保留：
  - `schema_version`。
  - `export_type`。
  - `created_at`。
  - `software_channel`。
  - `review_status`。
  - `draft_count`。
  - `drafts`。
  - `draft_reviews`。
  - `source_schema_version`。
  - `safety_note`。
  - `persistence_note`。

## 6. Safety And Semantics Boundaries

- 本地 JSON 是实验记录草稿持久化文件，不是完整 ELN。
- 使用前必须人工核对实验室 SOP、伦理/安全要求、试剂说明书和实验设计。
- 不构成临床、诊断、安全操作建议或正式实验记录。
- 不提供人体/动物实验、病毒包装、临床诊断、治疗建议或高风险合成操作草稿保存。
- Scratch assay 和免疫荧光模板仍只记录 manual-review 工作流，不自动判断迁移效果、细胞数量或荧光结论。

## 7. Persistence Status

- 保存只在用户选择 JSON 路径后发生。
- 载入只在用户选择 JSON 文件后发生。
- 不自动保存。
- 不写数据库。
- 不写历史记录系统。
- 不上传、不联网、不跨模块传递。
- 不覆盖已有文件。

## 8. Explicit Non-goals

- 未实现完整 ELN。
- 未实现权限、签名、审计合规或团队协作。
- 未实现自动保存、数据库或历史记录系统。
- 未实现正式实验报告系统。
- 未实现网络、AI、本地模型或自动实验设计。
- 未新增图像算法、自动 ROI、自动细胞计数、WB/凝胶灰度。
- 未修改 Bioinformatics、Meta Analysis、ReleaseBuild、Integration、MainLine。

## 9. Dependency Changes

- 未新增第三方依赖。
- 仅使用 Python 标准库 JSON、dataclass、datetime、pathlib、re。

## 10. Validation

已运行：

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q
```

结果：通过，`151 passed in 0.80s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

结果：通过，`152 passed in 9.53s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q
```

结果：通过，`18 passed in 2.40s`。

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

```bash
git diff --cached --check
```

结果：通过。

## 11. Known Limitations

- 当前 JSON schema 是 LabTools internal preview schema。
- 载入策略为追加到当前内存草稿列表，不提供复杂版本合并 UI。
- 基础范围检查是关键词级边界检查，不替代机构伦理、安全或 SOP 审核。
- 不支持用户自定义模板。
- 不提供完整 ELN、签名、权限、审计合规或团队协作。

## 12. Next Recommended Stage

- L6B.1：recipe JSON schema 文档化、导入冲突 UI 展示和草稿版本展示。
- L6A.2：图像导出 schema 文档化、更多 UI 回归测试和用户选择目录体验微调，但仍不得新增算法。
- L6C.2：实验记录草稿 Markdown 片段导出体验和导入冲突提示，但仍不做完整 ELN。

## 13. Git Status After Commit

- 待提交后回填最终状态。
