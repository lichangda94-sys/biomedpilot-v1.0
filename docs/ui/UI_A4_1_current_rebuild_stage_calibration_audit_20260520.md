# UI-A4.1 Current UI Rebuild Stage Calibration Audit

审计日期：2026-05-20

本阶段目标：对 UI-A4 v1 后已经执行的 UI-B0 到 UI-B8 / UI-B9a 工作进行阶段校准，确认当前实现与 MasterPlan、Stage Index、A1-A4 审计边界是否一致，标出已完成、部分完成、尚未开始、需要重命名或重新校准的阶段。此阶段只新增审计文档，不修改业务代码、不修改资源、不打包、不运行 packaged app、不覆盖桌面入口。

## 1. 审计范围

| input | audit_use |
|---|---|
| `docs/ui/UI_A4_rebuild_execution_plan_audit_20260520.md` | UI-B0 到 UI-B10 原始阶段边界和测试策略。 |
| `docs/ui/UI_Rebuild_MasterPlan_20260520.md` | 当前最高优先级 UI 重建标准。 |
| `docs/ui/UI_Rebuild_Stage_Index_20260520.md` | 阶段索引和验收基线。 |
| `docs/ui/UI_B8_resource_inventory_placeholder_strategy_audit_20260520.md` | 最新资源 inventory / placeholder 策略边界。 |
| `docs/ui/resource_inventory/UI_B8_resource_inventory_20260520.csv` | 缺失资源、placeholder、不能替换资源清单。 |
| `app/shell/**`, `app/shared/**`, `app/bioinformatics/workspace.py`, `app/meta_analysis/workspace.py` | 当前 UI shell、语义 key、结果/报告/导出壳层、模块 IA shell 状态。 |
| `tests/ui/**`, `tests/shared/test_semantic_keys.py`, `tests/shared/test_result_report_export_shell.py` | 当前 focused tests 覆盖。 |
| Git history `c901a21` 回溯到 UI-B1 | 校准实际完成顺序和提交边界。 |

## 2. 本阶段未修改业务代码声明

本阶段只新增：

`docs/ui/UI_A4_1_current_rebuild_stage_calibration_audit_20260520.md`

未修改：

- `app/**`
- `tests/**`
- `assets/**`
- `scripts/**`
- `dist/**`
- 桌面 `.app`

未打包，未运行 packaged app，未替换 active 图标，未覆盖桌面入口。

## 3. 当前提交链校准

| stage_or_scope | commit | observed_result |
|---|---|---|
| UI-B0 | `fd2d04e` | MasterPlan、Visual Style Guide、I18N Strategy、Stage Index 已建立。 |
| UI-B1 | `d2c6c92` | design tokens、theme、基础 primitives 与 focused tests 已建立。 |
| UI-B2 | `64841f6` | Welcome、三模块 Dashboard、Sidebar、About、Test Feedback 低保真壳层已建立。 |
| UI-B3 | `5f8ea5a` | Settings 二级导航、外部能力管理、detect-first UI、开发者诊断折叠入口已建立。 |
| UI-B9a | `b494c51` | brand/nav/module/status/report/export key registry 与核心语义枚举已落地。 |
| UI-B4 | `749f735` | LabTools IA shell 已建立，三入口和五类实验边界可见。 |
| UI-B5 | `152ae96` | Bioinformatics 目标 IA shell 已收束，正式分析执行器未启用。 |
| UI-B6 | `ffdc422` | Meta Analysis 目标 IA shell、10 类 active Meta 类型、Network Meta planned boundary 已建立。 |
| UI-B7 | `c802964` | Result / Report / Export 共享语义壳层、空状态、导出 gating、免责声明已建立。 |
| UI-B8 audit/inventory | `c901a21` | 资源清单与 placeholder 策略已建立；没有替换 active 图标。 |

当前 HEAD：`c901a21`

## 4. 阶段状态校准表

