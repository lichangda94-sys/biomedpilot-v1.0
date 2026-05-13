# BioMedPilot v1.0 Worktree Dirty State Audit

审计时间：2026-05-13 13:28:17 CST

范围：

- `/Users/changdali/Developer/biomedpilot v1.0`
- `MainLine`
- `Bioinformatics`
- `Meta`
- `Vocabulary`
- `UIShell`
- `LabTools`
- `AI`
- `Integration`
- `ReleaseBuild`

## 已阅读的总控文件

- `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/handoff/Global_Development_Manual.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/handoff/BioMedPilot_v1_global_control_audit_20260513.md`

两份 `Global_Development_Manual.md` 已用 `cmp` 检查，结果同步。

## Worktree 状态摘要

命令：

```bash
git --git-dir _repo.git worktree list --porcelain
```

结果摘要：

| Worktree | Branch | HEAD |
| --- | --- | --- |
| `_repo.git` | bare repository | not editable |
| `AI` | `dev/ai-gateway` | `2a2d1da444f62746d0728d9b5764995da5da7701` |
| `Bioinformatics` | `dev/bioinformatics` | `bf3cb2860f1f825479b8bdf0764927eb3c5f8f0b` |
| `Integration` | `dev/integration` | `80351d49f1adab0aabde52c62ba7c487e6d997dc` |
| `LabTools` | `dev/labtools` | `c2416e142568377663ded0162e97f745429345a5` |
| `MainLine` | `stable/mainline` | `f68d2b53e57cb655a644d9bc613b9a171a3dd46f` |
| `Meta` | `dev/meta-analysis` | `00765f49a8e37573ccf5fb18198ac36a2f105dea` |
| `ReleaseBuild` | `dev/release-internal-test` | `67e5b138ae38c2350caf7d19d7724f018653f92b` |
| `UIShell` | `dev/ui-shell` | `391c882c560760fd09b1b95cd6d3c3ab89d38e8e` |
| `Vocabulary` | `dev/shared-vocabulary` | `9c73d6a0af61f7b38e020200f9eb1c31b1a3aada` |

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
clean before this report was created

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

## Bioinformatics 未提交改动审计

当前 `Bioinformatics` worktree 没有未提交改动。

命令：

```bash
git -C Bioinformatics diff --stat
git -C Bioinformatics diff --name-only
git -C Bioinformatics diff --check
```

结果：

- `git diff --stat`：无输出。
- `git diff --name-only`：无输出。
- `git diff --check`：通过，无输出。

未提交改动文件列表：无。

Diff 摘要：无 diff 可审计。

归属判断：

- 当前没有 Bioinformatics dirty files，因此没有可归属到当前任务或先前任务的未提交业务代码。
- 不能从当前 dirty diff 判断是否存在曾经未提交、后来已被提交或清理的 Bioinformatics 改动。
- 当前主控层文档补强任务未在 Bioinformatics 中留下未提交改动。

风险判断：

- 未发现 LabTools 功能进入 Bioinformatics。
- 未发现 PubMed / 文献检索进入 Bioinformatics 的 dirty diff。
- 未发现 AI Gateway、网络、隐私、真实分析执行器、删除或移动高风险文件相关 dirty diff。

## LabTools 未提交改动审计

当前 `LabTools` worktree 没有未提交改动。

命令：

```bash
git -C LabTools diff --stat
git -C LabTools diff --name-only
git -C LabTools diff --check
```

结果：

- `git diff --stat`：无输出。
- `git diff --name-only`：无输出。
- `git diff --check`：通过，无输出。

未提交改动文件列表：无。

Diff 摘要：无 diff 可审计。

归属判断：

- 当前没有 LabTools dirty files，因此没有可归属到当前任务或先前任务的未提交业务代码。
- 不能从当前 dirty diff 判断是否存在曾经未提交、后来已被提交或清理的 LabTools 改动。
- 当前主控层文档补强任务未在 LabTools 中留下未提交改动。

风险判断：

- 未发现 LabTools dirty diff 跨入 Bioinformatics、Meta 或 MainLine。
- 未发现 LabTools 图像分析、计算器、单位换算、配方检索等功能误入 Bioinformatics 或 Meta 的 dirty diff。
- 未发现 LabTools 引入 AI Gateway、网络、隐私、真实分析执行器、删除或移动高风险文件相关 dirty diff。

