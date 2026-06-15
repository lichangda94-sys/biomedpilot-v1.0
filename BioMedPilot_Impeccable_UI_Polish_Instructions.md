# BioMedPilot UI 视觉升级指令：使用 Impeccable Skill

> 使用时机：本指令只能在 **UI 接线任务已经完成** 后执行。
> 前提状态：一级入口、二级页面、按钮跳转、页面栈/路由注册、核心业务流程已经可正常进入和返回。
> 本阶段目标不是修复业务逻辑，而是使用 Impeccable 对 BioMedPilot 的界面进行设计审计、视觉统一和安全美化。

---

## 0. 当前任务边界

你现在的任务是：

1. 使用 Impeccable skill 审计 BioMedPilot 当前 UI。
2. 建立或补全产品设计上下文。
3. 改进 UI 的视觉层级、间距、字体、按钮、卡片、导航、空状态、错误提示和结果页布局。
4. 保持现有接线、页面跳转、分析后端、导出逻辑和测试契约不被破坏。
5. 只做小步、可审计、可回滚的修改。

你不能做：

1. 不能重写整个 UI 框架。
2. 不能替换 PyQt 主架构。
3. 不能把当前已接通的页面改成新的路由系统。
4. 不能删除已有页面、按钮、测试、分析入口。
5. 不能改动 Meta 分析、生信分析、Labtools 的核心计算逻辑。
6. 不能为了视觉效果牺牲可用性。
7. 不能引入大体积、不必要、联网依赖强的新 UI 框架。
8. 不能使用营销型 SaaS 风格重做 BioMedPilot。

---

## 1. 建议分支

请先从当前已完成接线任务的分支创建新分支：

```bash
git status --short
git branch --show-current
git checkout -b ui/impeccable-polish
```

如果工作区不干净，请先停止，不要继续修改。先输出当前未提交文件列表并说明风险。

---

## 2. 安装或确认 Impeccable Skill

在项目根目录执行：

```bash
npx impeccable skills install
```

然后在 Codex 中确认 skill 是否可用。

Codex 环境下请优先使用：

```text
/impeccable
```

或：

```text
$impeccable
```

如果 skill 没有出现，请检查是否安装到 Codex 可识别的 skills 目录。不要因此改动项目代码。

---

## 3. 初始化产品设计上下文

如果项目根目录还没有 `PRODUCT.md` 或 `DESIGN.md`，请执行：

```text
/impeccable init
```

初始化时使用以下产品定义：

```text
Surface type: product app, not brand/marketing website.

Product name: BioMedPilot

BioMedPilot is a local biomedical research analysis platform for clinicians, PhD researchers, translational medicine researchers, and biomedical data users. The UI should feel calm, clinical, reliable, task-focused, and reproducible.

The product is not a SaaS marketing dashboard. Avoid decorative AI-dashboard clichés, purple/blue gradients, glassmorphism, excessive shadows, nested cards, fake analytics widgets, over-animation, and startup landing-page style.

Core product areas:
1. Shell: Welcome, Home, Settings, About
2. Bioinformatics module and subpages
3. Meta-analysis module and subpages
4. Labtools module and subpages

Primary design priorities:
1. Clear navigation
2. Stable page transitions
3. Visible module entry points
4. Readable forms and result tables
5. Safe export actions
6. Reproducible analysis reports
7. Local/offline trust
8. Low cognitive load
9. Clinical/research credibility
10. Accessibility and keyboard usability

Visual direction:
- calm biomedical desktop application
- restrained color palette
- strong hierarchy
- readable typography
- predictable spacing
- clear primary and secondary actions
- less decoration, more clarity
- analysis-first, not marketing-first
```

如果 `PRODUCT.md` 和 `DESIGN.md` 已存在，请不要直接覆盖。先读取并提出补丁建议，再谨慎更新。

---

## 4. 第一阶段：只审计，不改代码

先运行设计审计，不要修改文件：

```text
/impeccable audit current BioMedPilot UI
```

