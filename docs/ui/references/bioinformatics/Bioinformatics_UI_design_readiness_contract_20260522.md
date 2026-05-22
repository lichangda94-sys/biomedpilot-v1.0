# Bioinformatics UI Design Readiness Contract

日期：2026-05-22

范围：为 UI 设计模块说明当前 Bioinformatics 生信分析模块已经实现、可以接入 UI 设计的能力，仍需继续开发的缺口，以及设计时必须保留的分析边界。本文仿照 LabTools UI integration / screen inventory / backend gap audit 的逻辑，但合并为一份生信分析 UI 设计参考文档。

当前设计基线：

- ReleaseBuild candidate：`/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`
- ReleaseBuild HEAD：`59506d3 carry over Bioinformatics B16 legacy pipeline to ReleaseBuild`
- MainLine source：`7bcdb7f carry over Bioinformatics B16 legacy pipeline to MainLine`
- 当前候选范围：controlled two-group DEG、controlled ORA、controlled preranked GSEA、controlled two-group KM/log-rank、controlled single-variable Cox、legacy acquisition/standardization preflight。

本文不是新功能任务，不声明 Bioinformatics 已经 public-release ready 或 clinical-use ready。

## 1. UI 设计边界

当前 Bioinformatics 已有一套可用于 UI 设计的桌面工作流和后端契约，核心不是“任意分析按钮”，而是围绕 project、source acquisition、recognition、standardization、analysis gates、result semantics、plot/report package 的受控流程。

UI 设计可以接入：

- 项目创建 / 打开 / 项目健康状态。
- 数据源入口：本地导入、GEO/GSE 中文检索、TCGA、GTEx。
- acquisition status、recognition、readiness、standardized assets。
- Analysis Center：resolver packages、legacy pipeline、action gates、dependency state、formal DEG gates、ORA/GSEA gates、survival/clinical rows。
- formal DEG MVP：two-group controlled DEG only。
- ORA / GSEA enrichment：受控输入、资源、参数、结果、plot artifact、section-only report package。
- KM/log-rank 和 Cox univariate：受控 runtime 结果与语义边界。
- result browser：DEG / ORA / GSEA review、sort/filter、provenance、plot/report package gate preview。
- Settings dependency detection：detect-first，只显示依赖状态，不自动安装。

UI 设计不能暗示已完成：

- limma / DESeq2 / edgeR / R backend formal execution。
- multifactor DEG design。
- arbitrary GSEA / ORA without gated source result。
- Cox multivariate、risk score、nomogram。
- survival / clinical report-ready。
- clinical conclusion、prognosis、treatment recommendation。
- full integrated report。
- legacy GEO/TCGA/GTEx runner 直接作为 formal analysis。

## 2. UI 状态标签

| 标签 | 含义 |
|---|---|
| `active_backend_ready` | 后端数据模型、gate 或执行链路已存在，可作为 UI 主流程设计基础。 |
| `gated_formal_ready` | 只有全部 gate 通过后才可启用正式动作；UI 必须显示 disabled reason。 |
| `controlled_runtime_ready` | 受控 runtime 已验证；默认 GUI runtime 可能仍 graceful blocked。 |
| `ui_adapter_needed` | 后端可用，但 UI 需要 view model、文件选择、错误展示、长任务状态或路径适配。 |
| `review_only` | 可展示、筛选、复核，不应提供 formal run 或 report-ready 承诺。 |
| `preflight_only` | 只做输入/资源/参数/设计预检，不产生 formal result。 |
| `spec_only` | 只注册 artifact spec 或 gate 信息，不生成真实 PNG/SVG/PDF 等渲染产物。 |
| `section_report_only` | 只能生成单分析 section package，不是完整整合报告。 |
| `disabled_design_only` | 可在 UI 中展示计划、原因和边界，但不提供执行按钮。 |
| `legacy_reference_only` | 旧代码或迁入资产只能作为识别/标准化来源，不可直接接成正式分析。 |

## 3. UI Integration Contract

### 3.1 Primary state contract

