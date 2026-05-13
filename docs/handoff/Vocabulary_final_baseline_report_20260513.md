# Vocabulary Final Baseline Report

日期：2026-05-13

工作区：`/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`

分支：`dev/release-internal-test`

目标：归档 Vocabulary V0.0-V0.4 shared vocabulary scoped baseline，确认共享词库已经完成 Vocabulary、Integration、MainLine 到 ReleaseBuild 的 scoped apply / scoped sync / packaging resource validation，并明确剩余风险不属于 Vocabulary 主线。

## 1. 阶段总览

Vocabulary V0.0-V0.4 已完成共享词库主线阻塞审计、合入策略、Integration scoped apply、MainLine scoped apply、ReleaseBuild scoped sync 和 package smoke。

本 baseline 的结论：

- shared vocabulary 是共享能力，不属于 Bioinformatics 专属，也不属于 Meta Analysis 专属。
- `dev/shared-vocabulary` 仍禁止整分支合并。
- MainLine 和 ReleaseBuild 均已通过 scoped apply / scoped sync 接收已验证的 shared vocabulary baseline。
- `data/medical_terms/` 默认安全子集已进入 ReleaseBuild，并已在 packaged app 中验证存在。
- `medical_terms_index.sqlite` 仍是可选派生资源，不是运行硬依赖。
- V0.4 遗留的 UI 失败是 ReleaseBuild / UIShell / Bioinformatics workspace compatibility 风险，不是 Vocabulary 主线风险。

## 2. V0.0-V0.4 Commit 链路

| 阶段 | Commit | Worktree | 核心产物 |
| --- | --- | --- | --- |
| V0.0 / predevelopment audit | `ee8954c` | Vocabulary | `Vocabulary_predevelopment_blocker_audit_20260513.md` |
| V0.1 / scoped merge strategy | `9c73d6a` | Vocabulary | scoped merge plan、resource packaging strategy、merge checklist、README、merge readiness tests |
| V0.2 / Integration scoped apply | `ba41dca` | Integration | Integration scoped apply、packaging resource copy 最小修复、V0.2 report |
| V0.3 / MainLine scoped apply | `15a40bd` | MainLine | MainLine scoped vocabulary baseline、packaging resource copy、V0.3 report |
| V0.4 / ReleaseBuild scoped sync | `c74f207` | ReleaseBuild | ReleaseBuild scoped sync、package smoke、packaged resource presence check、V0.4 report |

## 3. 每个阶段实际修改 Worktree

- V0.0：只修改 Vocabulary，新增开发前阻塞审计报告。
- V0.1：只修改 Vocabulary，新增 scoped merge plan、资源与 packaging 策略、MainLine checklist、README 和最小回归测试。
- V0.2：只修改 Integration，执行 shared vocabulary scoped apply 验证，并补齐 packaging resource copy 最小修复。
- V0.3：只修改 MainLine，按 V0.1/V0.2 结果执行 MainLine scoped apply 和 packaging resource copy 同步。
- V0.4：只修改 ReleaseBuild，按 V0.3 结果执行 ReleaseBuild scoped sync、package smoke 和包内资源检查。

V0.0-V0.4 均未执行整分支 merge，未推送 GitHub，未调用外部 AI，未执行真实网络检索。

## 4. 每个阶段核心结论

### V0.0

- `dev/shared-vocabulary` 不能整分支直合 MainLine。
- 阻塞来自非词库差异、MainLine handoff / cleanup / archive 删除风险，以及 packaging 未复制 `data/medical_terms/`。
- 需要 scoped merge / scoped apply。

### V0.1

- 建立只合入词库相关内容的 scoped merge plan。
- 明确 `zh_term_overrides.json` 是人工维护源数据。
- 明确 `mini_medical_terms_index.json` 是可提交的最小运行时索引 / 规范化资源。
- 明确 SQLite 是 optional derived resource，不应成为 MainLine 运行硬依赖。
- 建立 MainLine merge checklist 和最小 readiness tests。

### V0.2

