# Vocabulary Stage V0.1 Scoped Merge Plan

日期：2026-05-13

范围：`dev/shared-vocabulary` 到 `stable/mainline` 的词库相关 scoped merge 计划。

本计划只定义可合入范围和验证顺序，不执行真实合并，不修改 MainLine。

## 1. 结论

`dev/shared-vocabulary` 不能整分支直合 MainLine。原因是该分支除了共享词库代码、资源和测试，还包含大量 MainLine handoff / cleanup / archive 删除、Bioinformatics 业务代码差异、UI 测试差异和历史文档搬迁差异。整分支合并会把非词库变更包装成词库变更，破坏 MainLine 当前基线。

安全路径是：在 Integration 或干净临时分支中只选择 Vocabulary/shared vocabulary 相关文件，用 cherry-pick、path-scoped checkout、patch apply 或手工 scoped apply 的方式合入，然后运行 Integration 验证。

## 2. 合入候选文件

这些文件属于 Vocabulary / shared vocabulary 合入候选，但仍需 Integration 验证：

- `app/shared/query_intelligence/medical_terms/**`
- `app/shared/query_intelligence/query_intelligence_models.py`
- `app/shared/query_intelligence/query_intelligence_service.py`
- `data/medical_terms/mini_medical_terms_index.json`
- `data/medical_terms/zh_term_overrides.json`
- `data/medical_terms/source_metadata.json`
- `data/medical_terms/license_attribution.md`
- `data/medical_terms/reference_checklists/**`
- `data/package_manifest.json` 的 `medical_terms_index` 段
- `scripts/update_medical_term_index.py`
- `scripts/audit_medical_vocabulary_coverage.py`
- `tests/shared/test_medical_term_lookup.py`
- `tests/shared/test_medical_term_index_runtime_strategy.py`
- `tests/shared/test_medical_terms_sqlite_index_build.py`
- `tests/shared/test_medical_vocabulary_*.py`
- `tests/shared/test_query_intelligence_service.py` 中 shared vocabulary / context isolation / AI Gateway audit 相关断言
- `docs/medical_term_index_contract.md`
- `docs/shared_medical_vocabulary_*.md`
- `docs/stage_2_*medical_vocabulary*.md`
- `docs/stage_v*_medical_vocabulary*.md`
- `docs/handoff/Vocabulary_predevelopment_blocker_audit_20260513.md`
- 本 Stage V0.1 新增的 Vocabulary handoff 和 README 文档

## 3. 需策略决定后才可合入的文件

以下文件不是无条件 MainLine 候选：

- `data/medical_terms/medical_terms_index.sqlite`
  - 当前是 mini-derived SQLite，可重复生成。
  - 默认建议不作为 MainLine 必需资源；可保留在 Vocabulary worktree 或 ReleaseBuild artifact。
  - 若决定进入 MainLine，必须记录 schema、build command、checksum、大小和 optional status。
- `data/medical_terms/medical_terms_index_build_report.json`
  - 属于生成报告；若 MainLine 不跟踪 SQLite，则该报告也不应作为 MainLine 必需文件。
- `data/medical_terms/coverage_audit_report.json`
  - 可作为审计产物合入，也可由 CI/ReleaseBuild 生成。进入 MainLine 前需确认是否接受 generated audit snapshot。

## 4. 不得随 Vocabulary 合入的文件范围

以下文件或差异不得随 Vocabulary 合入 MainLine：

- `app/bioinformatics/**` 中非 shared vocabulary 消费接口的业务流程变更
- `app/meta_analysis/**` 业务流程变更
- `tests/bioinformatics/**` 中非词库边界验证的业务测试删除或回退
- `tests/ui/**` 中 Bioinformatics / module selection UI 差异
- `docs/handoff/Global_Development_Manual.md` 删除
- `docs/handoff/MainLine_current_baseline_20260513.md` 删除
- `docs/cleanup/**` 删除
- `docs/archive/legacy_handoff_20260513/**` 删除
- `docs/architecture/**` 删除
- `docs/ui/**` 删除
- `docs/mainline_meta_analysis_boundary.md` 删除
- `docs/bioinformatics_*_v1.md` 删除
- 任何 `logs/**`、`dist/**`、`build/**`、`__pycache__/**`、`.pytest_cache/**`

