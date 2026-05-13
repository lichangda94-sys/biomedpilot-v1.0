# ReleaseBuild 打包前审计报告 2026-05-13

## 1. 审计目标

本阶段只审计 ReleaseBuild worktree 的打包前状态，不执行 MainLine 同步、不重新打包、不覆盖桌面入口、不修改业务代码。

重点确认：

- ReleaseBuild worktree 是否存在、分支和 HEAD 是否清晰。
- ReleaseBuild 与 MainLine 当前 HEAD 的差异是否会影响打包。
- 是否仍引用旧项目路径或旧桌面 app 入口。
- 是否存在过期 `.app`、缓存、构建产物或旧 metadata。
- 当前 ReleaseBuild 是否已包含 MainLine 中的 Meta active runtime。
- `app/meta_analysis/legacy/**` 是否进入 active 打包路径。
- 打包脚本是否会覆盖 `/Users/changdali/Desktop/BioMedPilot v1.0 Dev.command`。
- 是否建议进入实际打包阶段。

## 2. Worktree / 分支 / HEAD

项目 worktree 列表确认存在 `ReleaseBuild`：

| Worktree | Branch | HEAD |
|---|---:|---:|
| MainLine | `stable/mainline` | `73d4cc78c358192a2371eab0e866d26af98fba11` |
| Meta | `dev/meta-analysis` | `76f9a0e` |
| Integration | `dev/integration` | `f66be3d` |
| ReleaseBuild | `dev/release-internal-test` | `8b742c00e086ffa1f0f355937518f77465ef396a` |

ReleaseBuild 审计开始时 `git status --short` 无输出，工作区干净。

ReleaseBuild 当前最新提交：

- `8b742c0 docs(release): rebuild internal beta package from release head`

MainLine 当前最新提交：

- `73d4cc7 feat(mainline): apply meta active runtime`

## 3. 与 MainLine 当前 HEAD 的差异

命令：

```bash
git diff --name-status HEAD stable/mainline
git merge-base HEAD stable/mainline
git log --oneline --left-right --cherry-pick HEAD...stable/mainline
```

结论：

- ReleaseBuild 与 MainLine 不是快进关系。
- 两者共同基线为 `67e5b138ae38c2350caf7d19d7724f018653f92b`。
- ReleaseBuild 侧有 release/vocabulary 相关提交未进入 MainLine，例如 `8b742c0`、`43c3cd0`、`c369b26`、`c74f207`。
- MainLine 侧有 Meta active runtime、shared UI、主线治理与架构文档等大量提交未进入 ReleaseBuild。

关键差异类别：

| 类别 | 状态 |
|---|---|
| `CODEX.md` | MainLine 有，ReleaseBuild 当前无。 |
| Meta active runtime | MainLine 有大量 `app/meta_analysis/**` active 文件，ReleaseBuild 当前缺失。 |
| Meta tests | MainLine 有完整 `tests/meta_analysis/**`，ReleaseBuild 当前缺失。 |
| Shared UI token/helper | MainLine 有 `app/shared/ui/**` 与更新后的 `app/ui_style_tokens.py`，ReleaseBuild 当前仍为旧 token。 |
| Bioinformatics | MainLine 与 ReleaseBuild 存在 `app/bioinformatics/**` 差异，需同步时避免误判为 Meta 变更。 |
| docs/archive/handoff | MainLine 已完成文档归档和总控 handoff 更新，ReleaseBuild 当前未同步。 |

## 4. 旧路径与旧桌面入口审计

命令：

```bash
rg -n --hidden --glob '!**/.git/**' --glob '!**/__pycache__/**' \
  "/Users/changdali/Developer/BioMedPilot|/Users/changdali/Documents/BioMedPilot|/Users/changdali/Desktop/BioMedPilot|BioMedPilot v1.0 Dev.command|BioMedPilot.app" .
```

命中统计：

| 模式 | 文件数 | 结论 |
|---|---:|---|
| `/Users/changdali/Developer/BioMedPilot` | 0 | 未发现该旧 Developer 路径。 |
| `/Users/changdali/Documents/BioMedPilot` | 21 | 主要位于历史迁移、旧审计、tester guide 和 legacy 报告文档。 |
| `/Users/changdali/Desktop/BioMedPilot` | 16 | 主要位于 packaging 文档、tester guide 和历史 Meta 报告。 |
| `BioMedPilot v1.0 Dev.command` | 1 | 位于现有 release rebuild 报告，明确记录未覆盖该开发入口。 |

审计判断：

