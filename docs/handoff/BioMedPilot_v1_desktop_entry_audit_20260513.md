# BioMedPilot v1.0 Desktop Entry D0 Audit

日期：2026-05-13

范围：

- `/Users/changdali/Developer/biomedpilot v1.0/MainLine`
- `/Users/changdali/Desktop`
- `/Users/changdali/Applications/BioMedPilot.app`
- 只审计桌面开发入口和打包入口策略。

本次任务只新增本审计报告。未创建桌面入口，未修改业务代码，未修改 UI，未修改打包脚本，未删除旧 App，未覆盖 `/Users/changdali/Desktop/BioMedPilot.app`，未 push，未合并分支，未自动继续 D1。

## 已阅读的主控文件

- `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/handoff/Global_Development_Manual.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/handoff/BioMedPilot_v1_global_control_audit_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/handoff/BioMedPilot_v1_worktree_dirty_state_audit_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/README_总说明.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/CODEX.md`

两份 `Global_Development_Manual.md` 已用 `cmp` 检查，结果同步。

## 当前 Worktree 状态

审计开始时，以下 worktree 的 `git status --short` 均为空：

- `MainLine`: `stable/mainline`
- `Bioinformatics`: `dev/bioinformatics`
- `Meta`: `dev/meta-analysis`
- `Vocabulary`: `dev/shared-vocabulary`
- `UIShell`: `dev/ui-shell`
- `LabTools`: `dev/labtools`
- `AI`: `dev/ai-gateway`
- `Integration`: `dev/integration`
- `ReleaseBuild`: `dev/release-internal-test`

审计开始时 MainLine HEAD 为 `8fa20acd3202c7da2d34ac143e4f335b924a46ee`。在本任务提交前，MainLine HEAD 已前进到：

```text
6e2cfbb4e7c8c3ab5f15ed7869402d60e6f1cbc8
```

审计过程中 MainLine 曾出现本任务未创建的未提交改动：

```text
M app/bioinformatics/pages/geo_import_page.py
M app/bioinformatics/pages/local_expression_import_page.py
M app/shared/ui/__init__.py
M app/shared/ui/theme.py
M tests/ui/test_shared_ui_theme.py
?? docs/ui/BioMedPilot_UI_Stage_0_4_Status_Button_Page_Structure_Audit_20260513.md
```

这些文件属于业务/UI/test/docs surface，不属于本 D0 桌面入口审计范围。本任务未修改、未暂存、未提交这些文件。提交本报告前，上述改动已进入当前 MainLine HEAD `6e2cfbb`；最终待提交范围只包含本 D0 审计报告。

## 当前桌面入口现状

命令：

```bash
find "$HOME/Desktop" -maxdepth 1 \( -name '*BioMedPilot*.command' -o -name '*BioMedPilot*.app' -o -name '*BioMedPilot*' -o -name '*biomedpilot*' \) -print | sort
```

结果：

```text
/Users/changdali/Desktop/BioMedPilot
/Users/changdali/Desktop/BioMedPilot 2.app
/Users/changdali/Desktop/BioMedPilot 3.app
/Users/changdali/Desktop/BioMedPilot.app
/Users/changdali/Desktop/BioMedPilot_UI_audit_handoff_2026-05-13.md
/Users/changdali/Desktop/BioMedPilot测试数据
```

未发现：

- `/Users/changdali/Desktop/BioMedPilot v1.0 Dev.app`
- `/Users/changdali/Desktop/BioMedPilot v1.0 Dev.command`
- 任何 `*BioMedPilot*.command`

桌面其他相关项目：

- `/Users/changdali/Desktop/BioMedPilot`: 普通目录，包含 `demoexpressionmatrix.csv`。
- `/Users/changdali/Desktop/BioMedPilot测试数据`: 普通目录，包含多个测试数据文件。
- `/Users/changdali/Desktop/BioMedPilot_UI_audit_handoff_2026-05-13.md`: 桌面审计文档。

## 当前 Desktop App 是否可能过期

### `/Users/changdali/Desktop/BioMedPilot.app`

`BioMedPilot.app` 是 symlink：

