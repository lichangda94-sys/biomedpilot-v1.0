# BioMedPilot v1.0 Desktop Entry D0.1 Old Desktop Entries Cleanup

日期：2026-05-13

执行 worktree：

```text
/Users/changdali/Developer/biomedpilot v1.0/MainLine
```

分支与 HEAD：

```text
stable/mainline
db669939d7bd7d91ba6a503a077b35c7d02c864a
```

范围：只清理用户明确授权的三个 Desktop 旧 BioMedPilot 入口。

- `/Users/changdali/Desktop/BioMedPilot.app`
- `/Users/changdali/Desktop/BioMedPilot 2.app`
- `/Users/changdali/Desktop/BioMedPilot 3.app`

本次未创建 D1 开发入口，未修改业务代码，未修改 UI，未修改打包脚本，未 push，未 merge。

## 已阅读文件

- `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/handoff/Global_Development_Manual.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/handoff/BioMedPilot_v1_desktop_entry_audit_20260513.md`

两份 `Global_Development_Manual.md` 已用 `cmp` 检查，结果同步。

## 清理前桌面入口列表

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

- `/Users/changdali/Desktop/BioMedPilot v1.0 Dev.command`
- `/Users/changdali/Desktop/BioMedPilot v1.0 Dev.app`

## 清理前目标检查

### `/Users/changdali/Desktop/BioMedPilot.app`

类型：symlink。

只读检查结果：

```text
/Users/changdali/Desktop/BioMedPilot.app -> /Users/changdali/Applications/BioMedPilot.app
realpath=/Users/changdali/Applications/BioMedPilot.app
```

metadata 摘要：

```text
source_root=/Users/changdali/Developer/BioMedPilot
git_head=e97d87e
channel=Developer Preview / testing
launch_mode=packaged-local-python
```

来源判断：

- 不是当前 v1.0 MainLine 来源。
- metadata 未指向 `/Users/changdali/Developer/biomedpilot v1.0/MainLine`。
- `git_head=e97d87e` 不是当前 MainLine HEAD。
- 本任务只移动 Desktop symlink 本身，不移动、不删除 `/Users/changdali/Applications/BioMedPilot.app`。

安全确认：

- 不是 `/Users/changdali/Developer/biomedpilot v1.0/MainLine`。
- 不是 `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`。
- 不是 `/Users/changdali/Developer/biomedpilot v1.0/_repo.git`。
- 不是源码目录。
- 不是新的 v1.0 Dev 入口。

### `/Users/changdali/Desktop/BioMedPilot 2.app`

类型：app bundle。

只读检查结果：

```text
realpath=/Users/changdali/Desktop/BioMedPilot 2.app
is_symlink=no
```

metadata 摘要：

```text
source_root=/Users/changdali/Documents/BioMedPilot
git_head=1ab89e1
channel=Developer Preview / testing
launch_mode=packaged-local-python
```

来源判断：

- 明确来自旧路径 `/Users/changdali/Documents/BioMedPilot`。
- `git_head=1ab89e1` 不是当前 MainLine HEAD。
- 属于旧桌面打包遗留，不是当前 v1.0 MainLine 新入口。

安全确认：

- 不是 `/Users/changdali/Developer/biomedpilot v1.0/MainLine`。
- 不是 `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`。
- 不是 `/Users/changdali/Developer/biomedpilot v1.0/_repo.git`。
- 不是源码目录。
- 不是新的 v1.0 Dev 入口。

### `/Users/changdali/Desktop/BioMedPilot 3.app`

类型：app bundle。

只读检查结果：

```text
realpath=/Users/changdali/Desktop/BioMedPilot 3.app
is_symlink=no
```

metadata 摘要：

```text
source_root=/Users/changdali/Documents/BioMedPilot
git_head=8a75113
channel=Developer Preview / testing
launch_mode=packaged-local-python
```

来源判断：

- 明确来自旧路径 `/Users/changdali/Documents/BioMedPilot`。
- `git_head=8a75113` 不是当前 MainLine HEAD。
- 属于旧桌面打包遗留，不是当前 v1.0 MainLine 新入口。

安全确认：

