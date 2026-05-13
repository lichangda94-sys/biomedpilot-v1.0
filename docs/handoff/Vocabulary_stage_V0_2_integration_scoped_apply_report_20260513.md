# Vocabulary Stage V0.2 Integration Scoped Apply Report

日期：2026-05-13

工作区：`/Users/changdali/Developer/biomedpilot v1.0/Integration`

分支：`dev/integration`

目标：按 Stage V0.1 scoped merge plan 验证只合入共享词库相关路径，并补齐 `data/medical_terms/` 在 packaging 场景下的最小资源复制和包内加载验证。

## 1. 前置文件读取

本阶段开始前已读取：

- `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- `/Users/changdali/Developer/biomedpilot v1.0/README_总说明.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/handoff/Global_Development_Manual.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Integration/CODEX.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Vocabulary/docs/handoff/Vocabulary_predevelopment_blocker_audit_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Vocabulary/docs/handoff/Vocabulary_stage_V0_1_scoped_merge_plan_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Vocabulary/docs/handoff/Vocabulary_stage_V0_1_resource_packaging_strategy_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Vocabulary/docs/handoff/Vocabulary_mainline_merge_checklist_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Vocabulary/README.md`
- `/Users/changdali/Developer/biomedpilot v1.0/Vocabulary/docs/vocabulary/README.md`

未发现本任务与总开发手册或 V0.1 scoped merge plan 冲突。

## 2. Scoped Apply 候选路径

根据 V0.1 scoped merge plan，本阶段候选范围限定为：

- `app/shared/query_intelligence/medical_terms/**`
- `app/shared/query_intelligence/query_intelligence_models.py`
- `app/shared/query_intelligence/query_intelligence_service.py`
- `data/package_manifest.json` 的 shared vocabulary 段
- `data/medical_terms/mini_medical_terms_index.json`
- `data/medical_terms/zh_term_overrides.json`
- `data/medical_terms/source_metadata.json`
- `data/medical_terms/license_attribution.md`
- `data/medical_terms/reference_checklists/**`
- `data/medical_terms/coverage_audit_report.json`
- `scripts/update_medical_term_index.py`
- `scripts/audit_medical_vocabulary_coverage.py`
- `tests/shared/test_medical_term_*.py`
- `tests/shared/test_medical_vocabulary_*.py`
- `tests/shared/test_query_intelligence_service.py`
- `tests/shared/test_vocabulary_stage_v0_1_merge_readiness.py`
- `docs/medical_term_index_contract.md`
- `docs/shared_medical_vocabulary_*.md`
- `docs/stage_*medical_vocabulary*.md`
- `docs/handoff/Vocabulary_*20260513.md`
- `docs/vocabulary/README.md`

Packaging 最小修复候选范围：

- `scripts/package_app.py`
- `tests/test_package_app.py`

## 3. 实际应用路径

实际从 `dev/shared-vocabulary` scoped apply 到 Integration 的路径：

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
- shared vocabulary / medical term / query intelligence 相关 `tests/shared/**`
- Vocabulary contract、governance、stage、handoff、README 文档

本阶段手工新增或调整的 Integration 本地验证改动：

- `scripts/package_app.py`
  - 新增 `PACKAGE_RESOURCE_FILES` 和 `PACKAGE_RESOURCE_DIRS`。
  - 打包时复制 `data/medical_terms` 默认安全子集。
  - 默认不复制 `medical_terms_index.sqlite`。
  - 默认不复制 `data/medical_terms/raw/`。
- `tests/test_package_app.py`
  - 验证 packaged resource root 内存在 mini index、zh overrides、source metadata、license attribution 和 reference checklists。
  - 验证 package 默认不包含 SQLite 和 raw ontology。
- `tests/shared/test_medical_vocabulary_consolidation_regression.py`
  - 当仓库中不存在 `medical_terms_index.sqlite` 时，测试用临时目录生成 SQLite 验证资产。
  - 该测试不再要求 MainLine/Integration 必须跟踪 SQLite。

## 4. 明确排除路径

本阶段没有带入以下路径或差异：

- `app/bioinformatics/**` 业务流程修改或删除
- `app/meta_analysis/**` 业务流程修改
- `app/ai/**` AI Gateway 行为修改
- `app/shell/**` 或 UI 修改
- `tests/ui/**`
- `tests/bioinformatics/**` 中非词库边界验证差异
- `docs/handoff/Global_Development_Manual.md` 删除
- `docs/handoff/MainLine_current_baseline_20260513.md` 删除
- `docs/cleanup/**` 删除
- `docs/archive/**` 删除
- `docs/ui/**` 删除
- `docs/architecture/**` 删除
- `data/medical_terms/medical_terms_index.sqlite`
- `data/medical_terms/medical_terms_index_build_report.json`
- `data/medical_terms/raw/**`
- `dist/**`、`build/**`、cache、runtime logs

## 5. 非词库差异检查

对比 `dev/shared-vocabulary` 时发现仍存在非词库差异，包括 Bioinformatics 业务文件删除/修改、Bioinformatics tests 删除、UI tests 修改、Meta UI test 增加等。这些差异没有进入本次 Integration scoped apply。

结论：`dev/shared-vocabulary` 仍禁止整分支合并。MainLine 只能接受经过 Integration 验证的 scoped vocabulary patch。

## 6. Worktree 修改范围

- 修改 MainLine：否。
- 修改 Vocabulary：否。
- 修改 ReleaseBuild：否。
- 修改 Integration：是。
- 修改 Bioinformatics / Meta / AI / UIShell / LabTools worktree：否。
- 执行真实合并：否。
- 推送 GitHub：否。

## 7. Packaging 验证结果

本阶段在 Integration 中实施了最小 packaging 修复。`scripts/package_app.py` 现在会复制：

- `data/medical_terms/mini_medical_terms_index.json`
- `data/medical_terms/zh_term_overrides.json`
- `data/medical_terms/source_metadata.json`
- `data/medical_terms/license_attribution.md`
- `data/medical_terms/reference_checklists/`

默认不复制：

- `data/medical_terms/medical_terms_index.sqlite`
- `data/medical_terms/medical_terms_index_build_report.json`
- `data/medical_terms/raw/`
- full ontology source dump

验证结果：

- 源码运行路径：`<repo>/data/medical_terms/` 存在并可加载。
- 测试运行路径：`<repo>/data/medical_terms/` 存在并可加载。
- 打包后路径：`<BioMedPilot.app>/Contents/Resources/app/data/medical_terms/` 已通过 package CLI smoke 验证存在。
- 包内 smoke 使用 packaged resource root 运行，不依赖开发机绝对路径定位词库。
- 缺失 SQLite 时 runtime 通过 JSON mini index 和 zh overrides 正常回退。

ReleaseBuild worktree 尚未修改。后续进入 ReleaseBuild 时应同步该 packaging 修复或从 MainLine scoped merge 后验证 packaged smoke。

## 8. SQLite 运行依赖结论

本阶段未把 `medical_terms_index.sqlite` scoped apply 到 Integration。

结论：

- MainLine/Integration 运行不硬依赖 SQLite。
- SQLite 缺失时 JSON fallback 可用。
- 当前 `active_index_status()` 显示 `full_index_available=False`、`mini_index_available=True`。
- `lookup_medical_terms("脑胶质瘤", target_context="bioinformatics")` 使用 `zh_term_overrides`、`mini_medical_terms_index` 和 registry fallback。
- SQLite 仍是 optional enhancement / validation artifact。
- 生成命令存在：`python3 scripts/update_medical_term_index.py`。
- schema 和 term count 记录存在于 `source_metadata.json` 和 SQLite stage 文档：schema `biomedpilot.medical_terms.sqlite.v6`，terms count `572`。
- 由于本阶段不打包 SQLite，当前不要求 checksum；若后续决定包内包含或 Git 跟踪 SQLite，必须补 checksum、生成命令、schema、term count 和 optional status。

## 9. Bioinformatics / Meta 边界验证

Bioinformatics：

- 仍不得执行 PubMed 检索。
- Bioinformatics context 不返回 PubMed candidates。
- Bioinformatics search surface 仍面向 GEO / TCGA / GTEx / local expression data。
- modality-only terms 不会作为疾病或核心检索概念。
- Meta-only outcome / effect measure / PICO terms 不进入 Bioinformatics 主检索能力。

Meta Analysis：

- Meta context 不返回 GEO / TCGA / GTEx candidates。
- PubMed / MeSH query 仍是 draft 语境。
- Vocabulary 未开发 Meta 业务执行流程。
- `confirmed` / `user edited` 治理状态仍记录为后续 Meta 任务，不在 V0.2 跨模块开发。

## 10. AI / 网络 / 隐私边界验证

- 未调用 Ollama。
- 未调用外部 AI。
- 未执行真实网络检索。
- coverage audit 使用只读函数 `build_coverage_audit_report()`，未写回时间戳文件。
- ontology 下载默认关闭；V0.1 merge readiness 测试覆盖显式开关要求。
- Vocabulary provider contract 不允许直接网络访问、本地模型调用、ontology 下载或 raw prompt/raw response 保存。
- 本阶段未新增 raw prompt、raw response 或用户输入全文持久化。

## 11. 测试结果

已执行：

```bash
git status --short --branch
git diff --check
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
QT_QPA_PLATFORM=offscreen python3 scripts/package_app.py --output-dir /tmp/biomedpilot-vocab-v0-2-package --smoke-test
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/shared -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

结果：

- `git diff --check`：通过。
- app smoke：通过。
- coverage audit 只读结果：`quality_gate_status=pass`，`covered=621/621`，`weighted_coverage_rate=1.0`，`core_covered=533/533`。
- 最小相关 pytest + packaging tests：`75 passed in 7.80s`。
- packaged app smoke：通过。
- packaged resource check：`packaged_medical_terms_resources=pass`。
- `tests/shared -q`：`225 passed in 26.12s`。
- `tests/bioinformatics -q`：`264 passed in 3.87s`。
- `tests/meta_analysis -q`：`3 passed in 0.46s`。
- `tests/ui -q`：`6 failed, 40 passed, 87 skipped in 2.55s`。
  - 失败均发生在 `MainWindow()` 初始化调用 `BioinformaticsWorkspaceWidget(on_back=self.show_dashboard)` 时。
  - 错误为 `TypeError: BioinformaticsWorkspaceWidget() takes no arguments`。
  - 该失败位于 UI / Bioinformatics workspace 接口边界，不是本阶段 Vocabulary scoped apply 或 packaging 资源复制改动引入的文件范围；本阶段未跨模块修复。

## 12. 遗留问题

- MainLine 仍不得整分支合并 `dev/shared-vocabulary`。
- ReleaseBuild worktree 尚未同步 packaging 修复，需要在后续 ReleaseBuild 或 MainLine scoped merge 后验证。
- `tests/ui` 仍有 MainWindow / Bioinformatics workspace 构造接口失败，需要 UIShell 或 Bioinformatics scoped 任务处理。
- Meta `confirmed` / `user edited` 检索治理状态仍需 Meta 后续任务处理。
- Bioinformatics 内部 TCGA / GTEx / tissue fallback 去重仍需后续 Bioinformatics 或 Integration 任务处理。
- 如果后续决定打包或跟踪 SQLite，需要补 checksum 和明确 artifact policy。

## 13. 是否建议进入 MainLine Scoped Merge

建议进入 MainLine scoped merge 准备，但仅限本报告确认的 scoped vocabulary patch 和 packaging 最小修复。

仍然禁止：

- 整分支合并 `dev/shared-vocabulary`。
- 带入 Bioinformatics / Meta / UI 非词库业务差异。
- 带入 MainLine handoff / cleanup / archive 删除。
- 默认带入 SQLite 或 raw ontology。

## 14. 下一阶段建议

建议进入 Stage V0.3 / MainLine scoped merge preflight：

1. 从 MainLine 干净状态应用本 Integration scoped patch。
2. 保留 MainLine handoff / cleanup / archive / UI governance 文档。
3. 运行 MainLine smoke、shared vocabulary tests、Bioinformatics boundary tests、Meta shell contract tests、UI smoke tests。
4. 验证 MainLine packaged app 包含 `data/medical_terms` 默认安全子集。
5. 决定 SQLite 是否作为 ReleaseBuild artifact，而不是 MainLine 必需资源。
