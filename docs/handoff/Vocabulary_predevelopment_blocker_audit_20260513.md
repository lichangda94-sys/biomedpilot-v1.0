# Vocabulary Predevelopment Blocker Audit Against MainLine

日期：2026-05-13

工作区：`/Users/changdali/Developer/biomedpilot v1.0/Vocabulary`

当前分支：`dev/shared-vocabulary`

对比基线：`/Users/changdali/Developer/biomedpilot v1.0/MainLine`，`stable/mainline`，`fdc83c1`

## 1. 审计范围

本阶段是共享词库模块开发前审计，不是功能开发。审计只读检查了：

- 项目总开发手册：`/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- Vocabulary 工作区规则：`CODEX.md`
- 项目根 README：`/Users/changdali/Developer/biomedpilot v1.0/README_总说明.md`
- Vocabulary 词库代码：`app/shared/query_intelligence/medical_terms/`
- 词库数据：`data/medical_terms/`
- 生成和审计脚本：`scripts/update_medical_term_index.py`、`scripts/audit_medical_vocabulary_coverage.py`
- 共享 query intelligence、Bioinformatics query adapter/search center、Meta MainLine shell 相关代码和测试
- 既有词库报告、handoff、coverage、governance 文档
- MainLine 对应目录和 `stable/mainline..dev/shared-vocabulary` 差异

未执行真实合并、未执行网络访问、未调用 Ollama 或外部 AI 服务。

## 2. 当前词库模块结构

当前词库仍是 `BioMedPilot shared medical vocabulary`，不是 Bioinformatics 专属，也不是 Meta Analysis 专属。

主要结构：

- `app/shared/query_intelligence/medical_terms/`
  - `term_index_models.py`：`TermConcept`、`ChineseTermOverride`、`TermLookupResult`
  - `term_lookup.py`：中文/英文术语查找、上下文过滤、短 token 保护、SQLite-first fallback
  - `term_index_loader.py`：加载 `medical_terms_index.sqlite` 和 `mini_medical_terms_index.json`
  - `zh_overrides_loader.py`：加载 `zh_term_overrides.json`
  - `vocabulary_provider.py`：provider 协议和 provider match 类型
  - `ontology_importers/`：MONDO、DOID、NCIt、MeSH、EFO importer scaffold
- `data/medical_terms/`
  - `mini_medical_terms_index.json`：572 条 runtime concept
  - `zh_term_overrides.json`：1094 条中文 override
  - `medical_terms_index.sqlite`：572 条 `ontology_terms`，schema `biomedpilot.medical_terms.sqlite.v6`
  - `coverage_audit_report.json`：621/621 covered，quality gate `pass`
  - `reference_checklists/`：oncology、tissue、bioinformatics modality、meta analysis terms 等 checklist
  - `source_metadata.json`、`license_attribution.md`
- `scripts/update_medical_term_index.py`
  - 默认从 mini vocabulary 构建 SQLite；只有显式 `--download-sources` 才会下载外部 ontology。
- `scripts/audit_medical_vocabulary_coverage.py`
  - 生成 coverage JSON 和 Stage 2.3 markdown audit。

运行时加载路径清晰：`zh_term_overrides.json` -> 可选 `medical_terms_index.sqlite` -> `mini_medical_terms_index.json` -> `biomedical_term_registry` fallback。路径按 `Path(__file__).resolve().parents[4] / "data" / "medical_terms"` 解析。

## 3. 当前可复用资产

可复用资产：

- 共享 lookup API：`lookup_medical_terms(query, target_context=...)`
- Query Intelligence draft：`build_search_translation_draft(...)`
- Bioinformatics context 过滤：Bioinformatics 输出 GEO/TCGA/GTEx 草稿，清空 PubMed candidates
- Meta context 过滤：Meta 输出 PubMed/MeSH/PICO/PECO/PICOS 相关字段，清空 GEO/TCGA/GTEx candidates
- SQLite schema v6 和 mini-derived 构建脚本
- 覆盖率审计脚本和 checklist
- 词库治理文档：`docs/medical_term_index_contract.md`、`docs/shared_medical_vocabulary_governance_release_v1.md`

应进入 Git 的稳定源文件：

- `mini_medical_terms_index.json`
- `zh_term_overrides.json`
- `reference_checklists/*.json`
- `source_metadata.json`
- `license_attribution.md`
- 生成脚本、审计脚本、共享 tests

需要 MainLine/Integration 明确策略后再进入 MainLine 的资源：

- `medical_terms_index.sqlite`：当前是 2.6 MB、mini-derived、可重复生成、二进制生成物。它可作为 Vocabulary worktree 验证资产，但是否随 MainLine 跟踪或打包需要明确政策。
- `coverage_audit_report.json`、`medical_terms_index_build_report.json`：可作为审计产物保留，但合入 MainLine 时应确认是否需要随主线长期跟踪。

## 4. 与 MainLine 的差异

MainLine 已有 `app/shared/query_intelligence/medical_terms/` 代码目录，因此目录结构本身不冲突。主要差异如下：

- `data/medical_terms/` 在 MainLine 不存在，Vocabulary 新增完整数据资产。
- `data/package_manifest.json` 在 Vocabulary 标记 shared vocabulary 默认包资产和 optional SQLite。
- Vocabulary 修改了 shared query intelligence 和 medical term result schema，增加 Meta terms、assay/platform、TCGA primary site、context-aware filtering 等字段。
- Vocabulary 增加大量 `tests/shared/test_medical_vocabulary_*`、SQLite build/runtime strategy、query intelligence 边界测试。
- Vocabulary 相对 MainLine 还包含大量非词库差异：MainLine handoff/cleanup/archive 文档删除、Bioinformatics/UI 代码和测试删除或回退。这些不是共享词库模块本身的合入面。

结论：不能把 `dev/shared-vocabulary` 整分支直接合入 MainLine。需要 scoped merge/cherry-pick 或 Integration 过滤，只带入词库代码、词库数据、词库脚本、相关 shared tests 和必要文档。

## 5. 阻塞点和风险等级

| 等级 | 风险/阻塞点 | 证据 | 建议处理方式 |
| --- | --- | --- | --- |
| Blocking | `dev/shared-vocabulary` 不能整分支直合 MainLine | `git diff stable/mainline..dev/shared-vocabulary` 显示 MainLine `docs/handoff/Global_Development_Manual.md`、`docs/handoff/MainLine_current_baseline_20260513.md`、cleanup/archive 文档删除，并有大量 Bioinformatics/UI 文件删除或回退 | Integration 中做 scoped merge，只选择词库相关路径；不得带入文档删除和非词库业务代码差异 |
| Blocking | MainLine packaged app 当前不会复制顶层 `data/medical_terms/` | `scripts/package_app.py` 的 `COPY_DIRS` 不包含 `data`；但 runtime loader 期望 `Resources/app/data/medical_terms`；`data/package_manifest.json` 声称默认包包含 mini/zh/source/license | 在 Vocabulary 或 Integration 阶段明确 packaging 策略：复制安全子集 `data/medical_terms`，或让包内 fallback 明确只用 registry；合入前需 packaged smoke 验证 |
| High | `medical_terms_index.sqlite` 是已跟踪二进制生成物，且 package manifest 标记 optional full index 不默认包含 | 2.6 MB、mini-derived、可由脚本重复生成；全局手册默认不鼓励生成文件进入 Git | MainLine 合入前决定 SQLite 策略：不进 MainLine、或进 Git LFS/ReleaseBuild artifact、或小型可审计二进制随包；若保留，必须记录重生成命令和 checksum |
| High | Vocabulary 分支相对 MainLine 混有非词库业务差异 | `app/bioinformatics/*`、`tests/ui/*`、`tests/bioinformatics/*` 有大量 diff，和本阶段词库边界无关 | 不在 Vocabulary 阶段修复；Integration 只读审查并过滤，必要时从 MainLine 重新开干净集成分支 |
| High | Bioinformatics query understanding 仍有硬编码 TCGA/GTEx/tissue/abbreviation fallback | `app/bioinformatics/search_center/query_understanding.py` 中 `_tcga_projects`、`_gtex_tissues`、`_tissue_terms` 与共享词库重叠 | Stage V0.1 不重构业务模块；后续在 Bioinformatics 或 Integration 里改为优先消费 `SearchTranslationDraft.audit["term_lookup"]`，保留最小兜底 |
| High | Meta draft governance 状态不完整 | Shared draft 只有 `search_execution_status="draft_only"`；未见 `confirmed`、`user_edited` 状态模型 | 在 Meta 接入 PubMed 草稿前补充治理状态 contract，确保 confirmed/user edited 后才执行检索 |
| Medium | Provider abstraction和实现存在轻微语义不一致 | `default_vocabulary_providers()` 暴露 provider 顺序，但 `lookup_medical_terms()` 默认内部直读 overrides/index/registry；provider 注入仅作为额外结果入口 | Stage V0.1 明确 provider contract：要么把默认 provider 真正接入，要么文档声明 provider 仅用于测试/扩展注入 |
| Medium | 短 token/模态词 false positive 已有防护但仍需持续回归 | 当前有短 token guard、context filter 和 tests；既有审计也提到 raw lookup 曾有 `read count`/`microarray` 类风险 | Stage V0.1 保留并扩展 negative tests：OS/HR/OR/RR、PD/SD/PR、RNA/DNA/CNV/SNP、read count/TPM/FPKM/microarray |
| Medium | 隐私审计依赖下游不持久化 draft | AI Gateway 默认只记录 prompt/response length + sha256；但 draft/result 对象含 `original_question`，下游若持久化可能保存用户输入全文 | Integration 验证所有持久化路径；禁止 raw prompt/raw response，必要时只存 hash、长度和字段摘要 |
| Medium | `scripts/update_medical_term_index.py` 具备显式下载能力 | 只有 `--download-sources` 时调用 `urlretrieve`，本阶段未执行 | 保持开发时显式开关；ReleaseBuild/CI 不得默认下载；外部 ontology 进入前需 license 和来源记录 |
| Low | ignored cache 存在但未跟踪 | `__pycache__`、`.pytest_cache` 被 `.gitignore` 覆盖 | 无需处理；本阶段不删除文件 |
| Low | MainLine 缺少 Vocabulary 专属 pre-merge checklist 文档 | 已有 contract/governance/stage 文档，但缺一个 MainLine 合入前检查清单 | 本报告可作为初版 handoff；后续 Stage V0.1 可补正式 README/checklist |

## 6. MainLine 合入阻塞判断

存在 MainLine 合并阻塞。

阻塞不是因为共享词库目录名冲突，也不是因为 lookup API 完全不可用；阻塞来自三类问题：

1. 分支级阻塞：Vocabulary 分支混入大量非词库差异，不能整分支直合。
2. Packaging 阻塞：当前 `.app` 打包脚本不复制顶层 `data/medical_terms/`，词库资源在 packaged runtime 中可能缺失。
3. 资源策略阻塞：SQLite 二进制生成物是否进入 MainLine/Git/包内尚未定案。

在这些问题处理前，不建议把 Vocabulary 作为完整分支合入 MainLine。

## 7. Bioinformatics 边界审计

当前 Bioinformatics 侧总体保持边界：

- `build_search_translation_draft(..., target_context="bioinformatics", target_database="geo")` 会清空 PubMed candidates。
- `SearchContext` 明确 Bioinformatics allowed databases 为 `geo/gse/tcga/gtex/local`，forbidden databases 包含 `pubmed/web_of_science/embase/cnki/zotero/endnote`。
- `QueryUnderstandingLayer` 的 allowed sources 是 `("geo", "tcga_gdc", "gtex")`。
- 测试覆盖 `test_query_understanding_allows_only_three_dataset_sources_and_no_pubmed`、`test_bioinformatics_context_filters_literature_candidates`。
- broad query guard 要求无明确疾病词时不能默认执行宽泛 GEO 检索。

风险：

- `search_center/query_understanding.py` 仍有硬编码 fallback，会和共享词库长期重复。
- Bioinformatics 目前支持 draft 生成和 broad guard，但“用户确认 query draft 后再执行搜索”的治理主要在 search router 参数 `confirmed_geo_queries`/`allow_broad_geo_query` 和 UI 层，仍需 Integration 验证。
- `scripts/bio_geo_random_recognition_audit.py` 和 GEO adapter 有真实网络能力，但不属于词库模块；本阶段未调用。

结论：没有发现 Bioinformatics 侧直接接入 PubMed 的新增词库污染；但合入前必须验证 PubMed candidates 仍被过滤。

## 8. Meta Analysis 边界审计

当前 Meta 侧共享词库能力具备：

- `target_context="meta_analysis"` 时支持 PICO/PICOS/PECO 相关字段：`pico_terms`、`exposure_terms`、`intervention_terms`、`outcome_terms`、`study_design_terms`、`effect_measures`、`diagnostic_accuracy_terms`、`publication_type_terms`、`exclusion_type_terms`、`quality_assessment_terms`。
- Meta context 清空 `geo_query_candidates`，不输出 TCGA/GTEx/GEO/SRA candidates 作为主结果。
- PubMed query drafts 优先使用 MeSH terms。
- MainLine 当前 Meta 是 shell contract；完整 Meta workflow 不在 MainLine。

风险：

- 共享层能生成 PubMed 草稿，但没有完整的 `draft` / `confirmed` / `user edited` 状态治理模型。
- Meta business workflow 尚未在 MainLine 中消费这些字段；合入后需要 Integration 或 Meta 分支验证，不应由 Vocabulary 混入 Meta 业务流程。

结论：没有发现 Meta 调用 GEO/TCGA/GTEx 生信流程的新增词库污染；但 Meta 执行检索前必须补充确认状态治理。

## 9. AI Gateway、本地模型和隐私风险

当前词库/query intelligence 没有直接调用 Ollama CLI、`requests`、`subprocess` 或外部网络。可选本地模型路径走 `app/shared/ai_gateway.AIGateway`：

- 默认 `LocalModelConfig.enabled=False`
- 缺少 gateway module/task_type 时 fallback registry
- AI Gateway module policy 限制 `bioinformatics` 只能调用 `bio_` 前缀任务、`meta_analysis` 只能调用 `meta_` 前缀任务
- AI audit logger 默认只写 prompt/response 长度和 sha256，不写 raw prompt/raw response
- `save_ai_gateway_config()` 会强制 `store_raw_prompts=False`、`store_raw_responses=False`

风险等级：Medium。原因是 `SearchTranslationDraft` 和 `QueryIntelligenceResult` 对象仍包含 `original_question`。这不是持久化日志，但下游如果把对象整体写入项目记录或日志，可能保存用户输入全文。合入前需审计持久化路径。

## 10. 哪些问题必须先在 Vocabulary 解决

- 明确 `medical_terms_index.sqlite` 的 Git/包内策略，并在 contract 文档中写清楚。
- 为 Vocabulary 增加 MainLine 合入 checklist 或 README，说明 scoped merge 路径、资源策略、测试最小集。
- 加强 short-token 和 modality-only negative tests，防止 raw lookup 误判疾病。
- 明确 provider contract，避免文档和实现对 provider 顺序的理解不一致。

## 11. 哪些问题需要 Integration 验证

- 只合入词库相关路径，不带入 MainLine handoff/cleanup/archive 删除和 Bioinformatics/UI 无关差异。
- `python3 -m app.main --smoke-test`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/shared -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
- packaged app 是否能找到 `data/medical_terms/mini_medical_terms_index.json` 和 `zh_term_overrides.json`
- Bioinformatics 不出现 PubMed candidates；Meta 不出现 GEO/TCGA/GTEx candidates
- AI Gateway audit 不写 raw prompt/raw response

## 12. 可以推迟到后续开发阶段的问题

- Full ontology subset 导入 MONDO/DOID/NCIt/MeSH/EFO。
- SQLite FTS 或更复杂 ranking。
- Bioinformatics hardcoded fallback 完全去重。
- Meta 完整 PubMed/WOS/Embase/CNKI 执行 workflow。
- Unknown term review queue。
- 更完整的 external ontology license UI/导入工具。

## 13. 建议的 Stage V0.1 开发范围

Stage V0.1 应保持小范围、主线可合入：

1. 只处理 shared vocabulary contract、README/checklist、资源策略和 tests。
2. 不改 Bioinformatics/Meta 业务流程。
3. 将 `medical_terms_index.sqlite` 策略定为以下之一：
   - 不进入 MainLine，ReleaseBuild 生成；
   - 进入 MainLine 但明确为小型 mini-derived optional asset；
   - 转为包构建产物，不长期跟踪。
4. 修正或文档化 packaged runtime 的 `data/medical_terms` 包含策略。
5. 补齐 negative tests 和 package resource existence tests。
6. 输出 Integration scoped merge 清单。

## 14. 建议的最小测试集

Vocabulary worktree：

```bash
python3 scripts/audit_medical_vocabulary_coverage.py
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/shared/test_medical_term_lookup.py tests/shared/test_medical_term_index_runtime_strategy.py tests/shared/test_medical_terms_sqlite_index_build.py tests/shared/test_medical_vocabulary_consolidation_regression.py tests/shared/test_query_intelligence_service.py tests/bioinformatics/test_bio_query_adapter.py tests/bioinformatics/test_search_center_router.py tests/meta_analysis/test_mainline_meta_contract.py -q
git diff --check
git status --short
```

Integration scoped merge 后：

```bash
python3 -m app.main --smoke-test
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/shared -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
git diff --check
```

## 15. 本阶段操作声明

- 修改业务代码：否。
- 删除文件：否。
- 跨 worktree 写入：否。
- 真实合并：否。
- GitHub push：否。
- 新增外部依赖：否。
- 真实网络访问：否。
- 直接调用 Ollama 或外部 AI 服务：否。
- 绕过 AI Gateway：否。
- 改 UI 或业务流程：否。

本阶段唯一写入目标是 Vocabulary worktree 内的审计报告：

- `docs/handoff/Vocabulary_predevelopment_blocker_audit_20260513.md`

## 16. 验证结果

本报告创建后已执行：

```bash
git status --short
git diff --check
python3 - <<'PY'
from scripts.audit_medical_vocabulary_coverage import build_coverage_audit_report
report = build_coverage_audit_report()
overall = report["overall"]
print("quality_gate_status=" + str(overall.get("quality_gate_status")))
print("covered=" + str(overall.get("covered")) + "/" + str(overall.get("total_checklist_items")))
print("weighted_coverage_rate=" + str(overall.get("weighted_coverage_rate")))
print("core_covered=" + str(overall.get("core_covered")) + "/" + str(overall.get("core_checklist_items")))
PY
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/shared/test_medical_term_lookup.py tests/shared/test_medical_term_index_runtime_strategy.py tests/shared/test_medical_terms_sqlite_index_build.py tests/shared/test_medical_vocabulary_consolidation_regression.py tests/shared/test_query_intelligence_service.py tests/bioinformatics/test_bio_query_adapter.py tests/bioinformatics/test_search_center_router.py tests/meta_analysis/test_mainline_meta_contract.py -q
```

结果：

- `git status --short`：仅显示本报告所在 `docs/handoff/` 为新增未跟踪目录。
- `git diff --check`：通过。
- 只读 coverage audit 计算：`quality_gate_status=pass`，`covered=621/621`，`weighted_coverage_rate=1.0`，`core_covered=533/533`。
- 最小相关 pytest：`66 passed in 6.34s`。

说明：未直接运行 `python3 scripts/audit_medical_vocabulary_coverage.py` 的写入模式，因为该脚本会重写已有 generated JSON/markdown/metadata 时间戳或报告文件。本阶段只允许新增本审计报告，因此使用同一脚本的 `build_coverage_audit_report()` 进行只读计算。
