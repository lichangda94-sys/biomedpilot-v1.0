# BioMedPilot UI Stage 0.5：Bioinformatics 流程页面 UI 收敛审计与低风险迁移

日期：2026-05-13
范围：MainLine `app/bioinformatics` 流程型 UI、轻量 `pages/*_page.py`、`tests/ui`、本阶段 UI 审计报告

## 1. 本阶段工作范围

本阶段承接 UI Stage 0.1-0.4，只在 MainLine 工作树内执行 Bioinformatics 流程页面 UI 收敛审计和低风险迁移。

实际工作聚焦：

- 审计 `app/bioinformatics/workflow_pages.py` 中项目首页后主流程页面的状态、按钮、页面结构、技术字段暴露情况。
- 审计 `app/bioinformatics/pages/*_page.py` 中仍在复制硬编码标题、卡片、错误文本和按钮 QSS 的轻量流程页。
- 选择 4 个低风险轻量流程页做 shared UI helper 迁移试点。
- 增加 UI 测试，确认迁移页面可实例化且样式来自 shared token/helper。
- 记录仍需 Stage 0.6 或后续处理的技术字段和按钮层级问题。

未做的事：

- 未开发 Bioinformatics 新功能。
- 未修改下载、识别、标准化、分析任务、结果或报告服务逻辑。
- 未修改 Meta Analysis UI。
- 未创建 LabTools 代码。
- 未进入外部 Bioinformatics / Meta 独立 worktree。

## 2. 开始前 Git Status 结论

开始前确认当前目录：

```text
/Users/changdali/Developer/biomedpilot v1.0/MainLine
```

开始前执行 `git status --short`，输出为空。

本阶段实际观察到 `docs/handoff/BioMedPilot_v1_desktop_entry_audit_20260513.md` 文件存在，但它已被 Git 跟踪：

```text
100644 ... docs/handoff/BioMedPilot_v1_desktop_entry_audit_20260513.md
```

因此它不是当前 MainLine 的未跟踪脏文件。本阶段未修改、未移动、未删除该文件，也未纳入本阶段提交变更。

## 3. 对既有 Handoff 文件的处理说明

`docs/handoff/BioMedPilot_v1_desktop_entry_audit_20260513.md` 与 UI Stage 0.5 无直接关系。本阶段只做只读存在性和 Git 跟踪状态判断，不改动该文件。

## 4. 审计的 Bioinformatics 页面

本阶段重点审计：

- `app/bioinformatics/project_home.py`
- `app/bioinformatics/workspace.py`
- `app/bioinformatics/workflow_pages.py`
- `app/bioinformatics/pages/geo_import_page.py`
- `app/bioinformatics/pages/local_expression_import_page.py`
- `app/bioinformatics/pages/geo_download_page.py`
- `app/bioinformatics/pages/geo_asset_detection_page.py`
- `app/bioinformatics/pages/geo_cleaning_page.py`
- `app/bioinformatics/pages/sample_grouping_page.py`
- `app/bioinformatics/pages/differential_expression_page.py`
- `app/bioinformatics/pages/enrichment_page.py`
- `app/bioinformatics/pages/correlation_page.py`
- `app/bioinformatics/pages/survival_page.py`
- `app/bioinformatics/pages/bio_report_page.py`

## 5. 实际迁移的页面或区域

本阶段迁移 4 个轻量流程页：

- `app/bioinformatics/pages/geo_download_page.py`
- `app/bioinformatics/pages/geo_asset_detection_page.py`
- `app/bioinformatics/pages/geo_cleaning_page.py`
- `app/bioinformatics/pages/differential_expression_page.py`

迁移内容仅限纯视觉样式：

- 页面标题使用 `page_title_qss()`。
- 功能状态使用 `status_badge_qss("testing")`。
- 等待状态使用 `status_badge_qss("pending")`。
- 成功状态使用 `status_badge_qss("completed")`。
- 错误状态使用 `status_badge_qss("error")`。
- 主操作按钮使用 `primary_button_qss()`。
- 文件选择按钮使用 `secondary_button_qss()`。
- 禁用的下一步按钮使用 `navigation_button_qss()`。
- 摘要卡片使用 `surface_card_qss()`。
- 错误文本使用 `error_text_qss()`。

没有修改按钮连接、服务调用、结果生成、文件路径处理或业务状态计算。

## 6. 替换的硬编码 QSS 或样式

已替换：

- `font-size: 20px; font-weight: 700;`
  - 替换为 `page_title_qss()`。
- `QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }`
  - 替换为 `surface_card_qss()`。
- `color: #B42318;`
  - 替换为 `error_text_qss()`。
- 默认 `QPushButton` 主操作、次操作、禁用下一步按钮
  - 分别替换为 shared button helpers。
- 普通 `QLabel` 功能状态和流程状态
  - 替换为 shared status badge helper。

仍保留的硬编码或局部样式：

- `app/bioinformatics/workspace.py` 中 `_feature_row()` 的卡片和标题内联 QSS。
- `sample_grouping_page.py`、`enrichment_page.py`、`correlation_page.py`、`survival_page.py`、`bio_report_page.py` 中相同轻量页面 QSS。
- `workflow_pages.py` 仍依赖 `bioinformatics_project_home_stylesheet()`、objectName 和 `buttonRole` 属性管理大流程页样式。
- `app/ui_style_tokens.py` 仍是兼容入口，未在本阶段拆分。

保留原因：本阶段目标是 2-4 个低风险试点，不做全量替换。`workflow_pages.py` 影响面大，后续应单独做主流程页结构与技术字段治理。

