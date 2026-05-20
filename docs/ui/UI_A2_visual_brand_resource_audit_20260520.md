# UI-A2 Visual System, Brand and Resource Audit

审计日期：2026-05-20

本阶段目标：基于 UI-A1 审计结果，审计当前项目已有视觉系统、品牌标识、Logo、App icon、模块图标、状态图标、空状态插图、颜色、字体、布局、按钮、卡片、表格、状态标签、打包图标和桌面入口资源引用，为后续 `UI_Rebuild_MasterPlan`、`Visual Style Guide` 和高保真 UI 制作做准备。

本阶段结论：当前项目已有一套早期 light theme、局部 design token、app/module/UI01/UI02/UI03 图标资源和测试覆盖，但仍是“BioMedPilot / 医研智析 + 旧登录页 + 两模块 Dashboard”的资源体系。UI-A1 目标中的 `萤火虫 / Firefly` 主品牌、Welcome/About 主视觉、LabTools 图标、Settings 资源图标、状态图标、空状态插图、报告/导出图标、外部引擎/模型/分析资源图标均未进入 active 资源目录。高保真 UI 不应直接开始，建议先建立 Visual Style Guide。

## 1. 审计范围

### 1.1 输入文档

| 输入 | 状态 |
|---|---|
| `docs/ui/UI_A1_target_markdown_architecture_audit_20260520.md` | 已读取，作为目标页面和视觉缺口基线 |
| `docs/ui/target_design_drafts/**` | 已读取索引和草案归档，作为目标品牌/页面输入 |
| `docs/ui/UI_Cross_Branch_Runtime_IA_Audit_20260519.md` | 已读取，作为 LabTools 和旧 runtime 对照 |
| `docs/bioinformatics/stage_B8_0_1_analysis_ui_prebuild_supplemental_audit_20260520.md` | 已读取，作为 Bioinformatics 分析按钮和报告边界对照 |
| `app/**` | 已扫描当前 UI、品牌、图标、样式、状态标签 |
| `assets/**` | 已扫描 active icon/image 资源 |
| `archive/legacy_sources/model9/**` | 已扫描 legacy 图标和 launcher，仅作为历史资源风险 |
| `scripts/package_app.py`、`dist/BioMedPilot.app/Contents/Info.plist`、桌面 `BioMedPilot.app/Contents/Info.plist` | 已静态读取，未打包、未运行 |
| `tests/ui/**`、`tests/test_package_app.py` | 已读取视觉/资源/打包测试覆盖 |

### 1.2 资源目录现状

| 路径 | 状态 |
|---|---|
| `assets/icons/` | active 图标资源主目录 |
| `assets/images/` | 仅 `.gitkeep`，暂无 active 图片/插图 |
| `resources/`、`icons/`、`images/`、`branding/` | 仓库根部不存在这些独立目录 |
| `archive/legacy_sources/model9/assets/**` | 历史资源，包含旧 Meta、空状态、状态、toolbar、sidebar 图标 |
| `dist/BioMedPilot.app/` | 已存在旧构建产物，本阶段只静态审计 |
| `/Users/changdali/Desktop/BioMedPilot.app` | 已存在桌面包，本阶段只静态读取 Info.plist |

## 2. 本阶段未修改业务代码声明

本阶段只新增本文档：

`docs/ui/UI_A2_visual_brand_resource_audit_20260520.md`

未修改：

- `app/**`
- `tests/**`
- `assets/**`
- `archive/**`
- `scripts/package_app.py`
- `dist/**`
- `/Users/changdali/Desktop/BioMedPilot.app`

未替换 Logo、图标、图片，未删除旧资源，未运行 packaged app，未重新打包，未覆盖桌面入口，未推进 Bioinformatics / Meta Analysis / LabTools 功能开发。

## 3. 品牌关系审计

### 3.1 品牌与模块名使用表

