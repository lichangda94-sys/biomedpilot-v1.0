# Vocabulary Stage V0.1 Resource And Packaging Strategy

日期：2026-05-13

范围：`data/medical_terms/` 资源、SQLite 策略、源码/测试/打包后运行时定位策略。

## 1. 资源分层结论

`data/medical_terms/` 应作为共享词库资源进入 Git，但需要按资源类型分层：

| 资源 | 策略 | 理由 |
| --- | --- | --- |
| `zh_term_overrides.json` | 进入 Git，人工维护源数据 | 中文入口、同义词、上下文、概念映射和高风险别名需要人工审查 |
| `mini_medical_terms_index.json` | 进入 Git，curated runtime source + normalized runtime artifact | 它是包内默认运行时索引，也是人工策划概念的规范化快照 |
| `reference_checklists/*.json` | 进入 Git，审计源数据 | 定义覆盖率和质量门槛 |
| `source_metadata.json` | 进入 Git，资源治理和来源说明 | 记录 release、license、runtime strategy |
| `license_attribution.md` | 进入 Git，包内归属说明 | 包含外部来源和项目本地策划说明 |
| `coverage_audit_report.json` | 可进入 Git，但属于审计快照 | 可重复生成；进入 MainLine 前需接受 generated audit snapshot |
| `medical_terms_index_build_report.json` | 与 SQLite 同策略 | 只有跟踪 SQLite 时才应跟踪该 build report |
| `medical_terms_index.sqlite` | 默认不作为 MainLine 必需资源；是否跟踪需单独决定 | 二进制、可重复生成、当前是 mini-derived optional index |

## 2. `mini_medical_terms_index.json`

`mini_medical_terms_index.json` 兼具两种角色：

- 运行时默认索引：源码运行、测试运行和 packaged runtime 都可以直接读取。
- curated release snapshot：它把人工策划概念规范化成 `TermConcept` 可读取字段。

它不是外部 full ontology dump，也不是用户数据。它可以进入 Git，但更新必须通过审计和 tests。

更新要求：

1. 保持 schema 字段向后兼容。
2. 不直接导入未审查 full ontology。
3. 每个新增概念必须有 `concept_id`、`concept_type`、`category`、`contexts` 和必要 cross refs。
4. 修改后运行 coverage audit 和 shared vocabulary tests。

## 3. `zh_term_overrides.json`

`zh_term_overrides.json` 是人工维护源数据。它不是模型输出缓存，也不是自动采集结果。

维护规则：

- 中文术语必须映射到现有 runtime concept id。
- 短英文缩写只能在明确上下文和歧义说明存在时加入。
- Bioinformatics-only 输出不得包含 PubMed-only 主字段。
- Meta-only 输出不得包含 GEO / TCGA / GTEx 主字段。
- 本地模型候选不得直接写入 override；必须经过人工审查和测试。

## 4. SQLite 策略

当前 `medical_terms_index.sqlite`：

- 大小约 2.6 MB。
- schema：`biomedpilot.medical_terms.sqlite.v6`。
- fallback mode：`mini_vocabulary_only`。
- index kind：`mini-derived sqlite index`。
- terms count：572。
- 可由 `python3 scripts/update_medical_term_index.py` 重复生成。

V0.1 建议策略：

- MainLine 不应把 SQLite 作为必需资源。
- Runtime 应继续允许 SQLite absent/corrupt/schema mismatch 时回落到 JSON mini index。
- ReleaseBuild 可以选择生成或包含 SQLite，但必须记录 build command、schema、checksum、terms count 和 optional status。
- 如果 MainLine 决定跟踪 SQLite，必须说明原因：例如为了打包后启动速度、SQLite-first runtime parity、无网络可重复验证。否则应将 SQLite 视为派生 artifact。

如果后续决定 SQLite 不继续跟踪：

1. 先在 Integration 中确认 JSON fallback tests 全部通过。
2. 更新 `.gitignore` 或文档，避免重新误提交 SQLite。
3. 保留 build script 和 build report 模板。
4. 在 ReleaseBuild 或 CI 中生成 SQLite artifact。
5. 不删除 Vocabulary 当前文件，除非单独 cleanup 阶段明确授权。

