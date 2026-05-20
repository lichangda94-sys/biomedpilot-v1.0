# UI-B8 Resource Inventory and Placeholder Strategy Audit

审计日期：2026-05-20

本阶段目标：在不替换 active 图标、不修改业务代码、不打包、不覆盖桌面入口的前提下，建立资源清单和占位策略，明确缺失资源、继续 placeholder 的资源、需要正式设计的资源、当前不能替换的资源，并把 App icon 与桌面图标处理明确延后到 UI-B10。

## 1. 审计范围

读取和对照的范围：

| scope | result |
|---|---|
| `app/app_identity.py` | 当前 active 图标槽位 registry、loader、状态汇总来源。 |
| `assets/icons/**` | 当前 active 图标资源目录。 |
| `assets/images/**` | 当前只有 `.gitkeep`，无正式图片、插图或空状态图。 |
| `app/shell/**` | Welcome、Dashboard、Sidebar、Settings、LabTools shell、About、Test Feedback 的当前资源使用。 |
| `app/shared/result_report_export_shell.py` | Result / Report / Export 壳层目前是文本、状态 chip、按钮，无图标资源。 |
| `scripts/package_app.py` | 打包脚本静态审计；未运行打包。 |
| `dist/BioMedPilot.app/Contents/Info.plist` | 仅静态读取，未运行 packaged app。 |
| `docs/ui/UI_A2_visual_brand_resource_audit_20260520.md` | 作为视觉/品牌/资源缺口基线。 |
| `docs/ui/UI_A4_rebuild_execution_plan_audit_20260520.md`、`docs/ui/UI_Rebuild_MasterPlan_20260520.md` | 作为 UI-B8 / UI-B10 阶段边界依据。 |

新增 inventory：

`docs/ui/resource_inventory/UI_B8_resource_inventory_20260520.csv`

## 2. 本阶段未修改业务代码声明

本阶段只新增文档和资源 inventory：

| path | purpose |
|---|---|
| `docs/ui/UI_B8_resource_inventory_placeholder_strategy_audit_20260520.md` | UI-B8 资源清单与占位策略审计报告。 |
| `docs/ui/resource_inventory/UI_B8_resource_inventory_20260520.csv` | 资源 slot / 缺失资源 / placeholder / 替换边界 inventory。 |

未修改：

- `app/**`
- `tests/**`
- `assets/**`
- `scripts/package_app.py`
- `dist/**`
- 桌面 `.app` 入口

未替换 Logo、图标、图片资源；未删除旧资源；未运行 packaged app；未重新打包；未覆盖桌面入口。

## 3. 当前 Active 资源状态

`app.app_identity.icon_asset_summary()` 当前汇总：

| metric | count |
|---|---:|
| total icon slots | 45 |
| generated | 35 |
| connected | 33 |
| generated waiting | 2 |
| pending | 10 |

当前已生成并接入的主资源族：

| resource_family | active_paths | current_usage | B8_decision |
|---|---|---|---|
| App icon | `assets/icons/app/biomedpilot_app_icon.png`, `.icns`, `.iconset/*` | QApplication、MainWindow、Welcome 图标 fallback | 保持现状；不替换；UI-B10 再处理 App icon / desktop icon。 |
| Bioinformatics module icon | `assets/icons/modules/bioinformatics_module_icon.png` | Dashboard Bioinformatics 模块卡片 | 继续低保真复用；后续正式模块图标系统再重绘。 |
| Meta Analysis module icon | `assets/icons/modules/meta_analysis_module_icon.png` | Dashboard Meta 模块卡片 | 继续低保真复用；需避免暗示生产级系统综述能力。 |
| UI-01 login icon set | `assets/icons/ui01_login/*.png` | Welcome / 旧登录页按钮与账号占位 | 继续 legacy placeholder；不作为新 Welcome 高保真标准。 |
| UI-02 module selection icon set | `assets/icons/ui02_module_selection/*.png` | Dashboard header、support panel、workspace fallback | 继续低保真复用；LabTools 当前使用 workspace fallback。 |
| UI-03 Bio project home icons | `assets/icons/ui03_project_home/*.png` | Bioinformatics 项目首页旧实现 | 继续低保真复用；高保真前重新映射到目标 Bio IA。 |

当前 pending 的 registered slots：