UI 设计优先依赖：

- `app.bioinformatics.analysis_ui.state.build_analysis_center_state(project_root)`
- `app.bioinformatics.analysis_ui.action_rules.build_action_rows(...)`
- `app.bioinformatics.analysis_ui.labels`

Analysis Center state 已包含：

- `package_rows`
- `action_rows`
- `dependency_rows`
- `formal_deg_gate_rows`
- `ora_gate_rows`
- `gsea_gate_rows`
- `legacy_asset_pipeline`
- `result_rows`
- `gate_rows`
- `survival_clinical_rows`
- `top_blockers`
- `top_warnings`
- `developer_diagnostics`

UI 不应从临时表格、`recognition_report.json` 或 legacy runner 输出拼接正式分析状态。正式分析状态必须来自 B8/B9/B10/B11/B12-B16 contracts 和 result index v2。

### 3.2 Action rows contract

所有动作按钮应由 `action_rows` 驱动：

| 字段 | UI 用法 |
|---|---|
| `action_id` | 稳定按钮/动作标识。 |
| `label` | 用户可见动作名，可做中文产品化改写但不得改变边界。 |
| `state` | badge / segmented state。 |
| `button_behavior` | 决定按钮类型：formal run、review-only、preflight-only、developer-only。 |
| `enabled` | 是否可点击。 |
| `normal_user_visible` | 是否展示给普通用户。 |
| `disabled_reason` | 禁用原因，必须可见或可展开。 |
| `next_action` | 下一步引导文案。 |

禁止 UI 只根据 `can_run=True`、文件存在或表格非空来启用 formal action。

### 3.3 Result semantics contract

UI 必须显式区分：

| semantics | UI 表达 |
|---|---|
| `formal_computed_result` | 正式受控计算结果；仍需检查 validation、provenance、dependency snapshot。 |
| `imported_external_result` | 外部导入结果；可 review / derived analysis，但不得伪装为 BioMedPilot recomputed formal result。 |
| `testing_level` | 测试级结果；用于开发诊断，不作为正式报告。 |
| `exploratory` | 探索性结果；不得升级为正式结果。 |
| `preflight_only` | 预检/配置，不是结果。 |
| `not_a_result` | legacy candidate / manifest / selection，不是分析结果。 |

## 4. Screen Inventory

