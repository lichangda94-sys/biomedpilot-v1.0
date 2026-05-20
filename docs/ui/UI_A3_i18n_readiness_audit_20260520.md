# UI-A3 i18n Readiness Audit

Date: 2026-05-20

Scope: UIShell target UI internationalization and multilingual readiness audit.

## 1. 审计范围

本阶段基于以下输入进行只读审计：

- `docs/ui/UI_A1_target_markdown_architecture_audit_20260520.md`
- `docs/ui/UI_A2_visual_brand_resource_audit_20260520.md`
- `docs/ui/target_design_drafts/**`
- `docs/ui/UI_Cross_Branch_Runtime_IA_Audit_20260519.md`
- `docs/bioinformatics/stage_B8_0_1_analysis_ui_prebuild_supplemental_audit_20260520.md`
- `app/**`
- `tests/**`
- `docs/**`
- `config/**`
- `scripts/package_app.py`

审计重点：

- 当前中文硬编码来源、测试断言依赖、报告模板和导出文本。
- 未来英文版、西班牙语版及其他语言版本需要的 key、术语表、模板系统和布局弹性。
- Bioinformatics B8.0.1 语义状态、Meta Analysis Developer Preview 边界、LabTools 术语边界。
- 品牌命名层级：`萤火虫 / Firefly`、`BioMedPilot`、`医研智析` 的显示、打包和报告命名关系。

## 2. 本阶段未修改业务代码声明

本阶段只新增本审计报告。未抽取 i18n 文件，未翻译 UI，未修改业务代码、测试、报告模板、配置、资源、图标、图片、打包脚本或桌面入口；未引入依赖；未重构 UI；未重新打包；未运行 packaged app。

## 3. 中文硬编码来源

| file_path | text_sample | category | user_visible_or_developer | current_language | suggested_i18n_key_group | priority |
|---|---|---|---|---|---|---|
| `app/shell/login.py` | `BioMedPilot / 医研智析`, `欢迎使用 BioMedPilot`, `进入 BioMedPilot`, `本地测试版` | Welcome / Login / About | user visible | zh + en mixed | `shell.login.*`, `brand.*`, `app.status.*` | P0 |
| `app/shell/module_selection.py` | `生信分析模块`, `进入生信分析模块`, `Meta 分析模块`, `订阅 / VIP 服务：预留功能` | Dashboard | user visible | zh + en mixed | `dashboard.*`, `module.*`, `app.status.*` | P0 |
| `app/shell/sidebar.py` | `生信分析`, `Meta 分析`, `设置中心`, `测试入口` | Dashboard / Sidebar / Topbar | user visible | zh + en mixed | `nav.*` | P0 |
| `app/shell/main_window.py` | `Settings / 设置中心`, `设置中心当前为占位页...语言...导出格式...` | Settings | user visible + developer | zh + en mixed | `settings.*`, `settings.placeholder.*` | P0 |
| `app/shared/feature_availability.py` | `已开放`, `测试中`, `待接入`, `暂未开放` | Error / Warning / Empty State | user visible | zh | `feature.status.*` | P0 |
| `app/meta_analysis/workspace.py` | `Meta 分析模块`, `完整功能在 dev/meta-analysis 分支继续开发` | Meta Analysis | user visible + developer | zh + branch names | `meta.shell.*`, `app.status.*` | P0 |
| `app/bioinformatics/project_home.py` | `生信分析模块`, `当前状态：Developer Preview / 本地测试版`, `请先创建或打开一个生信分析项目。` | Bioinformatics | user visible | zh + en mixed | `bio.project_home.*`, `bio.status.*` | P0 |
| `app/bioinformatics/workflow_pages.py` | `数据识别`, `继续：数据准备与标准化`, `导出数据识别报告`, `不能继续：暂无可用于报告的结果。` | Bioinformatics / Report / Export | user visible | zh + en mixed | `bio.workflow.*`, `bio.action.*`, `bio.warning.*` | P0 |
| `app/bioinformatics/project_workflow_orchestrator.py` | `工作区验证`, `数据获取`, `未开始`, `完成但有警告`, `尚未生成项目报告。` | Bioinformatics / Developer Diagnostics | user visible + developer | zh | `bio.workflow.stage.*`, `workflow.status.*` | P0 |
| `app/bioinformatics/reports/project_report_builder.py` | `BioMedPilot 生信项目报告`, `BioMedPilot 生信项目报告草稿`, `报告草稿不会生成假差异基因表` | Report / Export | user visible | zh + en mixed | `report.bio.*`, `report.disclaimer.*` | P0 |
| `app/bioinformatics/services/bio_report_service.py` | `至少选择一个 JSON 结果文件。`, `报告导出`, `测试中`, `Bioinformatics Test Summary` | Report / Export | user visible + developer | zh + en mixed | `report.bio_export.*`, `feature.bio_report.*` | P0 |
| `app/bioinformatics/recognition_detail_report.py` | `BioMedPilot 数据识别报告` | Report / Export | user visible | zh + en mixed | `bio.recognition_report.*` | P1 |
| `app/shared/testing_mode.py` | `验证 BioMedPilot Dashboard...反馈流程是否清楚可用。`, `# BioMedPilot Test Feedback` | Developer Diagnostics / Test Feedback | developer + tester | zh + en mixed | `testing_mode.*` | P1 |
| `app/shared/report_center/__init__.py` | `生信分析报告`, `Meta 分析报告`, `图表包`, `结果表`, `导出历史` | Report / Export | planned user visible | zh | `report_center.*` | P1 |
| `app/shared/query_intelligence/biomedical_term_registry.py` | `甲状腺癌`, `脑胶质瘤`, `转录组`, `生信数据集检索` | Medical terminology | user visible + internal vocabulary | zh + en terms | `terminology.bio.*` | P0 |
| `scripts/package_app.py` | `CFBundleDisplayName: BioMedPilot / 医研智析` | Packaging / App identity | user visible in OS | zh + en mixed | `bundle.identity.*` with build-time freeze | P0 |
| `tests/ui/test_login_page.py` | assertions around old login brand, VIP/license, register/forgot placeholders | Tests assertions | test-only | zh + en mixed | use semantic objectName / roles | P0 |
| `tests/ui/test_module_selection.py` | Dashboard labels, module names, icon summary, settings placeholder | Tests assertions | test-only | zh + en mixed | use `module_id`, `buttonRole`, page keys | P0 |
| `tests/ui/test_sidebar.py` | fixed sidebar labels and order | Tests assertions | test-only | zh + en mixed | use nav item keys and objectName | P0 |
| `tests/ui/test_bioinformatics_workflow_pages.py` | hundreds of Chinese UI/report/status assertions including `请先创建或打开生信分析项目。` | Tests assertions | test-only | zh + en mixed | use i18n keys + semantic states | P0 |
| `tests/bioinformatics/test_*service.py` | service messages such as `请选择`, `不存在`, `测试中` | Tests assertions | test-only | zh | use message codes and status enums | P0 |
| `tests/test_package_app.py` | package smoke checks include `BioMedPilot / 医研智析` | Tests assertions | test-only | zh + en mixed | assert bundle identity variables, not literal localized display text | P1 |
| `docs/**` | historical Chinese reports and target drafts | Documentation | docs only | zh + en mixed | no runtime extraction; use as source requirements | P2 |

