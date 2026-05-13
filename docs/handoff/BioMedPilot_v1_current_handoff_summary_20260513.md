# BioMedPilot v1.0 Current Handoff Summary

生成时间：2026-05-13 16:15:11 CST

用途：给后续 Codex、ChatGPT 或人工继续 BioMedPilot v1.0 开发前快速恢复当前总控上下文。本文件是摘要入口，不替代 `Global_Development_Manual.md`。

## 1. 当前 v1.0 主目录结构

BioMedPilot v1.0 当前本地主目录：

```text
/Users/changdali/Developer/biomedpilot v1.0
```

该目录是外层开发管理目录，不是普通 Git worktree。它包含 bare repository、多 worktree、迁移备份、总控文档、handoff 文档和归档材料。

| 路径 | 当前职责 |
| --- | --- |
| `_repo.git` | bare repository；只保存 Git 对象、refs 和 worktree 管理信息，不直接编辑代码。 |
| `MainLine` | `stable/mainline`；稳定主线、桌面 shell、登录、模块选择、稳定入口、shared 接口、Bioinformatics 稳定流程、Meta 最小入口和当前可测试基线。 |
| `Bioinformatics` | `dev/bioinformatics`；GEO / TCGA / GTEx / 本地表达数据相关生信模块开发，不做 PubMed 文献检索。 |
| `Meta` | `dev/meta-analysis`；PICO、检索策略、文献库、去重、筛选、全文、提取、质评、统计和报告，不做 GEO / TCGA / GTEx 表达数据分析。 |
| `Vocabulary` | `dev/shared-vocabulary`；共享医学词库、query intelligence、上下文隔离、术语审计和测试。 |
| `UIShell` | `dev/ui-shell`；登录、主窗口、模块选择、导航、主题、视觉统一和可用性，不改业务逻辑。 |
| `LabTools` | `dev/labtools`；实验工具模块，承载浓度计算、单位换算、配方检索、图像分析等未来能力，不混入 Bioinformatics 或 Meta。 |
| `AI` | `dev/ai-gateway`；AI Gateway、本地模型接入、隐私策略、审计策略和默认关闭的 AI 能力。 |
| `Integration` | `dev/integration`；跨模块集成验证、冲突处理和阶段性测试，不直接承载新业务开发。 |
| `ReleaseBuild` | `dev/release-internal-test`；内部测试打包、包 metadata 验证和 packaged smoke test，不直接开发业务功能。 |
| `Archive` | 迁移 bundle、历史快照、旧材料和外部归档材料。 |
| `00_HandoffDocs` | 跨阶段交接材料。 |
| `01_ProjectControl` | 本地总控文档、迁移报告、总开发手册和阶段控制材料。 |

## 2. 当前最高优先级规则文件

最高优先级规则文件：

- `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/handoff/Global_Development_Manual.md`

规则：

- `01_ProjectControl/Global_Development_Manual.md` 是最高优先级开发规则。
- `MainLine/docs/handoff/Global_Development_Manual.md` 是 MainLine handoff 同步副本。
- 两者必须保持字节级同步。
- 如果任务、模块 handoff、阶段报告、branch note 或记忆与总手册冲突，Codex 必须停止并向人工报告。

本次检查结果：

```text
cmp_exit=0
```

## 3. 当前已完成的主控层工作

已完成：

- v1.0 迁移：建立新本地主目录、bare repo、多 worktree、迁移 bundle 和分支结构。
- MainLine P0 修复：`BioinformaticsWorkspaceWidget(on_back=...)` 初始化兼容问题已修复。
- Stage 0.2 repository cleanup audit：完成 MainLine 内容审计，确认当前有效测试、legacy、AI Gateway、词库接口和项目流程依赖不能直接删除。
- Stage 0.3 legacy Markdown archive：99 个旧 Markdown 审计、阶段报告、迁移说明和交接文件已归档到 `docs/archive/legacy_handoff_20260513/`，删除文件 0。
- Stage 0.4 cache/build cleanup：清理 ignored / untracked cache，加固 `.gitignore`，tracked logs 保留为人工确认项。
- Stage 0.5 baseline confirmation：确认 MainLine baseline、测试基线和总手册同步状态。
- Stage 0.6 architecture and integration rules：记录 v1.0 总体架构、多 worktree 关系、Integration / ReleaseBuild 规则和进入 MainLine 条件。
- UI Stage 0.1-0.8 governance and convergence：完成跨模块 UI governance、shared UI tokens/helper、Shell / Bioinformatics / Meta 视觉收敛，以及 LabTools 未来接入规范和工具型页面模板。
- Global development governance 补强：补齐文件权威性、开发前检查、禁止事项、停止事项、AI/网络/隐私、真实执行器、医学科研安全、LabTools 边界、报告写作、打包和 release wording。
- Dirty worktree state audit：确认当前未提交改动层面所有 worktree clean。

