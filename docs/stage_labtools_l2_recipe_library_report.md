# LabTools Stage L2 Recipe Library Report

日期：2026-05-13

## 范围

- 当前 worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- 权威总手册：`/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- 本阶段范围：本地试剂与配方库 MVP。

## 已实现

- 新增本地配方库模块 `app/labtools/recipes`：
  - `recipe_models.py`
  - `recipe_library.py`
  - `recipe_scaling.py`
  - `recipe_validation.py`
  - `user_recipe_store.py`
  - `built_in_recipes.py`
- 新增内置常用科研参考配方：
  - PBS
  - TBS
  - TAE
  - TBE
  - Tris-HCl buffer
  - SDS-PAGE running buffer
  - Western transfer buffer 示例
  - Blocking buffer 示例
  - Agarose gel 计算示例
  - RIPA buffer 示例框架
- 支持按目标体积线性缩放配方组分。
- 支持 `L`、`mL`、`µL` 之间体积换算。
- 对不能线性缩放的单位返回提示，不强行计算。
- 支持 `10× / 5× / 1×` 等 stock-to-working 稀释计算，使用 `C1V1 = C2V2`。
- 新增用户自定义配方草稿模型和内存 store：
  - 草稿必须 confirm 后才成为 confirmed user recipe。
  - 保存前校验名称、组分、单位和用量。
  - 支持导出 JSON-compatible dict。
  - 不自动写盘。
- LabTools 首页“试剂与配方”入口从“开发中”改为可用。
- 新增 `LabToolsRecipeWidget`：
  - 内置配方列表
  - 配方详情
  - 目标体积输入与缩放计算
  - stock-to-working 稀释计算
  - 缩放结果区
  - 用户自定义配方草稿确认区
- 配方详情显示来源、版本、适用范围、注意事项和人工复核提示。

## 安全与边界

- 未接入外部网络。
- 未检索网页。
- 未下载网页内容。
- 未调用 AI Gateway 或本地模型。
- 未接入 ImageJ/Fiji。
- 未开发图像分析算法。
- 未生成 fake 图像分析结果。
- 未实现危险化学品、毒性物质或受管制物质的详细制备流程。
- RIPA 条目仅作为“示例框架”，明确要求按实验室 SOP 和试剂说明复核。
- 内置配方均标注为 BioMedPilot 本地科研参考，不声明为外部标准方案。

## 未实现

- 未实现外部配方检索。
- 未实现文件自动保存或数据库持久化。
- 未实现多组分复杂用户配方编辑器。
- 未实现图像定量。
- 未实现实验模板。
- 未修改包装发布逻辑。

## 测试记录

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`
  - 结果：44 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  - 结果：135 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q`
  - 结果：18 passed
- `python3 -m app.main --smoke-test`
  - 结果：通过，输出包含 `workspace_entries=3`、`labtools_features=4`
- `python3 -m compileall app/labtools`
  - 结果：通过
- `git diff --check`
  - 结果：通过

## 边界影响

- LabTools 计算器功能：未修改核心计算行为。
- Bioinformatics：未修改业务逻辑。
- Meta Analysis：未修改。
- Shared Vocabulary：未修改。
- AI Gateway：未修改。
- MainLine：未修改；本阶段仅在 LabTools worktree 内开发。