Coverage note: the repository contains many repeated short phrases. This table groups the main sources that affect user-visible UI, reports, exports, diagnostics, package identity, and tests; it does not enumerate every repeated short word.

## 4. 品牌命名多语言策略

| brand_or_module_name | zh_display | en_display | should_translate | should_keep_original | risk | suggested_rule |
|---|---|---|---|---|---|---|
| 萤火虫 | 萤火虫 | Firefly | controlled brand pair only | yes | A1/A2 target brand is not yet wired into runtime; free translation could fragment identity. | Welcome H1 may use `萤火虫 / Firefly` after brand freeze; never translate ad hoc as a descriptive noun. |
| Firefly | 萤火虫 | Firefly | no | yes | Lowercase `firefly` in prose may look generic. | Treat as product brand token `brand.primary.en`. |
| BioMedPilot | BioMedPilot | BioMedPilot | no | yes | Runtime, bundle name, tests and reports still depend on BioMedPilot. | Keep as technical/bundle identity for now; expose as app family or internal product name until Visual Style Guide freezes final public brand. |
| 医研智析 | 医研智析 | not frozen | no free translation | yes | `BioMedPilot / 医研智析` appears in UI and bundle display name, but English subtitle is undefined. | Keep Chinese subtitle in zh locale; do not invent English marketing translation until brand guide. |
| Bioinformatics / 生信分析 | 生信分析 | Bioinformatics | yes as label pair | keep English scientific term | Module labels differ across shell, reports and docs. | Use `module.bioinformatics.name` with locale-specific display; preserve Bioinformatics in English locale and allow zh paired display in first mention. |
| Meta Analysis / Meta 分析 | Meta 分析 | Meta Analysis | yes as label pair | keep English method name | Could be incorrectly expanded to systematic review or meta-analysis workflow in all contexts. | Module name remains `Meta Analysis / Meta 分析`; use `systematic review`, `荟萃分析`, `系统综述` only in workflow-specific copy. |
| LabTools / 实验工具 | 实验工具 | LabTools | yes as label pair | keep LabTools | A1 flagged `Labors` as wrong/legacy. | Use `LabTools` as module brand and `实验工具` as zh explanation; never use `Labors` for product UI. |
| Settings / 设置中心 | 设置中心 | Settings | yes | no | Settings can become a dumping ground for technical resource entries. | Use `settings.name`; separate user settings from developer diagnostics and external resource management. |
| Developer Preview / 本地测试版 | 本地测试版 | Developer Preview | yes, controlled status | keep English status token | Over-localizing as production-ready language could mislead users. | Use `app.status.developer_preview`; keep visible and explicit in both locales. |
| Report Draft / 报告草稿 | 报告草稿 | Report Draft | yes | no | Current report copy can be mistaken for report-ready output. | Use `report.status.draft`; never render as final report unless report-ready gate passes. |

Brand conclusion:

- Welcome H1 can move toward `萤火虫 / Firefly` only after UI-A2 brand freeze.
- Bundle name should temporarily remain `BioMedPilot`; changing bundle identity is outside i18n extraction and must be handled with packaging/desktop-entry review.
- Report titles should use brand variables instead of fixed literals such as `BioMedPilot 生信项目报告`.

## 5. UI 文案类型分类

