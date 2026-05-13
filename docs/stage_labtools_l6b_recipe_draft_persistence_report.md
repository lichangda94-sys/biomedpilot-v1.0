# LabTools L6B Recipe Draft Persistence And Safety Review Report

日期：2026-05-13

## 1. Stage

- Stage name：LabTools L6B - reagent recipe draft local persistence and safety review
- Worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- Branch：`dev/labtools`
- Starting commit：`63e7b5e Harden LabTools ROI export packages`
- Ending commit：最终交接记录

## 2. Scope

本阶段在现有本地配方库、用户配方草稿和手动来源草稿基础上，新增用户确认配方的本地 JSON 持久化能力和安全范围检查。

本阶段只做用户选择路径后的本地保存/载入，不做网络、AI、数据库、自动保存、云同步或正式 SOP 管理。

## 3. Files Changed

- `app/labtools/recipes/recipe_persistence.py`
- `app/labtools/recipes/user_recipe_store.py`
- `app/labtools/recipes/__init__.py`
- `app/labtools/ui/recipe_widgets.py`
- `tests/labtools/test_recipe_persistence.py`
- `tests/labtools/test_labtools_imports.py`
- `tests/ui/test_labtools_recipe_persistence_ui.py`
- `docs/labtools_current_handoff.md`
- `docs/stage_labtools_l6b_recipe_draft_persistence_report.md`

## 4. Implemented Features

- 新增 recipe draft store JSON schema：`labtools_recipe_draft_store.v1`。
- 新增本地保存服务：
  - `save_user_recipe_store()`。
  - 仅保存用户确认配方。
  - 写入前进行安全范围检查。
  - 文件名 sanitize。
  - no-overwrite：同名文件自动使用 `_001` 等 suffix。
- 新增本地载入服务：
  - `load_user_recipe_store()`。
  - 校验 schema。
  - 校验 recipe 结构和单位。
  - 进行安全范围检查。
  - 返回结构化 load result，不自动写入其它模块。
- 新增安全审查：
  - `evaluate_recipe_safety()`。
  - 常规草稿状态为 `manual_review_required`。
  - 高风险化学品、毒物、高风险合成、动物/人体实验或病毒相关关键词会被阻断。
- `UserRecipeStore` 新增：
  - confirm 前安全范围检查。
  - `import_recipes()`，用于载入 JSON 后合并用户配方；冲突 id 会 clone 为 imported id。
- UI 新增：
  - “本地配方草稿持久化”区域。
  - “保存用户配方 JSON”按钮。
  - “载入用户配方 JSON”按钮。
  - 取消保存/载入不写盘。
  - 保存/载入失败显示用户可读错误。

## 5. Safety And Semantics Boundaries

- 本地 JSON 是用户配方草稿持久化文件，不是正式 SOP。
- 使用前必须人工核对实验室 SOP、SDS、试剂说明书和安全规范。
- 不提供危险化学品、毒物、高风险合成、动物/人体实验或病毒相关操作草稿保存。
- 不构成临床、诊断或安全操作建议。
- 不保存网络抓取内容，不调用 AI 进行配方生成或解释。

## 6. Persistence Status

- 保存只在用户选择 JSON 路径后发生。
- 载入只在用户选择 JSON 文件后发生。
- 不自动保存。
- 不写数据库。
- 不写历史记录系统。
- 不上传、不联网、不跨模块传递。
- 不覆盖已有文件。

## 7. Explicit Non-goals

- 未实现 recipe center 数据库。
- 未实现自动保存。
- 未实现云同步、网络来源同步或网页下载。
- 未实现 AI 配方生成、摘录或审查。
- 未实现正式 SOP 管理。
- 未实现危险化学品、高风险合成、动物/人体实验或病毒实验操作方案。
- 未修改图像算法、实验计算器、Bioinformatics、Meta Analysis、ReleaseBuild、Integration、MainLine。

## 8. Dependency Changes

- 未新增第三方依赖。
- 仅使用 Python 标准库 JSON、dataclass、datetime、pathlib、uuid。

## 9. Validation

已运行：

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q
```

结果：通过，`138 passed in 0.67s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

结果：通过，`144 passed in 9.07s`。

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q
```

结果：通过，`18 passed in 2.19s`。

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

## 10. Known Limitations

- 当前 JSON schema 是 LabTools internal preview schema。
- 载入冲突策略为重复 id clone，不提供复杂版本合并 UI。
- 安全范围检查是关键词级边界检查，不替代实验室安全审核。
- 不做多用户权限、签名、审计合规或完整 ELN。

## 11. Next Recommended Stage

- L6C：轻量实验模板和记录草稿。
- L6B.1：recipe JSON schema 文档化、导入冲突 UI 展示和草稿版本展示。

## 12. Git Status After Commit

- 待提交后回填最终状态。