| screen_id | screen_name | backend_contract | UI 状态 | priority | 设计重点 |
|---|---|---|---|---|---|
| `bio_project_home` | 生信项目首页 | `BioinformaticsProjectHomeWidget`, project summary | `active_backend_ready` + `ui_adapter_needed` | P0 | 创建/打开项目、项目健康、下一步入口。 |
| `bio_data_source` | 数据源选择 | `BioinformaticsDataSourceWidget` | `active_backend_ready` + `ui_adapter_needed` | P0 | 本地/GEO/TCGA/GTEx 来源清楚分区，显示下载/预览/限制。 |
| `bio_chinese_search` | 中文主题检索 | `BioinformaticsChineseDatasetSearchWidget`, search center | `active_backend_ready` + `ui_adapter_needed` | P0 | 中文意图到 GEO/TCGA/GTEx 候选，注册候选而非承诺分析完成。 |
| `bio_acquisition_status` | Acquisition status | acquisition manifests | `active_backend_ready` | P1 | 展示已注册来源、文件状态、来源路径。 |
| `bio_recognition` | 文件识别 | recognition contract | `active_backend_ready` | P0 | 识别类型、group preview、warnings；不把识别结果当正式输入。 |
| `bio_readiness` | 数据就绪检查 | readiness artifacts | `active_backend_ready` | P0 | 缺失项、可修复项、GSEA gene set 状态、TCGA clinical readiness。 |
| `bio_standardized_assets` | 标准化资产 | repository manifest / registry | `active_backend_ready` | P0 | expression/sample/group/clinical/gene set 默认选择；需要更好的人工多候选选择 UI。 |
| `bio_analysis_center` | 分析任务中心 | `build_analysis_center_state` | `active_backend_ready` + `gated_formal_ready` | P0 | 生信 UI 核心：packages、actions、dependencies、formal gates、legacy pipeline、survival rows。 |
| `bio_deg_config` | DEG 配置/预检 | DEG-ready + parameter gate | `active_backend_ready` + `gated_formal_ready` | P0 | comparison、method、threshold、value type、dependency、confirmation。 |
| `bio_formal_deg_run` | Controlled two-group DEG | `deg_engine.formal_runner` | `controlled_runtime_ready` + `gated_formal_ready` | P0 | 只支持 two-group controlled DEG；默认 GUI 缺依赖时必须 graceful blocked。 |
| `bio_formal_deg_review` | DEG result review | `deg_engine.result_review`, result index v2 | `active_backend_ready` | P0 | feature_id/gene/log2FC/p/FDR/significance、sort/filter、provenance。 |
| `bio_deg_plot_report` | DEG plot/report package | `plots.formal_deg`, `reports.formal_deg` | `section_report_only` | P1 | 只从 formal DEG result 生成；table-only mode 文案必须清楚。 |
| `bio_ora` | ORA execution/review | `app.bioinformatics.enrichment` | `active_backend_ready` + `gated_formal_ready` | P1 | Source DEG result、gene set resource、parameter、result review、plot/report gates。 |
| `bio_gsea` | Preranked GSEA execution/review | `app.bioinformatics.gsea` | `active_backend_ready` + `gated_formal_ready` | P1 | Preranked source/rank metric/gene set/parameter/result review；不要做任意 GSEA。 |
| `bio_survival_clinical` | Survival / clinical rows | `survival_clinical` gates | `controlled_runtime_ready` + `disabled_design_only` for advanced items | P1 | KM/log-rank 与 Cox univariate 可受控；multivariate/report/clinical advice 禁用。 |
| `bio_km_cox_plot` | KM/Cox plot artifact | plot artifact gates | `spec_only` | P2 | 当前 spec-only，不应 mock 成真实曲线/forest image 已生成。 |
| `bio_legacy_pipeline` | Legacy acquisition pipeline | `acquisition_adapters` | `preflight_only` + `review_only` | P1 | Build/materialize/merge/confirm selection；不能显示为 formal analysis ready。 |
| `bio_results_browser` | 结果浏览器 | result index v2 + review modules | `active_backend_ready` | P0 | DEG/ORA/GSEA review cards, provenance, gate preview, export path。 |
| `bio_report_viewer` | 报告草稿 / section package | report gates | `section_report_only` | P1 | DEG/ORA/GSEA section package；不是 full integrated report。 |
| `bio_gene_set_manager` | GSEA gene set resource manager | local GMT/resource registry | `active_backend_ready` + `ui_adapter_needed` | P1 | 本地 GMT 导入、资源选择、下载缓存状态。 |
| `bio_immune_scoring` | Immune/TME scoring | B7 immune scoring | `review_only` / `testing_or_internal` | P2 | 可展示为探索/辅助评分，不能并入 formal clinical report。 |
| `bio_settings_dependencies` | Settings dependency detection | dependency checks | `active_backend_ready` | P0 | numpy/pandas/scipy/statsmodels/lifelines 状态、版本、missing reason、packaging impact；无 install action。 |

## 5. P0 Mockup 建议

### 5.1 Bioinformatics 首页 / 项目首页

目标：工作流中控台，不做营销页。

建议展示：

- 当前项目路径、项目健康、已注册数据源数量、标准化资产状态、分析结果数量。
- 下一步主动作：选择数据源、运行识别、进入标准化、进入 Analysis Center。
- 状态 badge：未开始、需要修复、可预检、formal gates blocked、已有正式结果。

### 5.2 数据源与中文检索

目标：让用户理解“找数据”和“分析完成”是不同阶段。

建议布局：

- 数据源入口分为 Local / GEO / TCGA / GTEx。
- 中文主题检索展示 query draft、候选卡片、注册状态、下载候选。
- TCGA/GTEx 页面必须显示样本范围、用途、下载/构建步骤和限制；GTEx 不可被呈现为 TCGA normal control 的自动替代。

