# BioMedPilot v1.0 Global Control Audit

日期：2026-05-13

范围：

- `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/handoff/Global_Development_Manual.md`
- `/Users/changdali/Developer/biomedpilot v1.0/MainLine/docs/handoff/BioMedPilot_v1_global_control_audit_20260513.md`

## 当前已有原则

本次审计前，主控层文档已经覆盖以下原则：

- BioMedPilot / 医研智析 v1.0 是 Developer Preview / internal beta / local testing build，不是 production-ready、clinical-grade 或 submission-grade。
- v1.0 本地主目录使用 `_repo.git` bare repository 加多 worktree 结构。
- `MainLine`、`Bioinformatics`、`Meta`、`Vocabulary`、`UIShell`、`LabTools`、`AI`、`Integration`、`ReleaseBuild` 已有基本职责边界。
- Bioinformatics 不做 PubMed 文献检索；Meta 不做 GEO / TCGA / GTEx 表达数据分析。
- AI 默认关闭，模型调用必须经过 AI Gateway，不保存 raw prompt / raw response。
- UI Governance / UI Design Principles 是跨模块 UI 规范依据。
- 测试级、草稿、dry-run、preflight、imported result、real computed result 必须清楚区分。
- 用户项目数据、下载数据、PDF、中间分析输出、缓存、构建和打包产物默认不进入 Git。
- MainLine 当前 baseline、架构、cleanup、UI、AI Gateway、Meta governance、Meta statistics、packaging 等文档已分别记录阶段状态和边界。

## 本次补充原则

本次补强了以下主控层内容：

- 增加文件权威性与优先级：`01_ProjectControl/Global_Development_Manual.md` 是最高优先级规则；`MainLine/docs/handoff/Global_Development_Manual.md` 必须与其同步；任务与总手册冲突时 Codex 必须停止并报告。
- 增加强制开发前检查清单：确认路径、worktree、分支、`git status --short`、README、总手册、相关 handoff/audit/baseline，并判断是否涉及跨模块、AI、联网、隐私、真实执行器、删除、合并、打包或发布。
- 增加禁止事项总表：跨模块污染、伪造分析结果、绕过 AI Gateway、默认联网、保存 raw prompt/raw response、把 testing-level 描述为 production-ready、未经授权 push/merge/delete 等。
- 增加必须停止并向人工汇报事项总表：路径或 worktree 不匹配、未知未提交改动、跨模块修改、真实执行器接入、联网或外部 API、保存敏感原文、测试失败且无法安全修复、合并/push/删除/迁移/凭据处理等。
- 补充 Git、分支、worktree、提交、合并、push 规则，强调只提交 in-scope 文件、保留无关改动、不 push。
- 补充文档-only 任务最低验证标准：`git diff --check`、必要时 `cmp`、相关 worktree status，并说明未跑业务测试原因。
- 补充网络访问、数据库检索、外部下载规则，包括模块声明、用户确认、缓存位置、隐私风险、超时和审计字段。
- 补充真实 Bioinformatics 执行器接入门槛。
- 补充真实 Meta 统计执行器接入门槛。
- 补充医学、科研、伦理和临床安全边界，明确本软件仅为研究辅助，不提供诊断、治疗或临床决策。
- 补充 LabTools 未来模块边界，包括浓度计算、单位换算、配方检索、ImageJ/Fiji/OpenCV 图像分析、划痕实验、细胞计数、荧光强度、灰度值分析等能力，并禁止混入 Bioinformatics 或 Meta。
- 补充阶段报告、handoff、audit 文档写作规范。
- 补充打包、版本号、Developer Preview/testing/production-ready 表述规则。
- 补充当前人工待确认事项和下一阶段开发优先级。

## 仍需人工确认事项

- 是否在后续独立 cleanup 阶段处理 tracked historical validation log 和 legacy demo runtime log。
- 是否进一步归档或瘦身 large legacy snapshots、archive materials 和 old docs。
- 是否允许任何真实 Bioinformatics 执行器接入，以及对应依赖、输入输出、验证数据和结果标记规则。
- 是否允许任何真实 Meta 统计执行器升级或替换，以及对应统计方法、验证基线和审计要求。
- 是否允许任何联网、外部数据库检索、外部 API、模型服务、PDF/full text 下载或外部依赖安装。
- 是否允许保存 raw prompt/raw response、敏感原文、凭据、患者级数据、下载数据集、PDF 或全文。
- 是否允许后续 push 到远程；本任务未 push。

## 未修改哪些内容

- 未修改 Bioinformatics、Meta、Vocabulary、AI、UIShell、LabTools、Integration、ReleaseBuild 的业务代码。
- 未修改 MainLine 的业务代码、测试、配置、打包脚本或运行入口。
- 未删除历史文档。
- 未移动大量文件。
- 未处理 tracked logs、legacy snapshots、archive material、示例项目或缓存。
- 未执行合并、push、远程写入或凭据处理。
- 未运行完整业务测试，因为本任务仅修改主控层 Markdown 文档，不涉及业务代码、runtime config、测试文件、打包脚本或入口代码。

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

### Worktree 检查

命令：

```bash
git --git-dir _repo.git worktree list --porcelain
```

结果摘要：

```text
_repo.git                         bare repository
AI                                dev/ai-gateway
Bioinformatics                    dev/bioinformatics
Integration                       dev/integration
LabTools                          dev/labtools
MainLine                          stable/mainline
Meta                              dev/meta-analysis
ReleaseBuild                      dev/release-internal-test
UIShell                           dev/ui-shell
Vocabulary                        dev/shared-vocabulary
```

### Worktree status 检查

命令：

```bash
for d in MainLine Bioinformatics Meta Vocabulary AI UIShell LabTools Integration ReleaseBuild; do
  printf '\n[%s]\n' "$d"
  git -C "$d" status --short
done
```

结果摘要：

```text
[MainLine]
 M docs/handoff/Global_Development_Manual.md
?? docs/handoff/BioMedPilot_v1_global_control_audit_20260513.md

[Bioinformatics]
clean

[Meta]
clean

[Vocabulary]
clean

[AI]
clean

[UIShell]
clean

[LabTools]
pre-existing unrelated app/ and app/labtools/ changes observed; not modified by this task.

[Integration]
clean

[ReleaseBuild]
clean
```

### 总手册同步检查

命令：

```bash
cmp -s 01_ProjectControl/Global_Development_Manual.md MainLine/docs/handoff/Global_Development_Manual.md
printf 'cmp_exit=%s\n' "$?"
```

结果：

```text
cmp_exit=0
```

说明：两份 `Global_Development_Manual.md` 字节级一致。

### Diff whitespace 检查

命令：

```bash
git -C MainLine diff --check -- docs/handoff/Global_Development_Manual.md docs/handoff/BioMedPilot_v1_global_control_audit_20260513.md
```

结果：通过。

## 任务结论

本次审计确认：原有主控层文档已经具备基础边界，但对文件权威性、Codex 开发前检查、停止事项、联网下载、真实执行器接入、医学科研安全、LabTools 未来范围、报告写作规范和 release wording 的集中约束不够明确。

本次已在总开发手册中补齐上述治理规则，并新增本审计报告。外层 ProjectControl 手册与 MainLine handoff 手册已保持同步。