| copy_type | ordinary_i18n_key | needs_terminology_table | keep_english | needs_report_template_system | temporarily_do_not_translate | notes |
|---|---:|---:|---:|---:|---:|---|
| 固定导航标签 | yes | no | sometimes | no | no | Use `nav.*`; tests should assert page key or objectName. |
| 页面标题 | yes | sometimes | sometimes | no | no | First mention can use bilingual labels where target design requires. |
| 卡片标题 | yes | sometimes | sometimes | no | no | Dashboard card layout must tolerate longer Spanish. |
| 按钮 | yes | no | sometimes | no | no | Buttons should use short verb phrases, not long limitation sentences. |
| 状态标签 | yes | yes for analysis status | yes for enum code | no | no | Status semantics must remain separate from localized label. |
| 表单字段 | yes | sometimes | sometimes | no | no | Scientific fields may need label + tooltip. |
| 表格列名 | yes | yes | sometimes | no | no | Must support truncation/tooltip or responsive columns. |
| 错误提示 | yes | sometimes | sometimes | no | no | Prefer message code + localized template + parameters. |
| 警告提示 | yes | yes for scientific warnings | sometimes | no | no | TCGA+GTEx and imported DEG warnings require fixed bilingual wording. |
| 空状态说明 | yes | no | no | no | no | Empty states often contain long Chinese explanation; split title/body/action. |
| 帮助说明 | yes | yes | sometimes | no | no | Long help text belongs in body/tooltip, not buttons. |
| Developer Preview / limitation 文案 | yes | yes for status terms | keep status tokens | no | no | Must not imply formal analysis completion. |
| 报告正文 | no, not simple keys only | yes | sometimes | yes | no | Needs language-aware report templates, not string replacement. |
| 导出文件名 | controlled key/slug | no | prefer ASCII slug | yes for package manifests | no | Default filenames should be ASCII-safe with localized display name separately. |
| 医学/实验术语 | no ordinary free text | yes | many acronyms remain English | report templates need same glossary | no | Build a terminology table with zh/en/es/canonical ids. |
| 分析方法名 | yes + terminology | yes | DEG/GSEA/ORA etc. | yes | no | Keep canonical method acronyms stable. |
| 数据库/资源名称 | no translation | yes for display notes | yes | no | yes for official names | GEO, TCGA, GTEx, ImageJ/Fiji, GO/KEGG remain official names. |
| 开发者诊断 | yes if surfaced | no | many technical tokens | no | maybe | Developer-only copy can lag behind user-facing i18n, but must be separated. |

## 6. Bioinformatics i18n 审计

Bioinformatics 当前运行态已经有大量中文页面、按钮、状态和报告文案。A1/B8.0.1 的关键约束是 resolver-first、preflight-first、result-schema-first，不得把测试态、预检态或导入结果误译为正式分析能力。

### 6.1 关键语义状态 key 建议

| key | zh_label | en_label | usage_rule |
|---|---|---|---|
| `analysis.status.preflight_only` | 仅预检，未执行正式分析 | Preflight only, formal analysis not executed | Used for DEG/GSEA/survival/clinical association before formal runner and resolver are complete. |
| `analysis.status.developer_preview` | Developer Preview / 本地测试版 | Developer Preview | Product maturity label; keep visible. |
| `analysis.status.testing_level` | 测试级结果 | Testing-level result | Used for dry-run or testing summaries; never report-ready. |
| `analysis.status.blocked_missing_resolver` | 缺少标准化输入解析器，暂不能运行 | Blocked: standardized input resolver missing | Formal analysis button must be disabled or hidden. |
| `analysis.status.blocked_missing_result_schema` | 缺少稳定结果结构，暂不能生成正式结果 | Blocked: stable result schema missing | Blocks plot/report-ready output. |
| `analysis.status.planned_placeholder` | 计划中，占位未开放 | Planned placeholder | Used for future features, not runnable actions. |
| `result.semantic.imported_external_result` | 外部导入结果 | Imported external result | Imported DEG or external table; not BioMedPilot recomputation. |
| `result.semantic.formal_computed_result` | BioMedPilot 正式计算结果 | BioMedPilot formal computed result | Only after runner, provenance, result schema and validation gate pass. |
| `result.semantic.not_biomedpilot_recomputed` | 未由 BioMedPilot 重新计算 | Not recomputed by BioMedPilot | Must appear near imported DEG reuse. |
| `bio.warning.tcga_gtex_no_auto_merge` | TCGA 与 GTEx 不会自动合并为默认分析路径；需完成批次、组织和样本可比性检查。 | TCGA and GTEx are not auto-merged by default; batch, tissue and sample comparability checks are required. | Fixed warning for TCGA+GTEx. |
| `bio.warning.standardized_repository_required` | 请先生成标准化数据仓库。 | Generate the standardized data repository first. | Gate formal analysis task center. |
| `bio.warning.analysis_input_package_required` | 请先生成分析输入包。 | Generate the analysis input package first. | Gate formal DEG/GSEA/ORA/correlation/survival tasks. |
| `bio.action.run_preflight` | 运行预检 | Run preflight | Safe primary action before formal backend completion. |
| `bio.action.generate_input_package` | 生成分析输入包 | Generate analysis input package | Safe shell action after standardization. |
| `bio.report.disclaimer.testing_summary_only` | 本报告仅为测试摘要，不代表正式生信分析结果。 | This report is a testing summary and does not represent formal bioinformatics results. | Required in testing reports and drafts. |

### 6.2 模块级审计结论