- Integration scoped apply 成功。
- packaging 最小修复通过：默认复制 `data/medical_terms/` 安全子集。
- 默认不复制 SQLite、raw ontology、cache、临时输出。
- Integration 记录了非词库 UI / Bioinformatics workspace 构造接口失败。

### V0.3

- MainLine scoped apply 成功。
- MainLine 同步 shared vocabulary baseline 和 packaging resource copy。
- 包内资源验证通过。
- MainLine `tests/ui` 通过。
- `tests/shared` 曾有 AI audit 文档缺失的非词库遗留风险；未作为 Vocabulary 问题处理。

### V0.4

- ReleaseBuild scoped sync 成功。
- package smoke、packaged app CLI smoke、resource presence check 均通过。
- `tests/shared`、`tests/bioinformatics`、`tests/meta_analysis` 通过。
- `tests/ui` 仍有 `BioinformaticsWorkspaceWidget() takes no arguments` 失败，已记录为非词库 ReleaseBuild / UI 边界风险。

## 5. 当前 MainLine 状态

MainLine 已完成 V0.3 scoped apply：

- 已包含 shared vocabulary runtime baseline。
- 已包含 `data/medical_terms/` 默认安全子集。
- 已同步 `scripts/package_app.py` packaging resource copy。
- 已验证包内 resources 存在。
- `tests/ui -q` 在 MainLine V0.3 通过：`139 passed`。
- `tests/shared -q` 在 MainLine V0.3 有 2 个非词库 AI audit 文档缺失失败，原因是 `docs/ai_gateway_ollama_existing_call_audit.md` 在 MainLine 当时不存在；该问题不属于 Vocabulary scoped apply。

MainLine 仍禁止整分支合并 `dev/shared-vocabulary`。

## 6. 当前 ReleaseBuild 状态

ReleaseBuild 已完成 V0.4 scoped sync：

- 当前 scoped sync commit：`c74f207`。
- 已同步 MainLine V0.3 验证过的 shared vocabulary baseline。
- 已同步 packaging resource copy。
- 已完成 ReleaseBuild package smoke。
- 已完成 packaged app CLI smoke。
- 已完成包内 `data/medical_terms/` 默认安全子集存在性检查。
- `tests/shared -q`：`225 passed`。
- `tests/bioinformatics -q`：`264 passed`。
- `tests/meta_analysis -q`：`3 passed`。
- `tests/ui -q`：`6 failed, 40 passed, 87 skipped`，失败为非词库 UI / Bioinformatics workspace compatibility 风险。

ReleaseBuild 可作为 shared vocabulary scoped baseline 的当前 release 构建基线，但如果 release gate 要求 UI 全绿，应先开独立 UIShell / Bioinformatics compatibility 修复任务。

## 7. 当前资源策略

当前 `data/medical_terms/` 资源策略如下：

- `zh_term_overrides.json` 是人工维护源数据。
- `mini_medical_terms_index.json` 是可提交的最小运行时索引 / 规范化资源。
- `data/medical_terms/` 默认安全子集应进入 MainLine / ReleaseBuild / package。
- 默认安全子集包括：
  - `mini_medical_terms_index.json`
  - `zh_term_overrides.json`
  - `source_metadata.json`
  - `license_attribution.md`
  - `reference_checklists/`
- `medical_terms_index.sqlite` 是可选派生资源，不是运行硬依赖。
- raw ontology 不默认进入 Git 或 package。
- cache、临时覆盖率输出、用户输入、日志数据不得进入 package。
- SQLite 若未来进入 Release artifact，必须有 artifact policy、schema、生成命令、checksum、term count 和 optional status。

`coverage_audit_report.json` 当前作为审计快照随 scoped baseline 进入 ReleaseBuild；它不是用户数据，也不是 runtime 硬依赖。

## 8. 当前 Packaging 策略

当前 packaging 策略如下：

- `scripts/package_app.py` 已同步复制 `data/medical_terms/` 默认安全子集。
- 包内资源验证已通过。
- 包内存在：
  - `mini_medical_terms_index.json`
  - `zh_term_overrides.json`
  - `source_metadata.json`
  - `license_attribution.md`
  - `reference_checklists/`