- 不是 `/Users/changdali/Developer/biomedpilot v1.0/MainLine`。
- 不是 `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`。
- 不是 `/Users/changdali/Developer/biomedpilot v1.0/_repo.git`。
- 不是源码目录。
- 不是新的 v1.0 Dev 入口。

## 实际移动结果

创建隔离目录：

```text
/Users/changdali/Desktop/BioMedPilot_old_desktop_entries_20260513
```

实际移动：

```text
/Users/changdali/Desktop/BioMedPilot.app
-> /Users/changdali/Desktop/BioMedPilot_old_desktop_entries_20260513/BioMedPilot.app

/Users/changdali/Desktop/BioMedPilot 2.app
-> /Users/changdali/Desktop/BioMedPilot_old_desktop_entries_20260513/BioMedPilot 2.app

/Users/changdali/Desktop/BioMedPilot 3.app
-> /Users/changdali/Desktop/BioMedPilot_old_desktop_entries_20260513/BioMedPilot 3.app
```

`BioMedPilot.app` 移动后仍是 symlink：

```text
/Users/changdali/Desktop/BioMedPilot_old_desktop_entries_20260513/BioMedPilot.app -> /Users/changdali/Applications/BioMedPilot.app
```

本任务未使用 `rm -rf`，未永久删除上述旧入口。

## 明确未删除内容

本任务没有删除：

- `/Users/changdali/Applications/BioMedPilot.app`
- `/Users/changdali/Developer/biomedpilot v1.0`
- `/Users/changdali/Developer/biomedpilot v1.0/_repo.git`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine`
- `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`
- 任何源码目录
- 任何用户项目数据
- 任何新的 v1.0 Dev `.command`
- Bioinformatics、Meta、Vocabulary、UIShell、LabTools、AI、Integration 的业务代码

## 清理后桌面状态

命令：

```bash
ls -la "$HOME/Desktop" | grep -i "BioMedPilot" || true
```

结果：

```text
drwxr-xr-x@  3 changdali  staff     96 Apr 28 20:09 BioMedPilot
-rw-r--r--@  1 changdali  staff  31441 May 13 09:27 BioMedPilot_UI_audit_handoff_2026-05-13.md
drwxr-xr-x@  5 changdali  staff    160 May 13 13:53 BioMedPilot_old_desktop_entries_20260513
drwxr-xr-x@  7 changdali  staff    224 May 10 16:09 BioMedPilot测试数据
```

确认三个旧 Desktop `.app` 入口已不在原位置：

```text
/Users/changdali/Desktop/BioMedPilot.app: not-on-desktop
/Users/changdali/Desktop/BioMedPilot 2.app: not-on-desktop
/Users/changdali/Desktop/BioMedPilot 3.app: not-on-desktop
```

## 隔离目录状态

命令：

```bash
ls -la "$HOME/Desktop/BioMedPilot_old_desktop_entries_20260513" || true
```

结果：

```text
total 0
drwxr-xr-x@  5 changdali  staff  160 May 13 13:53 .
drwx------@ 21 changdali  staff  672 May 13 13:53 ..
drwx------@  3 changdali  staff   96 May 12 11:38 BioMedPilot 2.app
drwx------@  3 changdali  staff   96 May 12 17:58 BioMedPilot 3.app
lrwxr-xr-x@  1 changdali  staff   45 May 12 21:32 BioMedPilot.app -> /Users/changdali/Applications/BioMedPilot.app
```

## 保护对象复核

命令：

```bash
for p in "$HOME/Applications/BioMedPilot.app" \
  "/Users/changdali/Developer/biomedpilot v1.0" \
  "/Users/changdali/Developer/biomedpilot v1.0/_repo.git" \
  "/Users/changdali/Developer/biomedpilot v1.0/MainLine" \
  "/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild"; do
  ls -ld "$p"
done
```

结果摘要：上述对象均存在。

## Worktree 状态

命令：

```bash
for d in MainLine Bioinformatics Meta Vocabulary UIShell LabTools AI Integration ReleaseBuild; do
  printf '\n[%s]\n' "$d"
  git -C "/Users/changdali/Developer/biomedpilot v1.0/$d" status --short
