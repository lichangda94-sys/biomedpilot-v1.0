# BioMedPilot UI Stage 0.3：Shell / Bioinformatics QSS 轻量迁移试点报告

日期：2026-05-13
范围：MainLine `app/shell`、MainLine `app/bioinformatics/pages` 入口型页面、`app/shared/ui`

## 1. 本阶段迁移范围

本阶段只在 MainLine 工作树内执行低风险 UI 迁移试点，目标是验证 Stage 0.2 新增的 shared UI tokens 能够服务真实页面。

实际迁移范围：

- Shell 基础壳层：
  - `app/shell/sidebar.py`
  - `app/shell/status_panel.py`
  - `app/shell/main_window.py`
- Bioinformatics 入口型页面：
  - `app/bioinformatics/pages/geo_import_page.py`
  - `app/bioinformatics/pages/local_expression_import_page.py`
- Shared UI helper：
  - `app/shared/ui/theme.py`
  - `app/shared/ui/__init__.py`
- UI 测试：
  - `tests/ui/test_shared_ui_theme.py`

未迁移范围：

- Bioinformatics workflow 业务流程页。
- Bioinformatics 分析任务、结果、报告生成逻辑。
- Meta Analysis UI。
- LabTools UI 或业务代码。
- 外部 `Bioinformatics`、`Meta`、`UIShell` worktree。

## 2. 哪些文件被修改

代码与测试：

- `app/shared/ui/theme.py`
  - 新增纯字符串 QSS helper。
- `app/shared/ui/__init__.py`
  - 导出新增 QSS helper。
- `app/shell/sidebar.py`
  - 使用 shared helper 生成 sidebar 背景、边框、hover、标题和辅助文字样式。
- `app/shell/status_panel.py`
  - 使用 shared helper 生成 surface card 和 card title 样式。
- `app/shell/main_window.py`
  - 使用 shared helper 生成 entry card、list card、recent projects card 和标题样式。
- `app/bioinformatics/pages/geo_import_page.py`
  - 使用 shared helper 生成页面标题、summary card、错误文本样式。
- `app/bioinformatics/pages/local_expression_import_page.py`
  - 使用 shared helper 生成页面标题、summary card、warning/error 文本样式。
- `tests/ui/test_shared_ui_theme.py`
  - 覆盖 shared QSS helper 输出。

文档：

- `docs/ui/BioMedPilot_UI_Stage_0_3_QSS_Migration_Report_20260513.md`

## 3. 哪些硬编码颜色被替换为 Shared UI Tokens

通过 helper 间接替换的硬编码色包括：

- `#F8FAFC`
  - Shell sidebar 背景改为 `BioMedPilotColors.SURFACE_MUTED`。
- `#D8DEE9`
  - Shell card / sidebar border、Bioinformatics summary card border 改为 `BioMedPilotColors.BORDER_MEDIUM`。
- `#FFFFFF`
  - Shell card、Bioinformatics summary card 背景改为 `BioMedPilotColors.SURFACE_WHITE`。
- `#64748B`
  - Shell sidebar footer 辅助文字改为 `BioMedPilotColors.TEXT_SECONDARY`。
- `#B42318`
  - Bioinformatics 入口页错误文本改为 `BioMedPilotColors.STATUS_ERROR`。
- `#92400E`
  - Bioinformatics 本地表达矩阵导入页 warning 文本改为 `BioMedPilotColors.STATUS_WARNING`。
- `#EAF0F7`
  - Shell sidebar hover 背景改为 `BioMedPilotColors.BIO_SOFT`。

同时，`font-size: 20px; font-weight: 700;` 和 `font-weight: 700;` 在试点文件中改为 shared helper 输出，避免后续页面继续复制裸字符串。

## 4. 哪些 QSS 仍保留硬编码，原因是什么

仍保留的硬编码：

- `app/ui_style_tokens.py` 内部的大段历史 QSS。
  - 原因：这是当前登录页、模块选择页和 Bioinformatics 项目首页的兼容入口；全量拆分会超出 Stage 0.3 试点范围。
- Bioinformatics 其他普通子页面中的 summary card、title、error label QSS。
  - 原因：本阶段只选择 `geo_import_page.py` 和 `local_expression_import_page.py` 两个入口型页面验证可行性，避免一次性大规模替换。
