# LabTools L7B Recipe Template Safety Polish Report

日期：2026-05-13

## Stage

LabTools L7B - Recipe template safety polish / recipe draft 与模板安全边界 polish。

## Worktree

- Worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- Branch：`dev/labtools`
- Starting commit：`c465b4d Polish LabTools calculator result copy UX`
- Ending commit：committed as this report's containing commit; see `git log --oneline -5` for the exact hash.

## Scope

- 优化 recipe draft/template 的安全边界、用户核对提示和导入冲突提示。
- 保持 `labtools_recipe_draft_store.v1` 兼容；不做破坏性迁移。
- 不新增危险配方、不联网、不接 AI、不新增数据库、自动保存、云同步或正式 SOP 管理。

## Files Changed

- `app/labtools/recipes/__init__.py`
- `app/labtools/recipes/recipe_models.py`
- `app/labtools/recipes/recipe_persistence.py`
- `app/labtools/ui/recipe_widgets.py`
- `tests/labtools/test_recipe_persistence.py`
- `tests/ui/test_labtools_recipe_persistence_ui.py`
- `docs/labtools_current_handoff.md`
- `docs/labtools_schema_index.md`
- `docs/stage_labtools_l7b_recipe_template_safety_polish_report.md`

## Implemented

- Recipe review notice now explicitly states:
  - 本地草稿；
  - 使用前需按实验室 SOP、SDS、试剂说明书人工核对；
  - 用户需确认浓度、pH、储存条件、有效期和危险性；
  - 不构成安全操作规范；
  - 不自动适配所有实验。
- Recipe draft store payload includes `safety_category`:
  - `routine_buffer_draft`
  - `user_verified_only`
  - `requires_lab_sop_review`
- UI surfaces the same safety category in recipe persistence support text, recipe summary, detail panel, save success and load success messages.
- Import conflict behavior remains non-destructive:
  - conflict count is shown;
  - conflicting records are imported as `imported copy`;
  - existing user recipes are not overwritten;
  - failed import does not clear existing recipes.
- Schema index documents the compatibility boundary: v1 has top-level `created_at`; per-recipe `created_at` / `updated_at` are not required in current v1, and imported status is represented by source fields and cloned `user_recipe_imported_<token>` ids.

## Explicit Non-Goals

- No new recipe templates.
- No high-risk chemistry, toxins, controlled substances, explosive synthesis, animal/human protocol, clinical advice, or viral work SOP.
- No network, AI, database, cloud sync, autosave, history, formal SOP management, or cross-module persistence.

## Validation

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools/test_recipe_scaling.py tests/labtools/test_recipe_persistence.py -q`：14 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_labtools_recipe_persistence_ui.py -q`：8 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`：159 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：169 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q`：18 passed
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`：passed
- `python3 -m compileall app/labtools`：passed
- `git diff --check`：passed
- `git diff --cached --check`：pending before commit

## Known Limitations

- Current v1 payload remains backward compatible and does not force per-recipe `created_at` / `updated_at`.
- Safety review is a conservative keyword and boundary check, not a chemical safety validation engine.
- Recipe drafts remain local user-confirmed drafts and are not formal SOPs.

## Next Recommended Stage

Recommended next stage：LabTools L7C persistence documentation cleanup or targeted UI polish only after confirming whether recipe import preview/selective import is still desired.

## Git Status After Commit

Pending before commit.
