# BioMedPilot Project Control Constitution v2

日期：2026-05-29  
文件用途：替换原 `docs/project-control/PROJECT_CONTROL_CONSTITUTION.md`  
适用范围：BioMedPilot v1.0 后期开发、UI Shell 基线确定、模块页面迁移、旧功能回收、MainLine 同步、ReleaseBuild 前治理。

---

## 0. Codex 执行摘要

从本文件生效后，所有 Project Control 工作必须按照本宪法执行。

当前最新核心判断：

```text
9d4edf3 是用户认可的 UI Shell / 视觉基线。
9d4edf3 不是功能完整基线。
stable/mainline 是稳定主线，但不是当前目标 UI 的完整来源。
dev/integration 是集成层，但当前 HEAD 也不等同于用户认可的 9d4edf3 preview。
```

因此，后续开发不能再简单地问：

```text
是否把某个分支合进 MainLine？
```

而必须先问：

```text
这个改动属于 UI Shell、Feature Page、Runtime、测试、文档、打包，还是运行数据？
它的最好来源在哪里？
它是否已接入 UI route？
它是否只是旧页面、空按钮或 placeholder？
它是否会造成版本回退？
```

---

## 1. 当前事实基线

### 1.1 用户认可的 UI Preview

用户认可的正确 UI preview 来源为：

```text
/Users/changdali/Developer/biomedpilot v1.0/Integration/dist/BioMedPilot Integration Preview.app
```

该 `.app` 的身份信息：

```text
app_root:
/Users/changdali/Developer/biomedpilot v1.0/Integration/dist/BioMedPilot Integration Preview.app/Contents/Resources/app

git_head:
9d4edf3

launch_mode:
packaged-local-python
```

`9d4edf3` 所属分支：

```text
codex/integration-labtools-ui-c2-carryover
```

明确事实：

```text
9d4edf3 不是 dev/integration 的祖先。
9d4edf3 不是 stable/mainline 的祖先。
```

### 1.2 用户认可的部分

`9d4edf3` 中可作为目标 UI Shell / 视觉基线的部分包括：

```text
Welcome
首页视觉框架
About
Sidebar
三大模块首页视觉框架
部分 Settings / release gate / shell 结构
shared UI primitives
```

### 1.3 用户不认可或未完成的部分

`9d4edf3` 不得作为功能完整版本。已确认问题包括：

```text
Bioinformatics 模块首页有，但后续按钮基本没有真实页面或点击无反应。
Meta Analysis 模块首页有，但后续按钮基本没有真实页面或点击无反应。
LabTools 有分页面和模块页面，但很多是旧版本页面，不是最终 Figma/new UI 页面。
首页 Project Management 退化成图片，不是旧版完整项目设置 / 导入文件 / 历史项目模块。
可能存在 LabTools 已开发页面未被查找、未整合、未迁移。
```

---

## 2. 宪法核心原则

### 2.1 Shell 与功能分离

从现在起，BioMedPilot 必须把以下四类基线分开治理：

| Baseline | 含义 | 当前判断 |
| --- | --- | --- |
| UI Shell Baseline | 欢迎页、首页、About、Sidebar、模块首页视觉框架 | 以 `9d4edf3` preview 为主要参考 |
| Feature Page Baseline | 每个模块具体功能页 | 不能以 `9d4edf3` 为准，需逐项找最好来源 |
| Runtime Baseline | 实际计算、分析、导出、报告、artifact 生成能力 | 以当前测试通过且有 artifact 的 service/runtime 为准 |
| MainLine Baseline | 稳定主线代码 | 当前为 `stable/mainline`，但 UI 不完整 |

禁止把四类基线混为一谈。

### 2.2 9d4edf3 的边界

允许：

```text
把 9d4edf3 作为 UI Shell / 视觉风格 / 首页框架参考。
```

禁止：

```text
把 9d4edf3 当成功能完整版本。
整支合并 9d4edf3 所在分支。
直接 cherry-pick 9d4edf3。
把 LabTools 旧页面或空按钮视为完成。
把 Project Management 图片视为完整项目管理模块。
```

### 2.3 MainLine 的边界

`stable/mainline` 是稳定主线，但不是 UI 目标版本的完整来源。

进入 MainLine 的任何功能必须有：