- 包内不存在：
  - `medical_terms_index.sqlite`
  - raw ontology
- 打包路径不得依赖开发机绝对路径。
- 缺失资源时不得静默假成功。
- ReleaseBuild package smoke 已通过。

V0.4 验证的包内路径为：

```text
/tmp/biomedpilot-vocab-v0-4-package/BioMedPilot.app/Contents/Resources/app/data/medical_terms/
```

该路径是 package resource root 下的相对资源布局，不是运行时硬编码开发机路径。

## 9. 当前 SQLite 策略

当前 SQLite 策略如下：

- `medical_terms_index.sqlite` 未进入 ReleaseBuild scoped sync。
- `medical_terms_index.sqlite` 不是 MainLine 或 ReleaseBuild 运行硬依赖。
- SQLite 缺失时 JSON fallback 可用。
- `active_index_status()` 在 V0.4 显示 `full_index_available=False`、`mini_index_available=True`。
- `lookup_medical_terms("脑胶质瘤", target_context="bioinformatics")` 可通过 `zh_term_overrides`、`mini_medical_terms_index` 和 registry fallback 命中。
- SQLite 可作为后续 ReleaseBuild artifact candidate，但本 baseline 默认不带入。
- 若后续决定将 SQLite 纳入 package 或 Git，必须补充 artifact policy、schema、生成命令、checksum、term count 和 optional status。

## 10. Bioinformatics / Meta / AI / Privacy 边界

### Bioinformatics 边界

- Bioinformatics 不得执行 PubMed 检索。
- Bioinformatics 中文主题检索不得返回 PubMed-only / Meta-only 能力。
- Bioinformatics 仍只面向 GEO / TCGA / GTEx 等生信数据检索与导入语境。
- Bioinformatics TCGA / GTEx / tissue fallback 去重属于后续 Bioinformatics 模块任务，不属于 Vocabulary V0.5。
- Vocabulary V0.0-V0.4 未把 PubMed 接入 Bioinformatics。

### Meta Analysis 边界

- Meta 不得触发 GEO / TCGA / GTEx 生信流程。
- Meta 可以使用 PubMed 检索策略草稿语境，但不得污染 Bioinformatics。
- Meta confirmed / user edited 治理状态属于后续 Meta 阶段任务，不属于 Vocabulary V0.5。
- Vocabulary V0.0-V0.4 未开发 Meta 检索执行、筛选、统计或报告流程。

### AI / Privacy 边界

- Vocabulary 不得直接调用 Ollama。
- Vocabulary 不得调用外部 AI。
- Vocabulary 不得真实网络检索。
- Ontology 下载默认关闭，必须显式开启。
- 不得记录 raw prompt / raw response。
- 不得默认持久化用户输入全文。
- MainLine 曾记录 AI audit 文档缺失风险；ReleaseBuild 未复现。该问题若再出现，应走独立 AI / docs cleanup，不属于 Vocabulary V0.5。

## 11. 测试基线

V0.4 最终验证结果如下：

- `git diff --check`：通过。
- `git diff --cached --check`：通过。
- `python3 -m app.main --smoke-test`：通过。
- 最小 vocabulary / packaging pytest：`75 passed`。
- coverage audit：`covered=621/621`，`weighted_coverage_rate=1.0`。
- ReleaseBuild package smoke：通过。
- packaged app CLI smoke / resource presence check：通过。
- `tests/shared -q`：`225 passed`。
- `tests/bioinformatics -q`：`264 passed`。
- `tests/meta_analysis -q`：`3 passed`。
- `tests/ui -q`：`6 failed, 40 passed, 87 skipped`。

`tests/ui` 失败说明：

- 失败集中为 `BioinformaticsWorkspaceWidget() takes no arguments`。
- 已记录为非词库 ReleaseBuild / UI 边界风险。
- Vocabulary V0.5 不修复该问题。
- 如果 release gate 要求全绿，应新开独立 UIShell / Bioinformatics compatibility 修复任务。

## 12. Package Smoke 与包内资源验证结论

V0.4 已执行 ReleaseBuild package smoke：

