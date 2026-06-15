# ReleaseBuild Handoff Report - 2026-05-13

## 1. Branch / Worktree Summary

- 当前 worktree 路径：`/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`
- 当前 git branch：`dev/release-internal-test`
- 当前 HEAD commit：`d6f8d253f0f1c09cc1cb241e4c9c49b69744b372` (`d6f8d25 chore(release): sync from mainline for pre-package validation`)
- 报告开始前未提交改动：无，`git status --short --branch` 仅显示 `## dev/release-internal-test`
- 本报告生成后未提交改动：预计仅本文件 `docs/release/ReleaseBuild_handoff_report_20260513.md`
- 与 MainLine / upstream 分叉：
  - 当前本地 MainLine 分支：`stable/mainline`，HEAD `73d4cc7 feat(mainline): apply meta active runtime`
  - `git merge-base HEAD stable/mainline`：`67e5b138ae38c2350caf7d19d7724f018653f92b`
  - `git rev-list --left-right --count HEAD...stable/mainline`：`6 29`
  - 当前树内容与 `stable/mainline` 的实际文件差异很小：`CODEX.md` 为 ReleaseBuild-local 边界文件，另有 `docs/release/ReleaseBuild_sync_from_MainLine_pre_package_validation_20260513.md`。历史仍是分叉状态，后续不要误认为 ReleaseBuild 已 fast-forward 到 MainLine。
- 当前分支职责边界：ReleaseBuild 只用于从已验证 MainLine 或已验证发布源同步内部测试打包候选、预打包验证、打包 smoke、包内 metadata 检查和发布前检查；不得用于功能开发。

已安全执行的检查命令：

```bash
pwd
git status --short --branch
git branch --show-current
git rev-parse --short HEAD
git rev-parse HEAD
git log --oneline -5
git branch -vv
git merge-base HEAD stable/mainline
git rev-list --left-right --count HEAD...stable/mainline
git diff --name-status stable/mainline..HEAD
```

最近 5 个提交：

```text
d6f8d25 chore(release): sync from mainline for pre-package validation
7b6cd0a docs(release): audit pre-package readiness
8b742c0 docs(release): rebuild internal beta package from release head
43c3cd0 fix(release): restore bioinformatics workspace ui compatibility
c369b26 docs(vocabulary): finalize shared vocabulary baseline
```

## 2. Current Functional Scope

ReleaseBuild 当前不是独立功能开发分支，而是内部测试打包候选分支。当前代码树包含 MainLine `73d4cc7` 的源代码状态，并额外保留 ReleaseBuild-local `CODEX.md` 和同步验证报告。

已实现并可运行的功能：

- 源码启动入口：`python3 -m app.main --smoke-test` 可运行，当前输出 `app_version=0.1.0-internal-beta`、`app_channel=Developer Preview / testing`、`launch_mode=source`、`git_head=d6f8d25`。
- Shell / 桌面主入口：`app/main.py`、`app/shell/main_window.py`、`app/shell/dashboard.py` 提供登录、Dashboard、模块选择、设置页、测试模式页、Bioinformatics workspace 和 Meta Analysis workspace。
- Dashboard 当前识别的 Bioinformatics feature：`数据检索 / 导入`、`数据下载`、`数据资产识别`、`数据清洗`、`样本分组`。
- Dashboard 当前识别的 Meta Analysis feature：`文献导入`、`去重准备`、`Duplicate Review`、`Screening`、`Extraction`、`Analysis`、`Reporting`。
- 打包脚本能力：`scripts/package_app.py` 可构建本地 macOS `.app` launcher，写入 `BUILD_INFO.json`、`Info.plist`，并可在临时目录运行 packaged smoke。默认输出路径是 `dist/BioMedPilot.app`，本报告阶段未执行正式打包。

已接入 UI 但仍是占位 / 测试级 / draft 的功能：

- 设置页仍是占位页，用于展示默认项目路径、语言、Python/R 环境、本地 AI 模型、数据库、图表样式、导出格式和缓存清理等字段。
- Bioinformatics 多个分析能力属于 preflight / testing-level，不应描述为真实 DEG、富集、相关性或生存分析正式执行。
- Meta Analysis 的统计、报告、AI suggestion、PubMed 候选、文献导入、去重、筛选、提取、质评等当前按 Developer Preview / testing-level 处理；不能称为 production-ready、clinical-grade 或 submission-grade。

