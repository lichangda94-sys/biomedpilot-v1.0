# Meta Analysis UI 目标架构初步决策记录

日期：2026-05-20
适用范围：UIShell / Meta Analysis / dev/meta-analysis / 后续 Codex UI 开发
文件性质：阶段性 UI 架构决策记录，不是完整实现任务，不是 Figma 设计稿

---

## 1. 文件背景

本文件根据当前 Meta Analysis 审计信息和 UI 架构讨论形成，用于记录 Meta Analysis 模块的目标 UI 方向。

当前已知审计信息：

- 当前 Meta Analysis active runtime 位于 `dev/meta-analysis`；
- 当前 HEAD 为 `3aad58a Handle LaunchServices psn arguments`；
- 当前实现已不是早期 M0-M3，而是存在一条 testing 主链；
- 主链覆盖从 PICO、检索、文献库、去重、筛选、全文、提取、质量评价、分析计划、统计引擎到报告 / 复现包和 AI suggestion 等环节；
- 当前整体仍明确属于 Developer Preview / testing；
- 当前不是生产级系统综述工具，也不是投稿级统计软件；
- 当前 active runtime 和 legacy 历史快照需要严格区分。

本文件用于明确后续 Meta Analysis UI 应采用：

```text
通用主流程 + Meta 类型预分流 + 类型专属提取 / 分析模板
```

而不是一个完全通用、所有类型混在一起的大流程。

---

## 2. 核心架构原则

### 2.1 不做完全通用型 Meta 流程

Meta Analysis 不应设计成一个所有 Meta 类型共用同一套提取表、质量评价和统计设置的完全通用流程。

原因：

- 不同 Meta 类型的数据字段不同；
- 不同 Meta 类型的效应量不同；
- 不同 Meta 类型的质量评价工具不同；
- 不同 Meta 类型的统计方法和图表不同；
- 完全通用流程容易导致字段混乱、交叉污染和用户误填。

### 2.2 采用类型预分流

Meta Analysis UI 应采用：

```text
通用主流程
+ Meta 类型预分流
+ 类型专属提取 / 质量评价 / 统计 / 报告模板
```

也就是说，用户在早期必须选择本项目的 Meta 分析类型。该类型选择会控制后续流程。

### 2.3 Meta 类型选择是工作流控制项

Meta 类型不是普通标签，而是后续工作流控制项。

它会影响：

- 研究问题结构；
- 纳入 / 排除标准模板；
- 数据提取 schema；
- 质量评价工具；
- 统计分析任务；
- 结果表结构；
- 结果图类型；
- 报告章节模板。

---

## 3. 当前 active runtime 的 10 种 Meta 类型

根据当前审计，active 的 Data Extraction Schema Registry v1 中定义了 10 种 Meta 类型。
后续 UI 应以 active registry v1 为准，而不是 legacy registry。

### 3.1 类型列表

| 类型 ID | 中文能力 | 主要效应量 / 数据 |
|---|---|---|
| `binary_outcome_meta` | 二分类结局 Meta | OR / RR / RD |
| `continuous_outcome_meta` | 连续结局 Meta | MD / SMD / WMD |
| `survival_outcome_meta` | 生存结局 Meta | HR |
| `prevalence_incidence_meta` | 患病率 / 发生率 Meta | event / total / rate |
| `diagnostic_accuracy_meta` | 诊断准确性 Meta | TP / FP / FN / TN，基础 2x2 |
| `exposure_disease_risk_meta` | 暴露-疾病风险 Meta | OR / RR / HR |
| `biomarker_expression_difference_meta` | 生物标志物表达差异 Meta | 表达差异 / 组间比较 |
| `correlation_meta` | 相关性 Meta | r / Fisher z |
| `prognostic_factor_meta` | 预后因素 Meta | HR / OR |
| `dose_response_meta` | 剂量反应 Meta | testing schema only |

### 3.2 UI 要求

这 10 种类型应成为 Meta Analysis 中“研究问题与 Meta 类型”页面的类型选择项。

UI 可以采用：

- 卡片；
- 分组列表；
- 下拉选择；
- 类型说明面板。

但不能只作为后台 schema 隐藏。

---

## 4. Legacy registry 与 active registry 的边界

### 4.1 active registry 为准

Meta Analysis UI 类型选择应以 active runtime 的 Data Extraction Schema Registry v1 为准。

当前 active 类型为：

```text
binary_outcome_meta
continuous_outcome_meta
survival_outcome_meta
prevalence_incidence_meta
diagnostic_accuracy_meta
exposure_disease_risk_meta
biomarker_expression_difference_meta
correlation_meta
prognostic_factor_meta
dose_response_meta
```