## 7. 是否新增或扩展 Shared UI Helper

没有。

本阶段复用 Stage 0.3 / 0.4 已建立的 shared UI helper：

- `page_title_qss()`
- `surface_card_qss()`
- `status_badge_qss()`
- `primary_button_qss()`
- `secondary_button_qss()`
- `navigation_button_qss()`
- `error_text_qss()`

没有新增 helper，没有引入业务模块命名，没有制造循环 import。

## 8. 是否修改业务逻辑

没有。

本阶段未修改：

- Bioinformatics 服务层。
- 下载逻辑。
- 数据识别逻辑。
- 标准化逻辑。
- 分析任务中心逻辑。
- 结果生成逻辑。
- 报告生成逻辑。
- AI Gateway。
- 共享词库。
- 数据结构。

## 9. 是否触碰 Bioinformatics / Meta 独立 Worktree

没有。

本阶段只在 `/Users/changdali/Developer/biomedpilot v1.0/MainLine` 内操作。未进入、未修改、未提交外部 `Bioinformatics` 或 `Meta` 独立 worktree。

## 10. 技术字段暴露问题清单

### 已记录但本阶段不改

P1：

- `workflow_pages.py` 分析任务中心仍显示较多任务技术字段，包括 task type、run id、任务参数、任务记录和执行状态。
- `workflow_pages.py` 结果浏览和报告相关区域仍可能暴露结果路径、参数 JSON、warning 技术列、result index、run id。
- `workflow_pages.py` 标准化诊断区虽然已经折叠，但表格列仍包含资产 ID、默认资产、manifest 与 registry 相关内容；当前作为开发者诊断可接受，后续应继续限制普通主界面可见范围。
- `local_expression_import_page.py` 成功摘要仍显示 Manifest 路径，后续应移入开发者详情或改为压缩路径 / tooltip。
- 本阶段迁移的 4 个轻量页面成功摘要仍显示 `source_path` 和 `output_path`，属于旧 testing-level 手动页的技术字段，应在后续阶段统一折叠。

P2：

- `project_home.py` 的项目结构说明仍出现 `project_manifest.json`、`project_config.json` 和目录名；目前已有技术详情意识，后续可继续压缩主界面文案。
- 数据来源页仍存在“添加到项目”“下载补充文件”“进入数据识别”等多个操作并列，后续需要继续收敛主操作和次操作层级。
- 中文研究问题检索页中“确认草稿”“选择”“下载并添加”“创建下载清单”等操作词需要统一到有限动词集。

P3：

- legacy UI 和旧工具目录仍保留旧视觉语言和技术日志表达，本阶段只记录，不作为新 UI 参考。

## 11. 仍需后续阶段处理的问题

建议 Stage 0.6 或后续阶段处理：

1. 继续迁移 `sample_grouping_page.py`、`enrichment_page.py`、`correlation_page.py`、`survival_page.py`、`bio_report_page.py` 和 `workspace.py` 的轻量 QSS。
2. 将 4 个已迁移轻量页的 `source_path`、`output_path` 摘要移入统一 Developer Details / diagnostic card。
3. 对 `workflow_pages.py` 的 `_button()`、`_apply_button_semantics()` 做 shared button helper 接入设计，但需要先评估对全部流程页的视觉影响。
4. 分析任务中心应从“技术命令面板”收敛为“当前主操作 + 次操作 + 开发者诊断”结构。
5. 结果浏览和报告页应隐藏参数 JSON、run id、result path 等技术字段，主界面只保留研究人员可理解摘要。
6. 建立跨模块 `DeveloperDetails` 组件或 helper，承接 manifest、asset id、run id、raw JSON、schema、registry entry。
7. 新增 UI lint 或轻量测试，阻止新 Bioinformatics 页面继续直接硬编码 `#D8DEE9`、`#FFFFFF`、`#B42318` 和标题 QSS。

## 12. P0 / P1 / P2 / P3 风险分级

### P0

本阶段未发现需要立即停止的 P0 冲突。MainLine 仍遵守 UI Governance / UI Design Principles 权威，不涉及 Meta 独立主题合入或 LabTools 新建代码。

### P1

- 分析任务中心多个主操作竞争，仍可能影响用户判断下一步。
- 结果浏览、报告和部分轻量页仍有路径、JSON、run id、manifest 等技术字段主界面暴露。
- 轻量页只迁移 4 个，剩余轻量页继续保留重复硬编码 QSS，后续若继续复制会造成 UI 分裂。

### P2

- Bioinformatics `workflow_pages.py` 的状态标签、按钮语义和 objectName 样式还没有完全接入 shared helper。
- `workspace.py` feature row 和部分普通页面仍有局部卡片、标题、错误色硬编码。
- “登记 / 添加 / 选择 / 下载并添加 / 创建下载清单 / 保存默认资产选择”动词体系仍需统一。

### P3

- legacy UI 保留旧样式，当前不重构。
- 旧 testing-level 手动页仍有技术字段，因它们不是主线首屏流程，当前先记录。

## 13. 测试结果

已完成验证：

- `git diff --check`：通过
- `git diff --cached --check`：通过
- `python3 -m app.main --smoke-test`：通过
- `python3 -m pytest tests/ui/test_shared_ui_theme.py -q`：6 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_light_flow_page_styles.py -q`：4 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：143 passed
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`：264 passed

本阶段没有修改 Meta Analysis 代码，未运行 `tests/meta_analysis`。

## 14. 是否未执行 Git Push

未执行 `git push`。