```text
/Users/changdali/Desktop/BioMedPilot.app -> /Users/changdali/Applications/BioMedPilot.app
```

`BUILD_INFO.json`：

```json
{
  "app_name": "BioMedPilot",
  "version": "0.1.0-internal-beta",
  "bundle_version": "0.1.0",
  "channel": "Developer Preview / testing",
  "launch_mode": "packaged-local-python",
  "source_root": "/Users/changdali/Developer/BioMedPilot",
  "git_head": "e97d87e",
  "built_at": "2026-05-12T13:32:05.623639+00:00"
}
```

`Info.plist` 记录：

```text
BioMedPilotChannel = Developer Preview / testing
BioMedPilotGitHead = e97d87e
BioMedPilotVersion = 0.1.0-internal-beta
CFBundleIdentifier = local.biomedpilot.desktop
```

判断：

- 可识别构建来源，但来源是 `/Users/changdali/Developer/BioMedPilot`，不是当前 v1.0 根目录 `/Users/changdali/Developer/biomedpilot v1.0`。
- 记录了 `git_head=e97d87e`，但该 commit 当前只被 `dev/meta-analysis` 包含，不是当前 `stable/mainline` 的 HEAD。
- 未直接指向旧路径 `/Users/changdali/Documents/BioMedPilot`，但也未指向新路径 `/Users/changdali/Developer/biomedpilot v1.0`。
- 与当前 `MainLine` HEAD `6e2cfbb` 不一致，可能不是当前 MainLine 最新状态。
- 桌面文件名是通用 `BioMedPilot.app`，没有 `Dev`、`Developer Preview`、`git_head` 或来源路径提示，容易误导用户认为它是当前最新版本。

### `/Users/changdali/Desktop/BioMedPilot 2.app`

`BUILD_INFO.json`：

```json
{
  "source_root": "/Users/changdali/Documents/BioMedPilot",
  "git_head": "1ab89e1",
  "built_at": "2026-05-12T03:38:15.155677+00:00"
}
```

判断：

- 明确来自旧路径 `/Users/changdali/Documents/BioMedPilot`。
- `git_head=1ab89e1` 当前只被 `dev/meta-analysis` 包含，不是当前 MainLine HEAD。
- 应视为旧路径打包遗留，不应作为 v1.0 MainLine 桌面开发入口。

### `/Users/changdali/Desktop/BioMedPilot 3.app`

`BUILD_INFO.json`：

```json
{
  "source_root": "/Users/changdali/Documents/BioMedPilot",
  "git_head": "8a75113",
  "built_at": "2026-05-12T09:58:29.360470+00:00"
}
```

判断：

- 明确来自旧路径 `/Users/changdali/Documents/BioMedPilot`。
- `git_head=8a75113` 当前只被 `dev/meta-analysis` 包含，不是当前 MainLine HEAD。
- 应视为旧路径打包遗留，不应作为 v1.0 MainLine 桌面开发入口。

## 当前打包/启动脚本现状

### MainLine

已存在：

- `MainLine/scripts/run_app.py`
- `MainLine/scripts/run_tests.py`
- `MainLine/scripts/package_app.py`
- `MainLine/app/version.py`
- `MainLine/docs/packaging.md`
- `MainLine/tests/test_package_app.py`
- `MainLine/tests/test_versioned_packaged_entry.py`
- `MainLine/tests/test_app_version_entry.py`

`scripts/package_app.py` 当前能力：

- 构建本地 macOS `.app` launcher，默认输出 `dist/BioMedPilot.app`。
- 复制 `app`、`assets`、`config`、`docs`、`examples`、`reporting`、`scripts`。
- 写入 `Contents/Resources/app/BUILD_INFO.json`。
- 写入 `Contents/Info.plist`，包含 `BioMedPilotGitHead`、`BioMedPilotChannel`、`BioMedPilotVersion`。
- launcher 设置 `BIOMEDPILOT_LAUNCH_MODE=packaged-local-python`，进入 bundle 内 `Resources/app` 后执行 `python -m app.main`。
- 支持 `--smoke-test`，打包后运行生成的 launcher `--smoke-test`。

`app/version.py` 当前元数据：