### UI Stage 0.1-0.8 状态

当前 UI 开发脉络：

| Stage | Commit | 状态 |
| --- | --- | --- |
| UI Stage 0.1 | `bf33f07 docs(ui): audit cross-module ui governance` | 已确立 UI Governance / UI Design Principles，并写入 Global Development Manual。 |
| UI Stage 0.2 | `d981a9e feat(ui): add shared ui tokens foundation` | 已建立 shared UI tokens/helper 基础层。 |
| UI Stage 0.3 | `b8409ec refactor(ui): pilot shared token qss migration` | 已完成 Shell 和 Bioinformatics 入口页 shared token QSS 试点。 |
| UI Stage 0.4 | `6e2cfbb feat(ui): add shared status and button style helpers` | 已新增 shared status badge、button role QSS helpers、section card 和 diagnostic card helper。 |
| UI Stage 0.5 | `1dceec0 refactor(ui): converge bioinformatics flow page styles` | 已收敛 4 个 Bioinformatics 轻量流程页 UI。 |
| UI Stage 0.6 | `4e5c4ac refactor(ui): converge bioinformatics task result report pages` | 已收敛 Bioinformatics 分析任务中心、结果页、报告页按钮层级和技术字段暴露。 |
| UI Stage 0.7 | `327c63c refactor(ui): audit and converge meta ui styles` | 已收敛 MainLine Meta 最小入口；主状态不再直接暴露完整项目路径、manifest、内部状态和开发分支名。 |
| UI Stage 0.8 | `8045864 feat(ui): add tool page shared style helpers` | 已定义 LabTools UI 接入规范和工具型页面模板，新增通用工具页 card QSS helper，未创建 LabTools 业务代码。 |

UI 总规范恢复入口：

- `docs/ui/BioMedPilot_UI_Governance_Audit_20260513.md`
- `docs/ui/BioMedPilot_UI_Design_Principles_20260513.md`
- `docs/ui/BioMedPilot_UI_Tokens_And_Components_Audit_20260513.md`
- `docs/ui/BioMedPilot_UI_Stage_0_8_LabTools_UI_Integration_Template_20260513.md`

当前边界：LabTools 未来必须作为 MainLine Shell 内模块接入，使用 shared UI tokens、status badge、button role 和工具型页面模板；不得自建独立主色、独立导航、独立窗口框架或独立按钮体系；不得污染 Bioinformatics 或 Meta project manifest。

## 4. 当前关键 commit 摘要

MainLine 当前分支：`stable/mainline`

MainLine 当前 HEAD（本 handoff 同步前）：

```text
11d6454 docs(mainline): audit meta merge preparation
```

关键提交：

| Commit | 摘要 |
| --- | --- |
| `11d6454` | `docs(mainline): audit meta merge preparation`；新增 Meta mainline merge preparation 审计报告。 |
| `8045864` | `feat(ui): add tool page shared style helpers`；UI Stage 0.8 LabTools UI 接入规范和工具型页面 helper。 |
| `327c63c` | `refactor(ui): audit and converge meta ui styles`；UI Stage 0.7 Meta 最小入口视觉收敛。 |
| `4e5c4ac` | `refactor(ui): converge bioinformatics task result report pages`；UI Stage 0.6 Bioinformatics 任务、结果、报告 UI 收敛。 |
| `1dceec0` | `refactor(ui): converge bioinformatics flow page styles`；UI Stage 0.5 Bioinformatics 轻量流程页 UI 收敛。 |
| `6e2cfbb` | `feat(ui): add shared status and button style helpers`；UI Stage 0.4 shared status/button/page structure helper。 |
| `4bd6732` | `docs(project): audit dirty worktree state`；新增 worktree dirty state 审计报告。 |
| `f68d2b5` | `docs(project): strengthen global development governance`；补强全局开发治理并新增 global control audit。 |
| `b8409ec` | `refactor(ui): pilot shared token qss migration`；MainLine UI token / QSS 迁移推进。 |
| `d981a9e` | `feat(ui): add shared ui tokens foundation`；shared UI tokens 基础。 |
| `bf33f07` | `docs(ui): audit cross-module ui governance`；跨模块 UI governance 审计。 |
| `fdc83c1` | `docs(mainline): define v1 architecture rules`；Stage 0.6 架构与集成规则。 |
| `84ebda8` | `docs(mainline): record current baseline`；Stage 0.5 当前基线确认。 |
| `def9152` | `chore(mainline): clean caches and harden gitignore`；Stage 0.4 cache/build cleanup。 |
| `daca0fe` | `docs(mainline): archive legacy markdown handoff reports`；Stage 0.3 legacy Markdown archive。 |
| `6334a7a` | `docs(mainline): add global development manual`；总开发手册创建。 |
| `ca54434` | `docs(mainline): add repository cleanup audit`；Stage 0.2 cleanup audit。 |
| `f295672` | `fix(mainline): restore bioinformatics workspace initialization`；MainLine P0 修复。 |