然后输出一份 Markdown 审计报告，命名为：

```text
docs/ui/IMPECCABLE_UI_AUDIT_YYYYMMDD.md
```

报告必须包含以下部分：

```markdown
# Impeccable UI Audit

## 1. Executive Summary

## 2. Scope

## 3. Functional Safety Status
- 已确认接线完整的页面：
- 不允许改动的接线/业务逻辑：
- 本轮只允许改动的视觉区域：

## 4. Visual Hierarchy Issues

## 5. Navigation Clarity Issues

## 6. Component Consistency Issues

## 7. Form and Input UX Issues

## 8. Tables and Result Display Issues

## 9. Empty State / Error State / Loading State Issues

## 10. Accessibility Issues

## 11. AI-Generated UI Smell / Anti-pattern Issues

## 12. Safe Polish Plan
- P0: 不改逻辑的低风险视觉修复
- P1: 组件统一
- P2: 结果页和表格体验优化
- P3: 后续可选增强

## 13. Files Proposed for Modification

## 14. Files Explicitly Not To Touch

## 15. Verification Plan
```

注意：第一阶段只生成报告，不要修改代码。

---

## 5. 第二阶段：建立安全修改清单

基于审计报告，生成一个分阶段修改计划：

```text
/impeccable shape safe UI polish plan for BioMedPilot without touching routing or analysis logic
```

输出文件：

```text
docs/ui/IMPECCABLE_UI_POLISH_PLAN_YYYYMMDD.md
```

计划必须按页面分组：

```markdown
# BioMedPilot Impeccable UI Polish Plan

## 1. Safety Rules

## 2. Page Groups

### 2.1 Shell Pages
- Welcome
- Home
- Settings
- About

### 2.2 Bioinformatics Pages
- Module landing page
- DEG configuration
- Results page
- Export/report page

### 2.3 Meta-analysis Pages
- Module landing page
- Data input
- Analysis configuration
- Forest plot/result page
- Export/report page

### 2.4 Labtools Pages
- Module landing page
- Tool subpages

## 3. Component Targets
- Sidebar / top navigation
- Module cards
- Primary buttons
- Secondary buttons
- Forms
- Tables
- Result panels
- Export panels
- Error banners
- Empty states
- Loading states

## 4. Design Tokens To Standardize
- spacing
- typography
- colors
- border radius
- shadows
- icons
- disabled states
- focus states

## 5. Implementation Order

## 6. Regression Tests

## 7. Manual QA Checklist
```

不要在计划阶段修改代码。

---

## 6. 第三阶段：小步实施，不要一次性大改

每次只处理一个页面组。

推荐顺序：

1. Shell pages
2. Module landing pages
3. Forms and configuration pages
4. Result pages and tables
5. Export/report pages
6. Empty/error/loading states
7. Final polish pass

每完成一个页面组，必须：

```bash
git diff --check
python3 -m app.main --smoke-test
```

如果项目存在 PyQt UI 测试，也必须运行：

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

如果测试失败，先修复失败，不要继续下一组页面。

---

## 7. Shell Pages 修改指令

执行：

```text
/impeccable polish BioMedPilot shell pages: Welcome, Home, Settings, About. Keep all routing, button handlers, page registration, and business logic unchanged.
```

允许修改：

1. 页面标题层级
2. 间距
3. 模块卡片视觉
4. 按钮尺寸和状态
5. 设置项布局
6. 关于页信息层级
7. 空白区域比例
8. 可读性

禁止修改：

1. 页面跳转函数
2. signal/slot 接线
3. objectName/test id
4. 导航注册表
5. 分析模块入口函数
6. 配置保存逻辑
7. 关于页版本信息来源

完成后运行测试并输出：

```text
Modified files:
Test commands:
Test results:
Risk assessment:
```

---

## 8. Module Landing Pages 修改指令

执行：

```text
/impeccable polish BioMedPilot module landing pages for Bioinformatics, Meta-analysis, and Labtools. Improve clarity and consistency only. Do not alter entry wiring.
```

