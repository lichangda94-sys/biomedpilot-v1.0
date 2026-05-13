# Meta UI Theme Unification Report

日期：2026-05-13

## 1. 修复目标

本阶段目标是在不改变 Meta 业务流程、不合并 MainLine、不修改 Bioinformatics、不重构 legacy 的前提下，将 active Meta UI 的主视觉收敛到 BioMedPilot / 医研智析 当前统一色板：

- deep navy：`#12324A`
- teal：`#1BAE9F`
- light gray：`#F5F7F9`
- white：`#FFFFFF`

本阶段只处理 active Meta UI 主题 token、QSS 入口、页面卡片 / 文本 / 错误样式和对应测试，不修改 AI Gateway、shared vocabulary、数据 schema、分析逻辑或 legacy 文件。

## 2. 当前分支 / worktree / git head

| 项目 | 结果 |
| --- | --- |
| worktree | `/Users/changdali/Developer/biomedpilot v1.0/Meta` |
| branch | `dev/meta-analysis` |
| 起始 git head | `9153aab31e39d8e79805b7d19f582abc0ca443fa` |
| 起始状态 | clean |

## 3. 修改文件清单

代码：

- `app/ui_style_tokens.py`
- `app/meta_analysis/workspace.py`
- `app/meta_analysis/pages/literature_import_page.py`
- `app/meta_analysis/pages/duplicate_review_page.py`
- `app/meta_analysis/pages/screening_page.py`
- `app/meta_analysis/pages/prepare_screening_page.py`
- `app/meta_analysis/pages/extraction_page.py`
- `app/meta_analysis/pages/analysis_page.py`
- `app/meta_analysis/pages/reporting_page.py`
- `app/meta_analysis/pages/audit_log_page.py`
- `app/meta_analysis/pages/attachment_page.py`
- `app/meta_analysis/pages/workflow_dashboard_page.py`

测试：

- `tests/meta_analysis/test_literature_import_ui_construction.py`
- `tests/meta_analysis/test_meta_ui_theme_tokens.py`

文档：

- `docs/audit/meta_ui_theme_unification_report_20260513.md`

## 4. 移除或替换的颜色清单

| 原颜色 | 原用途 | 当前处理 |
| --- | --- | --- |
| `#6B4FD8` | `COLORS["meta"]` purple 主色 | 替换为 `COLORS["deep_navy"]` / `#12324A` |
| `#F0EDFF` | `COLORS["meta_soft"]` purple soft | 替换为 `COLORS["light_gray"]` / `#F5F7F9` |
| `#0F766E` | Meta workspace 主按钮 / badge 深 teal | 替换为 `COLORS["teal"]` / `#1BAE9F` |
| `#E6FFFB` | Meta status badge 背景 | 替换为 `COLORS["light_gray"]` / `#F5F7F9` |
| `#99F6E4` | Meta status badge 边框 | 替换为 `COLORS["teal"]` / `#1BAE9F` |
| `#D8DEE9` | 多个 active Meta 卡片边框 | 替换为 `COLORS["border"]` |
| `#111827` | active Meta workspace / import panel 文本 | 替换为 `COLORS["text"]` 或 `COLORS["deep_navy"]` |
| `#B42318` | 多个 active Meta 错误提示 | 替换为 `COLORS["danger"]` |

active Meta 代码扫描结果：排除 `app/meta_analysis/legacy/**` 后，`app/meta_analysis` 和 `app/ui_style_tokens.py` 不再包含上述 retired 主题色。

## 5. active Meta UI 当前使用的统一 token 说明

`app/ui_style_tokens.py` 现在提供统一主视觉别名：

- `COLORS["deep_navy"] = "#12324A"`
- `COLORS["teal"] = "#1BAE9F"`
- `COLORS["light_gray"] = "#F5F7F9"`
- `COLORS["white"] = "#FFFFFF"`
- `COLORS["meta"] = COLORS["deep_navy"]`
- `COLORS["meta_accent"] = COLORS["teal"]`
- `COLORS["meta_soft"] = COLORS["light_gray"]`

新增 active Meta UI helper：

- `meta_workspace_stylesheet()`
- `meta_card_stylesheet()`
- `meta_error_text_style()`
- `meta_text_style()`
- `meta_title_style()`

`app/meta_analysis/workspace.py` 不再维护独立 `_meta_workspace_stylesheet()`，而是使用 shared token helper。多个 active Meta page widget 的卡片、标题、错误和导入结果文本样式也改为使用这些 helper。

## 6. legacy 是否仍影响 active runtime

本阶段未修改、未删除、未重构 `app/meta_analysis/legacy/`。

检查结果：

- 未发现 active Meta UI 直接调用 legacy UI、`app_meta.ui`、demo project loader 或 mock runner。
- 未新增任何 legacy 依赖。
- 既有 active service adapter 仍存在 transitional legacy bridge，例如 literature import / duplicate review / extraction / screening / analysis adapter 通过 legacy path 复用历史 parser 或 service。这是既有文档记录的技术债，不属于本阶段主题修复范围。
- 因此，legacy 不影响本阶段 active UI 主题统一；但 MainLine 合并前仍应在 Integration 阶段继续把 legacy 作为隔离风险处理。

## 7. 测试结果

| 命令 | 结果 |
| --- | --- |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q` | 460 passed |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | 154 passed |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/shared -q` | 51 passed |
| `python3 -m app.main --smoke-test` | passed；`git_head=9153aab`；`pyside6_available=True` |
| `git diff --check` | passed |

新增测试覆盖：

- Meta token 不再使用 purple `#6B4FD8 / #F0EDFF`。
- Meta workspace stylesheet 使用 deep navy / teal / light gray / white。
- active Meta UI source 不包含本次 retired 主题色。
- active Meta UI source 不引用 legacy UI / demo runtime / mock runner。

## 8. 剩余风险

- `app/ui_style_tokens.py` 中 shell / login / Bioinformatics 仍有历史硬编码状态色、macOS traffic light 色和少量非主色 hover/soft 色；本阶段未处理非 Meta active UI。
- Meta report SVG / HTML 导出仍有报告物内部样式色。本阶段目标是 desktop active UI 主题统一，未重构 report/export 视觉 token。
- 既有 transitional legacy service adapters 仍是 MainLine 合并前技术债，但不属于本阶段主题修复。
- 尚未在 Integration worktree 做合并演练，也未运行 MainLine 全矩阵。

## 9. 是否建议进入 Integration 合并验证

建议进入 Integration 合并验证。

理由：

- active Meta UI 的主主题色已统一到 BioMedPilot 主色板。
- active Meta UI 不再使用审计指出的 purple / retired teal / retired border / retired error hardcoding。
- Meta、UI、shared 测试和 smoke test 均通过。
- 未修改 Bioinformatics、MainLine、AI Gateway、shared vocabulary、schema 或业务分析流程。

进入 Integration 前仍需确认合并清单：active Meta runtime、必要 tests/docs、legacy 隔离策略，不建议整目录无差别合并 legacy。

## 10. 下一阶段建议

下一阶段建议执行：

`integration(meta): validate themed Meta workflow merge surface`

建议内容：

- 在 Integration worktree 做 Meta 主题统一后的 staged merge 演练。
- 运行 Meta、UI、shared、architecture boundary 和必要 MainLine smoke。
- 明确 legacy 目录在 MainLine 的保留 / 隔离 / 不接入策略。
- 若 Integration 验证通过，再准备 MainLine merge readiness handoff。