```text
APP_VERSION = 0.1.0-internal-beta
APP_BUNDLE_VERSION = 0.1.0
APP_CHANNEL = Developer Preview / testing
BUILD_INFO_FILENAME = BUILD_INFO.json
```

`app.main --smoke-test` 会打印：

- `app_version`
- `app_channel`
- `launch_mode`
- `app_root`
- `git_head`

### ReleaseBuild

已存在与 MainLine 字节一致的：

- `ReleaseBuild/scripts/package_app.py`
- `ReleaseBuild/app/version.py`
- `ReleaseBuild/docs/packaging.md`
- `ReleaseBuild/tests/test_package_app.py`
- `ReleaseBuild/tests/test_versioned_packaged_entry.py`
- `ReleaseBuild/tests/test_app_version_entry.py`

`ReleaseBuild/README.md` 也记录了本地 `.app` launcher package 模式：不下载依赖，不是完整 standalone installer，复制项目文件到 `dist/BioMedPilot.app`，使用构建时 Python 启动。

### UIShell

已存在与 MainLine 字节一致的：

- `UIShell/scripts/package_app.py`
- `UIShell/app/version.py`
- `UIShell/docs/packaging.md`
- `UIShell/tests/test_package_app.py`
- `UIShell/tests/test_versioned_packaged_entry.py`
- `UIShell/tests/test_app_version_entry.py`

UIShell 也包含桌面壳和图标资产，例如：

- `UIShell/assets/icons/app/biomedpilot_app_icon.png`
- `UIShell/assets/icons/app/biomedpilot_app_icon.icns`

### ProjectControl

`01_ProjectControl` 主要保存治理文档、迁移报告和测试日志。发现 `01_ProjectControl/test_logs_20260513/*_smoke.log` 记录过历史 smoke 输出，但未发现适合作为运行入口或打包入口的脚本。

## MainLine / ReleaseBuild / UIShell / ProjectControl 职责判断

### MainLine

MainLine 是稳定主线和当前用户可测试源码入口。最适合放置 D1 的桌面开发 `.command` 入口源模板或生成说明，因为开发入口应直接指向当前稳定源码树，并清楚显示：

- worktree: `MainLine`
- branch: `stable/mainline`
- source path: `/Users/changdali/Developer/biomedpilot v1.0/MainLine`
- `git_head`
- `app_version`
- `app_channel`
- `launch_mode=source`

### ReleaseBuild

ReleaseBuild 是内部测试打包、package metadata validation 和 packaged smoke tests 的职责边界。最适合后续 D2 或 release packaging 阶段创建、验证和刷新 `.app` 打包入口。它不应承担日常源码开发入口职责，也不应从未验证模块 worktree 直接产出桌面包。

### UIShell

UIShell 负责桌面壳、登录、主窗口、模块选择、导航、主题和视觉一致性。它适合继续维护 shell 行为、图标、视觉一致性和 UI 入口体验，但不应直接作为全局桌面入口发布源，除非对应 shell 改动已经验证并进入 MainLine 或 ReleaseBuild。

### ProjectControl

外层 `01_ProjectControl` 是治理和审计层，适合保存全局策略、迁移/审计报告和人工确认事项。不适合放置用户双击运行入口，因为它不是 Git worktree，也不是运行源码根。

## 推荐方案

1. D1 先创建 `.command` 开发入口，不先创建或刷新 `.app`。
2. `.command` 应指向当前 MainLine 源码，不复制业务代码、不打包、不覆盖旧 App。
3. `.command` 启动前应打印或显示至少以下信息：

```text
BioMedPilot v1.0 Developer Preview
channel=Developer Preview / testing
entry_type=source-dev-command
worktree=MainLine
branch=stable/mainline
source_root=/Users/changdali/Developer/biomedpilot v1.0/MainLine
git_head=<current short head>
app_version=0.1.0-internal-beta
launch_mode=source
```

4. D1 桌面入口建议命名为：

```text
/Users/changdali/Desktop/BioMedPilot v1.0 Dev.command
```

5. D1 不建议使用 `BioMedPilot.app` 名称，因为当前桌面已有同名 symlink，且旧包和新 MainLine 状态不一致。
6. 后续 `.app` 打包入口建议命名为：