## 5. 当前 worktree clean 状态

本次检查命令：

```bash
for d in MainLine Bioinformatics Meta Vocabulary UIShell LabTools AI Integration ReleaseBuild; do
  printf '\n[%s]\n' "$d"
  git -C "$d" status --short
done
```

当前结果：

```text
[MainLine]
clean before this summary was created

[Bioinformatics]
clean

[Meta]
clean

[Vocabulary]
clean

[UIShell]
clean

[LabTools]
clean

[AI]
clean

[Integration]
clean

[ReleaseBuild]
clean
```

本 summary 创建后，MainLine 只应出现本文件新增。

## 6. 当前禁止事项摘要

后续任务默认禁止：

- 不得跨模块污染。
- 不得绕过 AI Gateway。
- 不得默认联网、默认调用外部 API、默认下载外部资源。
- 不得保存 raw prompt / raw response。
- 不得伪造 DEG、统计结果、图、筛选决定、PRISMA counts 或报告。
- 不得把 dry-run、preflight、imported、draft、testing-level 表述为 real computed result。
- 不得把 testing-level 功能表述为 production-ready、clinical-grade 或 submission-grade。
- 不得把 PubMed 文献检索混入 Bioinformatics。
- 不得把 GEO / TCGA / GTEx 表达数据分析混入 Meta。
- 不得把 LabTools 功能混入 Bioinformatics 或 Meta manifest。
- 不得未经授权 push、merge、force push、删除远程分支或处理凭据。
- 不得未经授权删除当前有效测试、legacy directories、audit reports、handoff docs 或其他高风险文件。

## 7. 必须人工汇报事项摘要

出现以下情况必须停止并向人工汇报：

- 需要跨模块修改。
- 需要把模块工作合入 MainLine。
- 需要真实 Bioinformatics 执行器接入。
- 需要真实 Meta 统计执行器接入。
- 需要启用外部 API、网络、外部数据库检索、外部下载或 AI / local model 能力。
- 需要保存 raw prompt、raw response、敏感原文、凭据、患者级数据、PDF、下载数据集或全文。
- 测试失败且无法在当前任务范围内安全修复。
- 需要 Git 凭据、远程 push、merge conflict 处理、force push、远程分支删除、迁移或高风险清理。
- 当前路径、worktree 或分支与任务预期不一致。
- `git status --short` 出现与任务相关的未知未提交改动。

## 8. 各模块下一步建议

### Bioinformatics

继续 B1D 或后续用户化流程。优先推进分析任务中心、结果浏览、报告页面用户化，保持 GEO / TCGA / GTEx / 本地表达数据边界，不混入 PubMed / Meta 文献检索。

### Meta

继续 M4 title/abstract screening、fulltext management、eligibility 和 PRISMA screening counts。保持研究治理：筛选、全文资格、提取、质评和最终统计/解释必须由人工确认。

### Vocabulary

先处理 V0.1 合入阻塞和词库资源包内策略，特别是 sqlite / `data/medical_terms` 是否随包进入 MainLine、如何控制体积、如何保持上下文隔离和 audit。

### UIShell

继续 UI token / QSS 迁移和跨模块视觉统一。遵守 Apple-like macOS premium biomedical research desktop software 方向，使用统一 Shell、统一色板、shared UI tokens，不创建模块私有主题体系。后续清理上下文时，应从本文件的 UI Stage 0.1-0.8 状态和 `docs/ui/` 阶段报告恢复 UI 开发脉络。

