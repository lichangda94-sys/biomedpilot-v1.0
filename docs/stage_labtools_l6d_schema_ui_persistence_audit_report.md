# LabTools L6D Schema Index, Persistence UI Regression, And Safety Audit Report

日期：2026-05-13

## 1. Stage

- Stage name：LabTools L6D - schema index, persistence UI regression, and safety audit
- Worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- Branch：`dev/labtools`
- Starting commit：`b16ce4d Harden LabTools recipe draft imports`
- Ending commit：最终交接记录

## 2. Scope

本阶段只做 schema 文档索引、现有 persistence UI 回归测试加固和写盘安全审计。不新增图像算法、recipe 算法、experiment template 功能、数据库、网络、AI、自动保存或跨模块持久化。

## 3. Files Changed

- `docs/labtools_schema_index.md`
- `docs/labtools_current_handoff.md`
- `docs/stage_labtools_l6d_schema_ui_persistence_audit_report.md`
- `tests/labtools/test_labtools_schema_index.py`
- `tests/ui/test_labtools_image_export_ui.py`
- `tests/ui/test_labtools_recipe_persistence_ui.py`
- `tests/ui/test_labtools_template_ui.py`

## 4. Schema Index

新增 `docs/labtools_schema_index.md`，统一记录：

- `labtools_roi_export_manifest.v1`
- `labtools_recipe_draft_store.v1`
- `labtools_experiment_template_draft.v1`
- `labtools_experiment_record_draft_store.v1`
- `CalculationRecord` JSON-compatible dict
- `Recipe` / `RecipeDraft` JSON-compatible dict

索引逐项记录用途、producer / consumer、主要字段、用户语义、是否建议公开分享、是否可能包含本地路径或路径片段，以及 draft / auxiliary / local persistence 边界。

## 5. UI Regression Coverage Added

- ROI export：
  - 导出按钮和说明文字存在。
  - 无结果时按钮禁用。
  - 取消目录选择不写盘，不显示成功。
  - 受控失败显示错误并保留结果。
  - fluorescence 成功导出显示四类输出。
  - wound 成功导出显示四类输出和 manual-review / semi-quantitative 语义。
- Recipe draft persistence：
  - save/load 按钮存在且启用。
  - 无用户配方时保存不写盘。
  - 取消保存/载入不写盘或不改变当前 store。
  - 保存失败显示用户可读错误。
  - malformed JSON 载入失败可见。
  - 成功载入显示 schema、version、import summary。
  - `recipe_id` 冲突导入不覆盖现有配方。
- Experiment record draft persistence：
  - save/load 按钮存在且启用。
  - 无 draft 时保存不写盘。
  - 取消保存/载入不写盘或不改变当前 drafts。
  - 保存失败显示用户可读错误。
  - malformed JSON 载入失败可见。
  - 成功保存显示 schema、人工核对和非完整 ELN 语义。

## 6. Persistence Safety Audit

| Path | User trigger | No autosave / DB / network / AI | No silent overwrite | Failure visible | Schema version | Semantics |
| --- | --- | --- | --- | --- | --- | --- |
| `export_fluorescence_analysis_package()` | UI button + selected directory | Pass | Pass, non-overwrite package paths + exclusive create | Pass | `labtools_roi_export_manifest.v1` | manual-review auxiliary output |
| `export_wound_healing_analysis_package()` | UI button + selected directory | Pass | Pass, non-overwrite package paths + exclusive create | Pass | `labtools_roi_export_manifest.v1` | manual-review / semi-quantitative output |
| `save_user_recipe_store()` | UI button + selected JSON path | Pass | Pass, `_001` suffix + exclusive create | Pass | `labtools_recipe_draft_store.v1` | local recipe draft, not SOP |
| `load_user_recipe_store()` | UI button + selected JSON path | Pass | Pass, merge/import never overwrites conflicting recipe ids | Pass | requires `labtools_recipe_draft_store.v1` | imported local draft, still manual-review |
| `save_experiment_draft_store()` | UI button + selected JSON path | Pass | Pass, `_001` suffix + exclusive create | Pass | `labtools_experiment_record_draft_store.v1` | structured draft, not ELN |
| `load_experiment_draft_store()` | UI button + selected JSON path | Pass | Pass, appends drafts in memory; no file write | Pass | requires `labtools_experiment_record_draft_store.v1` | structured draft, still manual-review |

No audit finding required a code behavior change outside tests/docs.

## 7. Explicit Non-goals

- No new persistence format or schema version.
- No automatic saving.
- No database, project storage, history system, cloud sync, network, AI Gateway, local model, OpenCV, scikit-image, ImageJ/Fiji.
- No image algorithm changes.
- No recipe algorithm or high-risk protocol expansion.
- No full ELN, signature, permissions, compliance audit, or formal report system.
- No changes to Bioinformatics, Meta Analysis, ReleaseBuild, Integration, MainLine, desktop app bundle, or `dist`.

## 8. Validation

Targeted validation already run:

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_labtools_image_export_ui.py tests/ui/test_labtools_recipe_persistence_ui.py tests/ui/test_labtools_template_ui.py -q
```

结果：通过，`21 passed in 0.56s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools/test_roi_export_package_schema.py tests/labtools/test_recipe_persistence.py tests/labtools/test_experiment_template_persistence.py tests/labtools/test_labtools_schema_index.py -q
```

结果：通过，`29 passed in 0.44s`。

Full validation：

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q
```

结果：通过，`154 passed in 0.65s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

结果：通过，`156 passed in 9.26s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q
```

结果：通过，`18 passed in 2.29s`。

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

## 9. Known Limitations

- Schema index 是 Developer Preview / testing 文档，不是公共稳定 API。
- Audit 基于当前六个明确写盘/载入服务和对应 UI handlers，不覆盖未来未实现的项目存储或数据库。
- UI regression 测试使用 Qt offscreen 和 monkeypatch selector，不测试原生 QFileDialog 本身。

## 10. Next Recommended Stage

- L6A.2：ROI export 用户体验微调和更多目录选择体验测试，但仍不得新增算法。
- L6C.2：实验记录草稿 Markdown 片段导出体验和导入冲突提示，但仍不做完整 ELN。
- L6B.2：recipe JSON 导入预览/选择性导入，但仍不做数据库、云同步或正式 SOP 管理。

## 11. Git Status After Commit

- 待提交后回填最终状态。
