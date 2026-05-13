# BioMedPilot v1.0 Desktop Entry D1 Dev Launcher Handoff

日期：2026-05-13

执行 worktree：

```text
/Users/changdali/Developer/biomedpilot v1.0/MainLine
```

分支与 HEAD：

```text
stable/mainline
09f2529bb841fbec7ec2d39de6cdda19fa460b99
```

范围：创建一个 Desktop 源码开发启动入口，并新增本 D1 handoff 报告。

## 已阅读文件

- `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/handoff/Global_Development_Manual.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/handoff/BioMedPilot_v1_desktop_entry_audit_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/handoff/BioMedPilot_v1_worktree_dirty_state_audit_20260513.md`
- `/Users/changdali/Developer/biomedpilot v1.0/README_总说明.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/CODEX.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/README.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/scripts/run_app.py`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/app/main.py`

两份 `Global_Development_Manual.md` 已用 `cmp` 检查，结果同步。

## 创建的桌面入口

创建路径：

```text
/Users/changdali/Desktop/BioMedPilot v1.0 Dev.command
```

权限：

```text
-rwxr-xr-x
```

入口用途：

- 双击后从当前 v1.0 MainLine 源码启动 BioMedPilot。
- 用于开发期人工测试和 UI / 流程检查。
- 不是 ReleaseBuild `.app`。
- 不是正式发布包。
- 不用于临床决策。

## 指向的 source_root

`.command` 中固定的 source root：

```text
/Users/changdali/Developer/biomedpilot v1.0/MainLine
```

入口启动前会检查该目录是否存在，并检查该目录是否为 Git worktree。

## 启动命令

当前 MainLine README 已记录可用启动方式：

```bash
python -m app.main
python scripts/run_app.py
```

本 D1 入口复用现有 `app.main` 启动方式。实际执行逻辑：

```bash
cd "/Users/changdali/Developer/biomedpilot v1.0/MainLine"
export BIOMEDPILOT_LAUNCH_MODE="source-dev-command"
exec "$PYTHON_BIN" -m app.main
```

Python 选择逻辑：

1. 如果存在并可执行，优先使用：

```text
/Users/changdali/Developer/biomedpilot v1.0/MainLine/.venv/bin/python3
```

2. 如果存在并可执行，再尝试：

```text
/Users/changdali/Developer/biomedpilot v1.0/MainLine/venv/bin/python3
```

3. 否则使用当前系统可找到的：

```text
python3
```

本次检查未发现 MainLine 固定 `.venv` 或 `venv`，当前系统 Python 为：

```text
/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
Python 3.14.4
```

## 启动前输出

入口启动前会打印：

- `BioMedPilot v1.0 Dev Launcher`
- `source_root`
- `current git branch`
- `current git commit`
- `current git status summary`
- `Developer Preview / internal testing`
- `非正式发布包，不用于临床决策`
- Python 路径
- launch command

如果 MainLine dirty，入口不会阻止启动，但会打印：

```text
WARNING: MainLine has uncommitted changes.
```

## 旧路径检查

禁止旧路径：

- `/Users/changdali/Developer/BioMedPilot`
- `/Users/changdali/Documents/BioMedPilot`

验证命令：

```bash
grep -n "Developer/BioMedPilot\|Documents/BioMedPilot" "$HOME/Desktop/BioMedPilot v1.0 Dev.command" || true
```

结果：无输出。

结论：新 `.command` 未指向旧路径。

## 没有覆盖旧 BioMedPilot.app

本任务没有创建、覆盖、删除或移动：

```text
/Users/changdali/Desktop/BioMedPilot.app
```

D0.1 后，旧桌面 `.app` 入口仍在隔离目录：

```text
/Users/changdali/Desktop/BioMedPilot_old_desktop_entries_20260513
```

本次 Desktop 列表显示：

```text
BioMedPilot
BioMedPilot v1.0 Dev.command
BioMedPilot_UI_audit_handoff_2026-05-13.md
BioMedPilot_old_desktop_entries_20260513
BioMedPilot测试数据
```

## 不是 ReleaseBuild App

本任务只创建：

```text
/Users/changdali/Desktop/BioMedPilot v1.0 Dev.command
```

没有创建 `.app` 包，没有运行 `scripts/package_app.py`，没有修改 `ReleaseBuild`，没有生成 ReleaseBuild app，也没有刷新通用 `BioMedPilot.app`。

后续正式 `.app` 入口应由 `ReleaseBuild` 基于 validated MainLine 或 validated release source 生成，并执行 package smoke 与 packaged app smoke。

## 人工测试步骤

1. 双击：

```text
/Users/changdali/Desktop/BioMedPilot v1.0 Dev.command
```

2. 检查终端输出包含：

```text
BioMedPilot v1.0 Dev Launcher
source_root=/Users/changdali/Developer/biomedpilot v1.0/MainLine
current git branch=stable/mainline
current git commit=<当前 MainLine short HEAD>
Developer Preview / internal testing
非正式发布包，不用于临床决策
```

3. 检查终端中 `current git status summary`。如果有未提交改动，应出现：

```text
WARNING: MainLine has uncommitted changes.
```

4. 检查软件是否打开。如果 PySide6 不可用，现有 `app.main` 会进入 console smoke mode 并打印原因。

5. 检查首页是否为当前 MainLine 版本，并确认不是旧 Desktop `.app` 包。

## 未修改内容

本任务未修改：

- Bioinformatics、Meta、Vocabulary、UIShell、LabTools、AI、Integration、ReleaseBuild 的业务代码。
- MainLine app 业务代码。
- UI。
- 打包脚本。
- 测试。
- `/Users/changdali/Desktop/BioMedPilot.app`。
- D0.1 隔离目录中的旧 app。
- `BioMedPilot 2.app` / `BioMedPilot 3.app`。
- `_repo.git`。

本任务未执行：

- 完整业务测试。
- UI 测试。
- 打包。
- packaged app smoke。
- push。
- merge。
- D2。

## 验证命令与结果

### 路径、分支和状态

命令：

```bash
pwd
git rev-parse --show-toplevel
git branch --show-current
git status --short --untracked-files=all
```

结果：

```text
/Users/changdali/Developer/biomedpilot v1.0/MainLine
/Users/changdali/Developer/biomedpilot v1.0/MainLine
stable/mainline
git status --short: clean before D1 report creation
```

### Worktree 状态

命令：

```bash
for d in MainLine Bioinformatics Meta Vocabulary UIShell LabTools AI Integration ReleaseBuild; do
  printf '\n[%s]\n' "$d"
  git -C "/Users/changdali/Developer/biomedpilot v1.0/$d" status --short