## 5. Packaging 策略

当前 `scripts/package_app.py` 的 `COPY_DIRS` 不包含顶层 `data`，因此 packaged app 默认不会复制 `data/medical_terms/`。这是 MainLine 合入前的 Blocking 风险。

V0.1 不直接修改打包脚本。建议后续在 Integration 或 ReleaseBuild 做小范围 packaging 修复：

- 复制安全子集：
  - `data/medical_terms/mini_medical_terms_index.json`
  - `data/medical_terms/zh_term_overrides.json`
  - `data/medical_terms/source_metadata.json`
  - `data/medical_terms/license_attribution.md`
  - 必要时复制 `data/medical_terms/reference_checklists/` 用于开发者诊断，不用于普通 UI。
- 默认不复制 `data/medical_terms/raw/`。
- 默认不复制 full ontology source 文件。
- SQLite 是否复制取决于 optional SQLite 策略。

## 6. 运行时资源定位

当前 loader 从代码文件向上解析 repo/resource root：

- `app/shared/query_intelligence/medical_terms/term_index_loader.py`
- `app/shared/query_intelligence/medical_terms/zh_overrides_loader.py`
- 路径为 `Path(__file__).resolve().parents[4] / "data" / "medical_terms"`

三种场景：

| 场景 | 期望路径 |
| --- | --- |
| 源码运行 | `<repo>/data/medical_terms/` |
| 测试运行 | `<repo>/data/medical_terms/` |
| 打包后运行 | `<BioMedPilot.app>/Contents/Resources/app/data/medical_terms/` |

如果未来支持用户自定义资源路径，应通过显式配置或 provider 注入，不应让 Bioinformatics 或 Meta 各自硬编码词库路径。

## 7. 缺失资源降级策略

缺失资源时必须：

- 不导致 UI 崩溃。
- 不静默宣称 full vocabulary available。
- 不伪造检索结果或正式分析结果。
- 给 audit/status 返回可诊断字段。

当前 runtime 行为：

- `load_zh_overrides()` 缺失或解析失败返回空 tuple。
- `load_full_term_index()` 缺失、损坏、schema mismatch 返回空 tuple。
- `load_mini_term_index()` 缺失或解析失败返回空 tuple。
- `lookup_medical_terms()` 最后回退 `biomedical_term_registry`。
- 完全未知词返回 `matched=False` 和 warning。

建议后续增强：

- `active_index_status()` 增加 packaged resource status。
- packaging smoke test 验证默认资源存在。
- UI 只显示 testing-level / developer preview 诊断，不显示 raw path 细节。

## 8. Ontology 下载策略

`scripts/update_medical_term_index.py` 只有显式 `--download-sources` 或 legacy `--download` 才允许下载 MONDO / DOID / NCIt / MeSH / EFO。

规则：

- 默认构建不得联网。
- 测试不得真实联网。
- ReleaseBuild 不得默认联网。
- 外部 ontology subset 进入 runtime 前必须经过 license、category、context、short-token 和 negative leakage 审查。

## 9. MainLine 资源策略建议

推荐进入 MainLine 的最小资源：

- `zh_term_overrides.json`
- `mini_medical_terms_index.json`
- `source_metadata.json`
- `license_attribution.md`
- `reference_checklists/`
- build/audit scripts
- shared tests

暂不作为 MainLine 必需资源：

- `medical_terms_index.sqlite`
- `medical_terms_index_build_report.json`
- `data/medical_terms/raw/**`

必须先在 Integration 验证：

- JSON fallback。
- packaged app resource copy。
- SQLite absent / corrupt / schema mismatch。
- Bioinformatics / Meta context isolation。

## 10. 需要后续改打包脚本吗

需要，但不在本 V0.1 直接修改。

建议后续 Stage：

- `Stage V0.2` 或 Integration packaging task：小范围修改 `scripts/package_app.py`，只复制 `data/medical_terms` 默认安全子集。
- ReleaseBuild packaged smoke：启动后检查 `active_index_status()`，确认 mini 和 zh resources 可用。