| brand_text | location | current_usage | risk | suggested_resolution |
|---|---|---|---|---|
| `BioMedPilot / 医研智析` | `app/app_identity.py`, `app/shell/login.py`, `app/shell/module_selection.py`, `app/shell/dashboard.py`, `app/shell/topbar.py`, `scripts/package_app.py`, `dist/**/Info.plist`, tests | 当前 runtime、窗口标题、Dashboard、打包显示名、测试断言的主显示名 | 与 UI-A1 目标的 `萤火虫 / Firefly` 主品牌不一致 | UI-A2 先冻结主品牌：建议 Welcome/About/Dashboard 第一信号为 `萤火虫 / Firefly`，`BioMedPilot / 医研智析` 作为产品线/副品牌；打包名称另行决定 |
| `BioMedPilot` | `scripts/package_app.py`, `CFBundleName`, `CFBundleExecutable`, `QApplication.applicationName`, Login 文案、报告标题、测试反馈模板 | 当前 bundle name、可执行名、报告/反馈默认名 | 如果 UI 显示名切到 Firefly，但 bundle/executable 仍是 BioMedPilot，会出现用户界面与 Finder/报告名称割裂 | 允许内部 bundle/executable 暂保留 `BioMedPilot`，但 Visual Style Guide 必须定义 visible brand、technical bundle name、report title 的映射 |
| `医研智析` | UI 标题、Info.plist display name、Login 中文副名 | 当前中文副品牌 | 与 `萤火虫` 的层级未定义 | 冻结为副标题或产品说明，不与 `萤火虫` 并列争主品牌 |
| `萤火虫` | UI-A1、target_design_drafts、UI Freeze 文档 | 目标主品牌文案，尚未进入 active runtime | 高保真 Welcome/About 无法统一 | Visual Style Guide 必须定义中文主品牌、语气、Logo 关系 |
| `Firefly` | UI-A1、target_design_drafts | 目标英文主品牌，尚未进入 active runtime | 英文版与 bundle/report 名称不一致 | 定义英文 visible brand；避免直接替换 bundle name 前造成打包风险 |
| `Bioinformatics / 生信分析` | Sidebar、Dashboard、Bio project、tests、报告 | active 一级模块 | 英文出现 `Bioinformatics Analyze Module` 语法不自然；目标页命名尚未统一 | 建议统一为 `Bioinformatics / 生信分析` 或 `Bioinformatics Analysis / 生信分析`，按钮短文案另定 |
| `Meta Analysis / Meta 分析` | Sidebar、Dashboard、Meta shell、docs/tests | active 一级模块 | 当前 UIShell shell-only，但目标草案是完整流程；视觉上可能过度正式 | 保留模块名，状态标签必须是 testing/shell |
| `LabTools / 实验工具` | UI-A1、LabTools 草案、跨分支审计 | 目标一级模块；当前 `dev/ui-shell` 不存在 | Dashboard/Sidebar 缺图标和 runtime，旧分支存在 `LabTools`/`实验工具` 混用 | 目标统一为 `LabTools / 实验工具`，active 资源需新增 LabTools module icon |
| `Labors` | 用户任务描述中提及；当前 active scan 未发现 runtime 使用 | 可能是历史/口误或旧命名 | 若进入文案会造成 LabTools 命名分叉 | 不作为目标名称；后续扫到应归并为 LabTools |

### 3.2 当前品牌冻结建议

| 位置 | 建议冻结 |
|---|---|
| Welcome H1 | `萤火虫 / Firefly` |
| Welcome subtitle | `BioMedPilot / 医研智析`，再接 Developer Preview / 本地测试版 |
| About 标题 | `关于萤火虫 / About Firefly` |
| Dashboard 顶部 | `萤火虫工作台` 或 `Firefly Workbench`，二级文案保留 `BioMedPilot / 医研智析` |
| App menu / bundle / executable | 暂不在 UI-A2 修改；建议后续单独决定是否从 `BioMedPilot` 改名 |
| 报告标题 | 当前可保留 `BioMedPilot 生信项目报告草稿`，但正式报告模板应有品牌变量 |

### 3.3 命名一致性风险

- UI 文案和测试大量断言 `BioMedPilot / 医研智析`，一旦进入 Firefly 重建，需要同步测试和包装策略。
- `CFBundleDisplayName` 是 `BioMedPilot / 医研智析`，`CFBundleName` 和 executable 是 `BioMedPilot`；当前不算错误，但与目标主品牌存在差异。
- 桌面 `/Users/changdali/Desktop/BioMedPilot.app` 仍是旧 GitHead `21e1a0f`，`dist/BioMedPilot.app` 是 `db4e27b`，均不是当前 HEAD `30d4f02`。
- 报告、反馈模板、user-agent 仍使用 BioMedPilot，后续需要区分“外部可见品牌”和“技术标识”。

## 4. Logo / App icon / 图片资源审计

### 4.1 active 资源表

