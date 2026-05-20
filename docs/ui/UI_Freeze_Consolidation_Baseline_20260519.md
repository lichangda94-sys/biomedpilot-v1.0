# UI Freeze / Consolidation Baseline - 2026-05-19

## 1. Baseline Decision

BioMedPilot / 医研智析 / 萤火虫 UI work is now in a UI Freeze / UI Consolidation phase.

This baseline follows `docs/ui/BioMedPilot_UI_Design_Constitution_v2_20260519.md` and supersedes older stage reports when they conflict with current runtime evidence.

Current priority:

1. Repair runtime blockers.
2. Keep current shell navigation small.
3. Mark shell-only, testing, placeholder, and runtime-blocked surfaces clearly.
4. Merge or downgrade historical status pages before adding new pages.
5. Do not generate high-fidelity visual assets for blocked or planned surfaces.

## 2. Current Runtime UI

These surfaces are current runtime UI when the listed checks pass on current HEAD:

| Surface | Runtime status | Notes |
|---|---|---|
| UI-01 Login | Current runtime UI | Local-only testing login; no real account, subscription, or cloud auth. |
| UI-02 Global Workbench / Module Selection | Current runtime UI | Entry point for Bioinformatics and Meta shell; shows Developer Preview state. |
| Shell sidebar | Current runtime UI | Only renders Dashboard, Bioinformatics, Meta Analysis, Settings, Testing Mode. |
| Settings center | Current runtime UI / Placeholder settings | Displays icon/resource/config placeholders; not a full settings system. |
| Testing mode | Current runtime UI | Generates local feedback template. |
| Bioinformatics project/workflow stack | Current runtime UI after P0 import repair | Must keep testing/preflight/result semantics visible. |
| Local `.app` launcher | Testing launcher | `packaged-local-python`; not signed and not standalone. |

## 3. Runtime Blocked / Repaired

| Surface | Previous blocker | Current handling |
|---|---|---|
| Bioinformatics UI-04 to UI-13 | `app.bioinformatics.deg_executor_preflight` missing, causing workflow page tests to skip | Add a preflight-only input materializer/validator. It does not run DEG and does not generate DEG results. |

Acceptance rule:

- Any future UI report must list passed/skipped/failed counts and skip reasons.
- A test suite with import-error skips is not a UI pass.

## 4. Shell-only Pages

| Surface | Label | Rule |
|---|---|---|
| Meta Analysis in UIShell | Shell-only | Show only project shell and branch boundary; do not imply complete Meta runtime in this worktree. |
| Future LabTools entry in UIShell | Planned / out of current UIShell | Do not add a primary navigation entry until the LabTools IA is accepted and runtime exists. |

## 5. Historical UI Assets

Historical assets remain useful as references, but they are not delivery evidence by themselves:

- `docs/stage_UI_01_*` through `docs/stage_UI_13_*`
- old UIShell handoff/audit reports
- generated UI icon groups
- old Figma or mockup references
- archived legacy UI code

Use them only after checking current import, workspace mounting, and test execution.

## 6. Pages To Merge Or Downgrade

| Page | Target treatment | Reason |
|---|---|---|
| UI-05 Acquisition Status | Merge into UI-04 status summary or downgrade to Developer Diagnostic | Ordinary users should not leave the data-source task just to inspect acquisition plan/record/handoff. |
| Bioinformatics technical JSON sections | Keep collapsed under technical details | Avoid code-driven UI. |
| Settings placeholder rows | Keep weak and clearly marked | They are not full configuration persistence. |
| Meta full workflow descriptions in UIShell | Downgrade to shell-only boundary copy | Full Meta runtime is not represented by this worktree. |

## 7. Navigation Baseline

Global navigation must stay limited to entries that exist as current user workflows:

```text
Dashboard
生信分析
Meta 分析
设置中心
测试模式
```

Do not expose Project Center, Data Center, Task Center, Report Center, Environment, Packaging, LabTools, or External Engines as top-level navigation until they become real user workflows.

## 8. Status Labels

All UI and reports should use these labels consistently:

- Current runtime UI
- Historical UI asset
- Runtime blocked
- Shell-only
- Fallback UI
- Developer diagnostic
- Reference only
- Testing
- Developer Preview
- Local-only
- Manual review required
- Not publication-ready
- Not clinical use

## 9. Technical Term Governance

Forbidden in ordinary user primary UI unless inside technical details or developer diagnostics:

```text
manifest
source_files
source_type
acquisition
plan_only
artifact
backend
registry
handoff
diagnostics
raw JSON
cache path
internal id
engine consumer
runner
dry-run
preview task
```

Preferred user-facing terms:

| Technical term | User-facing term |
|---|---|
| manifest | 项目记录 / 技术清单 |
| acquisition | 数据获取状态 |
| plan_only | 仅生成计划，尚未下载 |
| artifact | 数据资产 / 结果文件 |
| diagnostics | 技术详情 |
| dry-run | 测试运行 / 预检 |
| preview task | 预览任务 |

## 10. Validation Commands

Minimum checks for this baseline:

```bash
python3 -m app.main --smoke-test
QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/ui
QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/bioinformatics/test_analysis_task_runs.py tests/ui/test_bioinformatics_workflow_pages.py
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
```

ReleaseBuild still requires separate signing and packaging validation.

## 11. Next Development Tasks

1. Keep DEG executor preflight as input validation only; do not run real DEG until output contracts are designed.
2. Merge UI-05 ordinary flow into UI-04 or mark it as Developer Diagnostic.
3. Rewrite UI-02 Meta copy so it clearly says Shell-only in UIShell.
4. Reduce technical terms in visible Bioinformatics task pages after workflow tests run without skips.
5. Add a reusable status badge / notice component before any broader visual pass.