```bash
QT_QPA_PLATFORM=offscreen python3 scripts/package_app.py --output-dir /tmp/biomedpilot-vocab-v0-4-package --smoke-test
```

结果：

- package build：通过。
- packaged launcher smoke：通过。
- `launch_mode=packaged-local-python`。
- `network_downloads=false`。
- `packaged_medical_terms_resources=pass`。

包内资源检查结论：

- `data/medical_terms/mini_medical_terms_index.json` 存在。
- `data/medical_terms/zh_term_overrides.json` 存在。
- `data/medical_terms/source_metadata.json` 存在。
- `data/medical_terms/license_attribution.md` 存在。
- `data/medical_terms/reference_checklists/` 存在。
- `data/medical_terms/medical_terms_index.sqlite` 不存在。
- `data/medical_terms/raw/` 不存在。

因此，V0.0 审计中记录的 packaging 不复制 `data/medical_terms/` Blocking 风险，在 MainLine V0.3 和 ReleaseBuild V0.4 scoped baseline 中已经解决。

## 13. 当前仍禁止的操作

仍禁止：

- 整分支合并 `dev/shared-vocabulary`。
- 整分支合并 MainLine 到 ReleaseBuild。
- 整分支合并 Integration 到 ReleaseBuild。
- 将非词库 UI、Bioinformatics、Meta、AI Gateway、LabTools 差异包装成 Vocabulary 变更。
- 将 PubMed 接入 Bioinformatics。
- 将 GEO / TCGA / GTEx 接入 Meta。
- 默认打包 `medical_terms_index.sqlite`。
- 默认打包 raw ontology、cache、临时覆盖率输出、用户输入、日志数据。
- 真实联网、调用 Ollama、调用外部 AI。
- 保存 raw prompt、raw response 或不必要的用户输入全文。
- 在 Vocabulary 阶段修复 UI / Bioinformatics workspace compatibility 或 AI docs cleanup。

## 14. 当前遗留风险

当前遗留风险均不阻塞 shared vocabulary baseline 本身：

| 风险 | 等级 | 归属 | 说明 |
| --- | --- | --- | --- |
| ReleaseBuild `tests/ui` 6 个失败 | High | UIShell / Bioinformatics compatibility | `BioinformaticsWorkspaceWidget() takes no arguments`；不是 Vocabulary diff 范围 |
| Meta confirmed / user edited 治理状态未完整实现 | Medium | Meta Analysis | 后续 Meta 检索执行前必须补齐 |
| Bioinformatics TCGA / GTEx / tissue fallback 去重 | Medium | Bioinformatics | 后续可改为优先消费 shared vocabulary draft/audit |
| SQLite artifact policy 未定 | Medium | ReleaseBuild / Vocabulary governance | 只有未来决定打包或跟踪 SQLite 时才需要补 checksum、schema、term count |
| MainLine AI audit 文档缺失曾被记录 | Low/Medium | AI / docs cleanup | ReleaseBuild 未复现；若再出现应走独立 AI/docs cleanup |

## 15. 下一步建议

建议下一步：

1. 将 Vocabulary V0.0-V0.5 视为 shared vocabulary scoped baseline 完成。
2. 如需 internal beta package rebuild，可基于 ReleaseBuild 当前 scoped baseline 执行。
3. 如果 release gate 要求 UI 全绿，单独开 UIShell / Bioinformatics compatibility 修复任务，处理 `BioinformaticsWorkspaceWidget() takes no arguments`。
4. 单独开 Meta 阶段任务处理 confirmed / user edited 检索治理状态。
5. 单独开 Bioinformatics 阶段任务处理 TCGA / GTEx / tissue fallback 去重。
6. 继续保持 SQLite optional derived resource 策略；未来如纳入 Release artifact，先补 artifact policy。

## 16. V0.5 操作声明

本阶段只新增最终 baseline 文档：

- `docs/handoff/Vocabulary_final_baseline_report_20260513.md`

本阶段未修改业务代码，未修改 Bioinformatics / Meta / AI / UI，未执行真实网络访问，未调用 Ollama 或外部 AI，未删除文件，未跨 worktree 写入。