```text
/Users/changdali/Desktop/BioMedPilot v1.0 Developer Preview.app
```

或在 ReleaseBuild 阶段使用带日期/commit 的候选包名：

```text
BioMedPilot v1.0 Developer Preview 20260513 <git_head>.app
```

7. 后续只有在 ReleaseBuild 基于 validated MainLine 重新打包、完成 source smoke、packaged smoke 和 metadata 校验后，才考虑刷新通用 `BioMedPilot.app`。
8. 刷新或替换通用 `BioMedPilot.app` 前，应先人工确认如何处理当前 symlink 和旧包；本 D0 不删除、不覆盖。

## D1 创建入口的具体建议

D1 建议只做源码开发入口：

- 在 MainLine 中维护入口模板或生成脚本，但实际创建桌面 `.command` 前先记录审计和验证。
- `.command` 内容应 `cd "/Users/changdali/Developer/biomedpilot v1.0/MainLine"`。
- 启动前运行 `git rev-parse --short HEAD`、`git branch --show-current` 并打印。
- 设置 `BIOMEDPILOT_LAUNCH_MODE=source-dev-command` 或等价显式模式；如果现有 `app.version` 只识别 `source`，D1 应谨慎评估是否需要扩展元数据，避免改业务行为。
- 使用当前 Python 环境执行 `python3 -m app.main`，必要时支持 `--smoke-test`。
- 打开 GUI 前建议先提供 `--smoke-test` 验证路径，确保输出 `app_version`、`app_channel`、`app_root`、`git_head` 与 MainLine 一致。
- `.command` 文件名必须包含 `v1.0 Dev`，避免与旧 `BioMedPilot.app` 混淆。
- `.command` 内不得写旧路径 `/Users/changdali/Documents/BioMedPilot`。
- `.command` 内不得写旧中间路径 `/Users/changdali/Developer/BioMedPilot`。

D1 暂不建议创建 `.app`，原因：

- 当前桌面已有三个 BioMedPilot `.app` 相关入口或旧包，通用名称会放大误用风险。
- 当前 `BioMedPilot.app` 的 `git_head=e97d87e` 与 MainLine `6e2cfbb` 不一致。
- ReleaseBuild 才是内部打包和 packaged smoke 的职责边界。
- `.command` 更适合作为开发者预览源码入口，能避免复制旧代码和隐藏来源。

## 如何避免旧路径和旧包误用

- 桌面开发入口统一使用 `BioMedPilot v1.0 Dev.command`，不使用裸名 `BioMedPilot.command`。
- 打包入口统一使用 `BioMedPilot v1.0 Developer Preview.app` 或带日期/commit 的名称，不直接覆盖 `BioMedPilot.app`。
- 启动时显式打印 `source_root`、`branch`、`git_head`、`channel`。
- 对所有 `.app` 保留 `BUILD_INFO.json` 和 `Info.plist` git metadata 校验。
- 文档中标记当前 `/Users/changdali/Desktop/BioMedPilot 2.app` 和 `/Users/changdali/Desktop/BioMedPilot 3.app` 来自旧路径。
- 刷新通用桌面 app 前，先记录旧 symlink 目标、旧 `BUILD_INFO.json`、新包 metadata、source smoke、packaged smoke 和人工确认结论。

## 本次未修改内容

- 未创建 `/Users/changdali/Desktop/BioMedPilot v1.0 Dev.command`。
- 未创建 `/Users/changdali/Desktop/BioMedPilot v1.0 Dev.app`。
- 未修改 `/Users/changdali/Desktop/BioMedPilot.app`。
- 未修改 `/Users/changdali/Applications/BioMedPilot.app`。
- 未删除 `/Users/changdali/Desktop/BioMedPilot 2.app` 或 `/Users/changdali/Desktop/BioMedPilot 3.app`。
- 未修改 `MainLine/scripts/package_app.py`。
- 未修改 `ReleaseBuild/scripts/package_app.py`。
- 未修改 `UIShell/scripts/package_app.py`。
- 未修改 Bioinformatics、Meta、Vocabulary、AI、UIShell、LabTools 的业务代码。
- 未修改 UI。
- 未运行打包。
- 未运行 packaged app。
- 未 push。
- 未合并分支。
- 未自动继续 D1。