## 是否属于当前任务

本次任务开始时，所有列出的 worktree 在 `git status --short` 层面均为 clean。创建本报告之前，MainLine 也为 clean。

因此：

- Bioinformatics 当前没有未提交改动，不属于当前任务。
- LabTools 当前没有未提交改动，不属于当前任务。
- 当前任务只新增本审计报告。

## 跨模块污染判断

基于当前 `git status --short`、`git diff --stat`、`git diff --name-only` 和 `git diff --check`：

- 未发现 Bioinformatics 和 LabTools 的未提交跨模块污染。
- 未发现 Bioinformatics / Meta 职责边界混淆的 dirty diff。
- 未发现 LabTools 功能误入 Bioinformatics / Meta 的 dirty diff。
- 未发现 UI 主题体系偏离的 dirty diff。
- 未发现 AI / 网络 / 隐私边界改变的 dirty diff。
- 未发现真实 Bioinformatics 执行器或真实 Meta 统计执行器接入的 dirty diff。
- 未发现删除或移动高风险文件的 dirty diff。

注意：本结论只覆盖当前未提交改动状态，不评价历史提交内容。

## 是否需要人工决定

当前没有 Bioinformatics 或 LabTools 未提交改动，因此没有 dirty files 需要在本任务中决定保留、回滚、拆分、继续或提交。

如人工预期仍存在上一轮未完成改动，需要另开任务检查对应分支最近提交或 reflog；本次审计按用户授权范围只检查当前未提交状态，不追溯历史提交。

建议：

- 保留并提交：不适用；当前无 Bioinformatics / LabTools dirty files。
- 回滚：不适用；当前无 Bioinformatics / LabTools dirty files。
- 拆分成单独阶段：不适用；当前无 Bioinformatics / LabTools dirty files。
- 继续原任务：不适用；当前无 Bioinformatics / LabTools dirty files。

## 本次未修改哪些内容

- 未修改 Bioinformatics 业务代码。
- 未修改 LabTools 业务代码。
- 未修改 Meta、Vocabulary、UIShell、AI、Integration、ReleaseBuild。
- 未修改 MainLine 业务代码、测试、配置、打包脚本或运行入口。
- 未删除文件。
- 未回滚文件。
- 未合并分支。
- 未提交 Bioinformatics 或 LabTools。
- 未 push。
- 未继续任何 LabTools 中断任务。
- 未将任何 Bioinformatics 改动并入 MainLine。
- 未运行或修复业务测试。

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

### 总手册同步

命令：

```bash
cmp "01_ProjectControl/Global_Development_Manual.md" "MainLine/docs/handoff/Global_Development_Manual.md"
printf 'cmp_exit=%s\n' "$?"
```

结果：

```text
cmp_exit=0
```

### 分支确认

命令：

```bash
for d in MainLine Bioinformatics Meta Vocabulary UIShell LabTools AI Integration ReleaseBuild; do
  printf '%s ' "$d"
  git -C "$d" branch --show-current
done
```

结果：

```text
MainLine stable/mainline
Bioinformatics dev/bioinformatics
Meta dev/meta-analysis
Vocabulary dev/shared-vocabulary
UIShell dev/ui-shell
LabTools dev/labtools
AI dev/ai-gateway
Integration dev/integration
ReleaseBuild dev/release-internal-test
```

### Diff 检查

命令：

```bash
git -C Bioinformatics diff --stat
git -C Bioinformatics diff --name-only
git -C Bioinformatics diff --check
git -C LabTools diff --stat
git -C LabTools diff --name-only
git -C LabTools diff --check
```

结果：

```text
Bioinformatics: no diff; diff --check passed.
LabTools: no diff; diff --check passed.
```

### 本报告提交前检查

命令：

```bash
git -C MainLine diff --check
```

结果：通过，无输出。

## 结论

本次 worktree 清洁度与未提交改动归属审计未发现 Bioinformatics 或 LabTools 当前存在未提交改动。当前没有可归属、可拆分、可回滚、可继续或可提交的 Bioinformatics / LabTools dirty files。

本任务的唯一预期变更是新增 MainLine handoff 审计报告。
