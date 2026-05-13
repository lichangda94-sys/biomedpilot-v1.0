# MainLine Current Baseline

日期：2026-05-13

范围：`/Users/changdali/Developer/biomedpilot v1.0/MainLine`

## 基线定位

MainLine 当前作为 BioMedPilot / 医研智析 v1.0 的稳定主线工作区，承担桌面壳、登录、模块选择、设置、测试模式、Bioinformatics 稳定主流程、Shared 接口和 Meta 最小入口。

本基线仍属于 Developer Preview / internal beta / local testing build，不是 production-ready、临床级或投稿级系统。

## 当前分支和提交

- 当前分支：`stable/mainline`
- Stage 0.5 开始时最新提交：`def9152b4f24e5f1ef0ec4cd3b00fba9355e5c73`
- 最近阶段提交：
  - `def9152`：Stage 0.4 缓存清理和 `.gitignore` 加固。
  - `daca0fe`：Stage 0.3 旧 Markdown 归档。
  - `6334a7a`：全局开发手册创建。
  - `ca54434`：Stage 0.2 仓库内容审计。
  - `f295672`：P0 Bioinformatics workspace 初始化兼容修复。

## 迁移完成状态

- v1.0 本地主目录、bare repo、各 worktree、bundle 备份和分支结构已经建立。
- 迁移 bundle 已验证，包含旧仓库全部分支和标签。
- MainLine 可在本地作为 `stable/mainline` 工作区继续开发和验证。
- 远程仓库上传仍受本机 GitHub HTTPS 凭据或 SSH public key 权限限制；本基线不执行 `git push`，也不处理凭据。

## P0 修复状态

P0 修复已完成。

- 原问题：`app/shell/main_window.py` 初始化 `BioinformaticsWorkspaceWidget(on_back=self.show_dashboard)` 时，Bioinformatics workspace 构造参数不兼容，导致 `tests/ui` 失败。
- 当前状态：`app/bioinformatics/workspace.py` 中 `BioinformaticsWorkspaceWidget` 已支持 `on_back` 参数，并把返回行为接入项目首页。
- 修复提交：`f295672 fix(mainline): restore bioinformatics workspace initialization`。

## Stage 0.2 审计状态

Stage 0.2 已完成。

- 报告：`docs/cleanup/stage_0_2_repository_cleanup_audit_20260513.md`
- 结论：完成 `tests/`、`docs/`、`app/bioinformatics/legacy/`、archive、缓存、构建产物、临时文件和本地生成数据审计。
- 关键边界：当前有效测试、`app/bioinformatics/legacy/`、`assets/icons/`、AI Gateway、词库接口和项目流程依赖不得在第一阶段删除。

## Stage 0.3 Markdown 归档状态

Stage 0.3 已完成。

- 报告：`docs/cleanup/stage_0_3_markdown_archive_report_20260513.md`
- 索引：`docs/archive/legacy_handoff_20260513/README.md`
- 结果：99 个旧 Markdown 审计、阶段报告、迁移说明和交接文件已归档到 `docs/archive/legacy_handoff_20260513/`。
- 删除文件：0。

## Stage 0.4 缓存和 `.gitignore` 清理状态

Stage 0.4 已完成。

- 报告：`docs/cleanup/stage_0_4_cache_build_cleanup_report_20260513.md`
- 结果：清理 ignored / untracked 的 `.pytest_cache/` 和 `__pycache__/`，加固 `.gitignore`。
- 未处理 tracked logs：保留并列为人工确认项。
- 删除业务代码、测试、legacy、图标资源、当前 handoff / cleanup / archive 索引：0。

## 总开发手册一致性

以下两份文件已做字节级一致性检查，结果一致：

- `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- `docs/handoff/Global_Development_Manual.md`

## 当前测试基线

Stage 0.5 验收命令：

- `python3 -m app.main --smoke-test`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`
- `git diff --check`
- `git status --short --branch`

验收结果：

- `python3 -m app.main --smoke-test`：通过；`git_head=def9152`，`workspace_entries=2`，`bioinformatics_features=5`，`meta_analysis_features=9`，`pyside6_available=True`。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：通过，`133 passed in 7.96s`。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`：通过，`264 passed in 2.34s`。
- `git diff --check`：通过。
- `git status --short --branch`：提交前仅显示本阶段基线文档新增。

## 当前仍需人工确认的 tracked logs

以下文件仍被 Git 跟踪，本阶段只记录，不删除、不移动、不停止跟踪：

- `logs/validation/geo_random_recognition_audit.jsonl`
- `archive/legacy_sources/model9/demo_projects/MP-2024-0007/logs/app.log`

后续如需处理，应开独立 cleanup 阶段，并明确确认归档、删除或停止跟踪策略。

## 当前不应删除的内容

- 当前有效 `tests/`
- `app/bioinformatics/legacy/`
- `assets/icons/`
- `docs/handoff/`
- `docs/cleanup/`
- `docs/archive/legacy_handoff_20260513/`

这些内容可能支撑当前测试、模块边界、UI 启动、AI Gateway、词库接口、项目流程依赖、历史追溯或 handoff。后续清理必须先审计，再归档，最后才处理低风险删除。

## 后续建议开发顺序

1. Bioinformatics 用户可测试入口收敛。
2. Meta M4。
3. Vocabulary short-token hardening。
4. LabTools MVP。
5. UIShell 统一视觉。
6. Integration 阶段性合并验证。

## 本阶段边界

- 不开发新功能。
- 不修改业务代码。
- 不删除文件。
- 不移动文件。
- 不修改其他 worktree。
- 不处理 tracked logs。
- 不执行 `git push`。