- GEO / TCGA / GTEx / local import labels should use official source names plus localized descriptions; source names themselves should not be translated.
- Data check, preparation, grouping and design copy must separate data availability from analysis readiness.
- DEG / GSEA / ORA / correlation / survival / clinical association labels need three layers: display label, runnable status, and result semantic status.
- `preflight_only`, `testing_level`, `developer_preview`, `result_schema_missing`, `resolver_missing` must be stable semantic keys, not free translated prose.
- Imported DEG must always render as `imported_external_result` unless a formal BioMedPilot runner recomputes it.
- TCGA+GTEx automatic merge must never be a default-language implication. Both zh/en warning text should be fixed before UI rebuild.
- Report export must distinguish draft, testing summary, and report-ready package. Current Markdown report is a draft.

## 7. Meta Analysis i18n 审计

Current UIShell Meta runtime is shell-only / Developer Preview. Target drafts define multiple meta-analysis types, but A1 requires that planned or testing states remain explicit and that AI suggestion never becomes automatic conclusion.

| meta_type_key | zh_label | en_label | status | translation_risk | suggested_rule |
|---|---|---|---|---|---|
| `binary_outcome_meta` | 二分类结局 Meta 分析 | Binary outcome meta-analysis | testing schema / future workflow | Translating as generic systematic review may hide effect measure requirements. | Keep type key; label includes outcome class. |
| `continuous_outcome_meta` | 连续型结局 Meta 分析 | Continuous outcome meta-analysis | testing schema / future workflow | SMD/MD terminology may drift. | Require glossary entries for MD, SMD and units. |
| `survival_outcome_meta` | 生存结局 Meta 分析 | Survival outcome meta-analysis | testing schema / future workflow | HR, survival and prognosis can be conflated. | Keep HR and survival terms stable. |
| `prevalence_incidence_meta` | 患病率 / 发病率 Meta 分析 | Prevalence / incidence meta-analysis | testing schema / future workflow | Prevalence and incidence must not be merged. | Separate prevalence and incidence terms. |
| `diagnostic_accuracy_meta` | 诊断准确性 Meta 分析 | Diagnostic accuracy meta-analysis | testing schema / future workflow | Sensitivity/specificity/SROC terms need fixed translations. | Use diagnostic glossary. |
| `exposure_disease_risk_meta` | 暴露-疾病风险 Meta 分析 | Exposure-disease risk meta-analysis | testing schema / future workflow | Risk/association/causality may be overclaimed. | Avoid causal wording unless protocol says so. |
| `biomarker_expression_difference_meta` | 生物标志物表达差异 Meta 分析 | Biomarker expression difference meta-analysis | testing schema / future workflow | Biomarker and differential expression may be confused with Bioinformatics DEG. | Use Meta context label, not Bio DEG result label. |
| `correlation_meta` | 相关性 Meta 分析 | Correlation meta-analysis | testing schema / future workflow | Correlation may be mistranslated as association or causation. | Keep `correlation` semantic key. |
| `prognostic_factor_meta` | 预后因素 Meta 分析 | Prognostic factor meta-analysis | testing schema / future workflow | Prognostic factor and survival outcome overlap. | Use factor-focused language. |
| `dose_response_meta` | 剂量-反应 Meta 分析 | Dose-response meta-analysis | testing schema / future workflow | Dose-response curve terms need specialized translation. | Require methods glossary. |
| `NETWORK_META_ANALYSIS` | 网状 Meta 分析 | Network meta-analysis | planned only | Biggest overclaiming risk if shown as runnable. | May appear only as planned/disabled; not a formal entry. |

Meta-specific i18n rules:

- PICO / PECO / PICOS remain official acronyms with localized explanations.
- Search strategy, screening, full-text, data extraction, quality assessment, effect size, forest plot, heterogeneity and publication bias require a methods glossary.
- `AI suggestion` should translate as `AI 建议 / AI-assisted suggestion`, not automatic conclusion.
- Current shell-only warning needs fixed copy: zh `当前为 UIShell 占位入口，完整 Meta Analysis 工作流尚未在本壳层开放。`; en `This is a UIShell placeholder entry; the full Meta Analysis workflow is not yet available in this shell.`

## 8. LabTools i18n 审计

LabTools target drafts are not currently implemented in UIShell, but A1/A2 flagged LabTools terminology as important before UI rebuild.

