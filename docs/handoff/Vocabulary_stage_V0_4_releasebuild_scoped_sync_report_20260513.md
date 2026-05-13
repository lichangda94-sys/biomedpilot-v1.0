# Vocabulary Stage V0.4 ReleaseBuild Scoped Sync Report

日期：2026-05-13

工作区：`/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`

分支：`dev/release-internal-test`

Scoped sync 来源：`stable/mainline` / `15a40bd`

## 1. 前置文件读取

本阶段开始前已读取：

- `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- `/Users/changdali/Developer/biomedpilot v1.0/README_总说明.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/handoff/Global_Development_Manual.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/handoff/Vocabulary_stage_V0_3_mainline_scoped_merge_preflight_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/handoff/Vocabulary_stage_V0_2_integration_scoped_apply_report_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Vocabulary/docs/handoff/Vocabulary_stage_V0_1_scoped_merge_plan_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Vocabulary/docs/handoff/Vocabulary_stage_V0_1_resource_packaging_strategy_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Vocabulary/docs/handoff/Vocabulary_mainline_merge_checklist_20260513.md`

ReleaseBuild worktree 当前没有 `CODEX.md`，本阶段以全局开发手册、V0.1 scoped merge plan、V0.2 Integration 报告、V0.3 MainLine 报告和用户任务边界为准。

未发现本任务与总开发手册、V0.1 scoped merge plan、V0.2 Integration 报告或 V0.3 MainLine 报告冲突。

## 2. ReleaseBuild 初始状态

预检结果：

- 当前分支：`dev/release-internal-test`
- 初始 `git status --short --branch`：干净
- 初始 `data/medical_terms/`：不存在
- 初始 `scripts/package_app.py`：`COPY_DIRS` 不包含顶层 `data`，不会复制 `data/medical_terms/`
- 初始 `app/shared/query_intelligence/medical_terms/`：已有基础 shared vocabulary runtime code
- 初始 AI Gateway audit 单项测试：`4 passed in 0.30s`

## 3. Scoped Sync 来源

同步来源为 MainLine Stage V0.3 scoped commit：

- `15a40bd chore(vocabulary): apply scoped shared vocabulary and packaging resources`

本阶段没有 merge `stable/mainline` 整分支，没有 merge `dev/shared-vocabulary`，没有 merge `dev/integration`。

同步方式：

- 按路径从 `stable/mainline` 执行 scoped checkout。
- 只取 V0.3 已验证的 shared vocabulary baseline、safe resources、tests、docs 和 packaging resource copy。
- 不 cherry-pick 大提交。

## 4. 实际同步路径

实际同步到 ReleaseBuild 的路径：

- `app/shared/query_intelligence/medical_terms/**`
- `app/shared/query_intelligence/query_intelligence_models.py`
- `app/shared/query_intelligence/query_intelligence_service.py`
- `data/package_manifest.json`
- `data/medical_terms/mini_medical_terms_index.json`
- `data/medical_terms/zh_term_overrides.json`
- `data/medical_terms/source_metadata.json`
- `data/medical_terms/license_attribution.md`
- `data/medical_terms/coverage_audit_report.json`
- `data/medical_terms/reference_checklists/**`
- `scripts/update_medical_term_index.py`
- `scripts/audit_medical_vocabulary_coverage.py`
- `scripts/package_app.py`
- `tests/shared/test_medical_term_lookup.py`
- `tests/shared/test_medical_term_index_runtime_strategy.py`
- `tests/shared/test_medical_terms_sqlite_index_build.py`
- `tests/shared/test_medical_vocabulary_*.py`
- `tests/shared/test_query_intelligence_service.py`
- `tests/shared/test_vocabulary_stage_v0_1_merge_readiness.py`
- `tests/test_package_app.py`
- `docs/handoff/Vocabulary_*20260513.md`
- `docs/medical_term_index_contract.md`
- `docs/shared_medical_vocabulary_*.md`
- `docs/stage_*medical_vocabulary*.md`
- `docs/vocabulary/README.md`
- 本报告：`docs/handoff/Vocabulary_stage_V0_4_releasebuild_scoped_sync_report_20260513.md`

## 5. 明确排除路径

本阶段明确排除：

- `app/bioinformatics/**` 业务流程修改
- `app/meta_analysis/**` 业务流程修改
- `app/ai/**` AI Gateway 行为修改
- `app/shell/**` 或 UI 业务逻辑修改
- `tests/ui/**`
- `tests/bioinformatics/**`
- `tests/meta_analysis/**`
- AI audit 文档修复
- MainLine 通用 handoff / cleanup / archive 文件
- `data/medical_terms/medical_terms_index.sqlite`
- `data/medical_terms/medical_terms_index_build_report.json`
- `data/medical_terms/raw/**`
- `dist/**`、`build/**`、runtime caches、runtime logs

## 6. Merge 声明

- 使用整分支 merge：否。
- merge `dev/shared-vocabulary`：否。
- merge `stable/mainline`：否。
- merge `dev/integration`：否。
- cherry-pick 大提交：否。
- 删除文件：否。

## 7. Worktree 修改范围

- 修改 ReleaseBuild：是。
- 修改 MainLine：否。
- 修改 Vocabulary：否。
- 修改 Integration：否。
- 修改 Bioinformatics / Meta / AI / UIShell / LabTools worktree：否。

## 8. Packaging 资源复制同步

已将 MainLine V0.3 验证过的 packaging 资源复制同步到 ReleaseBuild：

- `scripts/package_app.py` 新增 `PACKAGE_RESOURCE_FILES`
- `scripts/package_app.py` 新增 `PACKAGE_RESOURCE_DIRS`
- `build_launcher_app()` 调用 `_copy_package_resources()`
- 只复制 `data/medical_terms` 默认安全子集
- 不改变 app 入口
- 不改变 launcher 行为
- 不引入外部依赖
- 不改变 Bioinformatics / Meta 业务流程

`tests/test_package_app.py` 验证：

- packaged app 中存在 `mini_medical_terms_index.json`
- packaged app 中存在 `zh_term_overrides.json`
- packaged app 中存在 `source_metadata.json`
- packaged app 中存在 `license_attribution.md`
- packaged app 中存在 `reference_checklists/`
- packaged app 中不存在 `medical_terms_index.sqlite`
- packaged app 中不存在 `raw/`

## 9. `data/medical_terms/` 包内资源验证结果

源码和测试运行时：

- `data/medical_terms/mini_medical_terms_index.json` 存在
- `data/medical_terms/zh_term_overrides.json` 存在
- `data/medical_terms/source_metadata.json` 存在
- `data/medical_terms/license_attribution.md` 存在
- `data/medical_terms/reference_checklists/` 存在
- `medical_terms_index.sqlite` 不存在
- `raw/` 不存在

打包后路径：

`/tmp/biomedpilot-vocab-v0-4-package/BioMedPilot.app/Contents/Resources/app/data/medical_terms/`

包内验证：

- `mini_medical_terms_index.json` 存在
- `zh_term_overrides.json` 存在
- `source_metadata.json` 存在
- `license_attribution.md` 存在
- `reference_checklists/` 存在
- `medical_terms_index.sqlite` 不存在
- `raw/` 不存在
- `packaged_medical_terms_resources=pass`

## 10. SQLite 运行依赖结论

本阶段没有提交 `medical_terms_index.sqlite`。

结论：

- ReleaseBuild 运行不硬依赖 SQLite。
- SQLite 缺失时 JSON fallback 可用。
- `active_index_status()` 显示 `full_index_available=False`、`mini_index_available=True`。
- `lookup_medical_terms("脑胶质瘤", target_context="bioinformatics")` 使用 `zh_term_overrides`、`mini_medical_terms_index` 和 registry fallback。
- SQLite 仍是 optional derived resource / future ReleaseBuild artifact candidate。
- 如果后续决定打包或跟踪 SQLite，仍需补充 checksum、生成命令、schema、terms count 和 optional status。

## 11. Bioinformatics / Meta 边界验证

Bioinformatics：

- Bioinformatics context 不返回 PubMed candidates。
- Bioinformatics 仍面向 GEO / TCGA / GTEx / local expression data 语境。
- Meta-only outcome / effect measure / PICO terms 不进入 Bioinformatics 主检索能力。
- 本阶段未把 PubMed 接入 Bioinformatics。

Meta Analysis：

- Meta context 不返回 GEO / TCGA / GTEx candidates。
- PubMed / MeSH query 保持 draft 语境。
- 本阶段未开发 Meta 检索执行、筛选、统计或报告流程。
- `confirmed` / `user edited` 检索治理状态仍是后续 Meta 任务。

## 12. AI / 网络 / 隐私边界验证

- 未直接调用 Ollama。
- 未调用外部 AI。
- 未执行真实网络检索。
- 未执行 ontology 下载。
- `scripts/update_medical_term_index.py` 仍要求显式 `--download-sources` 才允许下载 ontology。
- 未新增 raw prompt / raw response 记录。
- 未新增用户输入全文默认持久化。
- 未修复或修改 AI Gateway audit 文档。

## 13. ReleaseBuild Package Smoke 结果

已执行：

```bash
QT_QPA_PLATFORM=offscreen python3 scripts/package_app.py --output-dir /tmp/biomedpilot-vocab-v0-4-package --smoke-test
```

结果：

- package build：通过
- packaged launcher smoke：通过
- `launch_mode=packaged-local-python`
- `network_downloads=false`
- `app_root=/private/tmp/biomedpilot-vocab-v0-4-package/BioMedPilot.app/Contents/Resources/app`
- `packaged_medical_terms_resources=pass`

## 14. Packaged App CLI Smoke 结果

包内 launcher 输出包含：

- `BioMedPilot / 医研智析`
- `app_version=0.1.0-internal-beta`
- `app_channel=Developer Preview / testing`
- `launch_mode=packaged-local-python`
- `workspace_entries=2`
- `bioinformatics_features=5`
- `meta_analysis_features=9`
- `pyside6_available=True`

## 15. 测试结果

已执行：

```bash
git status --short --branch
git diff --check
git diff --cached --check
python3 -m app.main --smoke-test
python3 - <<'PY'
from scripts.audit_medical_vocabulary_coverage import build_coverage_audit_report
report = build_coverage_audit_report()
overall = report["overall"]
print(overall["quality_gate_status"])
PY
QT_QPA_PLATFORM=offscreen python3 -m pytest \
  tests/shared/test_medical_term_lookup.py \
  tests/shared/test_medical_term_index_runtime_strategy.py \
  tests/shared/test_medical_terms_sqlite_index_build.py \
  tests/shared/test_medical_vocabulary_consolidation_regression.py \
  tests/shared/test_query_intelligence_service.py \
  tests/shared/test_vocabulary_stage_v0_1_merge_readiness.py \
  tests/bioinformatics/test_bio_query_adapter.py \
  tests/bioinformatics/test_search_center_router.py \
  tests/meta_analysis/test_mainline_meta_contract.py \
  tests/test_package_app.py \
  -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/shared -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
QT_QPA_PLATFORM=offscreen python3 scripts/package_app.py --output-dir /tmp/biomedpilot-vocab-v0-4-package --smoke-test
```

结果：

- `git diff --check`：通过。
- `git diff --cached --check`：通过。
- app smoke：通过。
- coverage audit 只读：`quality_gate_status=pass`，`covered=621/621`，`weighted_coverage_rate=1.0`，`core_covered=533/533`。
- 最小相关 pytest + packaging tests：`75 passed in 8.32s`。
- `tests/shared -q`：`225 passed in 26.56s`。
- `tests/bioinformatics -q`：`264 passed in 4.02s`。
- `tests/meta_analysis -q`：`3 passed in 0.45s`。
- `tests/ui -q`：`6 failed, 40 passed, 87 skipped in 2.62s`。
- ReleaseBuild package smoke：通过。
- packaged app CLI smoke：通过。
- packaged app resource presence check：通过。

## 16. `tests/shared` 结果

ReleaseBuild `tests/shared -q` 通过：`225 passed in 26.56s`。

MainLine V0.3 记录的 AI audit 文档缺失失败没有在 ReleaseBuild 复现。ReleaseBuild 初始 AI Gateway audit 单项测试也通过：`4 passed in 0.30s`。

本阶段未修改 AI Gateway 行为，也未修复 AI audit 文档。

## 17. `tests/ui` 非词库遗留失败

`tests/ui -q` 有 6 个失败：

- `tests/ui/test_app_identity.py::test_main_window_uses_app_icon`
- `tests/ui/test_login_page.py::test_main_window_starts_at_login_and_enters_dashboard`
- `tests/ui/test_login_page.py::test_settings_page_displays_icon_asset_details`
- `tests/ui/test_module_selection.py::test_main_window_logout_returns_to_login_and_clears_session`
- `tests/ui/test_module_selection.py::test_main_window_module_buttons_enter_existing_workspaces`
- `tests/ui/test_module_selection.py::test_main_window_open_meta_project_binds_workspace_project_dir`

共同错误：

`TypeError: BioinformaticsWorkspaceWidget() takes no arguments`

结论：

- 该失败与 V0.2 Integration 已记录的 UI / Bioinformatics workspace 构造接口失败同源。
- 失败发生在 UI shell 初始化 `BioinformaticsWorkspaceWidget(on_back=...)`。
- 本阶段没有修改 UI、Bioinformatics workspace 或业务流程。
- 该失败不是 Vocabulary scoped sync 或 packaging resource copy 引入的词库失败。
- 按任务边界，本阶段不跨 UIShell/Bioinformatics 修复。

## 18. 遗留问题

- ReleaseBuild `tests/ui` 仍有 UI / Bioinformatics workspace 构造接口失败，需要 UIShell 或 Bioinformatics scoped 任务处理。
- `medical_terms_index.sqlite` 仍未进入 ReleaseBuild；如后续决定包含，需要明确 checksum 和 artifact policy。
- Meta `confirmed` / `user edited` 检索治理状态仍需 Meta 后续任务处理。
- Bioinformatics 内部 TCGA / GTEx / tissue fallback 去重仍需后续 Bioinformatics 或 Integration 任务处理。
- `dev/shared-vocabulary` 仍不得整分支合并 MainLine 或 ReleaseBuild。

## 19. 是否建议进入正式 Internal Beta Package Rebuild

建议进入 internal beta package rebuild / final vocabulary baseline report，但前提是：

- 本次 ReleaseBuild scoped sync commit 合入后，继续使用 scoped release packaging 流程。
- 不带入 SQLite 或 raw ontology。
- 不把 `tests/ui` 的非词库失败包装成 Vocabulary 风险。
- 如要发布更完整的 UI-gated package，应先由 UIShell/Bioinformatics 任务处理 `BioinformaticsWorkspaceWidget(on_back=...)` 失败。

## 20. 下一阶段建议

建议下一阶段：

1. 生成 final vocabulary baseline report，汇总 V0.0-V0.4。
2. 如需正式 internal beta package rebuild，使用 ReleaseBuild 当前 scoped baseline 构建。
3. 单独开 UIShell/Bioinformatics scoped task 修复 `BioinformaticsWorkspaceWidget(on_back=...)` UI 初始化失败。
4. 单独开 Meta task 处理 `confirmed` / `user edited` 检索治理状态。
5. 继续将 SQLite 作为 optional artifact，不作为运行硬依赖。

## 21. Vocabulary Handoff Summary

V0.0 / predevelopment audit：

- Commit：`ee8954c`
- 产物：`docs/handoff/Vocabulary_predevelopment_blocker_audit_20260513.md`
- 结论：`dev/shared-vocabulary` 不能整分支直合 MainLine；packaging 不复制 `data/medical_terms/` 是 Blocking。

V0.1 / strategy：

- Commit：`9c73d6a`
- 产物：scoped merge plan、resource packaging strategy、MainLine merge checklist、Vocabulary README、merge readiness tests。
- 结论：只允许 scoped vocabulary merge；SQLite 为 optional derived resource。

V0.2 / Integration：

- Commit：`ba41dca`
- 产物：Integration scoped apply、packaging resource copy 修复、V0.2 report。
- 结论：Integration 可只带入词库路径；package safe subset 验证通过；Integration `tests/ui` 有非词库 UI/Bioinformatics 构造接口失败。

V0.3 / MainLine：

- Commit：`15a40bd`
- 产物：MainLine scoped apply、packaging resource copy、V0.3 report。
- 结论：MainLine scoped vocabulary baseline 已合入；`tests/ui` 在 MainLine 通过；`tests/shared` 有非词库 AI audit 文档缺失失败。

V0.4 / ReleaseBuild：

- Commit：本报告所在 ReleaseBuild scoped sync commit；精确 hash 见最终任务回复。
- 产物：ReleaseBuild scoped sync、package smoke、packaged resource presence check、V0.4 report。
- 结论：ReleaseBuild package 中包含 `data/medical_terms` 默认安全子集，不包含 SQLite/raw ontology。

当前资源策略：

- `zh_term_overrides.json`：人工维护源数据。
- `mini_medical_terms_index.json`：可提交 runtime source / normalized artifact。
- `source_metadata.json`、`license_attribution.md`、`reference_checklists/`：进入 Git 和 package safe subset。
- `coverage_audit_report.json`：审计快照，当前随 scoped baseline 进入 ReleaseBuild。

当前 packaging 策略：

- 复制 `data/medical_terms` 默认安全子集。
- 默认不复制 SQLite。
- 默认不复制 raw ontology。
- package smoke 必须检查包内资源存在。

当前 SQLite 策略：

- `medical_terms_index.sqlite` 是 optional derived resource。
- 缺失时必须 JSON fallback。
- 不作为 MainLine / ReleaseBuild 运行硬依赖。
- 进入包或 Git 前必须补 checksum、schema、生成命令、term count 和 artifact policy。

禁止整分支合并结论：

- 仍禁止整分支合并 `dev/shared-vocabulary`。
- 仍禁止整分支合并 MainLine 到 ReleaseBuild。
- 仍禁止整分支合并 Integration 到 ReleaseBuild。
- 后续只允许 scoped patch / scoped checkout。

Bioinformatics / Meta / AI 边界：

- Bioinformatics 不得执行 PubMed 检索。
- Meta 不得触发 GEO / TCGA / GTEx 生信流程。
- Vocabulary 不直接调用 Ollama、外部 AI 或真实网络。
- Ontology 下载默认关闭，必须显式开启。
- 不记录 raw prompt / raw response。

下一步建议：

- 进入 final vocabulary baseline report。
- 如需 internal beta package rebuild，可基于 ReleaseBuild scoped baseline 执行。
- 将 UI/Bioinformatics 构造接口失败和 Meta confirmed/user edited 治理状态作为独立后续任务处理。