| resource_path | resource_type | format | size_if_detectable | used_by | branch_or_context | status | suggested_action |
|---|---|---|---|---|---|---|---|
| `assets/icons/app/biomedpilot_app_icon.png` | App icon / window icon | PNG | 1254x1254 | `load_app_icon()`, Login brand panel, MainWindow, QApplication | active UIShell | current / conflict | 可继续临时使用；UI-A2 需确认是否代表 Firefly 主品牌 |
| `assets/icons/app/biomedpilot_app_icon.icns` | macOS app icon source | ICNS | ICNS bundle | `load_app_icon()` fallback；未被 Info.plist 指定 | active UIShell | current but packaging gap | 打包脚本需后续显式写 `CFBundleIconFile` 或 `CFBundleIconName` |
| `assets/icons/app/biomedpilot_app_icon.iconset/*` | App icon source set | PNG | 16 到 1024 | 资源源文件 | active UIShell | current | 保留；后续若改品牌需整体重出 |
| `assets/icons/modules/bioinformatics_module_icon.png` | Bioinformatics module icon | PNG | 1254x1254 | `load_module_icon("bioinformatics")`, Dashboard module card | active UIShell | current | 需按新三模块图标体系复审风格 |
| `assets/icons/modules/meta_analysis_module_icon.png` | Meta Analysis module icon | PNG | 1254x1254 | `load_module_icon("meta_analysis")`, Dashboard module card | active UIShell | current | 需按 testing/shell 状态调整视觉 |
| `assets/icons/modules/*_512.png` | module icon variants | PNG | 512x512 | 未被 active loader 直接引用 | active UIShell | orphan-ish / source variant | 保留为导出尺寸；后续纳入资源清单 |
| `assets/icons/ui01_login/*.png` | Login page icons | PNG | 260x260 | `BioMedPilotLoginWidget` 用户名/密码/注册/VIP/License/订阅等 | active old Login | legacy/conflict | Welcome 重建后大部分不应进入第一屏；移动到 legacy 或按新 Welcome 重绘 |
| `assets/icons/ui01_login/*_128.png` | Login icon 128 variants | PNG | 128x128 | tests only indirectly by existence; loader不使用 | active old Login | orphan/source variant | 保留但不要作为新资源标准 |
| `assets/icons/ui01_login/ui01_login_icon_sheet.png` | icon contact sheet | PNG | 1586x992 | tests check existence | active old Login | documentation/source | 可作为审计素材；新 Welcome 需要新 sheet |
| `assets/icons/ui02_module_selection/*.png` | Dashboard/support icons | PNG | 224x224 | Dashboard header/support panel/icons | active UIShell | current/partial | 缺 LabTools、About、Test Feedback、状态图标；需扩展 |
| `assets/icons/ui02_module_selection/*_128.png` | Dashboard 128 variants | PNG | 128x128 | 未被 active loader 直接引用 | active UIShell | orphan/source variant | 保留为导出尺寸 |
| `assets/icons/ui02_module_selection/ui02_module_selection_icon_sheet.png` | icon contact sheet | PNG | 1536x1024 | tests check existence | active UIShell | documentation/source | 后续重出三模块 Dashboard sheet |
| `assets/icons/ui03_project_home/*.png` | Bioinformatics project home icons | PNG | 250x250 | `BioinformaticsProjectHomeWidget` | active Bioinformatics | current | 可低保真复用；高保真需与新视觉系统重审 |
| `assets/icons/ui03_project_home/*_128.png` | UI03 128 variants | PNG | 128x128 | 未被 active loader 直接引用 | active Bioinformatics | orphan/source variant | 保留为导出尺寸 |
| `assets/icons/ui03_project_home/ui03_project_home_icon_sheet.png` | icon contact sheet | PNG | 1448x1086 | tests check existence | active Bioinformatics | documentation/source | 后续需要按目标 7 页重组 |
| `assets/images/.gitkeep` | image directory placeholder | text | n/a | 无 | active UIShell | missing images | Welcome/About/空状态/报告插图均缺 |
| `archive/legacy_sources/model9/assets/icons/empty_state_illustrations/*.png` | Empty state illustrations | PNG | not audited in detail | 无 active 引用 | legacy archive | legacy/orphan | 不要直接使用；可作为旧资源参考 |
| `archive/legacy_sources/model9/assets/icons/status_icons/*.png` | Status icons | PNG | not audited in detail | 无 active 引用 | legacy archive | legacy/orphan | 可参考语义，需按新 token 重绘/迁移 |
| `archive/legacy_sources/model9/assets/meta_icons/**` | Meta-specific icons | PNG/SVG/ICNS | mixed | 无 active 引用 | legacy archive | legacy/conflict | 当前 Meta target 需要类型前置图标，但应先审计风格后再迁移 |
| `app/bioinformatics/legacy/geo_tool/app/geo_tool_icon.svg` | Legacy GEO tool icon | SVG | vector | legacy GEO tool only | legacy path | legacy | 不进入新全局 UI |

### 4.2 缺失目标资源表

| target_resource | status | suggested_action |
|---|---|---|
| Firefly / 萤火虫主 Logo | missing | UI-A2/Visual Style Guide 先定义品牌符号，再生成 |
| Welcome 主视觉 | missing | 需要 Figma 或视觉方向后生成，不使用旧 login gradient/账号图标 |
| About 页图像 | missing | 需要品牌叙事和视觉风格 |
| LabTools module icon | missing | 三模块 Dashboard 必需 |
| Settings main icon set | partial | 只有 UI02 settings；缺 Settings 五子页图标 |
| Developer Diagnostics icon | missing | 需与测试反馈、日志、反馈包区分 |
| Status icons | missing in active assets | 旧 archive 有，但 active 无；需定义状态 token 后绘制 |
| Empty state illustrations | missing in active assets | archive 有旧图，不建议直接使用 |
| Report / Export icons | missing in active assets | archive 有 Meta export/reporting，active 无统一资源 |
| External engines / models / analysis resources icons | missing | Settings 资源页必须新增 |
| Bioinformatics target UI04-UI13 workflow icons | registered as required=False but files missing | 目标 7 页会重组，不建议按旧 UI04-UI13 逐个补旧图 |
| Meta Analysis type icons | missing | 10 类 Meta 类型如果进入高保真，需要统一图标或色标 |

## 5. 模块图标与状态图标审计

| item | current_state | risk | suggested_resolution |
|---|---|---|---|
| Bioinformatics icon | 有 active 1254/512 PNG，代码和测试覆盖 | 与未来 Firefly 视觉系统是否一致未知 | 暂可低保真复用，高保真前重审风格 |
| Meta Analysis icon | 有 active 1254/512 PNG，代码和测试覆盖 | 当前 UIShell 只是 shell-only，图标可能暗示完整能力 | 保留但状态标签必须明确 testing/shell |
| LabTools icon | active assets 缺失 | Dashboard 三模块无法视觉一致 | UI-A2 必须新增设计输入 |
| Settings icon | UI02 中有设置图标 | 只服务旧 Dashboard support panel，不覆盖 Settings 子页 | 为常规/账户/存储/资源/诊断建立子图标 |
| Developer Preview icon | UI02 中有 | 状态 token 未统一，和 FeatureAvailability 文本状态分离 | 建立状态标签视觉 token |
| 当前用户、版本、退出登录图标 | UI02 中有 | UI-A1 目标 Dashboard 不应强调账号/退出登录 | Welcome/Dashboard 重建时降级或移除 |
| Login register/forgot/VIP/license/subscription icons | UI01 中有 | UI-A1 明确不进入第一屏 | 归为 legacy，不作为 Welcome 目标资源 |
| Bio Project Home icons | UI03 中有 | 只覆盖旧 UI03 项目首页，不覆盖目标 7 页 | 目标页重组后重新映射 |
| Status icons | active 缺失，archive 有旧 `completed/locked/ready/running` 等 | 状态标签只能靠颜色/文字，且颜色不统一 | 先定义 Developer Preview/testing/planned/blocked/ready/error/success token，再决定图标 |