目标：

1. 让用户明确知道每个模块能做什么。
2. 每个模块入口卡片风格一致。
3. 主操作按钮清晰可见。
4. 次要说明文字不要过长。
5. 页面视觉稳定，不使用夸张装饰。
6. 保留所有现有入口和子入口。

禁止：

1. 合并模块入口。
2. 删除“进入子页面”的按钮。
3. 改变页面层级结构。
4. 把可点击按钮改成不可点击装饰卡片。
5. 用图片替代真实控件。

---

## 9. Form / Configuration Pages 修改指令

执行：

```text
/impeccable polish BioMedPilot analysis configuration forms. Improve readability, grouping, labels, helper text, and validation display. Do not alter validation rules or analysis parameters.
```

目标：

1. 表单分组更清楚。
2. 参数说明更容易理解。
3. 错误提示更明显。
4. 必填项、可选项、默认值更明确。
5. 主操作按钮和返回按钮位置稳定。
6. 高风险操作需要清晰提示。

禁止：

1. 改分析参数名。
2. 改默认参数值。
3. 改校验规则。
4. 改数据读取逻辑。
5. 改测试依赖的字段名。
6. 改导出字段。
7. 改 R/Python 后端调用逻辑。

---

## 10. Result Pages / Tables 修改指令

执行：

```text
/impeccable polish BioMedPilot result pages and result tables. Improve scanability, table readability, figure placement, export affordance, and reproducibility metadata display. Do not alter result contracts.
```

目标：

1. 结果摘要优先显示。
2. 表格行距、列宽、标题更易读。
3. p value、effect size、CI、adj_p 等核心字段显示清楚。
4. 图像区域和表格区域不要互相挤压。
5. 导出按钮位置固定、语义清楚。
6. analysis_run_id、source_hash、参数摘要等可复现信息要可见但不过度抢眼。
7. 空结果、失败结果、部分成功结果要有清楚状态。

禁止：

1. 改结果数据结构。
2. 改 result contract。
3. 改导出文件格式。
4. 改图像生成逻辑。
5. 改统计计算逻辑。
6. 改测试断言依赖的列名。
7. 删除 reproducibility metadata。

---

## 11. Empty / Error / Loading States 修改指令

执行：

```text
/impeccable polish BioMedPilot empty states, error states, and loading states. Keep behavior unchanged and improve user guidance only.
```

目标：

1. 空状态告诉用户下一步该做什么。
2. 错误状态区分用户输入错误、文件错误、依赖缺失、分析失败。
3. loading 状态避免用户误以为程序卡死。
4. 本地运行、离线运行、依赖缺失时要有清楚提示。
5. 不要使用情绪化、营销化文案。

推荐文案风格：

```text
No analysis has been run yet.
Select an input file and configure the required parameters to begin.

The input file could not be read.
Check the file path, format, and required columns, then try again.

The analysis completed, but no significant result passed the current threshold.
Review the threshold settings or inspect the full result table.
```

---

## 12. 设计风格约束

BioMedPilot 应该避免：

1. 紫蓝渐变背景
2. 玻璃拟态
3. 过度圆角
4. 过多阴影
5. 卡片套卡片
6. 所有内容都做成 dashboard widgets
7. 无意义图标
8. fake AI assistant 风格
9. 大面积彩色发光边框
10. 过度动画
11. marketing landing page hero section
12. 低对比度灰字
13. 小号不可读文字
14. 纯装饰性图表
15. 用图片模拟页面控件

BioMedPilot 应该强调：

1. 医学/科研可信度
2. 本地化运行信任感
3. 清晰路径
4. 稳定操作
5. 数据可读性
6. 结果可复现
7. 分析流程透明
8. 控件真实可点击
9. 错误可解释
10. 导出行为明确

---

## 13. 推荐设计系统方向

可以建立统一 tokens，例如：

