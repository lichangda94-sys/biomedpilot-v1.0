# UI-B10 App Icon / Packaging Readiness Gate

Date: 2026-05-24

## 1. Scope

This readiness gate evaluates whether UI-B10 can proceed now.

UI-B10 is the first stage allowed to touch:

- App icon
- Finder icon
- `.icns`
- iconset
- Info.plist icon binding
- LaunchServices
- package smoke
- packaged app runtime
- desktop app / desktop entry replacement

This document does not execute UI-B10. It does not modify packaging scripts, `dist/**`, Info.plist, icon resources, LaunchServices, or desktop app entries.

## 2. Decision

Decision: `blocked_pending_human_intervention`.

UI-B10 should not be executed automatically in the current state.

Blocking reasons:

1. The current UIShell worktree has unrelated LabTools local_data runtime/test changes in progress.
2. Final App icon / Finder icon approval has not been explicitly confirmed for the desktop package.
3. The packaging script currently writes Info.plist metadata but does not bind `CFBundleIconFile` or copy the `.icns` into `Contents/Resources` as a UI-B10 step.
4. It is not yet confirmed whether UI-B10 should update only source packaging logic, rebuild `dist/BioMedPilot.app`, overwrite `/Users/changdali/Desktop/BioMedPilot.app`, or stop at a temp package validation.
5. Signing/codesign expectation is not confirmed.

## 3. Current Evidence

Existing source assets:

- `assets/icons/app/biomedpilot_app_icon.png`
- `assets/icons/app/biomedpilot_app_icon_1024.png`
- `assets/icons/app/biomedpilot_app_icon.icns`
- `assets/icons/app/biomedpilot_app_icon.iconset/`

Existing runtime identity:

- `app/app_identity.py` loads the source App icon for Qt runtime.
- `tests/ui/test_app_identity.py` checks source App icon assets and Qt icon loading.

Existing packaging script:

- `scripts/package_app.py` writes `Contents/Info.plist`.
- `scripts/package_app.py` writes `CFBundleName`, `CFBundleDisplayName`, `CFBundleIdentifier`, `CFBundleExecutable`, and BioMedPilot metadata.
- No `CFBundleIconFile` binding is currently visible in `_write_info_plist`.
- UI-B10 would need to copy `.icns` to `Contents/Resources` and bind Info.plist.

Existing dist:

- `dist/BioMedPilot.app/Contents/Info.plist` exists, but this readiness gate does not modify or validate packaged app runtime.

## 4. Required Human Decisions

Before UI-B10 execution, confirm:

1. Which App icon asset is final:
   - existing `assets/icons/app/biomedpilot_app_icon.icns`
   - regenerated iconset
   - another user-approved icon
2. Whether UI-B10 may modify:
   - `scripts/package_app.py`
   - `tests/test_package_app.py`
   - `tests/test_versioned_packaged_entry.py`
   - `dist/**`
   - desktop `/Users/changdali/Desktop/BioMedPilot.app`
3. Whether to run package smoke:
   - temp package only
   - repo `dist/**`
   - desktop app overwrite
4. Whether codesign is required:
   - no signing
   - ad-hoc signing
   - developer identity signing
5. Whether LaunchServices/Finder validation must include:
   - `open -W -n`
   - `-psn_*` handling
   - `/tmp` launcher logs
   - Apple Silicon architecture check

## 5. Safe Next UI-B10 Plan After Approval

If approved, UI-B10 should run as a separate stage:

1. Confirm final icon source.
2. Add package resource copy for `.icns`.
3. Add `CFBundleIconFile` or equivalent Info.plist binding.
4. Add/adjust package tests for icon resource and Info.plist key.
5. Build temp package first.
6. Run source smoke.
7. Run package smoke.
8. Run LaunchServices/Finder-style validation if requested.
9. Only then decide whether to update `dist/**` or desktop app.

## 6. What Must Not Happen Automatically

Do not automatically:

- overwrite desktop `/Users/changdali/Desktop/BioMedPilot.app`
- modify `dist/**`
- codesign
- bind a non-approved App icon
- claim Finder icon completion from source Qt icon loading alone
- merge unrelated LabTools local_data changes into UI-B10

## 7. Verification

Readiness checks run:

- source asset/path inventory
- `rg` over packaging and identity code for Info.plist / icon binding
- `git status --short`
- CSV structure check for `docs/ui/UI_B10_app_icon_packaging_readiness_gate_matrix_20260524.csv`: 12 rows, required fields present
- `python3 -m pytest -q tests/ui/test_app_identity.py`: 8 passed
- `python3 -m app.main --smoke-test`: passed

No package smoke, packaged app runtime, codesign, `dist/**` write, desktop app overwrite, or LaunchServices run was performed.

## 8. Conclusion

This is the point where human intervention is needed.

UI-B10 is technically feasible, but not safe to execute automatically until the user confirms final icon, packaging target, signing expectation, and whether dirty non-UI-B10 LabTools local_data changes should be completed, parked, or excluded.