### 4.2 legacy registry 只作历史参考

审计指出，早期 uppercase profile registry 中存在以下类型：

```text
TREATMENT_EFFECT_META
BIOMARKER_PREVALENCE_ASSOCIATION_META
PROGNOSTIC_FACTOR_META
DIAGNOSTIC_ACCURACY_META
PREVALENCE_INCIDENCE_META
CORRELATION_META
SINGLE_ARM_OUTCOME_META
CONTINUOUS_BIOMARKER_DIFFERENCE_META
EXPOSURE_DISEASE_RISK_META
NETWORK_META_ANALYSIS
```

其中 `NETWORK_META_ANALYSIS` 当前是 placeholder / not implemented。

因此：

```text
legacy schema_registry.py 中的 uppercase profile registry 仅作为历史参考，不作为当前 UI 类型来源。
```

### 4.3 Network Meta 当前不进入可用类型

Network Meta 当前不属于 v1 active extraction schema，不作为当前可用 Meta 类型。

它最多可放入：

```text
后续开放 / Planned
```

不能放入当前可用主流程。

---

## 5. Meta Analysis 目标主流程

建议 Meta Analysis 目标主流程为：

```text
Meta Analysis / Meta 分析
├── Project Home / 项目首页
├── Question & Meta Type / 研究问题与 Meta 类型
├── Search Strategy / 检索策略
├── Import & Deduplication / 文献导入与去重
├── Screening / 文献筛选
├── Full-text & Extraction / 全文与数据提取
├── Quality Assessment / 质量评价
├── Meta Analysis Tasks / 统计分析
├── Result & Report / 结果与报告
├── Report Export / 报告导出
└── Meta Settings / Meta 设置
```

其中：

- Project Home 是项目状态总览；
- Question & Meta Type 是类型预分流入口；
- Search Strategy 管理检索策略和检索计划；
- Import & Deduplication 管理导入、文献库和去重；
- Screening 管理标题摘要筛选、全文筛选和排除理由；
- Full-text & Extraction 根据 Meta 类型加载不同 extraction schema；
- Quality Assessment 根据 Meta 类型加载对应评价工具；
- Meta Analysis Tasks 根据 Meta 类型显示对应统计分析；
- Result & Report 展示当前分析任务结果；
- Report Export 导出报告草稿；
- Meta Settings 管理 Meta 模块偏好和日志入口。

---

## 6. Question & Meta Type / 研究问题与 Meta 类型

### 6.1 页面定位

该页面是 Meta Analysis 的关键分流页面。

用户在此处：

- 输入中文或英文研究问题；
- 选择 Meta 分析类型；
- 填写或生成结构化研究框架；
- 形成 protocol 草稿；
- 设置初步纳入 / 排除标准。

### 6.2 页面说明文案

该页面应明确提示：

```text
请选择本项目的 Meta 分析类型。该选择将决定后续的数据提取表、质量评价工具、统计分析任务和报告结构。
```

### 6.3 结构化研究框架

根据不同 Meta 类型，可以使用不同框架：

- 干预 / 二分类 / 连续结局：PICO / PICOS；
- 暴露-疾病风险：PECO；
- 诊断准确性：PIRT / PIRO；
- 预后因素：Population / Prognostic factor / Outcome；
- 患病率 / 发生率：Population / Condition / Measure；
- 相关性：Population / Variable A / Variable B；
- 剂量反应：Exposure / Dose levels / Outcome。

---

## 7. Meta 类型对后续页面的影响

Meta 类型选择后，应影响以下页面。

### 7.1 Full-text & Extraction

根据类型加载不同的数据提取 schema。

示例：

```text
binary_outcome_meta
→ event / total / OR / RR / RD

continuous_outcome_meta
→ mean / SD / n / MD / SMD / WMD

diagnostic_accuracy_meta
→ TP / FP / FN / TN

correlation_meta
→ r / Fisher z / n
```

### 7.2 Quality Assessment

根据类型显示不同质量评价工具或模板。

示例：

```text
诊断准确性 Meta
→ QUADAS-2

干预效果 / 结局类 Meta
→ RoB / Cochrane 风险偏倚工具，按实现状态

观察性关联 / 暴露风险 / 预后因素
→ NOS / ROBINS-I 等，按实现状态
```

当前工具若未完全实现，应标记 testing / 后续开放。

### 7.3 Meta Analysis Tasks