```text
来源
文件范围
UI route
handler
runtime/service
artifact
test
文档
audit
```

否则只能标记为：

```text
待迁移
部分接入
placeholder
old-page
missing
```

不得标记为完成。

---

## 3. 当前优先级

当前不应继续盲目执行 MainLine Meta L3 文件移植。新的优先级为：

### P0：写入 Project Control Constitution v2

必须覆盖或生成：

```text
docs/project-control/PROJECT_CONTROL_CONSTITUTION.md
```

### P1：建立 UI Shell Baseline Decision

必须生成：

```text
docs/project-control/UI_SHELL_BASELINE_DECISION.md
```

目标：记录为什么 9d4edf3 是 Shell baseline，但不是功能 baseline。

### P2：建立 UI Route Feature Inventory

必须生成：

```text
docs/project-control/UI_ROUTE_FEATURE_INVENTORY.md
```

目标：盘点每个模块首页按钮、handler、目标页面、runtime、测试、页面风格。

### P3：恢复 Project Management

必须生成：

```text
docs/project-control/PROJECT_MANAGEMENT_RESTORE_PLAN.md
```

目标：查找旧版完整项目设置 / 导入文件 / 历史项目模块，制定 scoped 恢复计划。

### P4：LabTools Reconciliation

必须生成：

```text
docs/project-control/LABTOOLS_RECONCILIATION_LEDGER.md
```

目标：查找 LabTools 已开发页面、旧页面、新设计页面、未接入页面、缺失 runtime 和测试。

### P5：MainLine Migration Ledger

必须生成：

```text
docs/project-control/MAINLINE_MIGRATION_LEDGER.md
```

目标：记录每一次进入 MainLine 的迁移来源、文件范围、测试、审计和边界。

---

## 4. 禁止事项

在完成 P0-P5 前，禁止：

```text
继续 MainLine Meta L3 实际移植
整支合并 dev/integration 到 stable/mainline
整支合并 dev/bioinformatics 到 stable/mainline
整支使用 9d4edf3
cherry-pick 9d4edf3
把当前 stable/mainline UI 视为目标 UI
把 9d4edf3 视为功能完整版本
把按钮存在视为功能完成
把旧页面视为最终页面
把图片替代的 Project Management 视为完整模块
```

任何任务都禁止触碰：

```text
project_storage/
```

除非用户明确要求处理运行数据。

---

## 5. 分支角色定义

### 5.1 `stable/mainline`

稳定主线。

规则：

1. 不直接接收长期分叉分支整支合并。
2. 不直接合并 `dev/integration`。
3. 不直接合并 `dev/bioinformatics`。
4. 不直接合并 `codex/integration-labtools-ui-c2-carryover`。
5. 只接收 scoped plan 验证过的内容。
6. 每次接收后必须生成 post-merge audit。

### 5.2 `dev/integration`

集成验证层。

规则：

1. 可承接 scoped 功能移植。
2. 可作为跨模块验证层。
3. 不等同于 MainLine。
4. 不等同于 9d4edf3 UI preview。
5. 每次合入都必须有边界记录。

### 5.3 `codex/integration-labtools-ui-c2-carryover`

当前用户认可 UI preview 的源码来源分支之一。

规则：

1. 只能作为 UI Shell baseline 来源。
2. 不得整支合入。
3. 不得直接 cherry-pick `9d4edf3`。
4. 其中 LabTools / Bioinformatics / dependency / package 等内容必须单独审计。

### 5.4 模块分支

包括但不限于：

```text
dev/bioinformatics
dev/labtools
dev/meta-analysis
dev/ui-shell
dev/release-internal-test
```

规则：

1. 可作为 Feature Page 或 Runtime 最好来源。
2. 进入 Integration 或 MainLine 前必须 scoped plan。
3. 不能整支直接进入 MainLine。

### 5.5 audit 分支

命名：

```text
audit/*
```

规则：

1. 只读审计。
2. 不修改业务代码。
3. 不 merge。
4. 不 cherry-pick。
5. 不提交功能。
6. 可生成审计文档。

### 5.6 scoped migration 分支

命名：

```text
mainline/*-scoped-pick
integration/*-scoped-pick
```

规则：