### 5.3 Recognition / Readiness / Standardized Assets

目标：把输入清洗和分析前置条件做成可操作流程。

建议：

- Recognition 页面显示文件识别、group preview、warning。
- Readiness 页面显示缺失项和 todo list。
- Standardized Assets 页面显示 expression/sample/group/clinical/gene set 的默认选择。
- 多候选资产需要设计人工选择器；当前自动确认只适合无歧义候选。

### 5.4 Analysis Center

目标：这是生信模块 UI 设计的核心页面。

必须展示：

- Resolver package table：package type、input_package_id、status、semantics、value type、gene id type、blockers、warnings、repair guidance。
- Action matrix：DEG、ORA、GSEA、KM/Cox、legacy pipeline、plot/report-ready，各自独立状态和 disabled reason。
- Dependency panel：detect-first，无安装按钮。
- Formal DEG gate rows：resolver、DEG-ready、dependency、parameter、user confirmation、result schema、controlled activation。
- ORA/GSEA gate rows。
- Legacy asset pipeline table。
- Survival/clinical rows。
- Developer diagnostics 与普通用户动作分离。

### 5.5 Formal DEG flow

目标：two-group controlled DEG MVP。

UI flow：

1. Resolver package ready。
2. DEG-ready matrix pass。
3. Dependency snapshot pass。
4. Parameter manifest pass。
5. 用户确认 comparison/method/threshold/value type/dependency/output plan。
6. Run controlled two-group DEG。
7. Result review。
8. Optional formal DEG plot artifact。
9. Optional section-only report package。

必须避免：

- 将 DEG 描述成 limma/DESeq2/edgeR。
- 在 dependency blocked 时显示可运行。
- 把 imported DEG result 显示为 BioMedPilot formal recomputed DEG。

### 5.6 Result Browser

目标：结果复核优先，不做临床结论页。

建议分区：

- Formal DEG review。
- ORA review。
- GSEA review。
- Gate preview。
- Provenance panel。
- Export table/package action。

所有 result card 必须有 semantics badge。

## 6. Backend / Contract Gap Audit

| 缺口 | 影响 UI | 建议优先级 |
|---|---|---|
| 默认 GUI package 缺 `scipy`/`statsmodels` | Formal DEG 在默认 GUI runtime graceful blocked | P0 packaging/runtime policy before release |
| 多候选 standardized asset 手工选择器不足 | legacy / standardization 复杂项目 UX 不够 | P0 UI design + adapter |
| limma / DESeq2 / edgeR 未接入 | 不应设计为可选 formal method | P2 backend planning |
| multifactor DEG 未接入 | 不应设计批次/协变量 DEG 页面 | P2 backend planning |
| survival report-ready 未实现 | KM/Cox 不能进入正式报告包 | P2 |
| Cox multivariate / risk score / nomogram 未实现 | 只能 disabled/design-only | P2 |
| KM/Cox plot 当前 spec-only | 不应展示真实 KM curve / forest plot 已生成 | P1/P2 |
| full integrated report 未实现 | DEG/ORA/GSEA 只做 section package | P2 |
| clinical conclusion / treatment advice 禁止 | 任何报告和结果页都不能输出临床建议 | permanent boundary |
| legacy runner 未审计为 formal execution | legacy pipeline 只能 preflight/standardization | permanent boundary |
| long-running download/execution progress 仍需 UI adapter | TCGA/GTEx/download/formal run UX 需要进度、取消、错误恢复 | P1 |
| unified file picker / export non-overwrite adapter | report package / table export / resource import | P1 |
| UI-facing error normalization | 多个 gate 的 blockers/warnings 需要一致呈现 | P0 |

## 7. 不应在 UI 设计中声明完成

UI mockup 或文案不得声明：