根据类型显示对应统计任务和效应量。

示例：

```text
binary_outcome_meta
→ OR / RR / RD pooling

continuous_outcome_meta
→ MD / SMD / WMD pooling

survival_outcome_meta
→ HR pooling

diagnostic_accuracy_meta
→ 基础 2x2 diagnostic summary

dose_response_meta
→ testing schema only
```

### 7.4 Result & Report

根据类型显示不同结果表和图表。

示例：

- 二分类 / 连续 / 生存：forest plot；
- 诊断准确性：2x2 summary / SROC，按实现状态；
- 相关性：pooled correlation / Fisher z；
- 患病率：pooled proportion；
- 剂量反应：testing schema only。

### 7.5 Report Export

根据类型生成不同报告章节模板。
报告仍为草稿，不是投稿级最终报告。

---

## 8. 类型与字段 / 统计方法映射规则

后续 Codex 实现时，应建立 Meta 类型映射表。

建议最小映射字段：

| Meta 类型 | 提取字段方向 | 统计方向 |
|---|---|---|
| `binary_outcome_meta` | event / total / effect estimate | OR / RR / RD |
| `continuous_outcome_meta` | mean / SD / n | MD / SMD / WMD |
| `survival_outcome_meta` | HR / CI / p value / endpoint | log HR pooling |
| `prevalence_incidence_meta` | event / total / rate | pooled prevalence / incidence |
| `diagnostic_accuracy_meta` | TP / FP / FN / TN | sensitivity / specificity / 2x2 |
| `exposure_disease_risk_meta` | exposure / disease / adjusted estimate | OR / RR / HR |
| `biomarker_expression_difference_meta` | biomarker expression / groups | expression difference |
| `correlation_meta` | r / Fisher z / n | pooled correlation |
| `prognostic_factor_meta` | factor / outcome / HR / OR | prognostic effect |
| `dose_response_meta` | dose levels / effect estimate / variance | testing schema only |

UI 不一定展示完整映射表，但文档和后端必须有。

---

## 9. 当前 19 环节与目标 UI 的收敛关系

审计指出当前 active runtime 有一条 testing 主链，覆盖约 19 个环节。
UI 不应把 19 个环节全部作为一级页面，而应收敛到目标主页面。

建议映射：

```text
PICO / research question
→ Question & Meta Type

检索 / 检索预检 / PubMed 执行
→ Search Strategy

文献库 / 导入 / 去重
→ Import & Deduplication

标题摘要筛选 / 全文筛选
→ Screening

全文 / PDF / 提取 schema
→ Full-text & Extraction

质量评价
→ Quality Assessment

分析计划 / 统计引擎
→ Meta Analysis Tasks

结果 / 报告 / 复现包
→ Result & Report / Report Export
```

---

## 10. active runtime 与 legacy 边界

### 10.1 active runtime 目录

Meta UI 应优先对接当前 active runtime：

```text
app/meta_analysis/pages/
app/meta_analysis/services/
app/meta_analysis/models/
app/meta_analysis/search/
app/meta_analysis/stats/
app/meta_analysis/fulltext/
app/meta_analysis/quality/
app/meta_analysis/reports/
```

### 10.2 legacy 目录

`app/meta_analysis/legacy/` 是历史快照，不是当前 runtime 来源。

后续 Codex 不应从 legacy 中恢复旧 UI 或旧 schema，除非任务明确要求迁移审计或兼容处理。

### 10.3 过渡 adapter 债务

审计指出文献导入 / 去重仍有历史 adapter 债务。
这类内容可以在后续实现中单独处理，但不应影响当前 UI 架构原则。

---

## 11. 当前能力边界

### 11.1 当前已有能力

当前 active runtime 可作为 testing-level 工作流基础，包含：

- PICO / 研究问题；
- PubMed 检索确认后执行；
- 本地导入；
- 文献库；
- 去重；
- 筛选；
- 全文；
- 数据提取；
- 质量评价；
- 分析计划；
- 统计引擎；
- 报告 / 复现包；
- AI suggestion；
- 基础 pooled effect；
- 异质性；
- subgroup；
- leave-one-out；
- Egger / funnel 数据等。

但这些均属于 testing-level。

### 11.2 当前未完成或不应显示为可用

以下能力不应作为当前可用主按钮：

- 生产级在线数据库适配；
- Network Meta；
- HSROC / 高级诊断模型；
- meta-regression；
- trim-and-fill；
- 正式 PRISMA 图；
- 生产 PDF；
- 多审稿人协作；
- 投稿级系统综述输出。

