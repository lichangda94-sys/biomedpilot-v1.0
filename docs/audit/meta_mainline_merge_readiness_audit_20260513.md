# Meta MainLine Merge Readiness Audit

审计日期：2026-05-13
审计对象：BioMedPilot v1.0 Meta Analysis worktree
审计性质：合并主线前审计，仅新增报告，不修改业务代码

## 1. 审计目标

本次审计用于判断 `dev/meta-analysis` 的 Meta 分析模块在后续进入 MainLine / Integration 前，是否存在结构、主题色、UI 样式、跨模块边界、旧 UI 残留、测试覆盖和合并阻碍风险。

重点按 BioMedPilot / 医研智析 当前统一视觉要求检查：

- deep navy：`#12324A`
- teal：`#1BAE9F`
- light gray：`#F5F7F9`
- white：`#FFFFFF`

本次不替换颜色、不重构 UI、不合并 MainLine、不修改 Bioinformatics、不打包、不 push。

## 2. 当前分支 / worktree / git head

| 项目 | 结果 |
| --- | --- |
| worktree | `/Users/changdali/Developer/biomedpilot v1.0/Meta` |
| branch | `dev/meta-analysis` |
| git head | `f4d8f958dabf87473f27d226331dc00edb1bc98a` |
| 审计前 status | clean |
| MainLine 架构文档基线 | `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/architecture/` |

已按要求阅读并核对：

- `/Users/changdali/Developer/biomedpilot v1.0/README_总说明.md`
- `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- Meta worktree 的 `README.md`、`CODEX.md`、`docs/architecture.md`、Meta current status、UI construction、boundary、readiness、handoff 相关文档
- MainLine 当前总体架构和代码结构文档
- `tests/meta_analysis`
- `tests/ui`

未发现本任务与总开发手册存在需要停止的冲突。注意：`docs/branch_development_rules.md` 仍含旧路径 `/Users/changdali/Documents/BioMedPilot`，与 2026-05-13 总说明和总开发手册的新根目录不一致；本次按总说明和总手册执行，并将该文档视为后续需更新的低风险文档债。

## 3. 检查方法

执行了以下检查：

- `pwd`
- `git status --short`
- `git rev-parse --abbrev-ref HEAD`
- `git rev-parse HEAD`
- 全量样式关键词扫描：`#[0-9A-Fa-f]{3,8}|rgb\\(|rgba\\(|QColor|QPalette|setStyleSheet|styleSheet|stylesheet|background|color|border|primary|accent|theme`
- 跨模块边界扫描：`app\\.bioinformatics|bioinformatics|GEO|TCGA|GTEx`
- 临时 / 占位 / 开发文案扫描：`TODO|FIXME|placeholder|mock|demo|Developer Preview|测试级|占位`
- active Meta runtime 扫描时排除了 `app/meta_analysis/legacy/**`，避免把历史归档误判为当前运行路径
- 运行指定测试和 smoke test
- 运行 `git diff --check`

结构统计：

- `app/meta_analysis` 非 legacy active 文件约 239 个。
- `app/meta_analysis/legacy` 文件约 353 个，属于历史快照和参考区，不应作为当前 runtime 合并依据。

## 4. 主题色与硬编码颜色审计结果

结论：存在合并前必须处理的主题统一风险。当前测试通过，但 active Meta UI 并未完全走统一主题变量。

### 4.1 全局 token 中仍有不符合当前主色板的 Meta purple

`app/ui_style_tokens.py` 当前包含：

- `meta = "#6B4FD8"`
- `meta_soft = "#F0EDFF"`

这与本阶段明确要求的 deep navy / teal / light gray / white 主色板不一致。虽然扫描未显示 active Meta workspace 大量使用这两个 token，但它们作为全局 token 存在，会在 MainLine 合并和后续 UI shell 统一时造成“Meta 分析 = purple 主题”的误导。

风险等级：High。

### 4.2 active Meta workspace 内有独立硬编码 QSS

`app/meta_analysis/workspace.py` 的 `_meta_workspace_stylesheet()` 直接硬编码：

- `#F5F7F9`
- `#FFFFFF`
- `#D8DEE9`
- `#111827`
- `#4B5563`
- `#92400E`
- `#0F766E`
- `#E6FFFB`
- `#99F6E4`
- `#F8FAFC`
- `#E5E7EB`
- `#CBD5E1`

其中 `#F5F7F9`、`#FFFFFF` 符合主色板；但 teal 使用的是 `#0F766E` 而不是统一 `#1BAE9F`，边框/文本/状态色也没有通过统一 token 管理。

风险等级：High。

### 4.3 active Meta page widgets 重复硬编码卡片、错误和文本颜色

多个页面存在重复 inline `setStyleSheet`：

- `app/meta_analysis/pages/literature_import_page.py`
- `app/meta_analysis/pages/duplicate_review_page.py`
- `app/meta_analysis/pages/screening_page.py`
- `app/meta_analysis/pages/prepare_screening_page.py`
- `app/meta_analysis/pages/extraction_page.py`
- `app/meta_analysis/pages/analysis_page.py`
- `app/meta_analysis/pages/reporting_page.py`
- `app/meta_analysis/pages/audit_log_page.py`
- `app/meta_analysis/pages/attachment_page.py`