| term | zh_label | en_label | translate_policy | suggested_rule |
|---|---|---|---|---|
| LabTools | 实验工具 | LabTools | keep English brand + localized explanation | LabTools is not Labors. |
| 通用计算器 | 通用计算器 | General calculators | translate label | Keep separate from experiment-specific calculators. |
| 试剂制备 | 试剂制备 | Reagent preparation | translate label | Reagent recipes need glossary and unit rules. |
| 实验记录系统 | 实验记录系统 | Experiment record system | translate label | Record/export labels should use stable nouns. |
| 实验模块 | 实验模块 | Experiment modules | translate label | Parent category only, not a runnable button. |
| 细胞实验 | 细胞实验 | Cell experiments | translate label | MTT/CCK-8/AlamarBlue belong here or cytotoxicity/cell viability, not ELISA. |
| 蛋白实验 | 蛋白实验 | Protein experiments | translate label | BCA, Western Blot and SDS-PAGE must stay stable. |
| 核酸实验 | 核酸实验 | Nucleic acid experiments | translate label | Require molecular biology glossary. |
| 免疫与吸光度实验 | 免疫与吸光度实验 | Immunoassay and absorbance assays | translate label carefully | Do not place MTT/CCK-8/AlamarBlue under ELISA-only labels. |
| 免疫组化 | 免疫组化 | Immunohistochemistry / IHC | bilingual | IHC acronym can be shown after first mention. |
| Western Blot | Western Blot | Western blot | keep established term | Avoid free translation. |
| BCA | BCA | BCA assay | keep acronym | Do not place under general calculator or ELISA. |
| SDS-PAGE | SDS-PAGE | SDS-PAGE | keep acronym | Do not place under general calculator. |
| MTT / CCK-8 / AlamarBlue | MTT / CCK-8 / AlamarBlue | MTT / CCK-8 / AlamarBlue | keep assay names | Add localized category explanation, not translated assay names. |
| ImageJ/Fiji | ImageJ/Fiji | ImageJ/Fiji | keep official engine name | External image engine name should not be translated. |
| external image engine | 外部图像分析引擎 | External image analysis engine | translate descriptor | User-triggered detect/install/update only. |
| reagent template | 试剂模板 | Reagent template | translate label | Template schema should be key-driven. |
| preparation record | 制备记录 | Preparation record | translate label | Report/export template needed. |
| inventory record | 库存记录 | Inventory record | translate label | Table columns need i18n. |

LabTools risks:

- `Labors` must be treated as legacy/wrong naming.
- Standard experiment acronyms should be canonical terminology entries, not ordinary UI strings.
- Formula rows, unit labels and export columns need parameterized translation, not concatenated Chinese strings.

## 9. 报告与导出 i18n 审计

| report_or_export | current_language | template_location | needs_i18n | needs_terminology_table | complexity | suggested_strategy |
|---|---|---|---:|---:|---|---|
| Bioinformatics Markdown project draft | zh + en mixed | `app/bioinformatics/reports/project_report_builder.py` | yes | yes | high | Convert to language-aware template with report status, provenance and result semantic variables. |
| Bioinformatics testing summary export | en body + zh validation messages | `app/bioinformatics/services/bio_report_service.py` | yes | yes | medium | Keep ASCII filename; localize display title and disclaimer through report template. |
| Bioinformatics standard report config | mostly en slugs | `config/bioinformatics/analysis_defaults.yaml` | partial | yes | medium | Keep filenames as ASCII slugs; localize UI labels separately. |
| Bioinformatics recognition/detail reports | zh + en technical terms | `app/bioinformatics/recognition_detail_report.py`, `workflow_pages.py` | yes | yes | high | Use report section keys and terminology table; avoid concatenated sentence fragments. |
| Meta Analysis future report draft | target design only / docs | target drafts and Meta docs | yes | yes | high | Build report template system before formal report UI; AI suggestion must stay suggestion. |
| LabTools TXT / CSV / Markdown / XLSX exports | target design only / future | target drafts | yes | yes | high | Separate export schema keys from localized column labels; default filenames should be ASCII-safe. |
| Test Feedback Markdown | en headings + zh summary source | `app/shared/testing_mode.py` | yes | no | low | Keep developer/tester template separate from end-user report templates. |
| DEG CSV filenames | ASCII slug pattern | `config/bioinformatics/analysis_defaults.yaml` | display only | yes | low | Keep filename template ASCII; localize UI display name and report caption. |
| Logs / manifest / provenance | mostly en keys + zh summaries | `app/bioinformatics/**`, `scripts/bio_geo_random_recognition_audit.py` | partial | yes | medium | Machine manifest keys stay English; localized summaries generated separately. |
| Figure titles / captions | not formalized | current plot/report placeholders | yes | yes | high | Must wait for result schema and Visual Style Guide before high-fidelity report export. |

Report conclusions:

- UI translation and report translation are separate systems.
- Report templates should accept `language`, `brand`, `module`, `status`, `result_semantics`, `terminology_profile`, and `provenance` parameters.
- Medical/statistical/experimental terms need a fixed glossary before formal multilingual reports.
- Default export filenames should avoid non-ASCII where portability matters; localized names can appear in UI and document titles.

## 10. 布局与英文/西班牙语长度风险