## 验证命令与结果

### 路径确认

命令：

```bash
pwd
```

结果：

```text
/Users/changdali/Developer/biomedpilot v1.0
```

### MainLine root 和 HEAD

命令：

```bash
git -C MainLine rev-parse --show-toplevel
git -C MainLine rev-parse HEAD
git -C MainLine branch --show-current
```

结果：

```text
/Users/changdali/Developer/biomedpilot v1.0/MainLine
6e2cfbb4e7c8c3ab5f15ed7869402d60e6f1cbc8
stable/mainline
```

### Worktree 列表

命令：

```bash
git --git-dir _repo.git worktree list --porcelain
```

结果摘要：

```text
AI             dev/ai-gateway
Bioinformatics dev/bioinformatics
Integration    dev/integration
LabTools       dev/labtools
MainLine       stable/mainline
Meta           dev/meta-analysis
ReleaseBuild   dev/release-internal-test
UIShell        dev/ui-shell
Vocabulary     dev/shared-vocabulary
```

### 初始 Worktree status

命令：

```bash
for d in MainLine Bioinformatics Meta Vocabulary UIShell LabTools AI Integration ReleaseBuild; do
  printf '\n[%s]\n' "$d"
  git -C "$d" status --short
done
```

结果：审计开始时所有列出的 worktree 均为 clean。

### 提交后 Worktree 复核

命令：

```bash
for d in MainLine Bioinformatics Meta Vocabulary UIShell LabTools AI Integration ReleaseBuild; do
  printf '\n[%s]\n' "$d"
  git -C "$d" status --short
done
```

结果摘要：

```text
[MainLine]
clean

[Bioinformatics]
M app/bioinformatics/workflow_pages.py
M tests/ui/test_bioinformatics_workflow_pages.py
?? docs/bioinformatics/stage_B1D_analysis_task_center_userization_20260513.md

[Meta]
clean

[Vocabulary]
clean

[UIShell]
clean

[LabTools]
M app/labtools/calculators/__init__.py
M app/labtools/calculators/calculator_models.py
M app/labtools/calculators/unit_conversion.py
M app/labtools/ui/calculator_widgets.py
M app/labtools/workspace.py
M tests/labtools/test_labtools_imports.py
?? app/labtools/calculators/calculation_record.py
?? app/labtools/calculators/cell_seeding_calculator.py
?? app/labtools/calculators/qpcr_mix_calculator.py
?? app/labtools/calculators/solution_preparation_calculator.py
?? tests/labtools/test_calculation_record.py
?? tests/labtools/test_cell_seeding_calculator.py
?? tests/labtools/test_qpcr_mix_calculator.py
?? tests/labtools/test_solution_preparation_calculator.py

[AI]
clean

[Integration]
dirty; many staged/unstaged Vocabulary-related files plus package/test files observed

[ReleaseBuild]
clean
```

处理：这些 Bioinformatics、LabTools、Integration 改动不属于本 D0 桌面入口审计范围，本任务未修改、未暂存、未提交。

### 审计过程中出现的非本任务改动

命令：

```bash
git -C MainLine status --short
```

结果：

```text
M app/bioinformatics/pages/geo_import_page.py
M app/bioinformatics/pages/local_expression_import_page.py
M app/shared/ui/__init__.py
M app/shared/ui/theme.py
M tests/ui/test_shared_ui_theme.py
?? docs/ui/BioMedPilot_UI_Stage_0_4_Status_Button_Page_Structure_Audit_20260513.md
```

处理：本任务未修改、未暂存、未提交。提交本报告前，MainLine HEAD 已前进到 `6e2cfbb`，上述文件不再显示为 dirty diff；本任务最终只暂存本审计报告。

### 总手册同步检查

命令：

```bash
cmp -s 01_ProjectControl/Global_Development_Manual.md MainLine/docs/handoff/Global_Development_Manual.md
printf 'manual_cmp_exit=%s\n' "$?"
```

结果：

```text
manual_cmp_exit=0
```

### 桌面入口检查

命令：