- 当前源码和打包脚本未发现硬编码 `/Users/changdali/Developer/BioMedPilot`。
- `/Users/changdali/Documents/BioMedPilot` 和旧 Desktop app 引用主要是历史文档残留，不是 active runtime 路径。
- `docs/packaging.md` 仍描述 `/Users/changdali/Desktop/BioMedPilot.app` 作为统一桌面测试入口；这不是自动覆盖行为，但在下一阶段需要更新为当前桌面开发入口策略，避免测试人员混淆。
- 当前 release 报告已明确：`/Users/changdali/Desktop/BioMedPilot v1.0 Dev.command` 未被覆盖。

## 5. 构建产物、缓存与旧 metadata

命令：

```bash
find . -maxdepth 4 \( -name '*.app' -o -name '.pytest_cache' -o -name '__pycache__' -o -name 'build' -o -name 'dist' -o -name '*.dmg' -o -name '*.pkg' \) -print
git status --short --ignored dist .pytest_cache app tests docs
```

发现：

- 存在 `dist/BioMedPilot.app`。
- 存在 `.pytest_cache/`。
- 存在多处 ignored `__pycache__/`。
- 未发现 `.dmg` 或 `.pkg`。
- `dist/`、`.pytest_cache/`、`__pycache__/` 当前均为 ignored，未进入 git 跟踪。

现有 app bundle metadata：

```json
{
  "source_root": "/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild",
  "git_head": "43c3cd0",
  "launch_mode": "packaged-local-python",
  "built_at": "2026-05-13T07:27:04.934010+00:00"
}
```

当前 ReleaseBuild 源码 smoke：

```text
launch_mode=source
app_root=/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild
git_head=8b742c0
workspace_entries=2
bioinformatics_features=5
meta_analysis_features=9
```

现有 packaged app smoke：

```text
launch_mode=packaged-local-python
app_root=/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild/dist/BioMedPilot.app/Contents/Resources/app
git_head=43c3cd0
workspace_entries=2
bioinformatics_features=5
meta_analysis_features=9
```

审计判断：

- `dist/BioMedPilot.app` 是旧产物，metadata 指向 `43c3cd0`，落后于当前 ReleaseBuild HEAD `8b742c0`，更落后于 MainLine HEAD `73d4cc7`。
- 该 bundle 不能作为当前 MainLine/Meta 状态的打包验证依据。
- 缓存和旧 bundle 均为 ignored，未污染 git，但实际打包前应在明确授权后重建或清理。

## 6. ReleaseBuild 是否能安全同步 MainLine 当前 commit

当前状态：

- ReleaseBuild 工作区干净。
- MainLine 工作区只读检查为 `stable/mainline` / `73d4cc7`，无 dirty 输出。
- ReleaseBuild 与 MainLine 已分叉，不是直接 fast-forward。

建议同步方式：

1. 不要从 Meta、Integration 或其它模块 worktree 直接打包。
2. 在 ReleaseBuild 中以 MainLine `73d4cc7` 为唯一 release source 进行显式同步。
3. 同步前先决定如何保留 ReleaseBuild 侧 release/vocabulary 文档提交：
   - 可选择从 MainLine 创建新的 release sync commit，再重新生成 release 报告。
   - 或执行受控 merge/cherry-pick，并审计冲突。
4. 同步后必须重新运行测试矩阵、source smoke、package smoke 和 metadata 检查。

结论：ReleaseBuild 可以进入“同步 MainLine 当前 commit 的准备阶段”，但当前状态不建议直接进入实际打包阶段。

## 7. Meta active runtime 是否进入打包源

当前 ReleaseBuild 源码检查：

```text
app/meta_analysis/__init__.py
app/meta_analysis/project_workspace.py
app/meta_analysis/version.py
app/meta_analysis/workspace.py
```

以下 active runtime 文件/目录当前不存在：

```text
app/meta_analysis/literature_import_core.py
app/meta_analysis/adapters/
app/meta_analysis/pages/
app/meta_analysis/services/
```

现有 `dist/BioMedPilot.app` 中的 `app/meta_analysis` 也只有旧入口级文件，未包含 MainLine 中的 Meta active runtime。

审计判断：

- 当前 ReleaseBuild 打包源未包含 MainLine `73d4cc7` 中的 Meta active runtime。
- 因此当前 ReleaseBuild 不能用于 Meta active runtime 内测包。
- 打包脚本会复制 `COPY_DIRS = ("app", "assets", "config", "docs", "examples", "reporting", "scripts")`，所以在 ReleaseBuild 正确同步 MainLine 后，Meta active runtime 会随 `app/` 进入包内。

## 8. legacy 是否进入 active 打包路径

当前 ReleaseBuild 检查：