1. 只能修改批准文件。
2. 禁止 `git add .`。
3. 禁止触碰 `project_storage/`。
4. 必须验证后才能提交。

---

## 6. UI Route 完整性标准

一个 UI 功能只有同时满足以下条件，才可标记为 `connected`：

```text
有用户可见入口
有 objectName 或测试可定位方式
入口连接到 handler
handler 打开目标页面或调用 runtime
目标页面存在
runtime/service 存在
有 artifact、状态或可见输出
有 UI 测试或至少 route 测试
文档注明功能等级
```

可用状态仅限：

| Status | 含义 |
| --- | --- |
| connected | UI → handler → page/runtime → artifact/test 完整 |
| partial | 有部分链路，但不完整 |
| placeholder | 明确占位 |
| empty-button | 按钮存在但无有效响应 |
| missing-handler | 无 handler |
| missing-target-page | handler 指向页面缺失 |
| old-page | 可打开但为旧版页面 |
| figma/new | 符合新设计页面 |
| broken | 点击报错或阻断 |
| not migrated | 旧分支有，当前未迁移 |

禁止把 `partial`、`placeholder`、`empty-button`、`old-page` 写成完成。

---

## 7. 页面风格分级

所有功能页必须标记页面风格：

| Page Style | 含义 |
| --- | --- |
| figma/new | 符合新 Figma / 新 UI shell 设计 |
| old | 旧版功能页，暂可用但需改造 |
| hybrid | 新 shell 包旧内容 |
| placeholder | 占位页面 |
| missing | 页面缺失 |
| unknown | 未审计 |

LabTools 当前默认不能标记为 `figma/new`，除非逐页审计证明。

---

## 8. Project Management 特别规则

Project Management 是首页基础能力，不能用图片替代。

完整 Project Management 至少包括：

```text
项目创建
项目设置
导入文件
历史项目
最近项目
工作区/session 记录
项目路径或存储策略
用户可见状态
```

当前 9d4edf3 中 Project Management 退化为图片，因此必须标记为：

```text
regressed
```

必须生成：

```text
docs/project-control/PROJECT_MANAGEMENT_RESTORE_PLAN.md
```

恢复前不得称 MainLine 首页完整。

---

## 9. LabTools 特别规则

LabTools 是当前实际页面最多、但 UI 风格最混杂的模块。

必须生成：

```text
docs/project-control/LABTOOLS_RECONCILIATION_LEDGER.md
```

至少盘点：

```text
通用试剂计算器
试剂准备
Western Blot
SDS-PAGE
BCA
PCR/qPCR
ELISA
细胞实验记录
细胞图像分析
scratch assay
transwell
fluorescence/staining
ImageJ/Fiji 外部引擎入口
```

每项必须记录：

| Field | Required |
| --- | --- |
| Feature | yes |
| Best source branch/commit | yes |
| Current UI route | yes |
| Page style | figma/new / old / hybrid / placeholder / missing |
| Runtime exists | yes/no |
| Test exists | yes/no |
| Migration priority | P0/P1/P2/P3/blocked |

---

## 10. Meta / Bioinformatics 空按钮规则

Bioinformatics 和 Meta Analysis 当前三大模块首页如果存在按钮但没有后续页面，必须记录为：

```text
empty-button
missing-handler
missing-target-page
placeholder
```

不得写成 connected。

每个按钮必须查明：

```text
按钮文本
UI 文件
handler
目标页面
runtime/service
artifact
测试
最好来源分支
迁移策略
```

---

## 11. 功能资产清单制度

必须维护：

```text
docs/project-control/FEATURE_ASSET_INVENTORY.md
```

字段：

| 字段 | 说明 |
| --- | --- |
| Feature ID | 唯一编号 |
| 模块 | Meta / Bioinformatics / LabTools / Project / Shell / Release |
| 功能名称 | 用户可理解名称 |
| 当前最好来源分支 | branch |
| 当前最好来源 commit | hash |
| UI Shell 是否接入 | yes/no |
| Feature Page 是否存在 | yes/no |
| Page Style | figma/new / old / hybrid / placeholder / missing |
| Handler | path/name |
| Runtime/service | path/name |
| Artifact | report/table/plot/file/state/none |
| Test | path |
| Test Result | passed/failed/missing |
| MainLine 状态 | not migrated / scoped planned / migrated / validated / blocked |
| 风险 | 备注 |