| ui_area | zh_text | expected_en_text_or_category | length_risk | layout_risk | suggested_layout_rule |
|---|---|---|---|---|---|
| Sidebar | `生信分析`, `Meta 分析`, `设置中心`, `测试入口` | Bioinformatics, Meta Analysis, Settings, Testing Mode | medium | Current sidebar width is fixed around 190 px and may truncate Spanish labels. | Use min/max responsive width, icon + short label, tooltip for full label. |
| Dashboard module card | `进入生信分析模块` | Open Bioinformatics workspace | high | Long button text and card copy may overflow fixed card grids. | Button uses short verb label; details go into body text. |
| Settings secondary nav | `外部引擎、模型、图像分析引擎、R/Python 包...` | External engines, models, image analysis engines, R/Python packages | high | Settings nav can become too wide or wrap inconsistently. | Use grouped tabs, short labels, descriptions below. |
| Bioinformatics task buttons | `运行 GEO 差异分析`, `绘制火山图`, `生成分析输入包` | Run GEO differential expression analysis / Generate analysis input package | high | Formal-looking long labels can overflow and overclaim capability. | Use compact action label + status chip + tooltip; disable/hide unsafe formal buttons. |
| Tables | `任务`, `是否可运行`, `来源与状态`, `缺失输入` | Task, Runnable, Source and status, Missing inputs | medium | Column headers grow in English/Spanish; dense tables risk horizontal overflow. | Allow horizontal scroll and column tooltips; avoid full sentences in headers. |
| Status labels | `完成但有警告`, `暂未开放`, `仅预检` | Completed with warnings, Not yet available, Preflight only | high | Status chips can expand and shift layouts. | Use fixed semantic chip sizes with wrapping or abbreviated label + tooltip. |
| Report Export buttons | `生成 / 刷新项目报告`, `导出 DOCX`, `导出 HTML` | Generate / refresh project report, Export DOCX, Export HTML | medium | Slash-separated labels are harder to localize. | Split combined actions where possible; use menu for export formats. |
| LabTools formula rows | `终浓度`, `母液浓度`, `目标体积` | Final concentration, Stock concentration, Target volume | high | Labels and units can exceed row width. | Use label column with responsive wrapping and stable unit selectors. |
| Meta type selection cards | `生物标志物表达差异 Meta 分析` | Biomarker expression difference meta-analysis | high | Card titles become very long. | Use title + method subtitle; allow two-line title and stable card height. |
| Dialogs / warning boxes | `TCGA 与 GTEx 不会自动合并为默认分析路径...` | Long fixed scientific warning | high | Long warnings can crowd modal buttons. | Use warning title + expandable details; buttons stay short. |

Spanish readiness note: Spanish labels often run longer than English. UI-A4 should require width, wrapping and tooltip rules before implementation of high-density shell, Settings, task center, report/export and LabTools formula controls.

## 11. 测试风险

| test_file | assertion_type | current_text_or_target | risk | suggested_update |
|---|---|---|---|---|
| `tests/ui/test_sidebar.py` | literal labels + nav order | `生信分析`, `Meta 分析`, `设置中心` | Language switch breaks test; target IA changes break order assertions. | Assert `nav_key`, objectName and route target; keep one zh smoke snapshot if needed. |
| `tests/ui/test_login_page.py` | literal brand/login copy | `BioMedPilot / 医研智析`, VIP/license/register placeholders | Brand freeze and locale switch break tests. | Assert semantic fields and visible key group; move literal text to locale fixture tests. |
| `tests/ui/test_module_selection.py` | literal Dashboard labels | module titles, icon summaries, Developer Preview labels | Dashboard rebuild and i18n will require large test rewrites. | Assert module IDs, button roles and availability states. |
| `tests/ui/test_app_identity.py` | brand/icon slot text | `APP_NAME`, icon descriptions | Bundle vs public brand split may fail tests. | Separate package identity tests from localized display-name tests. |
| `tests/test_package_app.py` | packaged smoke stdout / Info.plist | `BioMedPilot / 医研智析` | Localized display name and bundle name may diverge. | Assert Info.plist keys through expected variables; do not assume current localized display literal forever. |
| `tests/test_unified_entry.py` | Dashboard contract literal | `BioMedPilot / 医研智析` | New `萤火虫 / Firefly` target will break test. | Use `brand.primary_display_key` or frozen brand fixture. |
| `tests/ui/test_bioinformatics_workflow_pages.py` | hundreds of UI/report/status literals | `请先创建或打开生信分析项目。`, `导出数据识别报告`, `BioMedPilot 生信项目报告草稿` | Highest i18n migration risk; tests currently act as Chinese copy snapshots. | Introduce page keys, button roles, state enums and targeted locale snapshot tests. |
| `tests/bioinformatics/test_bio_report_service.py` | message/title/status literals | `至少选择`, `报告导出`, `测试中`, English summary title | Mixed zh/en service output makes locale behavior ambiguous. | Assert error codes and report semantic status; add locale-specific rendering tests later. |
| `tests/bioinformatics/test_geo_import_service.py` and related services | message fragments | `请选择`, `不存在`, `下载计划`, `测试中` | Service tests tightly couple logic to Chinese messages. | Add machine-readable result codes; keep text assertions only in i18n renderer tests. |
| `tests/bioinformatics/test_result_report_manifest.py` | report draft literals | section titles, imported DEG disclaimers | Report template i18n will break exact Markdown assertions. | Assert report manifest semantics; add per-locale golden files after template system. |
| `tests/bioinformatics/test_search_center_router.py` | Chinese biomedical queries and warning strings | `甲状腺癌`, `GTEx 在线检查失败...` | Some Chinese terms are legitimate NLP fixtures, but warning strings are UI/report copy. | Keep query fixtures; convert warnings to codes + localized renderer tests. |
| `tests/shared/test_testing_mode.py` | feedback template literals | `BioMedPilot Test Feedback`, `Project Creation` | Tester template may need locale setting. | Keep English developer template if policy says developer-only; otherwise add locale parameter. |

Testing conclusion: future i18n work should not begin by replacing strings in place. It first needs semantic IDs, status enums, objectName/page_key coverage, and a small number of locale snapshot tests.

## 12. i18n key 初始建议

### 12.1 Global shell and brand

- `brand.primary.zh`
- `brand.primary.en`
- `brand.technical_name`
- `brand.zh_subtitle`
- `app.status.developer_preview`
- `app.status.local_testing`
- `nav.dashboard`
- `nav.bioinformatics`
- `nav.meta_analysis`
- `nav.labtools`
- `nav.settings`
- `nav.testing_mode`
- `shell.login.title`
- `shell.login.action.enter`
- `shell.dashboard.title`
- `settings.placeholder.summary`

