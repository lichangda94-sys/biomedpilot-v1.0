# Vocabulary Stage V0.3 MainLine Scoped Merge Preflight

日期：2026-05-13

工作区：`/Users/changdali/Developer/biomedpilot v1.0/MainLine`

分支：`stable/mainline`

初始 HEAD：`d43cae4`

Scoped apply 来源：`dev/integration` / `ba41dca`，该提交已完成 Stage V0.2 Integration scoped apply 验证。

## 1. 前置文件读取

本阶段开始前已读取：

- `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- `/Users/changdali/Developer/biomedpilot v1.0/README_总说明.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/handoff/Global_Development_Manual.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/CODEX.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Vocabulary/docs/handoff/Vocabulary_predevelopment_blocker_audit_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Vocabulary/docs/handoff/Vocabulary_stage_V0_1_scoped_merge_plan_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Vocabulary/docs/handoff/Vocabulary_stage_V0_1_resource_packaging_strategy_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Vocabulary/docs/handoff/Vocabulary_mainline_merge_checklist_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Vocabulary/README.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/handoff/Vocabulary_stage_V0_2_integration_scoped_apply_report_20260513.md`

未发现本任务与总开发手册、V0.1 scoped merge plan 或 V0.2 Integration 报告冲突。

MainLine `CODEX.md` 提醒不要提交 shared vocabulary 大资产。本阶段按 V0.1/V0.2 的安全子集执行：不带入 SQLite、raw ontology、downloaded ontology source 或 full ontology dump。

## 2. MainLine 初始状态

预检结果：

- 当前分支：`stable/mainline`
- 初始 `git status --short --branch`：干净
- 初始 `data/medical_terms/`：不存在
- 初始 `data/package_manifest.json`：存在，但没有完整 `data/medical_terms/` runtime resources
- 初始 `scripts/package_app.py`：`COPY_DIRS` 不包含顶层 `data`，不会复制 `data/medical_terms/`
- 初始 `tests/ui -q`：`139 passed in 8.15s`

MainLine 当前已存在 `app/shared/query_intelligence/medical_terms/` 基础代码目录，但缺少 V0.2 验证过的资源、覆盖率审计、SQLite optional fallback hardening、context isolation 增强测试和 packaging resource copy。

## 3. Scoped Apply 来源

本阶段没有 merge `dev/shared-vocabulary`，也没有 merge `dev/integration` 整分支。

实际使用方式：

- 从 `dev/integration` 按路径执行 scoped checkout。
- 只选择 V0.1/V0.2 允许的 shared vocabulary、resource、test、documentation 和 packaging resource copy 路径。
- 没有 cherry-pick 大提交。
- 没有带入 MainLine handoff / cleanup / archive 删除。

## 4. 实际应用路径

实际应用到 MainLine 的路径：

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
- 本报告：`docs/handoff/Vocabulary_stage_V0_3_mainline_scoped_merge_preflight_20260513.md`

## 5. 明确排除路径

本阶段明确排除：

- `app/bioinformatics/**` 业务流程修改
- `app/meta_analysis/**` 业务流程修改
- `app/ai/**` AI Gateway 行为修改
- `app/shell/**` 或 UI 业务逻辑修改
- `tests/ui/**`
- `tests/bioinformatics/**`
- `tests/meta_analysis/**`
- `docs/handoff/Global_Development_Manual.md` 删除或修改
- `docs/handoff/MainLine_current_baseline_20260513.md` 删除
- `docs/cleanup/**` 删除
- `docs/archive/**` 删除
- `docs/ui/**` 删除
- `docs/architecture/**` 删除
- `data/medical_terms/medical_terms_index.sqlite`
- `data/medical_terms/medical_terms_index_build_report.json`
- `data/medical_terms/raw/**`
- `dist/**`、`build/**`、runtime caches、runtime logs

## 6. Merge 声明

- 使用整分支 merge：否。
- merge `dev/shared-vocabulary`：否。
- merge `dev/integration`：否。
- cherry-pick 大提交：否。
- 删除 MainLine handoff / cleanup / archive 文件：否。

## 7. Worktree 修改范围

- 修改 MainLine：是。
- 修改 Vocabulary：否。
- 修改 Integration：否。
- 修改 ReleaseBuild：否。
- 修改 Bioinformatics / Meta / AI / UIShell / LabTools worktree：否。

## 8. Packaging 资源复制同步

已将 V0.2 Integration 验证过的最小 packaging 修复同步到 MainLine：

- `scripts/package_app.py` 新增 `PACKAGE_RESOURCE_FILES`
- `scripts/package_app.py` 新增 `PACKAGE_RESOURCE_DIRS`
- `build_launcher_app()` 调用 `_copy_package_resources()`
- 只复制 `data/medical_terms` 默认安全子集
- 不改变 app 入口
- 不改变 launcher 行为
- 不引入外部依赖
- 不改变 Bioinformatics / Meta 业务流程

`tests/test_package_app.py` 已新增 package resource presence 断言：

- packaged app 中存在 `mini_medical_terms_index.json`
- packaged app 中存在 `zh_term_overrides.json`
- packaged app 中存在 `source_metadata.json`
- packaged app 中存在 `license_attribution.md`
- packaged app 中存在 `reference_checklists/`
- packaged app 中不存在 `medical_terms_index.sqlite`
- packaged app 中不存在 `raw/`

## 9. `data/medical_terms/` 包内资源策略

默认包内安全子集：

- `data/medical_terms/mini_medical_terms_index.json`
- `data/medical_terms/zh_term_overrides.json`
- `data/medical_terms/source_metadata.json`
- `data/medical_terms/license_attribution.md`
- `data/medical_terms/reference_checklists/`

默认不进入包：

- `data/medical_terms/medical_terms_index.sqlite`
- `data/medical_terms/medical_terms_index_build_report.json`
- `data/medical_terms/raw/**`
- full ontology source files

本阶段 package CLI smoke 已验证包内路径为：

`<BioMedPilot.app>/Contents/Resources/app/data/medical_terms/`

该路径由 packaged resource root 相对定位，不依赖开发机绝对路径。

## 10. SQLite 运行依赖结论

本阶段没有提交 `medical_terms_index.sqlite`。

结论：

- MainLine 运行不硬依赖 SQLite。
- SQLite 缺失时 JSON fallback 可用。
- `active_index_status()` 显示 `full_index_available=False`、`mini_index_available=True`。
- `lookup_medical_terms("脑胶质瘤", target_context="bioinformatics")` 使用 `zh_term_overrides`、`mini_medical_terms_index` 和 registry fallback。
- SQLite 仍是 optional derived resource / ReleaseBuild artifact candidate。
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

## 13. 测试结果

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
QT_QPA_PLATFORM=offscreen python3 scripts/package_app.py --output-dir /tmp/biomedpilot-vocab-v0-3-package --smoke-test
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/shared -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

结果：

- `git diff --check`：通过。
- `git diff --cached --check`：通过。
- app smoke：通过。
- coverage audit 只读：`quality_gate_status=pass`，`covered=621/621`，`weighted_coverage_rate=1.0`，`core_covered=533/533`。
- 最小相关 pytest + packaging tests：`75 passed in 8.39s`。
- packaged app smoke：通过。
- packaged resource check：`packaged_medical_terms_resources=pass`。
- `tests/bioinformatics -q`：`264 passed in 3.73s`。
- `tests/meta_analysis -q`：`3 passed in 0.50s`。
- `tests/ui -q`：`139 passed in 8.45s`。
- `tests/shared -q`：`2 failed, 223 passed in 26.01s`。

## 14. `tests/ui` 结果

MainLine 初始 `tests/ui -q` 为 `139 passed in 8.15s`。

MainLine scoped apply 后 `tests/ui -q` 为 `139 passed in 8.45s`。

V0.2 Integration 中记录的 `BioinformaticsWorkspaceWidget(on_back=...)` UI 失败没有在 MainLine 复现。本阶段没有修改 UI 业务逻辑，也没有修复 V0.2 Integration 的 UI/Bioinformatics workspace 遗留问题。

## 15. `tests/shared` 非词库遗留失败

`tests/shared -q` 有 2 个失败：

- `tests/shared/test_ai_gateway_ollama_migration_audit.py::test_ollama_existing_call_audit_records_all_direct_call_files`
- `tests/shared/test_ai_gateway_ollama_migration_audit.py::test_ollama_existing_call_audit_includes_required_sections`

失败原因：

- 测试读取 `docs/ai_gateway_ollama_existing_call_audit.md`
- MainLine 初始 HEAD `d43cae4` 中该文档不存在
- MainLine 初始 HEAD 中测试文件 `tests/shared/test_ai_gateway_ollama_migration_audit.py` 已存在

结论：这是 MainLine 既有 AI Gateway audit 文档缺失问题，不是本阶段 Vocabulary scoped apply 或 packaging resource copy 引入的词库失败。本阶段不跨 AI 文档范围修复。

## 16. 遗留问题

- `tests/shared -q` 仍有 AI Gateway audit 文档缺失的非词库失败。
- ReleaseBuild worktree 尚未同步 packaging resource copy，需要后续 ReleaseBuild scoped sync。
- `medical_terms_index.sqlite` 仍未进入 MainLine；如后续决定包含，需要明确 checksum 和 artifact policy。
- Meta `confirmed` / `user edited` 检索治理状态仍需 Meta 后续任务处理。
- Bioinformatics 内部 TCGA / GTEx / tissue fallback 去重仍需后续 Bioinformatics 或 Integration 任务处理。
- `dev/shared-vocabulary` 仍不得整分支合并 MainLine。

## 17. 是否建议进入正式 MainLine Commit / ReleaseBuild 同步

建议提交本 MainLine scoped apply commit，因为：

- MainLine 初始状态干净。
- 实际 diff 仅限 scoped vocabulary / packaging resource copy / docs / tests。
- 最小相关词库、Bioinformatics 边界、Meta shell、packaging resource tests 均通过。
- `tests/ui` 在 MainLine 通过。
- SQLite 未成为硬依赖。
- 未触碰 Bioinformatics / Meta / AI / UI 业务流程。

提交后建议进入 ReleaseBuild scoped sync / package smoke：

1. 将 MainLine 的 `scripts/package_app.py` 最小 resource copy 同步到 ReleaseBuild。
2. 在 ReleaseBuild 构建包。
3. 验证包内 `data/medical_terms` 默认安全子集存在。
4. 验证 package smoke 和 app smoke。

## 18. 下一阶段建议

Stage V0.4 / ReleaseBuild scoped sync：

- 只同步 MainLine 中已验证的 vocabulary resource packaging 修复。
- 不带入 SQLite/raw ontology。
- 运行 packaged smoke 和 package resource presence checks。
- 单独开 AI Gateway audit cleanup 任务处理 `docs/ai_gateway_ollama_existing_call_audit.md` 缺失问题。