只有后端或服务层，还没有确认完整 UI 闭环的功能：

- `app/meta_analysis/services/**` 中包含大量 Meta 服务，包括 fulltext、quality、analysis plan、meta statistics、publication export、AI suggestion、artifact review 等。ReleaseBuild 只同步和验证它们的当前状态，不声明这些服务都已形成最终用户闭环。
- `app/bioinformatics/services/**` 包含 GEO / TCGA / GTEx / 本地表达数据相关服务、preflight、runner 和 report service。真实执行器接入状态必须以后续模块报告为准，ReleaseBuild 不升级其成熟度。

仅有设计、文档或预留接口的功能：

- `docs/packaging.md` 描述当前 local launcher package 模式和限制，不表示已产出新的正式包。
- `docs/ui/**`、`docs/audit/**`、`docs/integration/**`、`docs/handoff/**` 是当前治理、审计和 handoff 文档，不等同于新功能实现。

## 3. Completed Work Since Last Handoff

- 完成：ReleaseBuild 从 MainLine `73d4cc7` 显式同步到预打包候选源状态。
  - 涉及文件：全树同步到 MainLine 源，重点包括 `app/meta_analysis/**`、`tests/meta_analysis/**`、`app/shared/ui/**`、`docs/audit/**`、`docs/handoff/**`、`docs/integration/**`、`docs/ui/**`。
  - 行为变化：ReleaseBuild 当前源代码包含 MainLine 的 Meta active runtime、Meta tests、shared UI helper 和当前治理/审计文档。
  - UI 变化：继承 MainLine 的 Shell、Bioinformatics 页面样式收敛、Meta active runtime 页面和 shared UI theme。
  - 数据/manifest：未新增正式 release manifest；继承 `data/package_manifest.json`、`app/version.py` 和 packaging metadata 写入逻辑。
  - 测试：上一阶段报告记录 `git diff --check`、source smoke、`tests/meta_analysis`、`tests/ui`、`tests/shared`、`tests/bioinformatics`、`scripts/run_tests.py` 均通过。

- 完成：新增 ReleaseBuild-local `CODEX.md`。
  - 涉及文件：`CODEX.md`
  - 行为变化：将工作区说明从 MainLine 改为 ReleaseBuild，明确本 worktree 只做同步、预打包验证、打包 smoke 和 metadata 检查。
  - UI 变化：无。
  - 数据/manifest：无。
  - 测试：`git diff --check` 通过。

- 完成：新增预打包同步验证报告。
  - 涉及文件：`docs/release/ReleaseBuild_sync_from_MainLine_pre_package_validation_20260513.md`
  - 行为变化：记录同步源、同步策略、包含/排除检查、未执行打包/未覆盖桌面入口/未 push、验证结果和下一阶段判断。
  - UI 变化：无。
  - 数据/manifest：无。
  - 测试：报告中记录完整验证结果。

## 4. Important Files and Entry Points

主要启动和 Shell 文件：

- `app/main.py`：源码启动入口；`--smoke-test` 加载 Dashboard、环境检查和版本信息后退出。
- `app/shell/main_window.py`：桌面主窗口；连接 login、Dashboard、Bioinformatics、Meta Analysis、settings、testing mode。
- `app/shell/dashboard.py`：Dashboard model；读取 Bioinformatics / Meta feature 列表、最近项目、最近任务和环境状态。
- `app/shell/module_selection.py`：模块选择页面。
- `app/version.py`：`APP_VERSION`、`APP_CHANNEL`、`BUILD_INFO.json` 读取和 `git_head` 摘要来源。

主要 UI / workflow 文件：

- `app/bioinformatics/workspace.py`：Bioinformatics workspace 入口和页面栈。
- `app/bioinformatics/workflow_pages.py`：Bioinformatics 轻量流程页、workflow status 和 analysis task UI。
- `app/meta_analysis/workspace.py`：Meta active runtime 主要 UI 集成点，包含 workflow home、PICO、search strategy、literature import、dedup/screening、manual extraction、statistics、report export 等路由。
- `app/meta_analysis/workflow_pages.py`：Meta protocol/search 兼容导出入口。
- `app/shared/ui/__init__.py`、`app/shared/ui/theme.py`、`app/ui_style_tokens.py`：shared UI helper 和治理色板。