- Bioinformatics legacy UI 中的旧色值。
  - 原因：legacy 目录仍可能存在历史依赖，按总手册要求不得在本阶段直接重构或删除。
- `app/ui_theme.py` 的全局 Qt palette 色值。
  - 原因：全局 palette 影响范围较大，适合 Stage 0.4 独立迁移和视觉回归确认。
- Shell 设置页、测试页中部分标题字号和 list card 内容文本样式。
  - 原因：本阶段只迁移重复卡片、sidebar 和基础 helper，不调整页面结构与信息层级。

## 5. 是否新增 Shared UI Helper

是。新增 helper 均在 `app/shared/ui/theme.py`，不依赖 Qt，不导入业务模块，不制造循环 import。

新增 helper：

- `surface_card_qss(selector: str = "QFrame")`
- `page_title_qss()`
- `card_title_qss()`
- `helper_text_qss()`
- `error_text_qss()`
- `warning_text_qss()`
- `shell_sidebar_qss()`

这些 helper 只封装基础视觉样式，不承载业务语义。业务模块仍负责流程、状态计算和按钮行为。

## 6. 是否修改 Bioinformatics / Meta / LabTools 业务代码

没有修改业务逻辑。

本阶段对 Bioinformatics 的改动仅限 MainLine 内两个 UI 页面中的纯视觉 QSS 替换：

- 不改变数据检索逻辑。
- 不改变本地表达矩阵导入逻辑。
- 不改变按钮行为。
- 不改变服务调用。
- 不改变数据结构或结果语义。

未修改 Meta Analysis 代码。未创建或修改 LabTools 代码。

## 7. 是否触碰外部 Bioinformatics / Meta Worktree

没有。

本阶段只在 `/Users/changdali/Developer/biomedpilot v1.0/MainLine` 内操作。外部 `Bioinformatics` 和 `Meta` worktree 已知存在未提交改动，本阶段未进入修改、未 reset、未 stash、未提交这些外部改动。

## 8. 当前仍存在的 UI 一致性风险

P1：

- Bioinformatics 其他普通子页面仍有重复硬编码 summary card、title、error label QSS。
- `app/ui_theme.py` 的全局 palette 尚未使用 shared tokens，仍可能与总色板产生轻微漂移。
- `app/ui_style_tokens.py` 仍是较长兼容样式入口，后续需要拆为 helper 或组件层。

P2：

- Shell 设置页和测试页仍有局部标题字号、页面边距和说明文案未抽取。
- Bioinformatics workflow 大页中仍有多种 objectName 和 buttonRole 样式，尚未迁移到 shared button helper。
- 状态标签已有 token，但还没有 `StatusBadge` QWidget 或统一 QSS 生成器。

P3：

- legacy UI 的旧视觉语言继续保留，不作为新 UI 参考。
- Meta mainline 最小入口未在本阶段迁移，因用户明确本阶段不修改 Meta Analysis UI。

## 9. 后续 UI Stage 0.4 建议

建议 Stage 0.4 继续保持小步迁移：

1. 将 Bioinformatics 其余普通 `pages/*_page.py` 的 summary card、title、error label 改为 shared helper。
2. 将 `app/ui_theme.py` 的全局 Qt palette 迁移到 shared colors，并保留 UI theme 测试。
3. 新增 `status_badge_qss(status)`，让 Ready / Warning / Error / Draft / Confirmed 状态标签开始统一。
4. 新增 `button_qss(role)` 或对象属性到 shared helper，对齐 primary、secondary、danger、back、next。
5. 对 Shell 设置页、测试页做一次技术字段密度审计，避免图标资源、路径和诊断信息过多出现在普通主界面。
6. 继续禁止新页面直接硬编码总色板和常用状态色；新增页面应优先引用 shared UI tokens 或 helper。

## 10. 本阶段结论

Stage 0.3 已完成 shared UI tokens 在真实 Shell / Bioinformatics 页面中的轻量试点迁移。迁移范围保持在纯视觉 QSS 层，没有修改业务流程、数据结构、分析逻辑、Meta Analysis 或 LabTools。

试点结果表明，`app/shared/ui/theme.py` 可以作为后续 QSS helper 和 common components 的稳定基础。后续应按页面族逐步迁移，而不是一次性替换所有硬编码样式。