## 5. MainLine handoff / cleanup / archive 删除说明

相对 MainLine，Vocabulary 分支显示了多类文档删除或重排：

- MainLine handoff 文件删除
- cleanup stage 报告删除
- archive 索引和 legacy handoff 文件删除
- UI governance 文档删除
- architecture 文档删除

这些差异来自分支历史和工作区分流，不是 Vocabulary 模块开发内容。Integration 必须保留 MainLine 当前 handoff、cleanup、archive、UI governance 和 baseline 文档，不得让 Vocabulary scoped merge 删除它们。

## 6. 需要 scoped apply 的文件

建议用 patch 或手工 scoped apply 的方式合入：

- `app/shared/query_intelligence/query_intelligence_models.py`
- `app/shared/query_intelligence/query_intelligence_service.py`
- `tests/shared/test_query_intelligence_service.py`
- `data/package_manifest.json`

原因：这些文件在 MainLine 已存在，且可能和 AI Gateway、Bioinformatics、Meta shell 其他分支同时演进。Integration 应逐块审查上下文过滤、AI Gateway 调用、raw prompt/raw response audit、draft-only 状态，不应盲目覆盖 MainLine。

## 7. 需要先进入 Integration 验证的文件

以下内容可以进入 Integration 验证，但不应直接写入 MainLine：

- `data/medical_terms/**`
- `scripts/update_medical_term_index.py`
- `scripts/audit_medical_vocabulary_coverage.py`
- shared vocabulary tests
- resource packaging policy文档
- 可选 SQLite 策略

Integration 验证重点：

- MainLine 启动不依赖缺失资源崩溃。
- 打包后可以定位默认词库资源，或明确降级到 registry fallback。
- Bioinformatics 不返回 PubMed-only / Meta-only 检索能力。
- Meta 不触发 GEO / TCGA / GTEx 生信流程。
- AI Gateway 不保存 raw prompt / raw response。

## 8. 建议安全合入顺序

1. 从 MainLine 或 Integration 创建干净 scoped merge 分支。
2. 先合入 shared model/API 变更：`medical_terms/**`、`query_intelligence_models.py`、`query_intelligence_service.py`。
3. 合入默认资源：`mini_medical_terms_index.json`、`zh_term_overrides.json`、metadata、license、reference checklists。
4. 合入脚本：coverage audit 和 SQLite builder。
5. 合入 shared tests 和最小 Bio/Meta 边界测试。
6. 决定 SQLite 是否进入 MainLine；默认先不把 SQLite 作为必需资源。
7. 处理 packaging：确保 packaged app 包含 `data/medical_terms` 默认安全子集，或有显式 fallback 验证。
8. 运行 Integration 测试清单。
9. 通过后再进入 MainLine，并保留 MainLine handoff/cleanup/archive 文件。

## 9. 合并方式建议

优先顺序：

1. 手工 scoped apply：最安全，适合 shared code 和 manifest。
2. `git checkout dev/shared-vocabulary -- <path>`：只用于新增且确认无 MainLine 本地差异的词库文件。
3. cherry-pick 后 revert 非词库路径：不推荐，容易携带删除。
4. 整分支 merge：禁止。

## 10. V0.1 完成标准

- scoped merge 清单存在。
- resource / packaging 策略存在。
- Vocabulary README / 维护规则存在。
- MainLine merge checklist 存在。
- 最小回归测试覆盖资源、fallback、context isolation、ontology 下载默认关闭、AI audit raw 输出。
- `git diff --check` 通过。
- 最小相关 pytest 通过。
