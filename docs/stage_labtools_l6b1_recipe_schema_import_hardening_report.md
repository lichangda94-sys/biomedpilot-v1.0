# LabTools L6B.1 Recipe Schema And Import Hardening Report

日期：2026-05-13

## 1. Stage

- Stage name：LabTools L6B.1 - recipe draft schema documentation and import conflict UI hardening
- Worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- Branch：`dev/labtools`
- Starting commit：`3102fcd Add LabTools experiment draft persistence`
- Ending commit：最终交接记录

## 2. Scope

本阶段对 L6B 用户配方草稿 JSON 持久化做小范围硬化和文档化：补充 schema 文档、显示导入冲突 summary，并在 UI 中展示用户配方 version。未新增 recipe 算法、配方来源、数据库、网络或 AI。

## 3. Files Changed

- `app/labtools/recipes/user_recipe_store.py`
- `app/labtools/recipes/__init__.py`
- `app/labtools/ui/recipe_widgets.py`
- `tests/labtools/test_recipe_persistence.py`
- `tests/ui/test_labtools_recipe_persistence_ui.py`
- `docs/labtools_current_handoff.md`
- `docs/labtools_recipe_draft_store_schema.md`
- `docs/stage_labtools_l6b1_recipe_schema_import_hardening_report.md`

## 4. Implemented Hardening Items

- 新增 `UserRecipeImportResult`：
  - `imported_recipes`。
  - `conflict_count`。
  - `warnings`。
  - `imported_count` property。
- `UserRecipeStore.import_recipes_with_summary()` 在导入时返回冲突 summary。
- 原有 `import_recipes()` 保持可用，继续返回导入后的 recipe tuple。
- 重复 `recipe_id` 会 clone 为 `user_recipe_imported_<token>`，不会覆盖现有用户配方。
- UI 在载入 JSON 后显示：
  - 载入配方数。
  - 实际写入当前内存配方数。
  - `recipe_id` 冲突数。
  - 未覆盖现有用户配方 warning。
- UI 的用户配方列表和 summary 显示 `version`。
- 新增 schema 文档：`docs/labtools_recipe_draft_store_schema.md`。

## 5. Schema Documentation

Schema 文档固定记录：

- `schema_version = labtools_recipe_draft_store.v1`。
- `export_type = labtools_user_recipe_draft_store`。
- 顶层字段。
- recipe 字段。
- component 字段。
- 载入校验规则。
- `recipe_id` 冲突处理规则。
- safety / manual-review 边界。

## 6. Safety And Semantics Boundaries

- JSON 仍是本地 recipe draft store，不是正式 SOP。
- 使用前必须人工核对实验室 SOP、SDS、试剂说明书和安全规范。
- 不新增危险化学品、高风险合成、动物/人体实验或病毒实验操作方案。
- 不联网、不调用 AI、不做自动配方生成。
- 不写数据库、不自动保存、不云同步。
- 不修改图像分析、实验模板、Bioinformatics、Meta Analysis、ReleaseBuild、Integration、MainLine。

## 7. Dependency Changes

- 未新增第三方依赖。
- 仅使用 Python 标准库 dataclass。

## 8. Validation

已运行：

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q
```

结果：通过，`152 passed in 0.57s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

结果：通过，`153 passed in 9.95s`。

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

```bash
git diff --cached --check
```

结果：通过。

## 9. Known Limitations

- 当前导入冲突策略是自动 clone，不提供导入预览或选择性导入。
- Version 只显示并保留，不做复杂版本比较、合并或迁移。
- Schema 文档是 internal preview 说明，不是稳定公共 API。

## 10. Next Recommended Stage

- L6A.2：图像导出 schema 文档化、更多 UI 回归测试和用户选择目录体验微调，但仍不得新增算法。
- L6C.2：实验记录草稿 Markdown 片段导出体验和导入冲突提示，但仍不做完整 ELN。
- L6B.2：recipe JSON 导入预览/选择性导入，但仍不做数据库、云同步或正式 SOP 管理。

## 11. Git Status After Commit

- 待提交后回填最终状态。
