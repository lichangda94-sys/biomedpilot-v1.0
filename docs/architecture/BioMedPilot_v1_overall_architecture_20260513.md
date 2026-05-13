# BioMedPilot v1.0 Overall Architecture

日期：2026-05-13

范围：`/Users/changdali/Developer/biomedpilot v1.0/MainLine`

本文件记录 BioMedPilot / 医研智析 v1.0 的本地多工作区结构、MainLine 与模块工作区关系、集成规则和打包前检查规则。它是架构与流程确认文档，不代表本阶段执行了目录迁移、代码重构或功能开发。

## 当前真实状态

### Worktree 列表

当前 `git --git-dir="../_repo.git" worktree list` 输出确认：

| 路径 | 分支 | 当前 HEAD |
| --- | --- | --- |
| `/Users/changdali/Developer/biomedpilot v1.0/_repo.git` | bare repository | 不直接修改代码 |
| `/Users/changdali/Developer/biomedpilot v1.0/MainLine` | `stable/mainline` | `84ebda8` |
| `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics` | `dev/bioinformatics` | `35e3686` |
| `/Users/changdali/Developer/biomedpilot v1.0/Meta` | `dev/meta-analysis` | `f4d8f95` |
| `/Users/changdali/Developer/biomedpilot v1.0/Vocabulary` | `dev/shared-vocabulary` | `d3feac3` |
| `/Users/changdali/Developer/biomedpilot v1.0/UIShell` | `dev/ui-shell` | `391c882` |
| `/Users/changdali/Developer/biomedpilot v1.0/LabTools` | `dev/labtools` | `0e4a4a9` |
| `/Users/changdali/Developer/biomedpilot v1.0/AI` | `dev/ai-gateway` | `2a2d1da` |
| `/Users/changdali/Developer/biomedpilot v1.0/Integration` | `dev/integration` | `9b94980` |
| `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild` | `dev/release-internal-test` | `67e5b13` |

### MainLine 状态

- 当前分支：`stable/mainline`
- Stage 0.6 开始时 HEAD：`84ebda8 docs(mainline): record current baseline`
- 最近主线阶段提交：
  - `84ebda8`：MainLine 当前基线确认。
  - `def9152`：缓存清理和 `.gitignore` 加固。
  - `daca0fe`：旧 Markdown 归档。
  - `6334a7a`：全局开发手册创建。
  - `ca54434`：仓库内容审计。

### MainLine 主要目录

当前 MainLine 已存在：

- `app/`
- `tests/`
- `docs/`
- `scripts/`
- `data/`
- `assets/`

当前 `data/` 内只确认到 `data/package_manifest.json`。

当前 `docs/` 内确认到：

- `docs/archive/`
- `docs/cleanup/`
- `docs/handoff/`
- `docs/meta_dev_reports/`
- `docs/migration/`
- `docs/user_testing/`

本阶段新增的架构文档位于 `docs/architecture/`。

### MainLine app 目录状态

当前存在：

- `app/shell/`
- `app/bioinformatics/`
- `app/meta_analysis/`
- `app/shared/`

当前不存在：

- `app/labtools/`
- `app/lab_tools/`
- `app/lab/`

因此 LabTools 在 MainLine 内目前不是已接入代码目录；它是独立 `LabTools` worktree 的开发方向。后续如需在 MainLine 接入 `app/labtools/`，必须经模块开发、测试和集成验证，不应在文档阶段创建业务代码。

### Ignored cache 状态

当前工作区可能存在测试运行生成的 ignored cache，例如 `.pytest_cache/` 和 `__pycache__/`。这些不是架构目录，不应作为推荐结构解释；它们已由 `.gitignore` 覆盖。本阶段按“不删除文件”要求不处理缓存。

## 本地开发总文件夹与 MainLine 的区别

`/Users/changdali/Developer/biomedpilot v1.0` 是开发管理层。它包含：

- bare repository：`_repo.git`
- 多个 worktree
- 迁移 bundle、总控文档、交接文档和归档材料

`/Users/changdali/Developer/biomedpilot v1.0/MainLine` 是稳定主线代码工作区。它用于维护当前可测试的主应用壳、稳定入口、shared 接口和稳定主流程，不等同于整个开发管理层。

`_repo.git` 是 bare repository，只保存 Git 对象、refs 和 worktree 管理信息，不直接编辑代码，不直接作为开发目录。

## 各 worktree 职责

### MainLine

MainLine 是稳定主干。职责包括桌面壳、登录、模块选择、设置、测试模式、稳定入口、shared 接口、Bioinformatics 稳定主流程、Meta 最小入口和当前可测试基线。

MainLine 不承载未经集成验证的大功能开发。

### Bioinformatics

Bioinformatics worktree 用于生信模块开发。范围包括 GEO / TCGA / GTEx / 本地表达数据的检索、导入、识别、标准化、分析准备、任务中心、结果和报告辅助。

Bioinformatics 不做 PubMed 文献检索，不承载 Meta 文献检索策略和筛选流程。

### Meta

Meta worktree 用于系统评价和 Meta 分析模块开发。范围包括 PICO / PICOS / PECO、检索策略、文献库、去重、标题摘要筛选、全文管理、全文资格判断、提取、质评、统计和报告。

Meta 不做 GEO / TCGA / GTEx 表达数据分析。

### LabTools

LabTools worktree 用于基础实验工具模块，例如稀释、浓度、qPCR、Western blot、ELISA、细胞计数和实验记录辅助。