## 6. 视觉系统与 design token 现状

### 6.1 existing_ui_primitives

| primitive | current_location | current_content | coverage | audit_result |
|---|---|---|---|---|
| Light app theme | `app/ui_theme.py` | Fusion palette、浅色全局 stylesheet | tests/ui/test_app_theme.py | 存在，但和 `ui_style_tokens.py` 色值不完全一致 |
| Color tokens | `app/ui_style_tokens.py` `COLORS` | background/surface/border/text/muted/bio/meta/warning/success/danger | Login/Dashboard/Bio project | 有雏形，但缺状态完整语义和 Firefly 品牌色 |
| Spacing tokens | `SPACING` | xs/sm/md/lg/xl/xxl | 部分 UI | 有雏形，但页面仍有大量硬编码 margins |
| Radius tokens | `RADIUS` | sm=8, md=14, lg=20 | 部分 UI | 与目标“卡片 8px 或更少”可能冲突；需重审 |
| Font size tokens | `FONT_SIZE` | app_title/page_title/card_title/body/secondary/caption/hero | 部分 UI | 缺字体族、行高、字重、英文长度规则 |
| Control height tokens | `CONTROL_HEIGHT` | field/button/primary | 部分 UI | 有雏形，未形成完整组件规范 |
| Login stylesheet | `login_stylesheet()` | 旧登录页高视觉样式 | Login | 与 Welcome 目标冲突，应 legacy 化 |
| Module selection stylesheet | `module_selection_stylesheet()` | Dashboard/module card/support card | Dashboard | 可低保真复用，但缺三模块和 Firefly 目标 |
| Bioinformatics stylesheet | `bioinformatics_project_home_stylesheet()` | Bio project/workflow 页通用样式 | Bioinformatics | 覆盖较广，但硬编码状态颜色多 |
| Feature status enum | `app/shared/feature_status.py` | 已开放/测试中/待接入/暂未开放 | 状态文本 | 有语义模型，但未绑定视觉 token |
| Feature availability registry | `app/shared/feature_availability.py` | open/testing/placeholder/unavailable | 功能状态 | 有语义模型，但和 Settings 资源状态不统一 |
| Icon inventory | `app/app_identity.py` | IconAssetSlot/Status/Summary | app/module/UI01/UI02/UI03 | 有早期资源登记，但包含旧登录页与旧 UI04-UI13 |

### 6.2 missing_ui_primitives

| missing_primitive | impact | suggested_stage |
|---|---|---|
| Brand token set | 无法统一 Firefly/BioMedPilot/医研智析 | UI-A2 |
| Logo usage rules | App icon、Welcome、About、Dashboard 可能混用旧图 | UI-A2 |
| Module icon system | LabTools 缺图，三模块风格不统一 | UI-A2 |
| Status label visual tokens | testing/planned/blocked/developer preview/detecting/failed/available 分散 | UI-A2 |
| Empty state component | 目标页面大量空状态只能临时文字 | UI-A2 |
| Settings resource status component | 外部引擎、模型、分析资源状态无统一 UI | UI-A2/UI-A4 |
| Table/data grid component | Bioinformatics/Meta/LabTools 表格视觉可能分裂 | UI-A2 |
| Form/input component spec | QLineEdit/QComboBox/QPlainTextEdit 仅局部样式 | UI-A2 |
| Tabs/segmented controls | Settings 二级页、LabTools 实验模块缺规范 | UI-A2 |
| Collapsible developer diagnostics | 技术信息折叠组件未定义 | UI-A2/UI-A4 |
| Report/export component | 报告草稿、导出按钮、图表预览缺规范 | UI-A2/UI-A3 |
| Dark mode policy | 当前强制浅色，无暗色预留策略 | UI-A2 决策是否暂不支持 |

### 6.3 duplicate_or_inconsistent_styles

| location | inconsistency | risk | suggested_resolution |
|---|---|---|---|
| `app/ui_theme.py` vs `app/ui_style_tokens.py` | 两套浅色 palette：`#F8FAFC/#0F172A` 与 `#F5F7F9/#1F2933` | 全局窗口和页面级 stylesheet 色值不一致 | 合并为唯一 token source |
| `app/shell/sidebar.py` | 直接硬编码 sidebar 背景、border、按钮 hover | sidebar 不受 token 控制 | 将 sidebar 纳入 token/component |
| `app/shell/main_window.py` | 多个 `_list_card` / `_entry_card` 直接硬编码边框、圆角、标题字号 | Settings/testing/card 风格与 token 页不同 | 抽象 Card/Section primitive |
| `app/bioinformatics/pages/*.py` | 每页重复 `font-size: 20px`、card border、error color `#B42318` | 重复样式、错误色与 token danger 不一致 | 迁移到共享 page shell/button/status tokens |
| `app/meta_analysis/workspace.py` | 标题/heading inline stylesheet | Meta shell 与 Bio/Dashboard 视觉割裂 | 纳入 module workspace stylesheet |
| `app/shared/feature_status.py` 与 `Settings_External_Engines...` 草案 | 功能状态仅 4 种，Settings 资源状态十余种 | 状态标签语义不足 | 建立统一 StatusToken taxonomy |
| `RADIUS["lg"] = 20` | 当前 module/card 大圆角 | 与目标设计规则中“卡片 8px 或更少”存在冲突 | Visual Style Guide 重新定 radius |