| stage | planned_scope | current_status | calibration |
|---|---|---|---|
| UI-B0 | 文档治理和路线冻结 | 完成 | 但 `UI_Rebuild_MasterPlan` 和 `UI_Rebuild_Stage_Index` 内仍写 `Current phase/stage: UI-B0`，现在已成为历史描述，需要在后续文档更新中校准。 |
| UI-B1 | tokens/theme/primitives | 完成 | `app/ui_style_tokens.py` 与 `app/shared/ui_components/primitives.py` 存在；focused tests 覆盖 status chip、button、card、empty state。 |
| UI-B2 | Welcome / Dashboard / Sidebar / About / Test Feedback shell | 完成低保真 | 三模块入口、Sidebar、About、Test Feedback 可见；仍保留 current user/version 等低保真状态信息，高保真前需再降噪。 |
| UI-B3 | Settings 二级导航和外部能力管理 shell | 完成低保真 | 外部能力、分析资源、模型与引擎、开发者诊断已覆盖；账户/订阅、本地项目与存储尚未作为完整 target 二级页展开。 |
| UI-B4 | LabTools IA shell | 完成低保真 | 三入口和五类实验模块存在；ImageJ/Fiji 指向 Settings；没有库存、云端协作、局域网共享和真实计算逻辑。 |
| UI-B5 | Bioinformatics target IA shell | 完成壳层收束 | 顶部 target IA shell 有 8 个 disabled nav items；正式分析执行器、假结果、假图、report-ready 未启用。旧 Bio workflow pages 仍在 stack 中，后续需决定隐藏、迁移或保留为 Developer Diagnostics。 |
| UI-B6 | Meta Analysis target IA shell | 完成壳层收束 | 10 类 active Meta 类型展示，Network Meta 不在 active types；仍保留 mainline 3 页 shell contract，需在后续 Meta runtime 校准时决定是否替换。 |
| UI-B7 | Result / Report / Export shared semantics | 完成共享壳层 | 空状态、report draft boundary、export gating 和 disclaimer 存在；尚未成为所有历史 Bio/Meta 报告页面的唯一实现。 |
| UI-B8 | 资源替换/新增 after brand freeze | 部分完成：audit/inventory only | 按用户本轮范围，只完成资源 inventory 和 placeholder 策略；没有替换 Logo、module icon、status icon、App icon 或 desktop icon。应记录为 `UI-B8a inventory`，不是完整 UI-B8 resource replacement。 |
| UI-B9 | i18n key boundaries | 部分完成：UI-B9a | 关键 key registry 和枚举已落地；未做全量翻译、语言切换、报告模板多语言化或 locale tests。 |
| UI-B10 | packaging / desktop entry | 未开始 | 不应开始，直到 UI shell/resources/i18n 边界稳定且用户明确授权。 |

## 5. 计划与现实的偏差