LabTools 不应污染 Bioinformatics 或 Meta project manifest，不应把实验工具流程伪装成生信或 Meta 分析项目。

### UIShell

UIShell worktree 用于登录、主窗口、模块选择、导航、主题、视觉统一和可用性改进。

UIShell 不改业务逻辑，不改变 Bioinformatics、Meta、LabTools、AI 或 Vocabulary 的业务边界。

### Vocabulary

Vocabulary worktree 用于共享医学词库、query intelligence、上下文隔离、术语审计和测试。

Vocabulary 提供共享能力，不承载 Bioinformatics 或 Meta 的具体业务流程。

### AI

AI worktree 用于 AI Gateway、本地模型接入、隐私策略、审计策略和默认关闭的 AI 能力。

AI 不得绕过 AI Gateway，不保存 raw prompt / raw response，不自动执行下载、筛选、分析或最终报告。

### Integration

Integration worktree 用于阶段性合并验证、冲突处理、跨模块测试和全量或阶段性验证。

Integration 不做大功能开发；它的主要职责是验证模块成果能否进入稳定主线。

### ReleaseBuild

ReleaseBuild worktree 用于内部测试版打包、打包 smoke test、包内 metadata 验证和发布前检查。

ReleaseBuild 不做功能开发，不从未经集成验证的单一模块分支直接发布内部测试版。

### Archive、00_HandoffDocs、01_ProjectControl

- `Archive/`：存放迁移 bundle、历史快照、旧材料或外部归档，不是当前开发入口。
- `00_HandoffDocs/`：可用于跨阶段交接材料，具体使用需与当前 handoff 体系保持一致。
- `01_ProjectControl/`：本地总控文档、迁移报告、总开发手册和阶段控制材料所在地；它是开发管理层的一部分，不等同于 MainLine Git worktree。

## MainLine 与模块工作区的关系

模块功能可以在各自 worktree 中开发，但进入稳定主线前应遵循以下顺序：

1. 在模块 worktree 中完成范围内开发。
2. 在模块 worktree 中运行对应测试。
3. 更新模块阶段报告、handoff 或审计文档。
4. 进入 Integration worktree 做合并验证或等效集成验证。
5. Integration 验证通过后，再进入 MainLine 作为稳定主线候选。
6. 需要内部测试包时，再从已验证的 MainLine 或 ReleaseBuild 产出。

不允许从未经集成验证的单一功能分支直接作为正式内部测试版发布。

## 进入 MainLine 的条件

模块成果进入 MainLine 前必须满足：

- 模块自身测试通过。
- 相关 UI 或集成测试通过。
- 无跨模块污染。
- 不改变业务边界，例如不把 PubMed 混入 Bioinformatics，不把 GEO / TCGA / GTEx 混入 Meta。
- 文档、阶段报告或 handoff 已更新。
- `draft`、`dry-run`、`testing-level`、`imported result`、`real computed result` 标记清楚。
- 没有绕过 AI Gateway。
- 没有保存 raw prompt / raw response。
- 没有把测试级功能描述为 production-ready、临床级或投稿级能力。
- 没有把用户项目数据、下载数据、PDF、中间分析结果、缓存或打包产物引入 Git。

## 集成规则

- MainLine 保持稳定可测试，不作为大功能试验场。
- Integration 承担跨模块合并、冲突处理、测试矩阵和回归验证。
- 模块 worktree 的开发结果应以清晰 commit、阶段报告和测试结果进入 Integration。
- 如果集成中出现模块边界冲突、数据契约冲突、AI / 网络启用争议、测试失败且修复方向不唯一，应停止并请求人工确认。
- ReleaseBuild 只接收已验证的稳定来源，不直接吸收未验证功能分支。

## 打包前必须考虑

内部测试包或 ReleaseBuild 打包前必须记录并核对：

- `git_head`
- `branch`
- `build_time`
- `app_version`
- `enabled_modules`
- `feature_flags`
- Developer Preview / internal beta 标记
- smoke test 结果
- 是否包含未完成或测试级功能
- 是否存在 dry-run、testing-level、imported result、real computed result 的清晰标记
- 是否存在需要隐藏到开发者诊断区的 manifest、schema、branch、raw path、asset id

内部测试版不得声称 production-ready、clinical-grade 或 submission-grade。

## 数据、缓存和 Git 规则

- 用户项目数据默认不进入 Git。
- 下载数据集默认不进入 Git。
- PDF 默认不进入 Git。
- 中间分析结果默认不进入 Git。
- 缓存和打包产物默认不进入 Git。
- `tests/fixtures/` 可保留小型、可解释、可复现的测试数据。
- demo projects 如存在，应保持小型、可追踪、可解释。
- tracked logs、示例项目、旧快照和 legacy 资料属于人工确认项，不能在普通清理任务中直接删除。

## AI 和网络规则

- AI 默认关闭。
- 本地模型和外部模型只能通过 AI Gateway。
- 外部网络能力必须按模块声明，并默认要求用户确认。
- AI 只能生成草稿或建议，不能自动下载、筛选、分析或生成最终报告。
- 不保存 raw prompt / raw response。
- AI、网络、下载、筛选、分析或最终报告能力的启用属于人工审核边界。

## 主界面暴露原则

主界面不得暴露大量 manifest、schema、branch、raw path、asset id 或调试细节。

这些信息如确有必要，只能放入开发者诊断区、日志审计、报告 manifest 或 handoff 文档中，并应避免干扰普通用户流程。
