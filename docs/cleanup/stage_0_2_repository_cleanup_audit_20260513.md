# Stage 0.2 Repository Cleanup Audit

日期：2026-05-13

范围：`/Users/changdali/Developer/biomedpilot v1.0/MainLine`

目标：只形成旧仓库内容清点与瘦身建议，不删除业务文件，不移动 legacy，不修改功能代码。

## 执行摘要

- 当前 MainLine 工作区的核心运行面是桌面 shell、Bioinformatics 稳定流程、Meta 最小入口、Shared 接口、AI Gateway、词库接口和当前测试套件。
- `tests/` 中有 134 个文件，其中当前有效测试主要集中在 `tests/ui`、`tests/bioinformatics`、`tests/shared`、`tests/meta_analysis`、`tests/integration`、`tests/architecture`、`tests/reporting` 和根目录 entry/package 测试。第一阶段不建议删除这些测试。
- `docs/` 中有 161 个文件，其中约 51 个位于 `docs/meta_dev_reports/`，大量 `stage_*`、`*_audit`、`*_report` 属于历史阶段记录，可进入归档计划。
- `app/bioinformatics/legacy/` 有 128 个文件，约 2.1 MB。虽然是 legacy，但仍有 MainLine import 或动态调用，第一阶段只能标记和清单化，不能删除。
- `archive/` 有 453 个 tracked 文件，约 10 MB，主要是旧项目快照和重复候选清单。它是瘦身优先候选，但应先确认是否已被 v1.0 迁移 bundle 或外部 archive 覆盖。
- 当前发现的缓存和本地生成物包括 `__pycache__/`、`.pytest_cache/`、`.pyc`，均已被 `.gitignore` 覆盖且未被 Git 跟踪。
- 未发现 tracked 的 `build/`、`dist/`、`.DS_Store`、`.bak`、`.tmp`、`.orig`、冲突副本或明显无引用备份文件。

## 扫描依据

本次审计扫描了：

- `tests/`
- `docs/`
- `app/bioinformatics/legacy/`
- `archive/`
- `build` / `dist` / `cache` / `.pytest_cache` / `__pycache__`
- 临时、备份、冲突副本命名模式
- `project_storage`、`logs`、`data`、`examples`、`assets`、`config`
- legacy import / reference：`rg "bioinformatics\\.legacy|app\\.bioinformatics\\.legacy|legacy/"`

## A. 必须保留

这些内容支撑当前测试、模块边界、UI 启动、AI Gateway、词库接口和项目流程，第一阶段不应删除或移动。

| 路径 | 原因 |
| --- | --- |
| `app/` 非 legacy 主代码 | 当前桌面 shell、Bioinformatics 流程、Meta 最小入口、Shared 服务、AI Gateway 都从这里启动。 |
| `reporting/` | `app/bioinformatics/reports/project_report_builder.py` 和报告测试依赖。 |
| `scripts/` | 打包、测试、词库审计和项目辅助脚本入口。 |
| `assets/icons/` | UI 启动、登录页、模块选择、项目首页图标测试直接依赖。 |
| `config/bioinformatics/` | Bioinformatics 默认参数和 package requirement 配置。 |
| `data/package_manifest.json` | packaging / manifest 相关测试依赖。 |
| `tests/ui/` | 当前 MainLine UI 启动与模块选择验证。 |
| `tests/bioinformatics/` | 当前 Bioinformatics 稳定流程和服务测试。 |
| `tests/shared/` | AI Gateway、Project/Data/Task Center、词库 query intelligence 接口测试。 |
| `tests/meta_analysis/` | MainLine Meta 最小 contract 测试。 |
| `tests/integration/` | workspace switching 集成测试。 |
| `tests/architecture/` | 模块边界和 legacy 禁止 import 规则测试。 |
| `tests/reporting/` | 标准报告输出测试。 |
| `tests/test_*entry.py`、`tests/test_package_app.py`、`tests/test_module_boundary_contract.py` | 应用入口、打包入口、模块边界基础测试。 |
| `tests/fixtures/` | Meta 文献导入与统计参考 fixture，不能在第一阶段删除。 |
| `.gitignore` | 已覆盖主要 Python 缓存、pytest cache、build/dist、项目本地 storage。 |

## B. 建议保留但可移动

这些内容不是运行时核心，但对交接、当前控制面和用户测试仍有价值。建议后续统一移动到 v1.0 主目录的 `00_HandoffDocs/` 或 `01_ProjectControl/`，移动前保持路径引用清晰。