| topic | observed_drift | severity | recommended_resolution |
|---|---|---|---|
| Stage Index 当前阶段 | `docs/ui/UI_Rebuild_Stage_Index_20260520.md` 仍写 `Current stage: UI-B0`。 | medium | 下一个文档治理阶段更新为当前完成到 UI-B8a + UI-B9a，UI-B10 未开始。 |
| MasterPlan 当前阶段 | `docs/ui/UI_Rebuild_MasterPlan_20260520.md` 仍写 `Current phase: UI-B0`。 | medium | 保留作为 UI-B0 完成声明也可以，但需要新增“current implementation checkpoint”避免误读。 |
| UI-B8 名称 | A4 v1 写 `Replace/add resources after brand freeze`，实际执行为资源清单与占位策略审计。 | high | 将当前成果命名为 `UI-B8a Resource Inventory / Placeholder Strategy`；正式资源替换另设 `UI-B8b` 或延后到高保真阶段。 |
| App icon / desktop icon | 当前资源 inventory 明确延后 UI-B10，但 A4 表中 UI-B8 仍含 App icon。 | high | App icon、Finder icon、Info.plist icon binding 全部归 UI-B10，不放入 UI-B8 replacement。 |
| UI-B9 范围 | `b494c51` 已做 semantic key registry，但不是完整 UI-B9。 | medium | 标记为 `UI-B9a critical semantic keys`；完整 UI-B9 仍需 key adoption, test migration, language switch strategy。 |
| Settings IA | 当前二级页为通用偏好、外部能力、分析资源、模型与引擎、开发者诊断；MasterPlan 还有账户与订阅、本地项目与存储。 | medium | 维持当前低保真；高保真前补齐或明确隐藏账户/订阅和存储页。 |
| Bioinformatics IA | target shell 有 8 个 items；MasterPlan 描述为 7 main pages + 2 auxiliary。 | medium | 明确 `settings_resources` 是辅助页，`Project Logs & Technical Details` 尚未作为 target shell item 出现。 |
| Legacy Bio pages | `BioinformaticsWorkspaceWidget` 仍实例化 acquisition/recognition/readiness/standardized assets/workflow status 等旧 pages。 | medium | 后续 UI-B5.1 决定迁移到 target pages、开发者诊断或隐藏。不要让旧页面绕过 target shell 状态。 |
| Meta runtime contract | Target IA shell 和旧 mainline 3 页 contract 并存。 | low-medium | 当前可接受；后续 Meta runtime calibration 决定是否替换旧 3 页为 target flow shell。 |
| Resource visuals | 缺 LabTools icon、status icons、empty states、report/export icons 等。 | high | 继续 placeholder；不要在未冻结品牌和资源 owner 前替换 active assets。 |

## 6. 当前可视 UI 状态

| area | current_visible_state | calibration |
|---|---|---|
| Welcome | `萤火虫 / Firefly` 文本主品牌，隐藏 credential flow，使用现有 App/Login icon placeholder。 | 符合低保真；不是最终品牌视觉。 |
| Dashboard | 三模块卡片：Bioinformatics、Meta Analysis、LabTools；LabTools 使用 workspace fallback icon。 | 符合 UI-B2/B4；缺正式 LabTools icon。 |
| Sidebar | Dashboard、Bioinformatics、Meta Analysis、LabTools、Settings、Test Feedback、About。 | 符合 target IA。 |
| Settings | 二级导航、资源状态卡、detect-first 按钮、禁用 install/cloud 按钮、开发者诊断折叠。 | 符合 UI-B3；仍是低保真。 |
| LabTools | 三入口和五类实验模块；planned/testing/shell-only 状态可见。 | 符合 UI-B4；不含真实计算。 |
| Bioinformatics | target IA shell 可见，但旧 workflow stack 仍存在。 | 壳层边界符合 UI-B5；旧页面迁移是后续校准点。 |
| Meta Analysis | target IA shell + 10 active types；Network Meta planned only。 | 符合 UI-B6；仍非生产 workflow。 |
| Result / Report / Export | shared components 有 draft/testing/report-ready future 语义与 export gating。 | 符合 UI-B7；尚未全量替换历史报告页。 |
| Resources | inventory 已建立，active 图标未替换。 | 符合用户要求；UI-B8 replacement 未开始。 |
| Packaging | 未打包，未运行 packaged app，未覆盖 desktop entry。 | 符合阶段边界。 |

## 7. 当前测试校准

已执行：

| command | result |
|---|---|
| `python3 -m app.main --smoke-test` | passed; `git_head=c901a21`, `workspace_entries=3`, `pyside6_available=True`. |
| `python3 -m pytest -q tests/ui tests/shared/test_semantic_keys.py tests/shared/test_result_report_export_shell.py` | passed; `167 passed in 17.78s`. |

测试覆盖现状：