## 7. 硬编码视觉参数清单

| file_path | symbol_or_line_hint | style_type | current_value | risk | suggested_token |
|---|---|---|---|---|---|
| `app/ui_theme.py` | `apply_light_app_theme` | colors | `#F8FAFC`, `#0F172A`, `#2563EB`, `#CBD5E1` | 与 `COLORS` 分裂 | `color.background`, `color.text`, `color.focus`, `color.border` |
| `app/ui_style_tokens.py` | `COLORS` | colors | `bio=#12324A`, `meta=#6B4FD8`, `bio_accent=#1BAE9F` | 缺 Firefly brand token；meta 紫色可能造成单一风格风险 | `brand.primary`, `brand.secondary`, `module.bio`, `module.meta`, `module.labtools` |
| `app/ui_style_tokens.py` | `RADIUS` | radius | `sm=8`, `md=14`, `lg=20` | 大圆角与目标规范冲突 | `radius.card=8`, `radius.control=6/8`, `radius.panel=8` |
| `app/ui_style_tokens.py` | `loginBrandPanel` | gradient/colors | `#092944 -> #0CA99C` | 旧登录页视觉，不适合 Welcome 目标 | `brand.hero.background` after UI-A2 |
| `app/ui_style_tokens.py` | `brandTitle` | font size | `44px` | Hero typography 与目标 Welcome 未验证 | `font.hero.title` |
| `app/ui_style_tokens.py` | `previewBadge`, `bioProjectPreviewBadge`, `readinessStatusBadge` | status colors | `#0E6F66`, `#E7F7F5`, `#BCE7E2` | testing/ready/developer preview 混用同一绿系 | `status.testing.*`, `status.ready.*`, `status.preview.*` |
| `app/ui_style_tokens.py` | `bioProjectStatusLabel[status=error]` | error colors | `#FFF1F0`, `#FFD0CC` | 与 `danger=#D43832` 只是局部绑定 | `status.error.bg/border/text` |
| `app/ui_style_tokens.py` | `QHeaderView::section` | table header | `bio_soft`, `bio`, `border` | 表格只偏 Bio 模块 | `table.header.bg/text/border` |
| `app/shell/sidebar.py` | `setFixedWidth(190)` | width | `190` | 英文/i18n 后可能不足 | `layout.sidebar.width` |
| `app/shell/sidebar.py` | `setStyleSheet` | colors/radius | `#F8FAFC`, `#D8DEE9`, `6px` | 绕过 token | `sidebar.bg/border/button.radius` |
| `app/shell/sidebar.py` | title/footer | font/color | `18px`, `#64748B` | 品牌/辅助入口风格不统一 | `sidebar.brand.font`, `color.muted` |
| `app/shell/main_window.py` | `setMinimumSize` | layout | `860x560` | Welcome/Dashboard 高保真响应式未验证 | `window.min_width/min_height` |
| `app/shell/main_window.py` | `_entry_card`, `_list_card`, `_recent_projects_card` | card | `#D8DEE9`, `8px`, `#FFFFFF` | 重复 card primitive | `card.border/radius/bg` |
| `app/shell/main_window.py` | Settings title | font size | `24px` | Settings 与 Dashboard/Bio 标题层级不统一 | `font.page.title` |
| `app/shell/login.py` | brand panel sizes | width/icon | `minWidth 360`, icon `108/96` | Welcome 主视觉需新布局 | `welcome.layout.brand_panel`, `icon.logo.size` |
| `app/shell/login.py` | link row and account status | padding/sizes | `10,4,10,2`, `28px`, `38px` | 旧注册/VIP/License 视觉不应进入 Welcome | legacy only |
| `app/shell/module_selection.py` | module card icon | size | container `64`, pixmap `60` | LabTools 加入后三模块视觉需验证 | `module_card.icon.size` |
| `app/shell/module_selection.py` | accent line | size | height `4`, width `96` | 装饰线可能与目标视觉不符 | `module_card.accent` or remove |
| `app/meta_analysis/workspace.py` | nav width | width | `260` | 目标 Meta 10 页导航可能溢出 | `module_nav.width` |
| `app/meta_analysis/workspace.py` | title/heading styles | font | `22px/18px`, weight `700` | Meta shell 与 token 不一致 | `font.module.title`, `font.section.title` |
| `app/bioinformatics/pages/*.py` | repeated title/card/error | style | `font-size:20px`, `#D8DEE9`, `#B42318` | 多页重复，未走 shared token | `page.title`, `card.*`, `status.error.text` |
| `app/bioinformatics/workflow_pages.py` | max heights | layout | `120`, `230`, `92`, `150`, `170` 等 | 长文本/i18n/数据量下可能截断 | `component.table.max_height`, responsive rules |

## 8. 页面级视觉缺口

