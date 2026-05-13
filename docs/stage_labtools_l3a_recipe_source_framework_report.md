# LabTools Stage L3A Recipe Source Framework Report

日期：2026-05-13

## 范围

- 当前 worktree：`/Users/changdali/Developer/biomedpilot v1.0/LabTools`
- 权威总手册：`/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- 本阶段范围：配方外部来源与手动摘录草稿框架。

## 已实现

- 新增配方来源模型：
  - `RecipeSourceRequest`
  - `RecipeSourceCard`
  - `RecipeExtractionDraft`
- 新增来源草稿转换流程：
  - 手动来源录入生成来源卡片。
  - 来源卡片和人工摘录内容生成摘录草稿。
  - 摘录草稿只能转为未确认的 `RecipeDraft`。
  - 用户确认后才通过 `UserRecipeStore` 保存为 confirmed user recipe。
- 新增来源字段记录：
  - `source_url`
  - `source_title`
  - `source_label`
  - `accessed_at`
  - `user_confirmed`
  - `edited_by_user`
- 保持 JSON-compatible dict 导出能力。
- 新增来源校验：
  - `network_enabled` 请求会被拒绝。
  - URL 仅接受 `http` 或 `https` 字符串，但本阶段不会访问该地址。
  - 高风险制备内容关键字会被拒绝保存到来源草稿。
- “试剂与配方”页面新增清晰分区：
  - 本地配方库
  - 用户配方
  - 外部来源草稿
- 外部来源草稿区包含：
  - 检索需求输入框
  - 禁用状态的网络检索按钮
  - 手动添加来源
  - 来源卡片结果
  - 摘录草稿
  - 转为用户配方草稿
  - 确认保存

## 安全与边界

- 未真实访问外部网络。
- 未抓取网页。
- 未下载网页内容。
- 未调用 AI Gateway 或本地模型。
- 未将网页内容自动保存为标准配方。
- 未实现危险化学品、毒性物质或受管制物质的详细制备流程。
- 未接入 ImageJ/Fiji。
- 未开发图像分析算法。
- 未生成 fake 图像分析结果。
- 未默认写盘。

## 未实现

- 未启用真实网络检索。
- 未实现网页解析、网页下载或远程来源同步。
- 未实现 AI 摘录、AI 总结或 AI 配方结构化。
- 未实现多组分复杂摘录编辑器。
- 未实现文件持久化或数据库持久化。

## 测试记录

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`
  - 结果：56 passed
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

- LabTools 计算器功能：不修改核心计算行为。
- 本地配方库：保留 L2 内置配方和缩放能力，新增来源草稿字段兼容导出。
- Bioinformatics：不修改业务逻辑。
- Meta Analysis：不修改业务逻辑。
- Shared Vocabulary：不修改业务逻辑。
- AI Gateway：不修改业务逻辑。
- MainLine：不修改；本阶段仅在 LabTools worktree 内开发。