- “支持 limma 差异分析”。
- “支持 DESeq2 / edgeR 正式分析”。
- “支持多因素差异分析”。
- “支持任意 GSEA / ORA 正式分析”。
- “支持完整生存分析报告”。
- “支持 Cox 多因素模型、风险评分、列线图”。
- “支持临床结论、预后判断、治疗建议”。
- “已生成 KM 曲线 / Cox forest plot 图片”，除非后续实现真实 plot renderer。
- “完整整合报告已生成”。
- “legacy GEO/TCGA/GTEx pipeline 可直接产生正式分析结果”。

## 8. UI Copy Rules

建议统一使用这些表达：

- “正式受控计算结果”用于 `formal_computed_result`。
- “外部导入结果”用于 `imported_external_result`。
- “预检 / 配置 / 设计检查”用于 `preflight_only`。
- “测试级结果”用于 `testing_level`。
- “section-only report package” 或 “单分析报告包”，不要写“完整报告”。
- “统计分析结果，不是临床结论”必须出现在 DEG/ORA/GSEA/KM/Cox review/report package 附近。
- Disabled reason 不应藏在 developer diagnostics；普通用户至少能看到简短原因。

## 9. Recommended UI Design Priority

| 优先级 | 页面 / 组件 |
|---|---|
| P0 | Project home、Data source、Chinese search、Recognition、Readiness、Standardized Assets、Analysis Center、Formal DEG gate/confirmation、Results Browser、Settings dependency panel |
| P1 | Formal DEG result review polish、DEG plot/report package UX、ORA/GSEA review and section package UX、GSEA gene set manager、Legacy pipeline review/operation UI、export path and non-overwrite UX |
| P2 | Survival/KM/Cox expanded result review、real KM/Cox plots、survival report-ready planning、immune scoring polish、full integrated report planning、limma/DESeq2/edgeR/multifactor DEG planning |

## 10. Validation Baseline

Latest ReleaseBuild B16.10 validation:

| Command | Result |
|---|---|
| `git diff --check` | passed |
| B16 + Analysis UI targeted tests | 43 passed |
| UI legacy targeted tests | 2 passed, 110 deselected |
| recognition/resolver/analysis_ui focused tests | 271 passed, 321 deselected |
| formal DEG/ORA/GSEA/survival/clinical focused tests | 211 passed, 381 deselected |
| UI focused tests | 17 passed, 95 deselected |
| `python3 -m pytest tests/bioinformatics -q` | 592 passed |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | 269 passed |
| `python3 -m app.main --smoke-test` | passed |
| `python3 scripts/package_app.py --smoke-test` | passed |
| `open -W -n dist/BioMedPilot.app --args --smoke-test` | passed |
| `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app` | passed |

## 11. Recommended Source of Truth for UI Design

Use these as source-of-truth references:

- ReleaseBuild candidate code at `59506d3`.
- `app/bioinformatics/analysis_ui/state.py`
- `app/bioinformatics/analysis_ui/action_rules.py`
- `app/bioinformatics/workflow_pages.py`
- `docs/bioinformatics/stage_B16_10_releasebuild_legacy_pipeline_receive_from_mainline_20260522.md`
- `docs/bioinformatics/stage_B14_9_releasebuild_survival_clinical_closure_gate_20260521.md`
- `docs/bioinformatics/stage_B11_5_enrichment_layer_carryover_release_readiness_planning_20260521.md`

Do not use `app/bioinformatics/legacy/` as active UI truth. It is historical/legacy reference unless a scoped adapter explicitly promotes a piece into the current contract.

## 12. Next Step for UI Design Module

Recommended next UI design task:

1. Build a Bioinformatics P0 screen map from the Screen Inventory above.
2. Create mockups for Project Home, Data Source, Recognition/Readiness/Standardized Assets, Analysis Center, DEG Confirmation, Results Browser, and Settings Dependencies.
3. For every action button, bind visual state to `action_rows`.
4. For every result card, show result semantics and provenance.
5. For disabled actions, show user-readable disabled reason.
6. Keep survival/clinical advanced outputs, limma/DESeq2/edgeR, full integrated report, and legacy formal execution out of the “已完成” visual language.