---

## 12. UI Route Feature Inventory

必须维护：

```text
docs/project-control/UI_ROUTE_FEATURE_INVENTORY.md
```

字段：

| Module | UI Text | Source UI Baseline | File | objectName/handler | Click Result | Target Page | Runtime | Test | Status | Page Style |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

每个按钮/卡片/入口都必须登记。

---

## 13. Legacy Feature Triage

必须维护：

```text
docs/project-control/LEGACY_FEATURE_TRIAGE.md
```

旧功能分级：

| Level | 含义 | 处理 |
| --- | --- | --- |
| A | 当前主线已有且测试通过 | 保留 |
| B | 旧分支有，当前缺失，价值明确 | scoped 迁移候选 |
| C | 旧分支有，但依赖旧架构 | 只提取思想 |
| D | 假实现或过时 | 归档 |
| E | 不确定 | 建立审计任务 |

旧功能不得通过整支 merge 回流。

---

## 14. MainLine Migration Ledger

必须维护：

```text
docs/project-control/MAINLINE_MIGRATION_LEDGER.md
```

字段：

| 字段 | 说明 |
| --- | --- |
| Migration ID | 唯一编号 |
| 日期 | YYYY-MM-DD |
| 目标 | stable/mainline |
| 来源 | branch/commit/app bundle |
| 迁移类型 | shell / feature page / runtime / test / docs |
| 迁移方式 | scoped checkout / manual port / merge |
| 文件范围 | list |
| 禁止路径检查 | empty/non-empty |
| 验证命令 | list |
| 验证结果 | passed/failed |
| Audit report | path |
| 是否封口 | yes/no |

---

## 15. 迁移策略规则

### 15.1 整支 merge 允许条件

只有同时满足以下条件，才允许整支 merge：

```text
diff 范围小
merge-tree 无冲突
无高风险路径
无大规模删除
无 package/dependency/release 污染
目标分支没有更先进实现
有完整测试
不是长期分叉分支
```

否则禁止整支 merge。

### 15.2 cherry-pick 允许条件

只有同时满足以下条件，才允许 cherry-pick：

```text
commit 文件范围小
不夹带 unrelated changes
不涉及 forbidden paths
不覆盖目标分支新结构
冲突可预测
可安全 abort
```

否则使用文件级 checkout 或手工移植。

### 15.3 文件级 checkout 适用条件

适合：

```text
新增文档
新增测试
目标分支不存在的独立文件
小型独立配置
```

不适合：

```text
已有核心 UI 文件
已有 runtime/service
已有测试文件中包含主线独有断言
app/main.py
workflow_pages.py
package_app.py
requirements.txt
pyproject.toml
```

### 15.4 手工最小移植适用条件

适合：

```text
app/main.py
app/shell/*
workflow_pages.py
analysis_page.py
LabTools workspace/page files
Project Management
shared registries
dependency/build files
```

原则：

```text
只移植所需代码块，不整文件替换。
```

---

## 16. 版本回退防护

每次迁移后必须检查：

```bash
git diff --stat
git diff --name-status
git diff --check
```

禁止路径检查：

```bash
git diff --name-status | grep -E 'app/bioinformatics/|app/labtools/|app/meta_analysis/legacy/|scripts/package_app.py|requirements.txt|pyproject.toml|project_storage/' || true
```

如果出现未批准路径，默认阻断提交。

### 16.1 UI 回退判定

以下情况均视为回退：

```text
完整 Project Management 变成图片
新 shell 页面被旧页面覆盖
按钮从 connected 变成 empty-button
figma/new 页面变成 old 页面
runtime 变成 placeholder
测试断言被放宽
artifact 输出消失
```

---

## 17. 测试标准

最小验证：

```bash
python3 -m app.main --smoke-test
git diff --check
```

UI Shell 验证：

```text
Welcome / Home / Sidebar / About / Settings / Module Home
```

模块验证：

```text
Meta: statistics / UI workflow / result table / export / report
Bioinformatics: workflow pages / DEG / dependency checks / acquisition
LabTools: calculators / WB / SDS-PAGE / BCA / qPCR / cell records / image entry
Project: create / settings / import / history
Release: package smoke / bundle metadata / launcher
```