```text
Spacing:
- page margin
- section gap
- card padding
- form row gap
- button gap

Typography:
- page title
- section title
- body text
- helper text
- table header
- table cell
- metadata text

Color roles:
- app background
- surface background
- border
- primary action
- secondary action
- warning
- error
- success
- muted text
- metadata text

Components:
- module card
- analysis card
- form section
- result summary panel
- table container
- export action bar
- error banner
- empty state panel
```

如果项目已有样式系统，请优先复用，不要另起一套冲突系统。

---

## 14. 使用 Impeccable CLI 检测

如适用，可以运行：

```bash
npx impeccable detect .
```

如果项目目录太大，优先扫描 UI 目录，例如：

```bash
npx impeccable detect app/
npx impeccable detect src/
npx impeccable detect ui/
```

如果支持 JSON 输出，可保存结果：

```bash
npx impeccable detect --fast --json . > docs/ui/impeccable_detect_YYYYMMDD.json
```

注意：CLI 检测结果只作为参考。不要机械修复所有提示。必须结合 BioMedPilot 的 PyQt 桌面应用实际情况判断。

---

## 15. 强制回归验证

每次修改后至少运行：

```bash
git diff --check
python3 -m app.main --smoke-test
```

如存在以下测试，必须运行：

```bash
python3 -m pytest tests/meta_analysis/test_meta_result_contract_adapter.py -q
python3 -m pytest tests/meta_analysis/test_meta_statistics_engine_v2.py -q
python3 -m pytest tests/meta_analysis/test_analysis_core_mvp.py tests/meta_analysis/test_figure_result_table_mvp.py tests/meta_analysis/test_publication_export_reproducibility.py -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_meta_analysis_workflow_pages.py -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

如果某些测试不存在，不要创建伪测试通过记录。请如实说明：

```text
Skipped because test file does not exist:
```

---

## 16. 手动 QA 清单

修改完成后，手动确认：

```markdown
## Manual QA Checklist

### Shell
- [ ] Welcome page opens
- [ ] Home page opens
- [ ] Settings page opens
- [ ] About page opens
- [ ] Back/home navigation works

### Bioinformatics
- [ ] Bioinformatics module entry opens
- [ ] DEG configuration page opens
- [ ] Form controls are real clickable controls
- [ ] Result page can be reached
- [ ] Export controls remain visible

### Meta-analysis
- [ ] Meta-analysis module entry opens
- [ ] Data input page opens
- [ ] Analysis configuration page opens
- [ ] Forest/result page opens
- [ ] Export/report page opens

### Labtools
- [ ] Labtools module entry opens
- [ ] Existing subpages open
- [ ] Tool controls remain clickable

### Visual
- [ ] No page appears as a static image
- [ ] Buttons have visible hover/pressed/disabled states where supported
- [ ] Text remains readable
- [ ] Tables remain usable
- [ ] Error and empty states are clear
- [ ] No decorative redesign broke usability
```

---

## 17. 输出要求

最终必须输出：

```markdown
# Impeccable UI Polish Summary

## Branch
- Current branch:

## Baseline
- Starting commit:
- Previous UI wiring status:

## Files Modified

## Files Created

## What Changed
- Shell:
- Bioinformatics:
- Meta-analysis:
- Labtools:
- Shared components/styles:

## What Was Not Changed
- Routing:
- Analysis logic:
- Result contracts:
- Export logic:
- Tests:

## Verification
| Command | Result |
|---|---|
| git diff --check | |
| python3 -m app.main --smoke-test | |
| pytest UI tests | |
| pytest meta tests | |

## Remaining Risks

## Recommended Next Step
```

---

## 18. 最重要原则

本轮 UI 升级的成功标准不是“看起来更炫”，而是：

1. 页面能进。
2. 按钮能点。
3. 信息更清楚。
4. 分析流程更可信。
5. 结果更容易阅读。
6. 导出更明确。
7. 代码更容易维护。
8. 所有既有功能不倒退。

如果视觉升级和功能稳定发生冲突，优先保留功能稳定。