主要 service / workflow 文件：

- `scripts/package_app.py`：本地 macOS `.app` launcher 构建脚本；默认写入 `dist/BioMedPilot.app`，正式运行需单独确认。
- `scripts/run_tests.py`：统一测试入口，设置 `QT_QPA_PLATFORM=offscreen` 后运行 `pytest -q`。
- `app/shared/project_center/service.py`：`project_storage/projects/projects.json` 的项目记录读写。
- `app/shared/task_center/service.py`：`project_storage/tasks/tasks.json` 的任务记录读写。
- `app/shared/data_center/service.py`：`project_storage/data/data_assets.json` 的数据资产记录读写。
- `app/meta_analysis/services/**`：Meta Analysis 业务服务集合。
- `app/bioinformatics/services/**`：Bioinformatics 业务服务集合。

主要 schema / manifest / metadata 文件：

- `data/package_manifest.json`：shared medical vocabulary package manifest；声明默认包内包含的 mini index、zh overrides、source metadata 和 license attribution。
- `data/medical_terms/**`：当前默认 package-safe medical terms assets。
- `app/version.py`：source / packaged launch metadata 的运行时读取入口。
- `dist/BioMedPilot.app/Contents/Resources/app/BUILD_INFO.json`：正式打包后由 `scripts/package_app.py` 写入；当前 `dist/` 是 ignored 本地产物，本报告阶段未覆盖。
- `dist/BioMedPilot.app/Contents/Info.plist`：正式打包后由 `scripts/package_app.py` 写入；本报告阶段未覆盖。

主要测试文件：

- `tests/test_package_app.py`：临时目录构建 launcher package，并验证 packaged smoke。
- `tests/test_versioned_packaged_entry.py`：验证 packaged metadata、`BUILD_INFO.json`、`Info.plist` 和 packaged smoke 输出。
- `tests/test_app_version_entry.py`：版本入口测试。
- `tests/ui/**`：Shell、模块选择、Bioinformatics / Meta UI 和 shared UI theme 测试。
- `tests/meta_analysis/**`：Meta active runtime、services、workflow、report/export、statistics、AI suggestion guard 和 regression 覆盖。
- `tests/bioinformatics/**`：Bioinformatics import、download、asset detection、preflight、workflow adapters 和 runner 相关覆盖。
- `tests/shared/**`：shared services、AI Gateway、query intelligence、medical vocabulary 和 testing mode 覆盖。

当前报告、审计、handoff 文件：

- `CODEX.md`：ReleaseBuild worktree 规则。
- `docs/release/ReleaseBuild_sync_from_MainLine_pre_package_validation_20260513.md`：上一阶段同步与预打包验证报告。
- `docs/packaging.md`：当前 local launcher package 说明和限制。
- `docs/handoff/BioMedPilot_v1_current_handoff_summary_20260513.md`：v1.0 总体 handoff 摘要。
- `docs/handoff/BioMedPilot_v1_desktop_entry_audit_20260513.md`：桌面入口和打包入口审计。
- `docs/handoff/Global_Development_Manual.md`：MainLine handoff copy，ReleaseBuild 只读取，不在本阶段修改。

## 5. Runtime / User Flow

源码用户流程：

```text
python3 -m app.main
-> Login
-> Dashboard / Module Selection
-> Bioinformatics Analysis 或 Meta Analysis
-> Settings / Testing Mode 可从 Shell 进入
```

Bioinformatics 当前主流程概括：

```text
项目入口
-> 数据检索 / 导入
-> 数据下载
-> 数据资产识别
-> 数据清洗
-> 样本分组
-> 分析任务中心 / workflow status
-> preflight / testing-level 输出
```

断点：Bioinformatics 的 DEG、富集、相关性、生存等能力不能从 ReleaseBuild handoff 中升级为正式真实执行结果；真实执行器状态以后续 Bioinformatics 分支报告为准。