| resource_id | path | current_state | B8_decision |
|---|---|---|---|
| `ui04.data_source` | `assets/icons/workflow/ui04_data_source.png` | 待生成 | 不现在补旧 UI04 图；等目标 Bio 页面图标映射确认。 |
| `ui05.acquisition` | `assets/icons/workflow/ui05_acquisition_status.png` | 待生成 | 不现在补旧 UI05 图；可能并入 Data Source。 |
| `ui06.recognition` | `assets/icons/workflow/ui06_recognition.png` | 待生成 | 不现在补旧图；目标名为 Data Check & Preparation。 |
| `ui07.readiness` | `assets/icons/workflow/ui07_readiness.png` | 待生成 | 保持 pending；不直接沿用旧 UI 编号设计。 |
| `ui08.standardization` | `assets/icons/workflow/ui08_standardization.png` | 待生成 | 保持 pending；等待 resolver-first 目标页稳定。 |
| `ui09.workflow` | `assets/icons/workflow/ui09_workflow.png` | 待生成 | 保持 pending；不恢复旧 workflow control 作为目标入口。 |
| `ui10.tasks` | `assets/icons/workflow/ui10_tasks.png` | 待生成 | 保持 pending；分析任务图标需遵守 gated/preflight 语义。 |
| `ui11.results` | `assets/icons/workflow/ui11_results.png` | 待生成 | 保持 pending；应与共享 Result shell 统一。 |
| `ui12.report` | `assets/icons/workflow/ui12_report.png` | 待生成 | 保持 pending；应与共享 Report shell 统一。 |
| `ui13.settings_ai` | `assets/icons/workflow/ui13_settings_ai.png` | 待生成 | 保持 pending；AI/模型资源先归 Settings。 |

## 4. 缺失资源清单

| missing_resource | affected_area | current_placeholder | priority | required_before |
|---|---|---|---|---|
| Firefly / 萤火虫正式 Logo lockup | Welcome、About、Dashboard | 文本品牌 + 当前 App icon | high | 高保真 Welcome/About |
| Welcome 主视觉 | Welcome | 低保真文本和卡片 | high | 高保真 Welcome |
| About 品牌图像 | About | 文字列表卡片 | medium | 高保真 About |
| LabTools module icon | Dashboard、Sidebar 未来图标化 | UI-02 workspace fallback | high | 三模块高保真 Dashboard |
| LabTools 三入口图标 | 通用计算器、试剂制备、实验模块 | 文本卡片 + status chip | high | LabTools 高保真 shell |
| LabTools 五类实验图标 | 细胞、蛋白、核酸、免疫与吸光度、免疫组化 | 文本卡片 + status chip | high | LabTools 高保真模块页 |
| Settings 外部能力图标 | Python、R、ImageJ/Fiji、外部图像引擎 | 文本卡片 + status chip | high | Settings 高保真资源管理 |
| Settings 分析资源图标 | GO、KEGG、MSigDB、resolver/input package、report templates | 文本卡片 + status chip | high | Settings 高保真资源管理 |
| Settings 模型/引擎图标 | 本地 AI、云端模型配置 | 文本卡片 + status chip | medium | 模型安全策略确认后 |
| 状态图标系统 | testing、planned、shell-only、blocked、preflight、available、not_configured、failed、draft | 文本 + 颜色 chip + `iconHint` | high | 高保真状态系统 |
| 空状态插图 | Result preview、Dashboard empty projects、Bio/Meta/LabTools 空页面 | 文本 empty card | medium | 高保真空状态 |
| Result / Report / Export 图标 | Markdown、HTML、DOCX、CSV、XLSX、report draft、export gated | 文本按钮 | high | 高保真 report/export shell |
| Bio target page icons | Bio 7 页 + 2 辅助页 | 旧 UI03 icons 或纯文本 | medium | Bio 高保真页面 |
| Meta type icons | 10 种 active Meta 类型 | 文本 type cards | medium | Meta 高保真 type-first page |
| App icon / Finder desktop icon final set | macOS App、dist、desktop entry | 当前 BioMedPilot icon | high but deferred | UI-B10 |

## 5. 继续 Placeholder 的资源