---

## 18. Codex 工作规范

每次任务开始必须输出：

```text
当前分支
当前 HEAD
git status --short
git stash list
本轮目标
允许路径
禁止路径
禁止命令
```

每次任务结束必须输出：

```text
实际改动文件
是否触碰禁止路径
测试命令结果
是否建议提交
下一条建议命令
```

Codex 未经用户确认不得执行：

```text
merge
cherry-pick
commit
reset --hard
git clean
git add .
继续切换分支做下一任务
```

---

## 19. 当前立即执行工作

当前应执行的工作不是继续 MainLine Meta L3 移植，而是生成 Project Control 文档：

```text
docs/project-control/PROJECT_CONTROL_CONSTITUTION.md
docs/project-control/UI_SHELL_BASELINE_DECISION.md
docs/project-control/UI_ROUTE_FEATURE_INVENTORY.md
docs/project-control/LABTOOLS_RECONCILIATION_LEDGER.md
docs/project-control/PROJECT_MANAGEMENT_RESTORE_PLAN.md
docs/project-control/MAINLINE_MIGRATION_LEDGER.md
docs/project-control/LEGACY_FEATURE_TRIAGE.md
```

本轮只生成文档，不修改业务代码。

---

## 20. Codex 替换旧宪法的执行指令

Codex 应执行：

```bash
mkdir -p docs/project-control
```

然后用本文件内容覆盖：

```text
docs/project-control/PROJECT_CONTROL_CONSTITUTION.md
```

并创建以下模板文件：

```text
docs/project-control/UI_SHELL_BASELINE_DECISION.md
docs/project-control/UI_ROUTE_FEATURE_INVENTORY.md
docs/project-control/LABTOOLS_RECONCILIATION_LEDGER.md
docs/project-control/PROJECT_MANAGEMENT_RESTORE_PLAN.md
docs/project-control/MAINLINE_MIGRATION_LEDGER.md
docs/project-control/LEGACY_FEATURE_TRIAGE.md
```

严格要求：

```text
不修改业务代码
不执行 merge
不执行 cherry-pick
不触碰 project_storage/
不提交
```

生成后输出：

```bash
git status --short
git diff --stat
git diff --name-status
```

并给出是否建议提交。

建议 commit message：

```text
docs(project-control): add constitution v2 for UI baseline governance
```

---

## 21. Historical UI Line Recovery Evidence

`docs/ui/UI线路既往检查.md` is the sealed historical UI line evidence document imported from UIShell into the software remediation control branch. It must be treated as evidence, not as migration authorization.

Recorded facts from that document:

```text
Preferred recovery source:
codex/integration-labtools-ui-c2-carryover

Recorded carryover HEAD:
e13d0f5f5dfda36a5c60a00ddc7820748fa1677f

Accepted packaged preview identity:
9d4edf3

Old dev/integration issue:
missing Bioinformatics / Meta Analysis / LabTools page commits
```

The recovery evidence lists Bioinformatics, Meta Analysis, LabTools, and shared UI foundation commits that may be useful for scoped recovery planning. These commits are not permission to merge or cherry-pick.

Governance rules:

1. Keep `9d4edf3` as UI Shell / packaged preview evidence only.
2. Keep `e13d0f5` and `codex/integration-labtools-ui-c2-carryover` as historical page recovery evidence only.
3. Do not merge whole `codex/integration-labtools-ui-c2-carryover`.
4. Do not cherry-pick historical UI commits without a scoped file list and conflict plan.
5. Do not treat recovered page presence as connected runtime.
6. Do not use LabTools recovered pages as final Figma/new pages until page-style audit passes.
7. Do not touch `project_storage/` during Project Control or recovery planning.

The detailed matrices live in:

```text
docs/project-control/UI_SHELL_BASELINE_DECISION.md
docs/project-control/UI_ROUTE_FEATURE_INVENTORY.md
docs/project-control/LABTOOLS_RECONCILIATION_LEDGER.md
docs/project-control/LEGACY_FEATURE_TRIAGE.md
docs/project-control/MAINLINE_MIGRATION_LEDGER.md
docs/project-control/PROJECT_MANAGEMENT_RESTORE_PLAN.md
docs/ui/UI线路既往检查.md
```