- `app/meta_analysis/legacy` 不存在。
- `dist/BioMedPilot.app/Contents/Resources/app/app/meta_analysis/legacy` 不存在。
- `rg "_legacy_path|LEGACY_ROOT|app/meta_analysis/legacy|meta_analysis\.legacy"` 在 `app/meta_analysis tests/meta_analysis` 无命中。

MainLine 只读检查：

- `MainLine/app/meta_analysis/legacy` 不存在。
- MainLine 已包含 `app/meta_analysis/literature_import_core.py` 与 `app/meta_analysis/adapters/**`。

审计判断：

- 当前 ReleaseBuild 未把 `app/meta_analysis/legacy/**` 放进 active 打包路径。
- 如果下一阶段只从 MainLine `73d4cc7` 同步，按当前 MainLine 状态也不会引入 `app/meta_analysis/legacy/**`。
- 同步后仍需重复 legacy guard 检查，避免旧分支内容混入。

## 9. 打包脚本是否会覆盖桌面开发入口

检查文件：

- `scripts/package_app.py`
- `docs/packaging.md`
- `docs/release/BioMedPilot_v1_internal_beta_rebuild_20260513.md`

结论：

- `scripts/package_app.py` 默认输出到 ReleaseBuild 内部 `dist/BioMedPilot.app`。
- 脚本只在目标 `app_path` 存在且未传 `--no-clean` 时删除该 `dist` 目标 bundle。
- 脚本没有写入 `/Users/changdali/Desktop/BioMedPilot v1.0 Dev.command`。
- 脚本没有自动覆盖 `/Users/changdali/Desktop/BioMedPilot.app`。
- `docs/packaging.md` 仍手工提示“refresh desktop entry”，但这不是脚本行为；下一阶段实际打包前应明确禁止自动覆盖当前开发入口。

审计判断：当前打包脚本本身不会覆盖 `/Users/changdali/Desktop/BioMedPilot v1.0 Dev.command`。

## 10. 风险清单

### High

- ReleaseBuild 当前未同步 MainLine `73d4cc7`，缺失 Meta active runtime、Meta tests、shared UI helper 和 MainLine 架构治理更新。
- 现有 `dist/BioMedPilot.app` metadata 指向 `43c3cd0`，是旧 bundle，不能代表当前 ReleaseBuild HEAD 或 MainLine HEAD。
- ReleaseBuild 与 MainLine 分叉，不能用简单 fast-forward 心智处理；同步必须显式审计 release-only 提交和 MainLine 差异。

### Medium

- ReleaseBuild 当前 `app/ui_style_tokens.py` 仍包含旧 Meta purple token：`#6B4FD8` / `#F0EDFF`；MainLine 已移除，但 ReleaseBuild 尚未同步。
- `docs/packaging.md` 仍描述 `/Users/changdali/Desktop/BioMedPilot.app` 作为桌面测试入口，容易与当前 `/Users/changdali/Desktop/BioMedPilot v1.0 Dev.command` 开发入口混淆。
- ReleaseBuild 缺少 MainLine `CODEX.md`，需要在同步 MainLine 后确认是否应进入 ReleaseBuild。

### Low

- 多处历史文档仍引用 `/Users/changdali/Documents/BioMedPilot` 和旧 Desktop app；当前未发现 active runtime 使用这些路径。
- ignored `.pytest_cache/` 与 `__pycache__/` 较多，不影响 git，但实际打包前建议在授权清理或重建流程中处理。

## 11. 是否建议进入实际打包阶段

不建议现在直接进入实际打包阶段。

建议先执行下一阶段：

1. ReleaseBuild 显式同步 MainLine `73d4cc78c358192a2371eab0e866d26af98fba11`。
2. 确认 release-only 文档/报告如何保留。
3. 重新验证 Meta active runtime、shared UI token、Bioinformatics、CODEX.md、legacy guard。
4. 重新运行 source smoke 和测试矩阵。
5. 清理或重建 `dist/BioMedPilot.app`，确认 metadata 指向同步后的 ReleaseBuild HEAD。
6. 仅在用户确认后，再进入实际打包和桌面入口处理。

## 12. 下一阶段建议

建议下一阶段为：

`ReleaseBuild sync from MainLine pre-package validation`

边界：

- 只在 ReleaseBuild worktree 操作。
- 以 MainLine `73d4cc7` 为唯一同步源。
- 不从 Meta/Integration 直接取文件。
- 不覆盖 `/Users/changdali/Desktop/BioMedPilot v1.0 Dev.command`。
- 不自动刷新 `/Users/changdali/Desktop/BioMedPilot.app`，除非用户单独确认。
- 同步完成后先验证，再决定是否实际打包。

