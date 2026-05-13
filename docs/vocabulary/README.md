# Vocabulary Shared Medical Vocabulary

BioMedPilot Vocabulary 是共享医学词库模块。它属于 shared capability，不属于 Bioinformatics 专属，也不属于 Meta Analysis 专属。

## 模块定位

Vocabulary 提供中文医学术语、英文医学术语、数据源候选、Meta 检索术语和上下文过滤能力。业务模块只能消费共享词库输出，不能各自维护疾病词库副本。

边界：

- Bioinformatics 可消费疾病、组织、癌种、GEO/TCGA/GTEx 相关候选和生信数据模态草稿。
- Meta Analysis 可消费 PICO/PICOS/PECO、outcome、exposure、intervention、comparator、effect measure、study design、PubMed/MeSH 草稿。
- Shared vocabulary 不执行真实检索，不下载数据，不做自动筛选，不做正式分析结论。

## 目录结构

- `app/shared/query_intelligence/medical_terms/`
  - runtime models、loader、lookup、normalizer、provider protocol、ontology importer scaffold
- `data/medical_terms/`
  - runtime JSON、中文 overrides、reference checklists、metadata、license、optional SQLite
- `scripts/update_medical_term_index.py`
  - 构建 optional SQLite index，默认不联网
- `scripts/audit_medical_vocabulary_coverage.py`
  - 运行 coverage audit
- `tests/shared/`
  - shared vocabulary、query intelligence、SQLite fallback、AI Gateway 边界测试
- `docs/handoff/`
  - MainLine 合入、资源策略和阶段审计文档

## 核心资源

- `zh_term_overrides.json`
  - 人工维护中文入口和高价值别名。
  - 必须映射到 runtime concept id。
- `mini_medical_terms_index.json`
  - 默认 runtime JSON index。
  - 当前同时作为 curated source snapshot 和 package-safe runtime asset。
- `medical_terms_index.sqlite`
  - optional SQLite enhancement。
  - 当前可由 mini index 生成，不是必需 runtime dependency。
- `reference_checklists/*.json`
  - 覆盖率和质量门槛源数据。
- `source_metadata.json`
  - 资源来源、license、runtime strategy 和 release metadata。
- `license_attribution.md`
  - 包内归属说明。

## JSON / SQLite / Override 关系

运行时顺序：

1. `zh_term_overrides.json`
2. `medical_terms_index.sqlite`，仅当存在且 schema 支持
3. `mini_medical_terms_index.json`
4. `biomedical_term_registry` fallback

SQLite 缺失、损坏或 schema mismatch 时必须回落到 JSON mini index。JSON mini 和 zh overrides 缺失时必须回落 registry，不得让 UI 崩溃。

## 如何更新词库

1. 明确新增术语属于哪个语义包：oncology、tissue、data modality、meta analysis term 等。
2. 更新 `mini_medical_terms_index.json` 和必要的 `zh_term_overrides.json`。
3. 更新或新增 reference checklist。
4. 运行 coverage audit。
5. 运行 shared vocabulary tests。
6. 检查 Bioinformatics 和 Meta context isolation。
7. 更新 handoff / stage report。

不得直接把本地模型输出写入词库。不得把 full ontology 原样导入 runtime。

## 覆盖率审计

写入模式：

```bash
python3 scripts/audit_medical_vocabulary_coverage.py
```

只读检查可以在测试或审计阶段调用：

```bash
python3 - <<'PY'
from scripts.audit_medical_vocabulary_coverage import build_coverage_audit_report
report = build_coverage_audit_report()
print(report["overall"]["quality_gate_status"])
PY
```

## 最小测试

```bash
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
  -q
```

## V0.1 测试覆盖图

- `tests/shared/test_medical_term_lookup.py`
  - provider 注入、zh override、最长中文匹配、index missing fallback。
- `tests/shared/test_medical_term_index_runtime_strategy.py`
  - SQLite-first、SQLite missing/corrupt/schema mismatch fallback、package manifest。