| placeholder | keep_until | reason |
|---|---|---|
| 当前 App icon PNG/ICNS/iconset | UI-B10 | App icon 涉及 bundle、Finder、LaunchServices、桌面入口，不在 B8 替换。 |
| Bioinformatics / Meta module icons | 模块图标系统正式设计完成 | 已被 active loader 和 tests 引用；低保真 Dashboard 可继续使用。 |
| LabTools workspace fallback icon | LabTools 正式 module icon 设计完成 | 当前没有正式 LabTools 图标；fallback 不冒充最终品牌。 |
| UI-01 login icon set | Welcome 资源替换方案确认 | 旧登录资源仍被 Welcome/登录壳使用；不能在审计阶段删除或替换。 |
| UI-02 Dashboard icon set | Dashboard 资源替换方案确认 | 当前 Dashboard support panel、状态说明、Settings 入口依赖。 |
| UI-03 Bio project icons | Bio target IA 高保真映射确认 | 当前 Bio project home 和 tests 依赖；不能因为目标 IA 变化直接删除。 |
| Text-only Settings capability cards | Settings resource icon set 完成 | detect-first UI 可以低保真运行；图标缺失不阻塞壳层。 |
| Text/color status chips | 状态图标系统完成 | UI-B1 已有 status token；B8 不引入临时图形。 |
| Text-only result/report/export buttons | Report/export icon set 和导出策略完成 | UI-B7 只允许 testing summary / draft，不应增加“正式输出”视觉暗示。 |
| Text-only Meta type cards | Meta 类型视觉 taxonomy 完成 | 防止图标暗示 Network Meta 或生产级能力。 |

## 6. 需要正式设计的资源

正式设计必须先有 owner、风格规则和替换窗口，不能直接从 archive 或生成图替换 active 资源。

| resource_group | formal_design_input_needed | suggested_owner_stage |
|---|---|---|
| Brand logo lockup | Firefly / BioMedPilot / 医研智析层级、横版/方版/小尺寸规则 | UI-B8 design follow-up |
| App icon | macOS iconset、PNG/ICNS、bundle display、Finder 显示策略 | UI-B10 |
| Module icons | Bioinformatics、Meta Analysis、LabTools、Settings 的统一风格和尺寸 | UI-B8 design follow-up |
| LabTools icons | 三入口、五类实验、实验专属术语和 ImageJ/Fiji Settings 归属 | UI-B8 design follow-up |
| Settings resource icons | 外部能力、模型、分析资源、检测状态的统一图标语义 | UI-B8 design follow-up |
| Status icons | `feature.status.*`、`resource.status.*`、`analysis.status.*`、`report.status.*` 的 icon mapping | UI-B8 design follow-up |
| Empty state illustrations | 空结果、空项目、缺资源、blocked/preflight 的插图规则 | UI-B8 design follow-up |
| Report/export icons | format icons、gated export、report draft、future report-ready 的视觉边界 | UI-B8 design follow-up |
| Bio target page icons | 目标 7 页 + 2 辅助页，不沿用旧 UI04-UI13 编号作为最终视觉标准 | UI-B8 design follow-up |
| Meta type icons | 10 种 active Meta 类型，Network Meta 只 planned，不给正式入口图标 | UI-B8 design follow-up |

## 7. 当前不能替换的资源

| resource | cannot_replace_now_reason | required_gate |
|---|---|---|
| `assets/icons/app/biomedpilot_app_icon.png` | 被 QApplication、MainWindow、Welcome 使用；品牌和包装策略未冻结。 | UI-B10 packaging/icon gate。 |
| `assets/icons/app/biomedpilot_app_icon.icns` | 关系到 macOS app icon，但当前 plist 未绑定；不能半替换。 | UI-B10 写 plist、复制资源、LaunchServices 验证。 |
| `assets/icons/app/biomedpilot_app_icon.iconset/*` | App icon source set 必须整体一致重出。 | UI-B10。 |
| `assets/icons/modules/bioinformatics_module_icon.png` | active loader 和 tests 依赖。 | 模块图标系统和 focused tests 同步更新。 |
| `assets/icons/modules/meta_analysis_module_icon.png` | active loader 和 tests 依赖。 | 模块图标系统和 focused tests 同步更新。 |
| `assets/icons/ui01_login/*.png` | Welcome/旧登录仍引用，删除或替换会破坏 UI tests。 | Welcome 资源设计和迁移测试。 |
| `assets/icons/ui02_module_selection/*.png` | Dashboard/support panel/Settings icon/fallback 依赖。 | Dashboard icon map 更新和测试迁移。 |
| `assets/icons/ui03_project_home/*.png` | Bio project home 仍引用。 | Bio target IA 高保真替换计划。 |
| `dist/BioMedPilot.app/**` | dist 包是构建产物且不是当前 HEAD；B8 不打包。 | UI-B10。 |
| 桌面 `BioMedPilot.app` | 用户桌面入口不能在资源审计阶段覆盖。 | UI-B10 明确授权和 launch validation。 |
| `archive/legacy_sources/**` | 历史资源不是 active 设计标准。 | 单独 legacy resource migration audit。 |