Meta Analysis 当前主流程概括：

```text
Meta project home
-> PICO / protocol
-> search strategy
-> literature import
-> dedup / screening review
-> manual extraction
-> statistics analysis
-> report export
```

断点：统计和报告仍是 Developer Preview / testing-level；不得输出医学结论，不得把 AI suggestion 或候选文献预览写成 confirmed extraction / final analysis。

ReleaseBuild 包装流程：

```text
确认源 HEAD 和 dirty 状态
-> 从已验证 MainLine / release source 同步
-> source smoke 和 test suites
-> 人工确认后运行 package command
-> 生成 dist/BioMedPilot.app
-> packaged smoke
-> 如需桌面入口刷新，另行确认后复制/替换桌面 app
```

当前断点：本阶段尚未执行实际打包，也未刷新 `/Users/changdali/Desktop/BioMedPilot.app` 或任何 `Dev.command`。

## 6. Data Contracts / Manifest Contracts

| Contract | 文件位置 | 生成者 | 读取者 | 当前状态 | 后续依赖建议 |
| --- | --- | --- | --- | --- | --- |
| Source / packaged version summary | `app/version.py`；packaged 时读取 `BUILD_INFO.json` | source 由 Git / constants 推导；packaged 由 `scripts/package_app.py` 写入 | `app/main.py --smoke-test`、packaged launcher tests | testing-level release metadata | ReleaseBuild 可依赖；正式 release 仍需独立确认 |
| Build info | `dist/BioMedPilot.app/Contents/Resources/app/BUILD_INFO.json` | `scripts/package_app.py` | `app/version.py` | 仅打包后存在；当前 dist 是 ignored 本地产物 | 下一阶段打包可依赖，但必须避免误读旧 dist |
| macOS bundle plist | `dist/BioMedPilot.app/Contents/Info.plist` | `scripts/package_app.py` | macOS launcher / tests | 仅打包后存在 | 下一阶段打包可依赖 |
| Package resource manifest | `data/package_manifest.json` | 当前源码维护 | packaging tests / handoff | testing-level package manifest | 可作为 ReleaseBuild packaging 检查输入；不要塞入 full ontology sqlite |
| Medical terms package assets | `data/medical_terms/mini_medical_terms_index.json`、`zh_term_overrides.json`、`source_metadata.json`、`license_attribution.md`、`reference_checklists/**` | Vocabulary / shared layer 当前源码 | `scripts/package_app.py`、query intelligence runtime | package-safe shared assets | 可依赖；`medical_terms_index.sqlite` 是 optional enhancement，不在默认包 |
| Project registry | `project_storage/projects/projects.json` | `ProjectCenter` | Dashboard / project open flow | local runtime data | 不提交用户数据；后续模块可通过 service 访问 |
| Task registry | `project_storage/tasks/tasks.json` | `TaskCenter` | Dashboard / task views / services | local runtime data | 不提交用户数据；任务状态不能伪造成真实分析完成 |
| Data asset registry | `project_storage/data/data_assets.json` | `DataCenter` | Bioinformatics / Meta service flows | local runtime data | 可作为本地测试级资产索引；不要提交真实用户数据 |
| Bioinformatics preflight / manifests | 多数生成在项目目录内，如 `geo_*_preflight_*.json`、`expression_matrix_asset_manifest.json`、`tcga_prepare_manifest.json` | Bioinformatics services | Bioinformatics UI / downstream preflight | testing-level / preflight | 后续可依赖 schema 但不得称为正式分析结果 |
| Meta project / literature / extraction / analysis / report artifacts | Meta project directory 下各步骤目录；服务位于 `app/meta_analysis/services/**` | Meta services / UI actions | Meta workspace pages and tests | testing-level / draft / confirmed-by-user where applicable | 后续 Meta 阶段可依赖，但必须保留人工确认和 testing-level 标记 |
| Audit / handoff docs | `docs/audit/**`、`docs/handoff/**`、`docs/release/**` | Codex / human stage tasks | 后续 handoff 和审计 | documentation evidence | 不要删除或重写历史证据 |

## 7. Tests and Validation

本报告生成阶段实际运行：