### 12.2 Feature and status

- `feature.status.open`
- `feature.status.testing`
- `feature.status.placeholder`
- `feature.status.unavailable`
- `workflow.status.not_started`
- `workflow.status.running`
- `workflow.status.completed`
- `workflow.status.completed_with_warnings`
- `workflow.status.skipped`
- `workflow.status.failed`
- `workflow.status.unavailable`
- `workflow.status.unknown`

### 12.3 Bioinformatics

- `module.bioinformatics.name`
- `bio.project.required_open_project`
- `bio.workflow.stage.workspace_validation`
- `bio.workflow.stage.acquisition`
- `bio.workflow.stage.recognition`
- `bio.workflow.stage.initial_readiness`
- `bio.workflow.stage.standardization`
- `bio.workflow.stage.task_center`
- `bio.workflow.stage.results`
- `bio.workflow.stage.report`
- `bio.action.run_preflight`
- `bio.action.generate_input_package`
- `analysis.status.preflight_only`
- `analysis.status.developer_preview`
- `analysis.status.testing_level`
- `analysis.status.blocked_missing_resolver`
- `analysis.status.blocked_missing_result_schema`
- `result.semantic.imported_external_result`
- `result.semantic.formal_computed_result`
- `bio.warning.tcga_gtex_no_auto_merge`
- `bio.report.disclaimer.testing_summary_only`

### 12.4 Meta Analysis

- `module.meta_analysis.name`
- `meta.shell.placeholder_warning`
- `meta.workflow.pico`
- `meta.workflow.peco`
- `meta.workflow.picos`
- `meta.ai_suggestion.label`
- `meta.ai_suggestion.disclaimer`
- `meta.type.binary_outcome_meta`
- `meta.type.continuous_outcome_meta`
- `meta.type.survival_outcome_meta`
- `meta.type.network_meta_analysis_planned`

### 12.5 LabTools

- `module.labtools.name`
- `labtools.category.general_calculators`
- `labtools.category.reagent_preparation`
- `labtools.category.experiment_records`
- `labtools.category.cell_experiments`
- `labtools.category.protein_experiments`
- `labtools.term.western_blot`
- `labtools.term.bca`
- `labtools.term.sds_page`
- `labtools.term.imagej_fiji`
- `labtools.warning.external_engine_detect_first`

### 12.6 Reports and exports

- `report.status.draft`
- `report.status.testing_summary`
- `report.status.report_ready`
- `report.action.generate_draft`
- `report.action.export_package`
- `report.warning.not_formal_result`
- `export.filename.bio_report_slug`
- `export.column.localized_label`
- `provenance.section.title`
- `manifest.section.parameters`

## 13. 术语表初始建议

| term_id | zh | en | translate_policy | notes |
|---|---|---|---|---|
| `source.geo` | GEO | GEO | official name | Do not translate. |
| `source.tcga` | TCGA | TCGA | official name | Do not translate. |
| `source.gtex` | GTEx | GTEx | official name | Do not translate. |
| `analysis.deg` | 差异表达分析 / DEG | Differential expression analysis / DEG | bilingual acronym | Formal status depends on resolver and runner. |
| `analysis.gsea` | GSEA | GSEA | keep acronym | Explain in help text. |
| `analysis.ora` | ORA 富集分析 | ORA enrichment analysis | keep acronym | Needs database term glossary. |
| `analysis.survival` | 生存分析 | Survival analysis | translate label | HR/KM/Cox/log-rank as separate terms. |
| `analysis.clinical_association` | 临床关联分析 | Clinical association analysis | translate label | Avoid causal claims. |
| `database.go` | GO | GO | official name | Do not translate. |
| `database.kegg` | KEGG | KEGG | official name | Do not translate. |
| `meta.effect.hr` | HR | HR | keep acronym | Hazard ratio in glossary. |
| `meta.effect.or` | OR | OR | keep acronym | Odds ratio in glossary. |
| `meta.effect.rr` | RR | RR | keep acronym | Risk ratio in glossary. |
| `meta.effect.md` | MD | MD | keep acronym | Mean difference in glossary. |
| `meta.effect.smd` | SMD | SMD | keep acronym | Standardized mean difference in glossary. |
| `meta.plot.forest` | 森林图 | Forest plot | translate stable term | Report caption needs locale. |
| `meta.plot.funnel` | 漏斗图 | Funnel plot | translate stable term | Publication bias context. |
| `lab.western_blot` | Western Blot | Western blot | keep established term | Do not freely translate. |
| `lab.bca` | BCA | BCA assay | keep acronym | Protein assay. |
| `lab.sds_page` | SDS-PAGE | SDS-PAGE | keep acronym | Gel preparation needs formula glossary. |
| `lab.imagej_fiji` | ImageJ/Fiji | ImageJ/Fiji | official name | External engine. |

## 14. i18n 改造路线