- `tests/shared/test_medical_terms_sqlite_index_build.py`
  - mini vocabulary 构建 SQLite、schema、重复构建。
- `tests/shared/test_medical_vocabulary_consolidation_regression.py`
  - checklist coverage、Bio/Meta context isolation、short token、modality boundary、SQLite/JSON consistency。
- `tests/shared/test_query_intelligence_service.py`
  - Bioinformatics 不返回 PubMed candidates、Meta 不返回 GEO/TCGA/GTEx candidates、AI Gateway module policy、raw model output 不进入 audit。
- `tests/shared/test_vocabulary_stage_v0_1_merge_readiness.py`
  - V0.1 合入准备：默认资源可加载、SQLite optional、ontology 下载默认关闭、provider unmatched contract、Bio/Meta 搜索面隔离。
- `tests/bioinformatics/test_bio_query_adapter.py` 和 `tests/bioinformatics/test_search_center_router.py`
  - Bioinformatics search draft 只面向 GEO/TCGA/GTEx，不接入 PubMed。
- `tests/meta_analysis/test_mainline_meta_contract.py`
  - MainLine Meta 仍是 shell contract，不由 Vocabulary 混入业务流程。

## 避免 Bioinformatics / Meta 语义污染

Bioinformatics：

- 不得执行 PubMed 检索。
- 不得消费 PubMed-only、effect measure、PICO-only 主输出。
- 宽泛 modality-only query 必须走 broad guard 或用户确认。
- 只输出 GEO/GSE、TCGA/GDC、GTEx、local expression data 相关候选。

Meta Analysis：

- 不得调用 GEO / TCGA / GTEx 生信流程。
- PubMed / MeSH query 只能作为草稿，执行前需要用户确认。
- 必须保留 draft / confirmed / user edited 治理状态。

## 中文到英文映射

中文映射优先级：

1. 精准人工 override。
2. runtime index exact / boundary-aware match。
3. mini index。
4. registry fallback。
5. 可选本地模型候选，仅用于 unknown term suggestion，不进入正式 query。

高风险中文词必须包含上下文、source、confidence 和 mapped concept id。

## 高风险术语规则

短 token、缩写、组织、癌种、结局指标和 effect measure 需要显式测试。

重点术语：

- 癌种缩写：`PTC`、`SCC`、`RCC`、`CRC`、`HCC`、`GBM`、`LGG`
- Meta 指标：`OS`、`HR`、`OR`、`RR`、`CI`、`MD`、`SMD`、`PR`、`SD`、`PD`
- 数据模态：`RNA`、`DNA`、`CNV`、`SNP`、`WGS`、`WES`、`TPM`、`FPKM`
- 组织词：thyroid、liver、lung、brain、adipose tissue、bone marrow、lymph node

规则：

- 短英文大写 token 使用 exact / boundary-aware match。
- 组织词不得自动升级为疾病。
- modality-only term 不得误匹配为疾病或核心检索概念。
- Bioinformatics context 过滤 Meta-only 输出。
- Meta context 过滤 GEO/TCGA/GTEx 输出。

## Provider Contract

`MedicalVocabularyProvider.lookup(query, normalized_query, target_context)` 必须：

- 返回 `VocabularyProviderMatch`。
- 不执行网络访问。
- 不调用本地模型。
- 不下载 ontology。
- 不保存 raw prompt、raw response 或用户输入全文。
- 失败时返回 unmatched match，或通过 `TermLookupResult.warnings` 表达可诊断状态。
- provider 可用于测试或外部注入，但默认 runtime 仍必须保持 JSON / SQLite / registry fallback 可用。

## 禁止事项

- 不得让 Bioinformatics 执行 PubMed 检索。
- 不得让 Meta 调用 GEO / TCGA / GTEx 生信流程。
- 不得绕过 AI Gateway。
- 不得记录 raw prompt / raw response。
- 不得把本地模型输出直接写入正式词库。
- 不得直接全量导入 ontology 到 runtime。
- 不得把 Vocabulary 分支整分支合入 MainLine。
- 不得删除 MainLine handoff / cleanup / archive 文档。