| target_page | missing_visual_spec | missing_icon_or_image | can_build_low_fidelity_now | requires_figma_before_high_fidelity | suggested_stage |
|---|---|---|---|---|---|
| Welcome | 主品牌版式、Welcome 主视觉、按钮层级、无账号启动页布局 | Firefly logo、Welcome image | 是 | 是 | UI-A2 |
| About | 品牌叙事版式、引文呈现、Developer Preview disclaimer | About illustration/logo lockup | 是 | 是 | UI-A2 |
| Dashboard | 三模块卡片、最近项目、底部状态、去账号化信息层级 | LabTools icon、三模块统一图标、状态图标 | 是 | 是 | UI-A2/UI-A4 |
| Sidebar | 新入口层级、底部 About/测试反馈、active/hover/focus 状态 | Sidebar icons optional | 是 | 否，低保真可先做 | UI-A4 |
| Settings | 左侧二级导航、资源状态卡、检测/安装状态、开发者诊断折叠 | Settings 子页图标、资源图标、状态图标 | 是 | 是 | UI-A2/UI-A4 |
| Bio Project Home | 当前 UI03 有资源，但目标文案/卡片需重组 | 可复用 UI03 icons；缺目标空状态 | 是 | 高保真需要 | UI-A4 |
| Bio Data Source | 数据来源卡、公共数据库等权展示、已记录/已下载状态 | GEO/TCGA/GTEx/local import icons | 是 | 是 | UI-A2/UI-A4 |
| Bio Data Check & Preparation | 文件级识别表、缺失项、技术详情折叠 | file type/status icons | 是 | 是 | UI-A2/UI-A4 |
| Bio Group & Design | raw group vs analysis design 对比、comparison list | group/design icons | 是 | 可后置 | UI-A4 |
| Bio Analysis Tasks | readiness cards、gated buttons、planned/preflight 状态 | task/status/preflight icons | 是 | 是 | UI-A2/UI-A4 |
| Bio Result & Report | 结果预览、图表占位、加入报告草稿 | result/chart/report icons, empty result illustration | 是 | 是 | UI-A2/B8.1 |
| Bio Report Export | Markdown/HTML/DOCX/PDF 状态、导出按钮 | export/report icons | 是 | 是 | UI-A2/UI-A3 |
| Bio Settings | 模块设置与全局资源关系 | settings/resource icons | 是 | 可后置 | UI-A4 |
| Project Logs & Technical Details | 折叠技术详情、日志/反馈包 | diagnostics/log/export icons | 是 | 否 | UI-A4 |
| LabTools Home | 三入口版式、实验模块分类 | LabTools module icon, calculator/reagent/experiment icons | 是 | 是 | UI-A2/UI-A4 |
| LabTools Calculator | 数值输入、单位选择、结果卡 | calculator/unit icons | 是 | 可后置 | UI-A4 |
| LabTools Reagent Preparation | template/current prep/history 三段式 | reagent/template/history icons | 是 | 是 | UI-A2/UI-A4 |
| LabTools Experiment Modules | cell/protein/nucleic/immuno/IHC 分类 | experiment category icons | 是 | 是 | UI-A2/UI-A4 |
| Meta Analysis flow | Meta type前置、检索/筛选/提取/QA/统计/报告 | Meta type icons, workflow icons | 是，shell-only | 是 | UI-A2/Meta audit |
| Result / Report / Export | 跨模块报告/导出一致性 | report/export/status icons | 是 | 是 | UI-A2/UI-A3 |
| Developer Diagnostics / Test Feedback | 诊断折叠、反馈包、日志状态 | diagnostic/log/feedback icons | 是 | 否 | UI-A4 |

## 9. 打包图标与桌面入口资源风险

| item | evidence | risk | suggested_resolution |
|---|---|---|---|
| `.app` bundle icon 配置 | `scripts/package_app.py` 写 Info.plist，但无 `CFBundleIconFile` / `CFBundleIconName`；`dist/BioMedPilot.app/Contents/Info.plist` 也无 icon key | Finder/LaunchServices 可能不显示自定义 App icon，即使 assets 中有 `.icns` | 后续 packaging 阶段显式复制 `.icns` 到 `Contents/Resources` 并写 plist icon key |
| `CFBundleDisplayName` | `BioMedPilot / 医研智析` | 与 UI-A1 目标 `萤火虫 / Firefly` 主品牌冲突 | UI-A2 先冻结是否改 Finder display name；不要在未决前改包名 |
| `CFBundleName` / executable | `BioMedPilot` | 若 visible brand 改 Firefly，技术名与显示名关系需说明 | 可保留为技术名，但 Visual Style Guide 要定义 |
| `dist/BioMedPilot.app` | Info.plist `BioMedPilotGitHead=db4e27b` | dist 不是当前 HEAD `30d4f02`，不能作为当前 UI 资源状态证据 | 标记 stale；本阶段不运行、不打包 |
| 桌面 `/Users/changdali/Desktop/BioMedPilot.app` | Info.plist `BioMedPilotGitHead=21e1a0f` | 桌面入口比 dist 更旧，不能代表当前 UI-A1/A2 文档状态 | 后续打包任务再刷新；本阶段不覆盖 |
| `archive/legacy_sources/model9/packaging/meta_app_launcher.command` | 旧 Meta launcher 指向 `app_meta/main.py` | 旧桌面入口/Meta 独立包路径不属于当前 UIShell | 仅保留历史，不用于当前桌面入口 |
| `scripts/package_app.py --smoke-test` | 支持 direct launcher smoke | 根据既有包装门槛，直接 smoke 不是 Finder-style launch 充分证据 | 后续 packaging 阶段应补 LaunchServices/Finder-style gate |

