# Stage 0.4 Cache and Build Artifact Cleanup Report

日期：2026-05-13

范围：`/Users/changdali/Developer/biomedpilot v1.0/MainLine`

## 目标

在不修改业务功能、不删除当前测试、不移动或删除 legacy / handoff / archive 当前文件的前提下，清理低风险缓存和构建产物，并加固 `.gitignore`。

## 执行边界

- 未修改 `app/` 业务代码。
- 未删除 `tests/` 下任何当前有效测试。
- 未删除 `app/bioinformatics/legacy/`。
- 未删除 `assets/icons/` 或其他图标资源。
- 未删除 `docs/handoff/`、`docs/cleanup/`、`docs/archive/legacy_handoff_20260513/` 中的当前索引和报告。
- 未修改 Meta、Vocabulary、LabTools、AI、Integration 等其他 worktree。
- 未执行 `git push`。

## 实际删除的 ignored / untracked 低风险缓存

本阶段删除的文件均为 Git ignored 的本地缓存或测试缓存，删除前未被 Git 跟踪。

### 删除的目录

- `.pytest_cache/`
- `app/__pycache__/`
- `app/bioinformatics/__pycache__/`
- `app/bioinformatics/adapters/__pycache__/`
- `app/bioinformatics/download/__pycache__/`
- `app/bioinformatics/legacy/geo_processing/__pycache__/`
- `app/bioinformatics/legacy/geo_processing/detector/__pycache__/`
- `app/bioinformatics/legacy/geo_tool/__pycache__/`
- `app/bioinformatics/models/__pycache__/`
- `app/bioinformatics/pages/__pycache__/`
- `app/bioinformatics/reports/__pycache__/`
- `app/bioinformatics/results/__pycache__/`
- `app/bioinformatics/retrieval/__pycache__/`
- `app/bioinformatics/search_center/__pycache__/`
- `app/bioinformatics/services/__pycache__/`
- `app/bioinformatics/standard_assets/__pycache__/`
- `app/bioinformatics/tcga/__pycache__/`
- `app/meta_analysis/__pycache__/`
- `app/shared/__pycache__/`
- `app/shared/ai_gateway/__pycache__/`
- `app/shared/ai_gateway/logging/__pycache__/`
- `app/shared/ai_gateway/policies/__pycache__/`
- `app/shared/ai_gateway/providers/__pycache__/`
- `app/shared/data_center/__pycache__/`
- `app/shared/environment/__pycache__/`
- `app/shared/project_center/__pycache__/`
- `app/shared/query_intelligence/__pycache__/`
- `app/shared/query_intelligence/medical_terms/__pycache__/`
- `app/shared/settings/__pycache__/`
- `app/shared/storage/__pycache__/`
- `app/shared/task_center/__pycache__/`
- `app/shell/__pycache__/`
- `reporting/__pycache__/`
- `scripts/__pycache__/`
- `tests/__pycache__/`
- `tests/bioinformatics/__pycache__/`
- `tests/ui/__pycache__/`

### 未发现需删除的同类文件

- 未发现 `.mypy_cache/`。
- 未发现 `.ruff_cache/`。
- 未发现 `htmlcov/`。
- 未发现 `.coverage` 或 `.coverage.*`。
- 未发现 `.DS_Store`。
- 未发现 `*.tmp`、`*.bak`、`*.orig`。
- 未发现 tracked 的 `build/` 或 `dist/` 产物。
- 未发现超过 5 MB 的大文件。

## `.gitignore` 加固内容

本阶段补充和整理了以下规则：

- Python / pytest 缓存：`__pycache__/`、`*.py[cod]`、`*.pyo`、`.pytest_cache/`。
- 类型检查和 lint 缓存：`.mypy_cache/`、`.ruff_cache/`。
- 覆盖率输出：`.coverage`、`.coverage.*`、`htmlcov/`。
- tox / nox 环境：`.tox/`、`.nox/`。
- 本地虚拟环境：`.venv/`、`.venv-meta/`。
- 构建和打包产物：`dist/`、`build/`、`*.egg-info/`、`*.app/`、`*.dmg`、`*.pkg`。
- macOS 和编辑器临时文件：`.DS_Store`、`._*`、`*~`、`*.tmp`、`*.bak`、`*.orig`。
- 本地测试与运行输出：`test_inputs/`、`test_outputs/`、`tmp/`、`.tmp/`、`logs/**/*.log`、`logs/ai_gateway/*.jsonl`。
- 本地项目运行数据：`project_storage/**/*.json`、`project_storage/projects/*`、`project_storage/tasks/*`、`project_storage/reports/*`、`project_storage/data/*`、`project_storage/test_feedback/*`，并继续保留 `.gitkeep` 例外。

## 发现但未处理的 tracked 文件

以下文件已被 Git 跟踪，虽然看起来像历史日志或旧运行产物，但根据总开发手册和本阶段边界，本次不直接删除：

| 路径 | 状态 | 本阶段处理 |
| --- | --- | --- |
| `logs/validation/geo_random_recognition_audit.jsonl` | tracked 历史 validation log | 保留，列入后续人工确认。 |
| `archive/legacy_sources/model9/demo_projects/MP-2024-0007/logs/app.log` | tracked legacy demo project log | 保留，随 legacy archive 后续统一决策。 |

## 需要人工确认

- 是否将 tracked historical validation log 归档或停止跟踪。
- 是否在后续 archive / legacy 瘦身阶段处理 `archive/legacy_sources/` 中的 demo project runtime log。
- 是否进一步处理 `archive/legacy_sources/` 整体快照和 legacy 参考资料。本阶段未移动、未删除。

## 验收记录

- `python3 -m app.main --smoke-test`：通过。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：通过，`133 passed in 8.20s`。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`：通过，`264 passed in 2.78s`。
- `git diff --check`：通过。
- `git status --short --branch`：仅显示本阶段 `.gitignore` 修改和本报告新增。

测试运行会重新生成 ignored 的 Python cache；验收后已再次清理低风险 cache，最终工作区只保留本阶段文档和 `.gitignore` 变更。
