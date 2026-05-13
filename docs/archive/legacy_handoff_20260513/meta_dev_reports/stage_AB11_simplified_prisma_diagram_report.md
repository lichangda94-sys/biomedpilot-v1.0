# Stage AB11 - Simplified PRISMA Diagram

## 本阶段目标

在已有 PRISMA summary / source references 基础上，生成 testing 级简化 PRISMA Markdown 和 SVG 图。该图仅用于内部 beta 检查和测试人员理解流程，不是正式 PRISMA 2020 diagram。

## Continuity Audit

- 当前分支：`codex/biomedpilot-root`
- 起始 HEAD：`761fe6f feat(meta): add analysis setup workflow`
- 工作区状态：仅存在既有未跟踪 `test_inputs/`，本阶段未修改或提交该目录。
- 审计正式项目模块：
  - `app/meta_analysis/services/formal_report_service.py`
  - `app/meta_analysis/models/prisma.py`
  - `app/meta_analysis/pages/reporting_page.py`
  - `app/meta_analysis/services/project_contract_service.py`
  - `app/meta_analysis/services/report_manifest_service.py`
  - `tests/meta_analysis/test_prisma_formal_report_mvp.py`
  - `tests/meta_analysis/test_stage_9_prisma_audit_display.py`
- 已有能力：PRISMA number collector、`prisma_flow_summary.json`、`prisma_flow_summary.md`、source references、Reporting page trace。

## Legacy Capability Audit

- 检查 legacy 目录中 PRISMA/report 相关实现。
- 未迁移 legacy 图形逻辑；原因是当前正式项目已有 PRISMA source references、report manifest 和 project contract，新增简化 SVG 直接复用当前服务更安全。

## 本阶段新增行为

- `PRISMAService.export_simplified_prisma_flow()` 生成：
  - `reports/prisma_summary.json`
  - `reports/prisma_flow.md`
  - `reports/prisma_flow.svg`
- SVG 包含：
  - records identified；
  - duplicates removed；
  - records after deduplication；
  - records screened；
  - title/abstract excluded；
  - full-text sought；
  - full-text excluded；
  - studies included。
- Markdown 明确写明 Developer Preview、testing、not formal PRISMA 2020。
- Formal Markdown report builder 在缺少简化 PRISMA SVG 时自动生成 testing SVG。
- Reporting page state 更新为说明“简化 PRISMA SVG”，不再说完全不生成 diagram。

## Data Center / Task Center / Audit / Manifest / Lineage 影响

- Data Center 新增：
  - `prisma_summary`
  - `simplified_prisma_flow`
- Task Center 继续复用既有 `prisma_collect`。
- Project contract 新增 canonical paths：
  - `prisma_summary`
  - `prisma_flow_markdown`
  - `prisma_flow_svg`
- Lineage 新增：
  - `reports/prisma_flow.svg -> reports/prisma_summary.json`
- Report manifest PRISMA section 同时列出旧 summary 和新简化输出；旧项目没有新 SVG 时只给 optional warning，不破坏旧测试。

## 测试

新增：

- `tests/meta_analysis/test_stage_ab11_simplified_prisma_diagram.py`

覆盖：

- 生成 summary JSON、flow Markdown、flow SVG；
- SVG 文件存在且包含 Developer Preview 限制；
- Data Center 登记；
- Report manifest / artifact manifest 包含简化 PRISMA 输出；
- Formal report builder 自动生成简化 PRISMA flow；
- Reporting page state 显示简化 testing diagram。

## 当前限制

- 不生成正式 PRISMA 2020 diagram。
- 不生成 PRISMA PNG，默认使用轻量 SVG。
- full-text workflow 不完整时，full-text 数字仍带 testing estimate / incomplete note。
- 图形布局为稳定可读版本，不是投稿级排版。

## 下一阶段建议

进入 AB12：Report Template Hardening。建议继续复用 formal Markdown/HTML/DOCX testing report，补充 internal beta 报告章节和 report manifest source 列表；正式 PDF 继续保持未实现。