## 10. Visual Style Guide 前置建议

| guide_item | required_decision |
|---|---|
| 品牌命名规则 | 定义 `萤火虫 / Firefly`、`BioMedPilot / 医研智析`、bundle/report/technical name 的层级 |
| Logo 使用规则 | App icon、Welcome logo、About logo、sidebar wordmark 是否同源 |
| App icon 使用规则 | active `.png/.icns/iconset` 是否保留，是否重出 Firefly 版本 |
| 模块图标规范 | Bioinformatics、Meta Analysis、LabTools 同一尺寸、风格、背景、状态表达 |
| 颜色 token | brand、module、status、surface、border、focus、chart、report tokens |
| 字体 token | 中文/英文 font family、字号层级、字重、行高、按钮最大长度 |
| 间距 token | page/container/card/form/table/sidebar 的 spacing scale |
| 圆角 token | 按目标约束重审，建议 card/control 默认 8px 或以下 |
| 状态标签 token | Developer Preview、testing、planned、blocked、ready、available、failed、detecting、not configured |
| 按钮规范 | primary/secondary/quiet/danger/link/icon-only/disabled/gated 状态 |
| 卡片规范 | module card、resource card、result card、empty state card、diagnostic card |
| 表格规范 | dense data table、file recognition table、result preview table、QA/extraction table |
| 空状态规范 | 无项目、无数据、无任务、无结果、无报告、资源未配置 |
| Developer Preview 视觉规则 | 不能高保真包装为正式能力；必须可见但不压过主流程 |
| 浅色/深色模式 | 当前强制浅色；建议明确 v1 暂不支持深色，避免双主题成本 |

## 11. 高风险问题清单

| risk | severity | impact | next_action |
|---|---|---|---|
| 目标主品牌 Firefly/萤火虫 未进入 active runtime 和 assets | High | Welcome/About/Dashboard 高保真无法开始 | UI-A2 冻结品牌关系和 logo |
| LabTools 图标缺失 | High | 三模块 Dashboard 无法视觉闭环 | 新增 LabTools icon 设计输入 |
| active assets 缺状态图标/空状态插图/报告导出图标 | High | Settings、Bio、Meta、LabTools 目标页会大量临时文字化 | 建立状态和空状态资源清单 |
| 打包 Info.plist 未配置 bundle icon | High | Finder/桌面包图标可能不一致或缺失 | packaging 阶段写 icon key 并验证 |
| `dist` 和 Desktop `.app` 均旧于当前 HEAD | High | 不能作为当前 UI/资源证据 | 后续 packaging 专项再刷新，UI-A2 不运行 |
| 两套浅色主题和大量 inline stylesheet 并存 | Medium | 高保真制作后难以统一 | 建立唯一 token source |
| 旧 Login/VIP/License/注册图标仍被 active UI 使用 | Medium | 与 Welcome 无账号目标冲突 | Welcome 重建时 legacy 化 |
| Bioinformatics UI04-UI13 workflow icons registered but missing | Medium | 当前资源 inventory 会持续显示 pending | 按目标 7 页重构后重新定义 icon slots |
| archive 旧图标丰富但无 active 引用 | Medium | 容易误拿旧图当新规范 | 标注 legacy，迁移前做视觉审查 |

## 12. 后续 UI-A3 / UI-A4 建议

### 12.1 是否建议进入 UI-A3

建议进入 UI-A3。原因：

- 当前品牌、状态、按钮、报告、模块名均存在中英混排和硬编码。
- Firefly/BioMedPilot/医研智析 的品牌层级会影响英文显示名、报告标题、bundle display name。
- Bioinformatics/Meta/LabTools 的术语很长，必须做英文长度和医学/实验术语边界审计。

### 12.2 UI-A4 前置条件

进入 UI-A4 实施路线审计前，建议先完成：

1. Brand/Logo/Icon 冻结。
2. Visual Style Guide v1。
3. 状态标签 token 和 Settings 资源状态 token。
4. 目标资源清单：缺失、可复用、legacy、需重绘。
5. i18n key 和中英术语表。

### 12.3 可低保真先行的内容

- Welcome / About shell。
- Dashboard 三模块低保真。
- Sidebar 入口模型。
- Settings 二级导航低保真。
- Bioinformatics 目标 7 页 shell。
- LabTools Home shell。
- Meta Question & Meta Type shell。

高保真必须等待 UI-A2/Visual Style Guide 的页面：

- Welcome、About、Dashboard。
- 模块图标体系。
- Settings 外部资源状态页。
- Result / Report / Export。
- LabTools 实验模块。

## 13. 命令记录与验证