### AI Gateway

继续保持统一入口和隐私审计。AI 默认关闭；本地模型、外部模型和任何模型调用都必须经过 AI Gateway；不保存 raw prompt / raw response；只允许草稿或建议，不自动下载、筛选、分析或生成最终报告。

### LabTools

先按 UI Stage 0.8 的工具型页面模板设计 LabTools 页面，再进入 L0 + L1A。LabTools 独立承载浓度计算、单位换算、配方检索、ImageJ / Fiji / OpenCV 图像分析、划痕实验、细胞计数、荧光强度和灰度值分析等能力，不得混入 Bioinformatics 或 Meta。MainLine 当前仍没有 `app/labtools/`，也没有 LabTools Shell 入口；未来接入前应先在 LabTools 独立 worktree 完成模块开发与测试，再经 Integration 或等效验证进入 MainLine。

### Integration

仅用于跨模块集成验证、冲突处理和测试矩阵确认，不直接承载新业务开发。模块成果进入 MainLine 前，应先经过 Integration 或等效集成验证。

### ReleaseBuild

仅用于打包验证、包 metadata 检查和 packaged smoke test，不直接开发。内部测试包应来自已验证 MainLine 或已验证 release source，不能从未经集成验证的单一模块 worktree 直接产出。

## 9. 当前未完成或需人工确认事项

- GitHub push 仍需本地凭据或 SSH 权限；当前不得自动 push。
- tracked logs 是否保留、归档、删除或停止跟踪仍需人工确认。
- LabTools 业务模块开发仍需在独立 worktree 中启动；MainLine 目前只完成 UI Stage 0.8 接入规范和通用工具页 helper。
- Vocabulary sqlite / `data/medical_terms` 包内策略仍需明确。
- 真实分析执行器接入门槛仍未进入实现阶段。
- 真实 Meta 统计执行器升级或替换仍需方法、验证数据和人工确认。
- 外部 API、联网检索、数据库下载、PDF/full text 下载和外部模型启用仍需显式授权。
- 保存 raw prompt / raw response、敏感原文、凭据、患者级数据、下载数据集或全文仍需隐私审查。
- MainLine、Integration、ReleaseBuild 的合入和打包边界仍需按总手册执行。

## 10. 后续使用说明

新对话、新 Codex 任务或人工接手时，建议先读：

1. 本文件：`MainLine/docs/handoff/BioMedPilot_v1_current_handoff_summary_20260513.md`
2. `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
3. `MainLine/docs/handoff/Global_Development_Manual.md`
4. 当前任务相关 worktree 的 `CODEX.md`
5. 当前任务相关的最新 handoff / audit / baseline / architecture 文档
6. UI 相关任务还应读取 `MainLine/docs/ui/BioMedPilot_UI_Stage_0_8_LabTools_UI_Integration_Template_20260513.md` 以及前序 UI Stage 报告。

如果上下文过长或新会话失去历史，应以上述文件恢复项目状态，而不是依赖聊天记忆。

继续任何任务前，必须重新运行：

```bash
pwd
cmp "01_ProjectControl/Global_Development_Manual.md" "MainLine/docs/handoff/Global_Development_Manual.md"
for d in MainLine Bioinformatics Meta Vocabulary UIShell LabTools AI Integration ReleaseBuild; do
  printf '\n[%s]\n' "$d"
  git -C "$d" status --short
done
```

## 11. 本次验证

本次同步只修改 MainLine handoff Markdown 文档，未修改业务代码、测试、运行配置、打包脚本或模块 worktree。因本轮承接 UI Stage 0.8，总控 handoff 更新后仍按 UI Stage 0.8 要求执行 MainLine smoke 和 UI 测试。

已执行：

```bash
pwd
git status --short
git diff --check
git diff --cached --check
python3 -m app.main --smoke-test
python3 -m pytest tests/ui/test_shared_ui_theme.py -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

结果摘要：

- 当前路径：`/Users/changdali/Developer/biomedpilot v1.0/MainLine`
- MainLine diff：仅本 handoff 文件修改。
- `git diff --check`：通过。
- `git diff --cached --check`：通过。
- `python3 -m app.main --smoke-test`：通过；`git_head=11d6454`，`workspace_entries=2`，`bioinformatics_features=5`，`meta_analysis_features=9`，`pyside6_available=True`。
- `python3 -m pytest tests/ui/test_shared_ui_theme.py -q`：7 passed。
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`：144 passed。
- 未 push。