| stage | goal | scope | required_before |
|---|---|---|---|
| I18N-0 | 建立 i18n strategy 和 key naming rules | brand, shell, module, status, report, terminology key naming | Any extraction work |
| I18N-1 | 品牌、导航、状态标签 key | `brand.*`, `nav.*`, `feature.status.*`, `analysis.status.*` | UI-A4 implementation planning |
| I18N-2 | Settings 和全局 shell 文案抽取 | login, welcome, dashboard, sidebar, topbar, settings shell | New shell UI implementation |
| I18N-3 | Bioinformatics / Meta / LabTools 页面文案抽取 | module page titles, actions, warnings, empty states | Module page rebuild |
| I18N-4 | 报告模板多语言化 | Bio/Meta/LabTools report templates, export titles, limitations | Formal report/export UI |
| I18N-5 | 医学/实验/统计术语表 | disease, assay, analysis method, database, effect measure terms | Multilingual reports and scientific warnings |
| I18N-6 | 语言切换设置和测试 | Settings language switch, locale fixtures, semantic UI tests | Public multilingual release |

Recommended sequencing:

1. Do not start with ad hoc translation. Freeze key naming and brand variables first.
2. Extract status semantics before long page copy, because B8.0.1 safety depends on status meaning.
3. Treat report templates as a separate subsystem after UI shell labels.
4. Convert high-risk tests to semantic assertions before enabling runtime language switching.

## 15. 是否建议进入 UI-A4

建议进入 UI-A4，但 UI-A4 的实施路线审计必须把以下 i18n 前置条件写入 master plan：

- UI rebuild should reserve i18n key boundaries even if the first implementation remains Chinese.
- Brand display variables must be defined before Welcome/About/Dashboard high-fidelity work.
- Bioinformatics formal-looking buttons must be gated by semantic status keys, not translated labels.
- Report/export UI must not be treated as simple string extraction; it needs template and terminology planning.
- Tests should be migrated toward objectName/page_key/status enum assertions before broad language switching.

## 16. Command log and validation

Commands executed during this audit:

| command | result |
|---|---|
| `rg -n "BioMedPilot|UI-A3|i18n|commit|audit|packag|LaunchServices|萤火虫|Firefly" /Users/changdali/.codex/memories/MEMORY.md` | Passed; confirmed scoped audit commit defaults and packaging boundary memory. |
| `git status --short --branch` | Passed; branch `dev/ui-shell` was clean before report creation. |
| `ls docs/ui \| sort` | Passed; A1/A2 and target draft directory exist. |
| `wc -l docs/ui/UI_A1_target_markdown_architecture_audit_20260520.md` | Passed; A1 report exists. |
| `wc -l docs/ui/UI_A2_visual_brand_resource_audit_20260520.md` | Passed; A2 report exists. |
| `rg -n "[\p{Han}]" app tests docs config ...` | Passed; found major Chinese hardcoded UI, report, docs and test sources. |
| `rg -n "assert .*['\"]\|== ['\"]\|in .*\.text\|findText..." tests -g '*.py'` | Passed; found high-risk literal text assertions in UI and Bioinformatics tests. |
| `rg -n "report|报告|export|导出|Markdown|HTML|DOCX|PDF|CSV|xlsx..." app docs config reporting tests ...` | Passed; found report/export templates, filenames, placeholders and report tests. |
| `nl -ba app/shared/testing_mode.py \| sed -n '1,130p'` | Passed; verified mixed zh summary and English feedback template. |
| `nl -ba app/bioinformatics/reports/project_report_builder.py \| sed -n '1,280p'` | Passed; verified Bioinformatics Markdown report draft strings and limitations. |
| `nl -ba app/bioinformatics/services/bio_report_service.py \| sed -n '1,260p'` | Passed; verified zh errors and English testing summary report. |
| `nl -ba config/bioinformatics/analysis_defaults.yaml \| sed -n '1,140p'` | Passed; verified ASCII report filename defaults. |
| `rg -n "binary_outcome_meta|continuous_outcome_meta|...|NETWORK_META_ANALYSIS|AI suggestion..." docs/ui/target_design_drafts/meta/... docs/ui/UI_A1... docs/ui/UI_A2...` | Passed; verified Meta type keys, planned network meta status and AI suggestion boundary. |
| `rg -n "萤火虫|Firefly|BioMedPilot|医研智析|..." app tests docs config scripts packaging resources assets icons images ...` | Returned code 2 because optional directories `packaging`, `resources`, `icons`, `images` do not exist; still produced useful findings from existing paths. |
| `rg -n "[\p{Han}]" app tests config scripts packaging ...` | Returned code 2 because optional directory `packaging` does not exist; still produced useful findings from existing paths. |
| `rg -n "assert .*['\"]\|findText\|windowTitle..." tests -g '*.py'` | Passed; confirmed literal text assertions across UI and service tests. |
| `rg -n "report|报告|export|导出|Markdown|HTML|DOCX|PDF|CSV|xlsx..." app reporting config tests docs/ui docs/bioinformatics ...` | Passed; confirmed report/export and B8.0.1 sources. |
| `git diff --check` | Passed; no whitespace errors. |
| `git status --short` | Passed; only `docs/ui/UI_A3_i18n_readiness_audit_20260520.md` was newly untracked before staging. |
| `wc -l docs/ui/UI_A3_i18n_readiness_audit_20260520.md` | Passed; report has 449 lines before this validation update. |

## 17. 本阶段边界确认

- 未修改业务代码。
- 未修改测试。
- 未修改报告模板。
- 未修改配置。
- 未替换 Logo、图标或图片。
- 未引入新依赖。
- 未重构 UI。
- 未重新打包。
- 未运行 packaged app。
- 未覆盖桌面入口。
