# Stage P UX And Production Gap Report

## 本阶段目标

从真实医学研究者视角检查当前 Meta Analysis 是否清楚表达 testing 状态、每一步的输入/输出/下一步、empty state、用户可读 warning/error，以及 production/internal beta 前差距。

## 实际完成内容

- 为 Meta Analysis 页面状态补充统一的 `input_summary`、`output_summary`、`next_step`、`empty_state`、`warning_summary` 字段。
- 保持所有 Meta 功能为 `testing`，没有升级为 open/production。
- 新增 Stage P tests，验证 7 步主链加 AI Suggestions Queue 的 testing 状态、页面状态说明和关键 placeholder 明确性。

## 修改/新增文件列表

- `app/meta_analysis/pages/literature_import_page.py`
- `app/meta_analysis/pages/prepare_screening_page.py`
- `app/meta_analysis/pages/duplicate_review_page.py`
- `app/meta_analysis/pages/screening_page.py`
- `app/meta_analysis/pages/extraction_page.py`
- `app/meta_analysis/pages/analysis_page.py`
- `app/meta_analysis/pages/reporting_page.py`
- `app/meta_analysis/pages/ai_suggestions_page.py`
- `tests/meta_analysis/test_stage_p_ux_production_gap.py`
- `docs/meta_dev_reports/stage_P_ux_production_gap_report.md`

## 已可稳定用于内部测试的能力

- 本地文献 CSV/RIS/NBIB 导入 testing 流程。
- 标准化筛选准备、重复候选识别、最小去重决策。
- 标题摘要筛选队列和 include/exclude/maybe 决策保存。
- 结构化 ExtractionRecord 保存、校验、CSV 导出。
- Analysis-ready dataset 构建。
- 基础 pooled effect、forest plot、funnel plot、result table。
- PRISMA summary、formal Markdown/HTML/DOCX testing report、supplementary exports、figure package、snapshot、reproducibility package。
- AI suggestion queue 的人工确认安全机制。

## 可以升级为 experimental 的候选能力

- 基础 pooled effect 统计核心：Stage N 已增加 reference tests，但仍建议保持 testing，待真实项目和统计专家复核后再考虑 experimental。
- HTML/DOCX report export：已可生成 testing 输出，但模板与引用管理尚不足以标为 production。
- Traceability audit：适合 internal beta 审计辅助，但仍是轻量 checker。

## 仍必须保持 testing 的能力

- 所有 Meta Analysis 7 步主链。
- Extraction 表单和 advanced method outcome 输入。
- Analysis 页面中的 preflight、dataset builder、run result、advanced analysis。
- Reporting 页面中的 formal Markdown/HTML/DOCX testing report。
- AI-assisted Review。

## Placeholder 能力

- Network meta-analysis：明确 not implemented。
- PDF formal report：正式 PDF 未开放。
- Diagnostic advanced bivariate / HSROC：未实现。
- Begg test：当前为 placeholder。
- Full-text PDF 管理和全文流程仍未达到生产级。

## 进入 beta 前必须修复的问题

- 统一项目目录数据契约，减少 early service 输出落在 storage-root 而非 project_dir 的情况。
- 改善 Extraction/Quality 录入体验，降低人工补数据成本。
- 在 UI 中更清晰地区分 Analysis preflight、analysis-ready dataset、analysis run result 和 advanced analysis。
- 对统计结果添加更明确的解释限制和适用条件。
- Formal report 需要结构化 artifact manifest，而不是仅依赖 Markdown 文本路径。
- PDF 策略需要明确：轻量 HTML-to-PDF、系统依赖方案，或暂不开放。

## 可以后置的增强项

- 投稿级 Word/PDF 模板。
- 双人筛选冲突仲裁完整流程。
- OCR/PDF 自动数据抽取。
- 高级 diagnostic bivariate/HSROC。
- Network meta-analysis。
- 外部在线检索 Stage Q。
- AI provider 接入和更复杂的人机审核工作流。

## 测试结果

Stage P 新增 page-state/UX tests。

- Stage P focused tests: `5 passed`
- M-P focused tests: `18 passed`
- Full venv pytest: `256 passed`
- Unified `scripts/run_tests.py`: `256 passed`
- Smoke test: passed
- Local shell `python` / `pytest`: unavailable in this environment; venv commands passed.

## 当前结论

Meta Analysis 已具备 internal beta 候选所需的本地 testing 验证基础，但仍不是 production。下一步如要进入 Stage Q，必须单独授权联网检索验证。