| stage | focused_tests_observed |
|---|---|
| UI-B1 | `tests/ui/test_ui_style_tokens.py`, `tests/ui/test_ui_primitives.py`, `tests/ui/test_app_theme.py`. |
| UI-B2 | `tests/ui/test_login_page.py`, `tests/ui/test_module_selection.py`, `tests/ui/test_sidebar.py`. |
| UI-B3 | `tests/ui/test_settings_shell.py`. |
| UI-B4 | `tests/ui/test_labtools_shell.py`. |
| UI-B5 | `tests/ui/test_bioinformatics_ia_shell.py`. |
| UI-B6 | `tests/ui/test_meta_analysis_ia_shell.py`. |
| UI-B7 | `tests/ui/test_result_report_export_shell.py`, `tests/shared/test_result_report_export_shell.py`. |
| UI-B8a | `tests/ui/test_app_identity.py` covers current icon registry; inventory itself is documented but not machine-tested. |
| UI-B9a | `tests/shared/test_semantic_keys.py`. |

## 8. Next Stage Recommendation

Recommended immediate next step is not UI-B10.

| priority | stage | reason |
|---|---|---|
| P0 | UI-A4.2 / Stage Index checkpoint update | Current stage docs still say UI-B0. Update or supersede Stage Index so future work does not restart from stale stage labels. |
| P0 | UI-B5.1 Bioinformatics legacy page routing calibration | Old Bio workflow pages still exist under target IA shell. Decide what is visible, hidden, or developer-diagnostic. |
| P1 | UI-B8b resource design decision, not asset replacement | Freeze resource taxonomy and ownership first; continue placeholder until formal design exists. |
| P1 | UI-B9b key adoption/test migration | Expand semantic keys into nav/module/status surfaces and reduce fragile literal assertions. |
| P2 | UI-B10 packaging only after explicit authorization | App icon/desktop icon/Info.plist/LaunchServices are packaging concerns and should remain last. |

## 9. Audit Conclusion

Current implementation is calibrated as:

```text
Completed:
UI-B0, UI-B1, UI-B2, UI-B3, UI-B4, UI-B5 shell, UI-B6 shell, UI-B7 shell

Partial:
UI-B8a resource inventory / placeholder strategy
UI-B9a critical semantic keys

Not started:
UI-B8b formal resource replacement
UI-B9 full i18n adoption / language switch
UI-B10 packaging and desktop entry
```

The main risk is not test failure; the current focused tests pass. The main risk is stage-label drift: documents still describe the project as UI-B0 while the runtime has already advanced through multiple low-fidelity shell stages. The next governance step should freeze this checkpoint before additional implementation or packaging work.

## 10. Command Log

| command | result |
|---|---|
| `git status --short` | clean before UI-A4.1 edits. |
| `git log --oneline -12` | confirmed UI-B0 through UI-B8a/UI-B9a commit chain. |
| `rg --files docs/ui tests/ui app/shell app/shared app/meta_analysis app/bioinformatics \| sort` | read current docs, UI code, shared code and tests inventory. |
| `sed -n '90,170p' docs/ui/UI_A4_rebuild_execution_plan_audit_20260520.md` | read UI-B0 to UI-B10 stage definitions and test strategy. |
| `sed -n '1,260p' docs/ui/UI_Rebuild_Stage_Index_20260520.md` | found stale `Current stage: UI-B0`. |
| `sed -n '1,340p' docs/ui/UI_Rebuild_MasterPlan_20260520.md` | found stale `Current phase: UI-B0` and target IA rules. |
| `python3 -m app.main --smoke-test` | passed. |
| `python3 -m pytest -q tests/ui tests/shared/test_semantic_keys.py tests/shared/test_result_report_export_shell.py` | passed; `167 passed in 17.78s`. |

## 11. Verification

Completed verification:

| command | result |
|---|---|
| `git diff --cached --check` | passed, no whitespace errors. |
| `git status --short` | only `docs/ui/UI_A4_1_current_rebuild_stage_calibration_audit_20260520.md` is staged. |