| command | result |
|---|---|
| `rg -n "BioMedPilot\|医研智析\|萤火虫\|Firefly\|LabTools\|Labors\|实验工具\|Bioinformatics\|生信分析\|Meta Analysis\|Meta 分析" app tests docs scripts packaging assets resources icons images branding dist ...` | 初始品牌扫描；因 `packaging/resources/icons/images/branding` 根目录不存在返回目录缺失错误，已改用存在目录重跑 |
| `find . -maxdepth 4 ... -iname '*.png' ... -iname '*.plist' -iname '*.command'` | 成功；发现 active icons、dist Info.plist |
| `rg --files app tests docs scripts packaging assets resources icons images branding dist ...` | 成功但提示部分目录不存在；用于定位 style/resource/package 文件 |
| `rg -n "#[0-9A-Fa-f]{3,8}\|font-size\|font-weight\|border-radius\|padding\|margin\|setFixed..." app tests -g '*.py'` | 成功；输出硬编码视觉参数和 token 使用位置 |
| `rg -n "BioMedPilot\|UI-A1\|UI-A2\|commit\|packag\|LaunchServices\|萤火虫\|Firefly" /Users/changdali/.codex/memories/MEMORY.md` | 成功；确认本任务只提交 scoped docs，不打包 |
| `nl -ba app/app_identity.py \| sed -n '1,280p'` | 成功；确认 APP_NAME、icon paths、IconAssetSlot、loader、QApplication identity |
| `nl -ba app/ui_style_tokens.py \| sed -n '1,760p'` | 成功；确认 COLORS/SPACING/RADIUS/FONT_SIZE 和页面 stylesheets |
| `nl -ba app/ui_theme.py \| sed -n '1,220p'` | 成功；确认全局 light palette |
| `plutil -p dist/BioMedPilot.app/Contents/Info.plist` | 成功；dist bundle display name 为 `BioMedPilot / 医研智析`，GitHead 为 `db4e27b`，未见 icon key |
| `nl -ba scripts/package_app.py \| sed -n '1,260p'` | 成功；确认打包脚本写 Info.plist 但未写 bundle icon key |
| `find assets/icons -type f ... sips -g pixelWidth -g pixelHeight ...` | 成功；记录 active icon 尺寸 |
| `rg -n "load_.*icon\|load_.*pixmap\|...setWindowIcon..." app tests -g '*.py'` | 成功；确认图标引用和测试覆盖 |
| `find . -maxdepth 5 \( -name 'packaging' -o -name 'resources' ... \)` | 成功；发现 active `assets/icons`, `assets/images`, `dist` 和 legacy archive 目录 |
| `find . -maxdepth 5 \( -iname '*.command' -o -iname '*.plist' -o -iname '*.app' \)` | 成功；发现 legacy command、dist app、dist Info.plist |
| `rg -n "BioMedPilot\|医研智析\|萤火虫\|Firefly..." app tests scripts docs/ui docs/bioinformatics docs/packaging.md docs/meta_known_limitations.md dist/...` | 成功；确认 active runtime 仍以 BioMedPilot/医研智析为主，Firefly 仅在文档 |
| `find assets/images -maxdepth 3 -type f -print` | 成功；仅有 `.gitkeep` |
| `find archive/legacy_sources/model9 -maxdepth 4 ...` | 成功；发现 legacy Meta、status、empty-state、toolbar、sidebar 图标 |
| `sed -n '1,220p' archive/legacy_sources/model9/packaging/meta_app_launcher.command` | 成功；确认旧 Meta launcher 指向历史 `app_meta/main.py` |
| `rg -n "setStyleSheet\(...` app/shell app/bioinformatics app/meta_analysis app/shared ...` | 成功；确认 active inline style 和硬编码尺寸 |
| `git status --short --branch` | 成功；写报告前工作区 clean |
| `nl -ba tests/ui/test_app_identity.py \| sed -n '1,220p'` | 成功；确认图标存在/加载测试覆盖 |
| `nl -ba app/shell/login.py \| sed -n '110,380p'` | 成功；确认旧登录页品牌和图标使用 |
| `nl -ba app/shell/module_selection.py \| sed -n '130,330p'` | 成功；确认 Dashboard 品牌、两模块、support icon 使用 |
| `nl -ba tests/test_package_app.py \| sed -n '1,220p'` | 成功；确认 packaging tests 未检查 bundle icon key |
| `rg -n "CFBundleIcon\|IconFile\|biomedpilot_app_icon\|app_icon\|icns\|icon" ...` | 成功；确认无 active bundle icon plist key |
| `nl -ba tests/ui/test_app_theme.py \| sed -n '1,200p'` | 成功；确认浅色主题测试 |
| `nl -ba tests/ui/test_sidebar.py \| sed -n '1,200p'` | 成功；确认 sidebar 仍无 LabTools |
| `nl -ba app/shared/feature_status.py \| sed -n '1,220p'` | 成功；确认功能状态语义 |
| `nl -ba app/shared/feature_availability.py \| sed -n '1,160p'` | 成功；确认 feature availability 状态与文案 |
| `nl -ba app/shell/status_panel.py \| sed -n '1,120p'` | 成功；确认 status panel inline style |
| `ls -ld /Users/changdali/Desktop/BioMedPilot.app` | 成功；桌面 app 存在 |
| `plutil -p /Users/changdali/Desktop/BioMedPilot.app/Contents/Info.plist` | 成功；桌面 app GitHead 为 `21e1a0f`，未见 icon key |
| `git rev-parse --short HEAD` | 成功；当前审计基线为 `30d4f02` |
| `git diff --check` | 成功；无 whitespace error 输出 |
| `git status --short` | 成功；仅显示 `docs/ui/UI_A2_visual_brand_resource_audit_20260520.md` 为新增文档 |

### 13.1 验证结论

本阶段只新增本审计报告，不涉及 runtime 代码、测试代码、资源文件、打包脚本、打包产物或桌面入口，因此未运行完整测试套件。