## 8. App Icon 与桌面图标延后到 UI-B10

UI-B8 不处理 App icon 或桌面图标替换。原因：

- App icon 不只是图片替换，还涉及 `.icns`、`.iconset`、Info.plist、bundle resources、Finder/LaunchServices 缓存和桌面入口。
- `scripts/package_app.py` 当前没有写入 `CFBundleIconFile` 或 `CFBundleIconName`。
- `dist/BioMedPilot.app/Contents/Info.plist` 当前 `BioMedPilotGitHead` 为 `db4e27b`，不是当前 HEAD，不能作为当前资源结果。
- 桌面入口属于用户可见运行入口，不能在 B8 资源清单阶段覆盖。

UI-B10 应包括：

| UI-B10_item | required_check |
|---|---|
| App icon final art | PNG/ICNS/iconset 尺寸一致性。 |
| Info.plist icon binding | `CFBundleIconFile` 或 `CFBundleIconName` 明确写入。 |
| Bundle resource copy | `.icns` 复制到 `Contents/Resources`。 |
| Desktop entry update | 单独授权后刷新，不在 UI-B8 自动覆盖。 |
| Launch validation | direct smoke 加 Finder/LaunchServices-style gate。 |
| Tests | package metadata tests + focused App icon tests。 |

## 9. High Risk Issues

| risk | severity | mitigation |
|---|---|---|
| 把 workspace fallback 当成 LabTools 正式图标 | high | inventory 标记为 fallback；LabTools 正式图标单独设计。 |
| 在品牌未冻结时替换 App icon | high | 明确延后 UI-B10。 |
| 用 archive legacy 图标作为 final | high | archive 只能参考，不能直接进入 active。 |
| 给 Result/Report/Export 加强视觉后暗示正式 report-ready | high | 图标和文案必须绑定 gated/testing/draft 语义。 |
| 给 Meta 类型图标时误开放 Network Meta | high | Network Meta 只 planned，不给正式可运行视觉。 |
| 给 Bio workflow 补旧 UI04-UI13 图标导致目标 IA 回退 | medium | 先按目标 7 页 + 2 辅助页重新映射。 |
| 替换 active icons 但未更新 tests | medium | 任何后续替换必须同步 focused tests。 |

## 10. Recommended Next Steps

| next | recommendation |
|---|---|
| UI-B8 design follow-up | 冻结 resource taxonomy：brand、module、settings resource、status、empty state、report/export、Bio page、Meta type、LabTools category。 |
| UI-B9 continuation | 保持语义 key 与状态枚举作为图标命名依据，不让图标承担功能状态。 |
| UI-B10 | 单独处理 App icon、desktop icon、plist icon binding、dist/desktop entry、LaunchServices 验证。 |
| Tests | B8 本阶段只做文档校验；后续资源替换阶段需要 focused UI/resource tests。 |

## 11. Commands and Results

| command | result |
|---|---|
| `git status --short` | clean before B8 edits. |
| `git rev-parse --short HEAD` | `c802964`. |
| `rg --files docs/ui \| sort` | Found A1/A2/A3/A4/MasterPlan/Style/I18N docs and target drafts. |
| `sed -n '1,260p' app/app_identity.py` | Read icon registry and loader paths. |
| `find assets resources icons images branding packaging dist -maxdepth 4 -type f 2>/dev/null \| sort` | Found active `assets/icons/**`, `assets/images/.gitkeep`, stale `dist/BioMedPilot.app`; no root `resources/icons/images/branding/packaging` dirs. |
| `python3 - <<'PY' ... icon_asset_summary() ... PY` | `total=45`, `generated=35`, `connected=33`, `generated_waiting=2`, `pending=10`. |
| `sed -n '1,240p' scripts/package_app.py` | Static read; packaging script does not write plist icon binding. |
| `plutil -p dist/BioMedPilot.app/Contents/Info.plist` | Static read; no icon key; stale git head `db4e27b`. |

## 12. Verification

Completed verification:

| command | result |
|---|---|
| `git diff --check` | passed, no whitespace errors. |
| `git status --short` | only `docs/ui/UI_B8_resource_inventory_placeholder_strategy_audit_20260520.md` and `docs/ui/resource_inventory/UI_B8_resource_inventory_20260520.csv` are new before staging. |

Full tests are not required for UI-B8 because only documentation and inventory files are added.
