# UI-C2h.2 Integration Shared Foundation Carry-over

Date: 2026-05-22

## 1. Scope

This stage starts the local Integration carry-over branch and applies only Batch 0 and Batch 1 from the UI-C2h.1 plan.

Target worktree:

- `/Users/changdali/Developer/biomedpilot v1.0/Integration`

Target branch:

- `codex/integration-labtools-ui-c2-carryover`

Base branch:

- `dev/integration`

Base HEAD reviewed before branch creation:

- `ea57a49 Restore bioinformatics task plan import surface`

Strict boundary:

- No merge from `dev/ui-shell`.
- No cherry-pick.
- No push.
- No package smoke.
- No packaged app.
- No App icon / Finder icon / `.icns` / iconset / Info.plist / LaunchServices.
- No LabTools runtime page carry-over.
- No `app/labtools_runtime.py`.
- No LabTools save/export/history enablement.
- No UI-B10 work.

## 2. Branch Preparation

Created local branch:

```bash
git -C "/Users/changdali/Developer/biomedpilot v1.0/Integration" switch -c codex/integration-labtools-ui-c2-carryover dev/integration
```

This branch is local-only. Nothing was pushed.

## 3. Batch 1 Shared Foundation Changes

Added or updated:

| File | Change |
| --- | --- |
| `app/shared/semantic_keys.py` | Added semantic key registry for brand/nav/module/page/status/report/export keys. |
| `app/shared/ui_components/primitives.py` | Added shared primitive helpers for status chips, buttons, cards, empty states, and diagnostics disclosure titles. |
| `app/shared/ui_components/__init__.py` | Exported shared primitive helpers. |
| `app/ui_style_tokens.py` | Added compatibility status/button token API while preserving Integration's shared-theme-backed token dictionaries. |
| `app/app_identity.py` | Added non-App status and empty-state loader fallbacks required by shared primitives. Existing App icon behavior was preserved. |
| `tests/shared/test_semantic_keys.py` | Added semantic key registry tests. |
| `tests/ui/test_ui_primitives.py` | Added shared primitive tests. |

Explicitly not added in this stage:

- `app/labtools_runtime.py`
- LabTools C2 page implementations
- active non-App icon asset directories
- result/report/export icon active pilot assets
- Settings resource icon assets
- App icon / `.icns` / iconset / packaging files

## 4. Preserved Integration Surfaces

This stage did not modify:

- `app/shell/main_window.py`
- `app/labtools/workspace.py`
- `app/shared/local_engines/**`
- Integration `ExternalEngineManagerPage`
- Bioinformatics runtime pages
- Meta Analysis runtime pages
- existing App icon paths and application identity behavior

## 5. Verification

| Command | Result |
| --- | --- |
| `git -C .../Integration status --short` before branch creation | Clean |
| `python3 -m pytest -q tests/shared/test_semantic_keys.py tests/ui/test_ui_primitives.py` | Passed; 9 tests |
| `python3 -m app.main --smoke-test` | Passed |
| `python3 -m pytest -q tests/ui/test_app_identity.py` | Failed 1 existing MainWindow instantiation case; 7 passed |
| `git diff --check` | Passed |
| `git diff --cached --check` | Pending final verification |

`tests/ui/test_app_identity.py::test_main_window_uses_app_icon` fails while constructing `MainWindow()`. The failure is:

```text
TypeError: BioinformaticsWorkspaceWidget() takes no arguments
```

The failure occurs at the existing Integration route boundary in `app/shell/main_window.py` when it calls `BioinformaticsWorkspaceWidget(on_back=self.show_dashboard)`. This stage intentionally did not modify `app/shell/main_window.py`; resolving that route/interface mismatch belongs to the next Integration reconciliation stage, not Batch 1 shared foundation.

## 6. Carry-over Boundary Status

Batch 0:

- Completed.
- Local branch created.
- No push.

Batch 1:

- Completed.
- Semantic keys and shared primitives are available.
- Minimal token compatibility layer is available.
- Non-App status/empty-state fallback loaders are available.
- Existing App icon and packaging scope untouched.

Batch 2 and later:

- Not started.
- Active assets, LabTools runtime bridge, LabTools navigation, calculator, reagent, WB, and boundary pages remain deferred.

## 7. Next Recommendation

Recommended next stage:

`UI-C2h.3 Integration asset loader and non-App asset carry-over`

Scope should remain local-only and should avoid App icon / Finder icon / `.icns` / iconset / Info.plist / LaunchServices. If the user wants to avoid assets first, an alternative is:

`UI-C2h.3a Integration MainWindow/Bio workspace route compatibility audit`

That alternative would specifically resolve the existing `MainWindow()` instantiation blocker before wider UI regression tests are used as gates.

## 8. Non-modification Statement

This stage did not merge, cherry-pick, push, package, run package smoke, run a packaged app, or touch App icon / Finder icon / `.icns` / iconset / Info.plist / LaunchServices. It did not carry over LabTools runtime pages or enable save/export/history behavior.