| 路径 | 建议 |
| --- | --- |
| `README.md` | 保留在 MainLine 根目录，作为仓库入口说明。 |
| `CODEX.md` | 保留在 MainLine 根目录，作为工作区边界说明。 |
| `docs/architecture.md` | 可保留在 `docs/`，当前架构边界入口。 |
| `docs/module_boundaries.md` | 可保留，描述 legacy snapshot 和 active shell 边界。 |
| `docs/module_boundary_contract.md` | 可保留，配合 `tests/test_module_boundary_contract.py` 和 architecture 测试。 |
| `docs/branch_development_rules.md` | 建议移动到项目控制文档区，仍有分支治理价值。 |
| `docs/packaging.md` | 建议保留，打包工作仍依赖。 |
| `docs/user_testing/` | 建议保留或移动到 handoff/testing 文档区，属于当前 tester guide。 |
| `docs/bioinformatics_developer_preview_status.md` | 建议保留，当前 Developer Preview 状态说明。 |
| `docs/bioinformatics_asset_contracts.md` | 建议保留，结果和资产 contract 仍用于开发判断。 |
| `docs/bioinformatics_task_contracts.md` | 建议保留，Task Center 合同说明。 |
| `docs/mainline_meta_analysis_boundary.md` | 建议保留，MainLine 与 Meta 分支边界说明。 |
| `docs/mainline_shared_vocabulary_boundary.md` | 建议保留，MainLine 与 Vocabulary 分支边界说明。 |
| `docs/ai_gateway_internal_design_v1.md`、`docs/ai_gateway_desktop_ai_module_v1.md`、`docs/ai_gateway_ollama_provider_v1.md` | 建议保留或移动到 AI handoff 区，当前 AI Gateway 约束仍有价值。 |
| `docs/meta_pubmed_candidates_handoff.md` | 文件名包含 handoff，第一阶段保留。 |

## C. 可归档

这些内容主要是历史阶段记录、旧迁移记录、旧 UI 快照或 legacy 参考资料。建议归档到 v1.0 主目录 `Archive/` 或单独文档包，而不是直接删除。

| 路径 / 模式 | 观察 | 建议 |
| --- | --- | --- |
| `docs/stage_*.md` | 多个 Bioinformatics / UI / Meta 阶段报告。 | 归档到 `Archive/docs_stage_reports/`，保留索引。 |
| `docs/*_audit.md`、`docs/*_audit_report.md` | 多数为阶段审计或旧 gap audit。 | 归档，当前仍被引用的边界审计除外。 |
| `docs/*_report.md` | 大量阶段报告，不是当前运行依赖。 | 归档，保留当前状态类报告。 |
| `docs/meta_dev_reports/` | 约 51 个 Meta 阶段开发报告。 | MainLine 可归档；Meta worktree 可另行决定是否保留。 |
| `docs/migration/` | 旧迁移清单和 merge log。 | 可归档；v1.0 当前迁移报告在主目录 `01_ProjectControl/`，不要删除。 |
| `archive/legacy_sources/` | 旧 bioinformatics_project 和 model9 快照，约 10 MB archive 的主要来源。 | 高优先级归档候选；先确认 bundle/外部 archive 覆盖后再从 MainLine 移出。 |
| `archive/duplicate_candidates/` | model9 重复候选清单。 | 可归档，适合作为旧合并审计附件。 |
| `archive/old_docs/` | 旧文档归档区。 | 继续留在 archive 或移出 MainLine。 |
| `app/bioinformatics/legacy/tests/` | legacy 自带测试，不属于当前 `pytest tests/...` 套件。 | 随 `app/bioinformatics/legacy/` 整体归档评估，不单独删除。 |
| `app/bioinformatics/legacy/docs/` | legacy 内部历史文档。 | 随 legacy 整体归档评估。 |

## D. 可删除

这些是缓存、构建产物、本地运行产物或无引用临时文件。第一阶段只记录建议；如果后续要删除，应单独提交并先确认没有 tracked 文件混入。

| 路径 / 模式 | 当前状态 | 建议 |
| --- | --- | --- |
| `.pytest_cache/` | ignored，未 tracked。 | 可本地删除，不需要提交。 |
| `**/__pycache__/` | ignored，未 tracked。 | 可本地删除，不需要提交。 |
| `*.pyc` | ignored，未 tracked。 | 可本地删除，不需要提交。 |
| `build/` | `.gitignore` 已覆盖；当前未发现 tracked build 产物。 | 保持忽略。 |
| `dist/` | `.gitignore` 已覆盖；当前未发现 tracked dist 产物。 | 保持忽略。 |
| `.DS_Store` | `.gitignore` 已覆盖；当前未发现 tracked 文件。 | 保持忽略。 |
| `*.bak`、`*.tmp`、`*.orig`、`*conflict*`、`* copy*`、`*副本*`、`*冲突*` | 未发现匹配文件。 | 无需操作。 |
| `project_storage/projects/*`、`project_storage/tasks/*`、`project_storage/reports/*`、`project_storage/data/*`、`project_storage/test_feedback/*` | `.gitignore` 已覆盖；当前仅 `.gitkeep` tracked。 | 保持忽略，保留 `.gitkeep`。 |
| `logs/validation/geo_random_recognition_audit.jsonl` | tracked 的历史 validation log。 | 可归档或删除候选；建议先确认是否仍需作为 audit evidence。 |
| `archive/legacy_sources/model9/demo_projects/MP-2024-0007/logs/app.log` | tracked，位于 legacy archive demo project。 | 随 archive 归档；若保留 archive，建议删除该 `.log` 并在后续 cleanup 中补 ignore 规则。 |