常见硬编码包括：

- 卡片：`border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF`
- 结果卡片：`background: #F8FAFC`
- 文本：`#111827`
- 错误：`#B42318`

这些颜色本身多数是专业浅色系，但没有走统一主题 token。后续 MainLine 合并时如果 UIShell 主题更新，Meta 页面会保留自己的局部风格，导致视觉割裂。

风险等级：High。

### 4.4 报告 SVG / HTML 导出也硬编码了非统一调色

`app/meta_analysis/services/formal_report_service.py` 的简化 PRISMA SVG 使用：

- `#475569`
- `#ffffff`
- `#7a4a00`
- `#f8fafc`
- `#64748b`
- `#0f172a`

`app/meta_analysis/services/publication_export_service.py` 的 HTML style 使用：

- `#172033`
- `#d8dee9`
- `#fff7ed`
- `#fed7aa`

这些属于导出物样式，不是桌面主 UI shell，但如果后续希望报告预览与主视觉一致，需要抽取 shared report/export style token。

风险等级：Medium。

## 5. UI 风格一致性审计结果

结论：active Meta UI 大体保持 macOS-like 白卡、浅灰背景、Developer Preview 标记和人工确认边界，但尚未达到主线统一主题标准。

正向结果：

- Meta 主入口不是 shell-only 占位页，已恢复 8 步中文 workflow。
- 主要页面保留 Developer Preview / testing 标记。
- 普通 workflow 中未发现直接声称 production-ready、clinical-grade 或 submission-grade。
- 旧 `branch/schema/manifest` 原始细节主要放在开发者诊断或文档语境，不是普通用户主流程核心。
- `tests/ui/test_meta_analysis_workflow_pages.py`、`tests/ui/test_meta_search_stage_m2.py`、`tests/ui/test_meta_stage_m3_dedup_workflow.py` 覆盖了 Meta UI 基础流程。

主要问题：

- active Meta workspace 自己定义了一套局部 QSS，没有统一依赖 `app/ui_style_tokens.py` 或 MainLine/UIShell 的 shared theme API。
- 当前 Meta 主按钮色为深 teal `#0F766E`，不是要求的 `#1BAE9F`。
- 状态 badge、警告、错误色没有明确规范化到 shared semantic tokens。
- `app/ui_style_tokens.py` 的 `meta` / `meta_soft` purple token 与当前主视觉不一致。
- legacy Meta UI 中存在旧蓝色主题 `#2563EB`、旧 `Theme` 类、旧 app shell、Demo/Mock UI；目前位于 legacy，但如果后续整目录合并或误接入，会造成明显风格割裂。

## 6. Meta 与 Bioinformatics 隔离审计结果

结论：active Meta runtime 未发现直接依赖 `app.bioinformatics` 业务代码；隔离总体可接受，但 legacy 目录仍是合并前重点隔离风险。

扫描结果：

- active `app/meta_analysis` 未发现 `from app.bioinformatics...` 或 `import app.bioinformatics...`。
- 非 legacy 命中主要是边界保护逻辑，例如 `app/meta_analysis/services/internal_beta_rc_service.py` 检查 changed paths 中是否包含 `app/bioinformatics/` 或 `tests/bioinformatics/`。
- `tests/meta_analysis/test_meta_workflow_ui_integration_v1.py` 明确断言 workflow 文本不包含 `app.bioinformatics`。
- `tests/meta_analysis/test_stage_z_release_candidate_freeze.py` 覆盖 Bioinformatics changed path 阻断。

保留风险：

- `app/meta_analysis/legacy/` 中仍包含 GEO/GSE/TCGA/GTEx、Bioinformatics readiness、旧 desktop shell、demo/mock runner 等历史内容。
- `app/meta_analysis/legacy/README.md` 已明确声明这些不属于当前 Meta runtime，不能新增引用；这个边界正确，但 MainLine 合并时必须保留或强化 exclude/隔离策略。
- shared query intelligence 中同时包含 Bioinformatics 和 Meta context，这是共享层设计，不是 Meta 直接依赖；后续合并时必须保留 `target_context="meta_analysis"` 的过滤测试。

## 7. MainLine 合并准备度评估

当前不建议直接进入 MainLine 合并。

建议状态：暂缓 MainLine 直接合并，先进入 “Meta UI 主题统一修复 + Integration 验证”。

理由：

- 测试通过，说明功能基线稳定。
- active Meta 未直接污染 Bioinformatics，边界总体可控。
- 但主题色与硬编码样式不满足本次主视觉要求，且 `app/ui_style_tokens.py` 中存在 purple Meta token。
- legacy 目录内容较多，包含旧 UI 和 Bio/GEO 历史内容；需要合并策略明确哪些目录进入 MainLine、哪些仅归档保留、哪些测试不作为主线 runtime。
- MainLine 当前文档要求模块成果进入 MainLine 前应经 Integration 或等效集成验证；本次只在 Meta worktree 审计，没有做 Integration 合并验证。