done
```

结果：所有列出的 worktree 均为 clean。

## 后续建议

1. 下一步 D1 创建源码开发入口：

```text
/Users/changdali/Desktop/BioMedPilot v1.0 Dev.command
```

2. D1 `.command` 应指向：

```text
/Users/changdali/Developer/biomedpilot v1.0/MainLine
```

并在启动时显示 `branch`、`git_head`、`channel`、`Developer Preview`、`source_root`。

3. 后续正式 `.app` 打包入口应由 `ReleaseBuild` 基于 validated MainLine 或 validated release source 生成，并执行 package smoke 和 packaged app smoke。

4. 在新的 `.app` 验证完成前，不建议恢复通用桌面名 `BioMedPilot.app`，以免再次混淆旧路径、旧 commit 与当前 v1.0 MainLine。

## 验证命令与结果

### 位置与分支

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
git status --short: clean before report creation
```

### 总手册同步

命令：

```bash
cmp -s /Users/changdali/Developer/biomedpilot\ v1.0/01_ProjectControl/Global_Development_Manual.md /Users/changdali/Developer/biomedpilot\ v1.0/MainLine/docs/handoff/Global_Development_Manual.md
printf 'manual_cmp_exit=%s\n' "$?"
```

结果：

```text
manual_cmp_exit=0
```

### 目标只读检查

命令：

```bash
for p in "$HOME/Desktop/BioMedPilot.app" "$HOME/Desktop/BioMedPilot 2.app" "$HOME/Desktop/BioMedPilot 3.app"; do
  ls -ld "$p"
  readlink "$p" || true
  realpath "$p" 2>/dev/null || true
  sed -n '1,120p' "$p/Contents/Resources/app/BUILD_INFO.json"
  plutil -p "$p/Contents/Info.plist"
done
```

结果摘要：

```text
BioMedPilot.app: symlink to /Users/changdali/Applications/BioMedPilot.app; source_root=/Users/changdali/Developer/BioMedPilot; git_head=e97d87e
BioMedPilot 2.app: app bundle; source_root=/Users/changdali/Documents/BioMedPilot; git_head=1ab89e1
BioMedPilot 3.app: app bundle; source_root=/Users/changdali/Documents/BioMedPilot; git_head=8a75113
```

### 移动命令

命令：

```bash
archive="$HOME/Desktop/BioMedPilot_old_desktop_entries_20260513"
mkdir -p "$archive"
for p in "$HOME/Desktop/BioMedPilot.app" "$HOME/Desktop/BioMedPilot 2.app" "$HOME/Desktop/BioMedPilot 3.app"; do
  mv "$p" "$archive/"
done
```

结果：三个目标均移动到隔离目录。`BioMedPilot.app` 只移动 symlink 本身。

### 用户要求的清理后验证

命令：

```bash
ls -la "$HOME/Desktop" | grep -i "BioMedPilot" || true
ls -la "$HOME/Desktop/BioMedPilot_old_desktop_entries_20260513" || true
git diff --check
```

结果：

- Desktop 列表只剩普通目录、测试数据、旧 UI 审计文档和隔离目录。
- 隔离目录包含 `BioMedPilot.app` symlink、`BioMedPilot 2.app`、`BioMedPilot 3.app`。
- `git diff --check`：通过，无输出。

## 业务测试说明

本任务只移动 Desktop 上明确授权的旧入口，并只新增 Markdown 清理报告。未修改业务代码、UI、runtime config、测试文件或打包脚本，因此未运行完整业务测试、UI 测试、source smoke、packaged smoke 或打包命令。

## 结论

三个旧 Desktop BioMedPilot `.app` 入口已安全移入：

```text
/Users/changdali/Desktop/BioMedPilot_old_desktop_entries_20260513
```

`/Users/changdali/Applications/BioMedPilot.app`、v1.0 源码根、`_repo.git`、MainLine、ReleaseBuild 和所有业务代码均未删除、未修改。下一步应创建明确命名的 `BioMedPilot v1.0 Dev.command`，正式 `.app` 入口留给后续 ReleaseBuild 阶段。