```bash
find "$HOME/Desktop" -maxdepth 1 \( -name '*BioMedPilot*.command' -o -name '*BioMedPilot*.app' -o -name '*BioMedPilot*' -o -name '*biomedpilot*' \) -print | sort
```

结果：

```text
/Users/changdali/Desktop/BioMedPilot
/Users/changdali/Desktop/BioMedPilot 2.app
/Users/changdali/Desktop/BioMedPilot 3.app
/Users/changdali/Desktop/BioMedPilot.app
/Users/changdali/Desktop/BioMedPilot_UI_audit_handoff_2026-05-13.md
/Users/changdali/Desktop/BioMedPilot测试数据
```

### Desktop App metadata 检查

命令：

```bash
for app in "$HOME/Desktop"/BioMedPilot*.app; do
  [ -d "$app" ] || continue
  realpath "$app"
  readlink "$app" || true
  sed -n '1,160p' "$app/Contents/Resources/app/BUILD_INFO.json"
  plutil -p "$app/Contents/Info.plist"
done
```

结果摘要：

```text
BioMedPilot.app realpath=/Users/changdali/Applications/BioMedPilot.app
BioMedPilot.app readlink=/Users/changdali/Applications/BioMedPilot.app
BioMedPilot.app source_root=/Users/changdali/Developer/BioMedPilot
BioMedPilot.app git_head=e97d87e

BioMedPilot 2.app source_root=/Users/changdali/Documents/BioMedPilot
BioMedPilot 2.app git_head=1ab89e1

BioMedPilot 3.app source_root=/Users/changdali/Documents/BioMedPilot
BioMedPilot 3.app git_head=8a75113
```

### Desktop App commit 归属检查

命令：

```bash
for h in e97d87e 1ab89e1 8a75113; do
  git -C MainLine branch --contains "$h" 2>/dev/null || true
done
```

结果：三个 desktop app `git_head` 当前均只显示在 `dev/meta-analysis`，不是 `stable/mainline` HEAD。

### 脚本与元数据检查

命令：

```bash
cmp -s MainLine/scripts/package_app.py ReleaseBuild/scripts/package_app.py
cmp -s MainLine/scripts/package_app.py UIShell/scripts/package_app.py
cmp -s MainLine/app/version.py ReleaseBuild/app/version.py
cmp -s MainLine/app/version.py UIShell/app/version.py
```

结果：四项 `cmp` 均返回 `0`，说明当前 MainLine、ReleaseBuild、UIShell 的 package script 和 version metadata 字节一致。

### Markdown diff 检查

命令：

```bash
git -C MainLine diff --cached --check -- docs/handoff/BioMedPilot_v1_desktop_entry_audit_20260513.md
git -C MainLine diff --check
```

结果：通过，无输出。

### 业务测试说明

本任务只新增 Markdown 审计报告，不修改业务代码、UI、runtime config、测试文件或打包脚本。因此未运行业务测试、UI 测试、source smoke、packaged smoke 或打包命令。后续 D1 创建入口时应单独运行 source smoke；后续 `.app` 打包入口阶段应在 ReleaseBuild 运行 package smoke 和 packaged app smoke。

## 结论

当前桌面上存在多个 BioMedPilot 相关入口，但不存在 v1.0 Dev `.command` 或 v1.0 Dev `.app`。当前通用 `/Users/changdali/Desktop/BioMedPilot.app` 是指向 `/Users/changdali/Applications/BioMedPilot.app` 的 symlink，metadata 指向非 v1.0 当前根路径，`git_head=e97d87e` 也不是当前 MainLine HEAD。`BioMedPilot 2.app` 和 `BioMedPilot 3.app` 明确来自旧路径 `/Users/changdali/Documents/BioMedPilot`。

推荐 D1 先创建明确命名的源码开发入口 `/Users/changdali/Desktop/BioMedPilot v1.0 Dev.command`，并在入口启动时显式显示 `git_head`、`channel`、`Developer Preview`、`source_root` 和 `branch`。后续 `.app` 打包入口应放在 ReleaseBuild 职责范围内，从 validated MainLine 或 validated release source 产出，并避免直接覆盖当前通用 `BioMedPilot.app`。