## 8. 测试现状

本次执行：

| 命令 | 结果 |
| --- | --- |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q` | 457 passed |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | 154 passed |
| `python3 -m app.main --smoke-test` | passed；`git_head=f4d8f95`，`pyside6_available=True` |
| `git diff --check` | passed |

测试覆盖评价：

- Meta service、workflow、M2 search、M3 dedup/PRISMA、internal beta、report/export、AI suggestion guard、boundary guard 覆盖较广。
- UI 测试覆盖 offscreen 实例化和关键流程，但缺少专门的“统一主色板 / 禁止 purple token / 禁止 active Meta inline hardcoded color”审计测试。
- 暂未执行 MainLine worktree 的完整测试矩阵，也未执行 Integration 合并测试；这是主线合并前残余风险。

## 9. 风险清单

### High

1. `app/ui_style_tokens.py` 中 `meta="#6B4FD8"`、`meta_soft="#F0EDFF"` 与当前主色板冲突。
2. `app/meta_analysis/workspace.py` active QSS 使用 `#0F766E` 等独立主题色，没有走统一 `#1BAE9F` / shared token。
3. 多个 active Meta page widgets 重复硬编码卡片、错误、文本颜色，后续 MainLine/UIShell 主题调整时容易风格割裂。
4. `app/meta_analysis/legacy/` 包含旧 UI、GEO/TCGA/GTEx/Bioinformatics readiness 和 demo/mock runner 内容；若合并策略不明确，存在旧 UI 或跨模块概念误接入风险。

### Medium

1. 报告 SVG / HTML 导出样式使用独立灰蓝/橙色系，尚未纳入 shared report style token。
2. 状态色、错误色、warning 色没有语义化规范；红/绿/橙目前可读，但不是统一设计系统的一部分。
3. MainLine 当前只有 Meta 最小入口；Meta 完整 workflow 合并后会显著扩大 `app/meta_analysis` 和 `tests/meta_analysis` 面积，需要 Integration 验证路径、导入路径和测试耗时。
4. shared query intelligence 同时服务 Bioinformatics 和 Meta，需要继续用 context filter 测试防止 GEO/TCGA/GTEx 候选进入 Meta。
5. `docs/branch_development_rules.md` 存在旧路径说明，容易误导后续合并/打包人员。

### Low

1. Placeholder / Developer Preview / testing 文案大量存在，但多数是正确的成熟度标记，不是生产化错误。
2. `PDF placeholder`、`GRADE placeholder`、`Network Meta 未实现` 等文案需要保留，但可在后续 UI 文案阶段进一步中文化和统一。
3. shell 层仍有部分硬编码浅灰边框和 sidebar 背景；这属于 UIShell 统一主题任务，不是 Meta 独有阻塞项。
4. 未进行截图级视觉验收；当前测试主要验证结构和行为。

## 10. 建议修复顺序

1. 新增或扩展 shared UI theme token，明确 `deep_navy=#12324A`、`teal=#1BAE9F`、`light_gray=#F5F7F9`、`white=#FFFFFF`，并提供 semantic tokens：text、muted、border、surface_muted、success、warning、danger。
2. 移除或重定义 `app/ui_style_tokens.py` 中的 Meta purple token，避免 MainLine 继续传播 purple Meta 主题。
3. 将 `app/meta_analysis/workspace.py` 的 `_meta_workspace_stylesheet()` 改为使用 shared token，不再硬编码 `#0F766E` 等局部主题。
4. 抽取 active Meta page 的 common card/error/title 样式，替换重复 inline QSS。
5. 为 active Meta 添加轻量审计测试：禁止 `#6B4FD8` / `#F0EDFF` 出现在 active Meta UI；检查主按钮使用统一 teal；检查 legacy 目录以外无 `app.bioinformatics` import。
6. 明确 Integration 合并清单：active `app/meta_analysis`、必要 tests/docs；legacy 目录按主线策略决定归档保留或隔离，不做整目录无差别接入。
7. 更新旧路径文档或在主线合并前归档旧 `branch_development_rules.md`。
8. 在 Integration worktree 执行合并演练和完整验证，再决定进入 MainLine。

## 11. 是否建议现在进入主线合并

不建议现在直接进入 MainLine 合并。

建议先进入下一阶段：`Meta UI 主题统一修复`。完成主题统一、active/legacy 合并清单、边界审计测试后，再进入 Integration worktree 做合并演练。Integration 验证通过后，再考虑合入 MainLine。

## 12. 下一阶段 Codex 开发建议

建议下一阶段任务名称：

`fix(meta-ui): align Meta theme with BioMedPilot main visual system`

建议范围：

- 只改 Meta active UI 和 shared style token。
- 不改 Bioinformatics 业务代码。
- 不改变 AI Gateway、shared vocabulary 行为。
- 不启用网络、AI 自动筛选、自动提取、自动分析或正式报告。
- 不删除 legacy 文件，只强化隔离和测试。

建议验收：

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
- `python3 -m app.main --smoke-test`
- `git diff --check`
- 新增主题审计测试通过。
