# Vocabulary MainLine Merge Checklist

日期：2026-05-13

用途：在 Vocabulary scoped merge 进入 MainLine 前逐项检查。此清单不授权整分支合并。

## 1. 合入前检查

- [ ] 已从 MainLine 或 Integration 干净分支开始。
- [ ] 已读取 Global Development Manual。
- [ ] 已读取 Vocabulary scoped merge plan。
- [ ] 已确认不会修改 MainLine handoff / cleanup / archive 文件。
- [ ] 已确认不会开发 Bioinformatics 或 Meta Analysis 业务流程。
- [ ] 已确认不会执行真实网络访问、Ollama 或外部 AI。

## 2. 文件范围检查

- [ ] 只包含 `app/shared/query_intelligence/medical_terms/**`。
- [ ] 只包含必要 shared query intelligence schema / service 变更。
- [ ] 只包含 `data/medical_terms/**` 安全资源。
- [ ] 只包含 vocabulary scripts。
- [ ] 只包含 shared vocabulary tests 和必要边界测试。
- [ ] 只包含 Vocabulary docs / handoff / checklist。
- [ ] 不包含 `app/bioinformatics/**` 业务流程改动。
- [ ] 不包含 `app/meta_analysis/**` 业务流程改动。
- [ ] 不包含 UI 改动。
- [ ] 不包含 MainLine 文档删除。

## 3. 资源文件检查

- [ ] `zh_term_overrides.json` 存在并可解析。
- [ ] `mini_medical_terms_index.json` 存在并可解析。
- [ ] `source_metadata.json` 存在。
- [ ] `license_attribution.md` 存在。
- [ ] `reference_checklists/` 存在。
- [ ] 没有 `data/medical_terms/raw/**` 进入默认包。
- [ ] 没有用户数据、下载数据、PDF、runtime cache 进入 Git。

## 4. SQLite 策略检查

- [ ] 已决定 `medical_terms_index.sqlite` 是否进入 MainLine。
- [ ] 若进入 MainLine，已记录 schema、build command、terms count、checksum、optional status。
- [ ] 若不进入 MainLine，JSON fallback tests 已通过。
- [ ] SQLite absent/corrupt/schema mismatch 均可降级。
- [ ] SQLite 不得成为 MainLine 启动必需资源。

## 5. Packaging 检查

- [ ] 打包脚本或 ReleaseBuild 流程会复制 `data/medical_terms` 默认安全子集。
- [ ] packaged app 中可找到 `mini_medical_terms_index.json`。
- [ ] packaged app 中可找到 `zh_term_overrides.json`。
- [ ] packaged app 不复制 full ontology raw source。
- [ ] packaged smoke test 记录 `active_index_status()`。
- [ ] 若未改打包脚本，必须把 packaging 风险保留为 Blocking。

## 6. Bioinformatics 边界检查

- [ ] Bioinformatics context 不返回 PubMed candidates。
- [ ] Bioinformatics allowed sources 仍为 GEO/GSE、TCGA/GDC、GTEx/local。
- [ ] PubMed / WOS / Embase / CNKI 不进入 Bioinformatics search execution。
- [ ] modality-only query 不自动执行宽泛 GEO 检索。
- [ ] 用户确认 query draft 后才允许执行 broad/online search。

## 7. Meta Analysis 边界检查

- [ ] Meta context 不返回 GEO candidates。
- [ ] Meta context 不返回 TCGA / GTEx candidates。
- [ ] Meta PubMed / MeSH query 仍是草稿。
- [ ] confirmed / user edited 状态由 Meta workflow 管理，不由 Vocabulary 直接执行。
- [ ] Meta 不调用 GEO / TCGA / GTEx 生信流程。

## 8. AI Gateway / Local Model 边界检查

- [ ] 默认 local model disabled。
- [ ] 启用 local model 时必须走 AI Gateway。
- [ ] module/task_type prefix policy 生效。
- [ ] Vocabulary provider 不直接调用 Ollama。
- [ ] Vocabulary provider 不直接联网。
- [ ] Unknown-term model candidates 不进入最终 PubMed/GEO/TCGA/GTEx query。

## 9. 隐私与日志检查

- [ ] AI audit log 不写 raw prompt。
- [ ] AI audit log 不写 raw response。
- [ ] 不持久化完整用户输入，除非业务对象明确需要并有治理策略。
- [ ] audit 中只保留必要摘要、hash、长度、状态和来源。
- [ ] 不暴露 raw path / schema / internal ids 到普通 UI。

## 10. 测试清单

Vocabulary scoped tests：

```bash
python3 - <<'PY'
from scripts.audit_medical_vocabulary_coverage import build_coverage_audit_report
report = build_coverage_audit_report()
print(report["overall"]["quality_gate_status"])
PY
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/shared/test_medical_term_lookup.py tests/shared/test_medical_term_index_runtime_strategy.py tests/shared/test_medical_terms_sqlite_index_build.py tests/shared/test_medical_vocabulary_consolidation_regression.py tests/shared/test_query_intelligence_service.py tests/shared/test_vocabulary_stage_v0_1_merge_readiness.py -q
git diff --check
```

Boundary tests：

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics/test_bio_query_adapter.py tests/bioinformatics/test_search_center_router.py tests/meta_analysis/test_mainline_meta_contract.py -q
```

## 11. Integration 验证清单

- [ ] `python3 -m app.main --smoke-test`
- [ ] `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/shared -q`
- [ ] `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`
- [ ] `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q`
- [ ] `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
- [ ] packaged app smoke if packaging changed
- [ ] `git diff --check`

## 12. MainLine 验证清单

- [ ] MainLine handoff / cleanup / archive files remain present.
- [ ] MainLine smoke test passes.
- [ ] UI tests pass.
- [ ] Bioinformatics tests pass.
- [ ] Shared vocabulary tests pass.
- [ ] Meta shell contract tests pass.
- [ ] `git status --short --branch` is clean before commit.
- [ ] Commit message clearly states scoped vocabulary merge.

## 13. 回滚策略

如果合入后出现启动、packaging、context leakage 或 AI Gateway 边界问题：

1. 回滚 scoped vocabulary merge commit。
2. 保留 MainLine handoff / cleanup / archive 当前状态。
3. 不删除 `data/medical_terms` 历史资源，除非单独 cleanup 阶段确认。
4. 在 Integration 重新应用更小 patch。
5. 先恢复 JSON mini fallback，再恢复 optional SQLite。
6. 对触发失败的 query/context 增加 regression test 后再重试。