```bash
git diff --check
```

结果：通过，无输出。

```bash
QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
```

结果：通过。

```text
BioMedPilot / 医研智析
app_version=0.1.0-internal-beta
app_channel=Developer Preview / testing
launch_mode=source
app_root=/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild
git_head=d6f8d25
workspace_entries=2
bioinformatics_features=5
meta_analysis_features=7
pyside6_available=True
```

上一阶段 `docs/release/ReleaseBuild_sync_from_MainLine_pre_package_validation_20260513.md` 记录的完整验证：

| Command | Result |
| --- | --- |
| `git diff --check` | passed |
| `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test` | passed |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q` | passed; 465 passed |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | passed; 170 passed |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/shared -q` | passed; 225 passed |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q` | passed; 264 passed |
| `python3 scripts/run_tests.py` | passed; 1147 passed |

本报告阶段未重新运行 full pytest；原因是本任务只新增 handoff 文档，不改业务代码、runtime config、package script 或 tests。正式进入实际打包前建议重新运行 ReleaseBuild 指定测试和 package smoke。

手动测试：未进行 GUI 手动点击测试。

用户手动确认需求：正式打包、覆盖 `dist/BioMedPilot.app`、刷新桌面 app 或任何桌面 Dev.command 前需要人工确认。

## 8. Known Issues / Risks

- 当前报告文件本身是未提交改动。本任务明确要求不要自动提交，除非当前分支规则明确要求报告提交；因此本报告保存后会留下一个未提交 Markdown 文件。
- ReleaseBuild 与 `stable/mainline` 历史明显分叉。虽然当前树内容基本对齐 MainLine `73d4cc7`，但不能用 fast-forward 关系推断同步状态。
- `dist/` 当前存在为 ignored 本地产物，`git status --ignored --short dist` 显示 `!! dist/`。本报告阶段未覆盖它；下一阶段打包前必须确认是否允许清理或覆盖。
- `README.md` 仍描述历史 legacy snapshots 路径 `app/bioinformatics/legacy/` 和 `app/meta_analysis/legacy/`；当前 `app/meta_analysis/legacy` 不存在。后续如修改 README，应独立审计措辞，避免把历史说明误认为当前 runtime。
- `scripts/package_app.py --smoke-test` 默认写入 `dist/BioMedPilot.app`，属于高风险产物覆盖操作。预打包报告阶段没有执行该命令。
- 桌面 app `/Users/changdali/Desktop/BioMedPilot.app` 在既有审计中被标记为可能过期或来源不一致；本报告阶段未检查、未覆盖、未刷新。
- Bioinformatics 和 Meta 的多项功能是 testing-level / preflight / draft。handoff、UI 和 release 文案中不得升级为正式科研结果、临床级或投稿级能力。
- 真实 Bioinformatics 执行器和真实 Meta statistics executor 仍受全局手册 gate 约束；ReleaseBuild 不能绕过模块确认直接升级能力。
- AI Gateway 默认关闭；不得保存 raw prompt / raw response，不得自动把 AI suggestion 写入筛选、提取、分析或报告结果。
- `project_storage/**` 是本地运行数据位置，不能把真实用户数据、下载数据集、PDF、全文或 runtime cache 纳入 Git。

## 9. Do Not Touch / Boundary Rules

- 不要在 ReleaseBuild 开发新功能；功能变更应在对应模块 worktree 或 Integration / MainLine 流程中完成。
- 不要修改 `MainLine`、`Bioinformatics`、`Meta`、`Vocabulary`、`UIShell`、`LabTools`、`AI`、`Integration` 等其他 worktree。
- 不要 push remote，不要处理凭据，不要 force push，不要删除远程分支。
- 不要删除当前有效测试、handoff、audit、release 报告、legacy/archive 文档或高风险历史证据。
- 不要运行会覆盖 `dist/BioMedPilot.app` 的打包命令，除非任务明确进入实际打包阶段并授权覆盖。
- 不要覆盖 `/Users/changdali/Desktop/BioMedPilot.app`、`/Users/changdali/Desktop/BioMedPilot v1.0 Dev.command` 或其他桌面入口。
- 不要把 PubMed 文献检索混入 Bioinformatics。
- 不要把 GEO / TCGA / GTEx 表达数据分析混入 Meta。
- 不要把 draft、preflight、testing-level、imported result 写成 real computed result。
- 不要启用外部网络、下载、外部 API、外部模型或本地模型自动执行，除非经过对应 gate 和人工确认。

## 10. Recommended Next Tasks

### Immediate Next Step

- 执行 `ReleaseBuild actual packaging pre-confirmation`：在不覆盖桌面入口的前提下，确认是否允许覆盖 `dist/BioMedPilot.app`，记录现有 dist metadata，并给出实际打包前的 go/no-go 报告。
- 在实际打包前重新运行：`git status --short --branch`、`git diff --check`、`QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`。

### Before Integration

- 如需让 ReleaseBuild 与 MainLine 历史关系更清晰，先设计单独的 release branch strategy；不要在无确认情况下 merge / rebase / rewrite history。
- 正式打包前运行完整验证：`tests/meta_analysis`、`tests/ui`、`tests/shared`、`tests/bioinformatics`、`scripts/run_tests.py`。
- 如果执行 `scripts/package_app.py --smoke-test`，必须先确认输出目录，避免意外覆盖当前 `dist/BioMedPilot.app` 或桌面 app。
- 打包完成后读取并记录 `dist/BioMedPilot.app/Contents/Resources/app/BUILD_INFO.json` 和 `dist/BioMedPilot.app/Contents/Info.plist` 的 `version`、`channel`、`git_head`、`source_root`、`built_at`。

### Later / Optional

- 清理或刷新 README 中关于 legacy snapshots 的表述，但必须先确认当前历史说明是否仍需保留。
- 为 ReleaseBuild 增加专门的 non-destructive preflight script，使预打包验证不默认写入 `dist/BioMedPilot.app`。
- 为 desktop entry refresh 建立单独报告流程，明确从 `dist/` 到 `/Users/changdali/Desktop/BioMedPilot.app` 的复制、备份、metadata 验证和回退策略。

## 11. Suggested Codex Instruction for Next Stage

请在 `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild` 执行 ReleaseBuild actual packaging pre-confirmation 阶段。

目标：在不执行正式打包、不覆盖桌面入口的前提下，确认当前 ReleaseBuild 是否满足实际打包前条件，并产出 go/no-go 报告。

允许修改范围：

- 仅允许新增一份 `docs/release/ReleaseBuild_actual_packaging_pre_confirmation_20260513.md` 报告。
- 如需保存命令输出摘要，只能写入该报告。

禁止事项：

- 不要修改其他 worktree。
- 不要开发功能、重构代码或修复业务逻辑。
- 不要删除文件。
- 不要运行会覆盖 `dist/BioMedPilot.app` 的正式打包命令。
- 不要覆盖 `/Users/changdali/Desktop/BioMedPilot.app` 或任何 `Dev.command`。
- 不要 push remote。
- 不要启用网络、下载、外部 API、AI 或本地模型自动执行。

必须检查：

```bash
pwd
git status --short --branch
git branch --show-current
git rev-parse HEAD
git log --oneline -5
git diff --check
QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
git status --ignored --short dist
```

建议检查：

```bash
find dist/BioMedPilot.app -maxdepth 4 -name BUILD_INFO.json -o -name Info.plist
```

如果人工明确授权实际打包，再进入单独的 packaging execution 阶段，并运行：

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/shared -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q
python3 scripts/run_tests.py
python3 scripts/package_app.py --smoke-test
```

报告要求：

- 记录当前 HEAD、branch、dirty 状态、是否存在 ignored `dist/`、是否会覆盖旧包。
- 记录 source smoke 输出。
- 明确是否允许进入实际 packaging execution。
- 明确未覆盖桌面入口、未 push、未修改其他 worktree。

停止条件：

- 当前路径或分支不是 ReleaseBuild。
- 出现与任务相关的未知未提交改动。
- 需要覆盖桌面入口或旧 app 产物但未获得明确授权。
- 测试失败且无法在报告阶段安全解释。
- 需要修改其他 worktree、push remote、处理凭据、启用网络/AI/下载或做发布声明。