`.gitignore` 当前已覆盖主要缓存和构建产物：

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
dist/
build/
.DS_Store
test_inputs/
project_storage/projects/*
project_storage/tasks/*
project_storage/reports/*
project_storage/data/*
project_storage/test_feedback/*
```

后续可考虑追加建议，不在本阶段直接修改：

```gitignore
logs/**/*.log
logs/**/*.jsonl
archive/**/logs/*.log
```

注意：`logs/validation/geo_random_recognition_audit.jsonl` 当前已 tracked，单纯加入 `.gitignore` 不会停止跟踪，需要后续单独决策。

## E. 需要人工确认

这些内容看起来旧、重复或可归档，但仍可能被 import、测试或文档边界依赖。第一阶段不得删除。

| 路径 | 风险 / 依赖 |
| --- | --- |
| `app/bioinformatics/legacy/geo_processing/module1_contracts.py` | `app/bioinformatics/project_workspace_binding.py` 直接 import `build_download_plan_payload`。 |
| `app/bioinformatics/legacy/geo_tool/geo_pipeline/download.py` | `app/bioinformatics/download/dataset_download_service.py` 通过 `importlib.import_module(...)` 动态调用。 |
| `app/bioinformatics/legacy/geo_tool/geo_info_fetcher.py` | `app/bioinformatics/retrieval/geo_search_service.py` 和 `app/bioinformatics/workflow_pages.py` 使用。 |
| `app/bioinformatics/adapters/legacy_geo.py` | active adapter 中仍标记 legacy GEO source。 |
| `app/shared/feature_availability.py` 中 legacy source 字段 | UI 功能状态展示仍引用 legacy 路径作为历史来源。 |
| `tests/shared/test_ai_gateway_ollama_migration_audit.py` | 明确检查 legacy GEO tool 里的 Ollama 直接调用路径，用于迁移审计。 |
| `tests/architecture/test_module_retrieval_boundaries.py` | 检查 legacy 禁止 import / 模块边界，不应删除相关边界文档和测试。 |
| `docs/module_boundary_contract.md` | 明确列出 legacy 禁止 import 或边界，仍有架构约束作用。 |
| `archive/legacy_sources/` | 内容重复但可能是旧仓库合并证据；需确认外部 bundle 和 v1.0 Archive 是否已覆盖。 |
| `examples/meta_analysis_*` | 属于 MainLine 内 Meta 最小入口和测试样例，虽然不是 Bioinformatics 主线，但可能被 Meta/测试文档使用。 |
| `assets/icons/app/*.icns`、`assets/icons/*_sheet.png` | 体积较大但 UI 测试和应用身份依赖；不能作为构建产物删除。 |

## 建议的后续阶段

1. Stage 0.3：只删除本地 ignored 缓存，不提交业务 diff。
2. Stage 0.4：把 `docs/stage_*`、`docs/meta_dev_reports/`、`docs/migration/` 迁入主目录 `Archive/docs/`，生成索引。
3. Stage 0.5：确认 `archive/legacy_sources/` 是否已被迁移 bundle 覆盖；若覆盖，移出 MainLine 或压缩到主目录 Archive。
4. Stage 0.6：拆除 active code 对 `app/bioinformatics/legacy/` 的剩余 import，完成替代后再评估 legacy 整体归档。
5. Stage 0.7：单独处理 tracked logs：`logs/validation/geo_random_recognition_audit.jsonl` 和 legacy demo `app.log`。

## 第一阶段禁止删除清单

- 不删除 `tests/bioinformatics/`
- 不删除 `tests/ui/`
- 不删除 `tests/shared/`
- 不删除 `tests/meta_analysis/`
- 不删除 `tests/integration/`
- 不删除 `tests/architecture/`
- 不删除 handoff / 迁移报告 / 当前总控文档
- 不删除 `app/bioinformatics/legacy/`
- 不删除 UI icon assets
- 不删除 AI Gateway、词库接口、Project/Data/Task Center 相关测试和实现