这些可以标记为：

```text
后续开放 / Planned / Developer Preview note
```

---

## 12. Developer Preview / testing 表达规则

Meta Analysis 当前仍为 Developer Preview / testing。

UI 应持续表达：

```text
Developer Preview / testing
```

但不应在每个页面大字重复。

建议：

- 模块首页显示整体状态；
- 结果页和报告页显示结果边界；
- 报告导出页显示报告草稿性质；
- 每个未完成能力标记后续开放。

结果和报告页面应明确：

```text
结果用于测试与内部整理，不构成医学结论、临床建议或投稿级系统综述结果。
```

---

## 13. Meta Analysis 目标 IA 初稿

```text
Meta Analysis / Meta 分析
├── Project Home / 项目首页
│   ├── 项目状态
│   ├── Meta 类型
│   ├── 推荐下一步
│   └── 最近文献 / 结果 / 报告
│
├── Question & Meta Type / 研究问题与 Meta 类型
│   ├── 中文研究问题输入
│   ├── Meta 类型选择
│   ├── PICO / PECO / PIRT 等结构化框架
│   ├── 纳入 / 排除标准草稿
│   └── Protocol 草稿
│
├── Search Strategy / 检索策略
│   ├── 中文问题到英文检索词
│   ├── PubMed 检索式
│   ├── 数据库选择，第一版可先 PubMed
│   ├── 检索预检
│   └── 检索计划
│
├── Import & Deduplication / 文献导入与去重
│   ├── PubMed 结果导入
│   ├── RIS / BibTeX / CSV 导入
│   ├── 去重
│   └── 文献库
│
├── Screening / 文献筛选
│   ├── 标题摘要筛选
│   ├── 全文筛选
│   ├── 纳入 / 排除理由
│   └── PRISMA 流程数据
│
├── Full-text & Extraction / 全文与数据提取
│   ├── PDF / 全文记录
│   ├── 类型专属提取表
│   ├── 人工确认
│   └── 提取日志
│
├── Quality Assessment / 质量评价
│   ├── 类型对应质量评价工具
│   ├── 评分 / 风险判断
│   └── 评价记录
│
├── Meta Analysis Tasks / 统计分析
│   ├── 类型专属效应量
│   ├── 固定 / 随机效应
│   ├── 异质性
│   ├── 敏感性 / 亚组，按类型开放
│   └── 开始分析
│
├── Result & Report / 结果与报告
│   ├── 当前分析结果
│   ├── 统计结果预览
│   ├── forest plot / funnel plot / SROC 等类型专属图
│   ├── 云端 AI 结果分析，待开发
│   └── 加入报告草稿
│
├── Report Export / 报告导出
│   ├── 已加入报告草稿的结果
│   ├── PRISMA 信息
│   ├── 方法和结果草稿
│   ├── Markdown 导出
│   └── AI 润色，后续开放
│
└── Meta Settings / Meta 设置
    ├── 检索偏好
    ├── PDF / OCR 引擎引用
    ├── 质量评价工具偏好
    ├── 结果与报告偏好
    └── Meta 日志入口
```

---

## 14. 后续需要继续讨论的点

后续讨论建议从以下内容开始：

1. 10 种 Meta 类型如何在 UI 中分组展示；
2. Question & Meta Type 页面具体布局；
3. Search Strategy 页面如何承接中文研究问题和 PubMed 检索；
4. Import & Deduplication 如何展示文献库和去重；
5. Screening 页面如何组织标题摘要和全文筛选；
6. Full-text & Extraction 的类型专属提取表如何展示；
7. Quality Assessment 如何根据 Meta 类型切换工具；
8. Meta Analysis Tasks 与 Result / Report 是否复用 Bioinformatics 的“任务页 → 单次结果页 → 报告导出”逻辑。

---

## 15. 当前确认决策摘要

已确认：

```text
1. Meta Analysis 采用“通用主流程 + Meta 类型预分流 + 类型专属提取/分析模板”。
2. 当前 UI 类型以 active Data Extraction Schema Registry v1 为准。
3. 当前 active registry 包含 10 种 Meta 类型。
4. Network Meta 当前是 legacy / placeholder，不作为当前可用类型。
5. Meta 类型选择会控制提取 schema、质量评价、统计分析、结果模板和报告结构。
6. 当前 Meta Analysis 仍是 Developer Preview / testing。
7. Legacy registry 只作历史参考，不作为当前 UI 类型来源。
8. 当前 active runtime 已有 testing 主链，但不代表生产级系统综述能力。
```