done
```

结果：所有列出的 worktree 均为 clean。

### Desktop 入口权限

命令：

```bash
ls -l "$HOME/Desktop/BioMedPilot v1.0 Dev.command"
```

结果：

```text
-rwxr-xr-x@ 1 changdali  staff  1991 May 13 13:59 /Users/changdali/Desktop/BioMedPilot v1.0 Dev.command
```

### 旧路径 grep

命令：

```bash
grep -n "Developer/BioMedPilot\|Documents/BioMedPilot" "$HOME/Desktop/BioMedPilot v1.0 Dev.command" || true
```

结果：无输出。

### Shell 语法检查

命令：

```bash
zsh -n "$HOME/Desktop/BioMedPilot v1.0 Dev.command"
printf 'zsh_syntax_exit=%s\n' "$?"
```

结果：

```text
zsh_syntax_exit=0
```

### Desktop 列表

命令：

```bash
ls -la "$HOME/Desktop" | grep -i "BioMedPilot" || true
```

结果摘要：

```text
BioMedPilot
BioMedPilot v1.0 Dev.command
BioMedPilot_UI_audit_handoff_2026-05-13.md
BioMedPilot_old_desktop_entries_20260513
BioMedPilot测试数据
```

### 旧入口隔离目录

命令：

```bash
ls -la "$HOME/Desktop/BioMedPilot_old_desktop_entries_20260513" || true
```

结果摘要：

```text
BioMedPilot 2.app
BioMedPilot 3.app
BioMedPilot.app -> /Users/changdali/Applications/BioMedPilot.app
```

### Diff whitespace 检查

命令：

```bash
git diff --check
```

结果：通过，无输出。

## 业务测试说明

本任务只创建 Desktop `.command` 源码开发入口，并只新增 Markdown handoff 报告。未修改业务代码、UI、runtime config、测试文件或打包脚本，因此未运行完整业务测试、UI 测试、source smoke、packaged smoke 或打包命令。

## 结论

D1 已创建明确命名的源码开发入口：

```text
/Users/changdali/Desktop/BioMedPilot v1.0 Dev.command
```

该入口只指向：

```text
/Users/changdali/Developer/biomedpilot v1.0/MainLine
```

它会打印 source root、branch、commit、status summary 和 Developer Preview / internal testing 提示，然后从 MainLine 源码执行 `python3 -m app.main`。本任务没有覆盖旧 `BioMedPilot.app`，没有创建 `.app` 包，没有修改业务代码、UI、测试或打包脚本。
