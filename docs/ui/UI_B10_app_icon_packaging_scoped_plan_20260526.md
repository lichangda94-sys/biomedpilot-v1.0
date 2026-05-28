# UI-B10 App Icon / Packaging Scoped Plan After UI-D6

Date: 2026-05-26

## 1. Purpose

This document defines the safe entry plan for UI-B10 after the UI-D6 source-runtime screenshot re-review.

It is a planning artifact only. It does not implement UI-B10, rebuild a package, modify icon assets, touch `Info.plist`, run LaunchServices, codesign, write `dist/**`, or overwrite any desktop app bundle.

## 2. Current Decision

Decision: `ready_for_human_scope_confirmation`.

UI-D6 shows that the rebuilt source-runtime PySide UI can be captured and reviewed consistently, and no screenshot shows formal executor, report, or export enablement. That is necessary evidence for UI-B10 planning, but it is not enough to execute packaging or App icon work automatically.

UI-B10 should start only after the product owner confirms:

- the D6 screenshot set is visually acceptable, or identifies pages that need targeted polish first
- the final App icon and Finder icon source
- the packaging target and whether `dist/**` or a desktop bundle may be written
- the signing expectation
- the LaunchServices/Finder-style validation gate

## 3. Evidence Read

Existing UI-D6 evidence:

- `docs/ui/UI_D6_runtime_ui_screenshot_re_review_20260526.md`
- `docs/ui/UI_D6_runtime_screenshot_manifest_20260526.csv`
- `docs/ui/runtime_screenshots/20260526_d6_runtime_review/`

The D6 set contains 16 source-runtime screenshots and records these remaining review risks:

- Dashboard and Settings still require final product-owner acceptance before icon/package work.
- LabTools Reagent and WB pages remain dense operational pages.
- Bioinformatics Analysis Tasks remains table-heavy.
- Meta Screening / Extraction remains dense and draft-only.

Existing UI-B10 baseline evidence:

- `docs/ui/UI_B10_app_icon_packaging_readiness_gate_20260524.md`
- `docs/ui/UI_B10_app_icon_packaging_readiness_gate_matrix_20260524.csv`

Existing packaging implementation shape:

- `scripts/package_app.py` builds a local Python launcher `.app`.
- The generated `Info.plist` currently writes bundle identity and BioMedPilot metadata.
- The packaging path does not yet bind `CFBundleIconFile`.
- The packaging path does not yet copy the approved `.icns` into `Contents/Resources` as an explicit UI-B10 step.
- Existing package tests cover basic bundle metadata and smoke behavior, but not Finder icon binding.

## 4. B10 Scope Split

### UI-B10a: Acceptance And Scope Freeze

Type: documentation / decision gate.

Allowed:

- product-owner review of the D6 screenshot set
- confirmation of the final App icon source
- confirmation of package output target
- confirmation of signing and Finder validation expectations

Not allowed:

- package rebuild
- App icon asset modification
- `Info.plist` modification
- `dist/**` write
- desktop app overwrite

### UI-B10b: Package Icon Binding

Type: source implementation after approval.

Allowed only after UI-B10a:

- copy the approved `.icns` into `Contents/Resources`
- bind `CFBundleIconFile` in generated `Info.plist`
- add focused tests that verify icon resource copy and plist binding

Still not allowed unless separately approved:

- changing the approved icon design
- overwriting desktop app bundles
- codesigning with a developer identity

### UI-B10c: Non-Destructive Package Validation

Type: local validation after package icon binding.

Preferred first target:

- temporary package output outside persistent release paths

Validation should include:

- source smoke
- package smoke
- generated `Info.plist` check
- generated `Contents/Resources` icon check
- launcher executable permission check
- no network downloads
- no executor/report/export enablement

### UI-B10d: Finder / LaunchServices Gate

Type: desktop launch validation after non-destructive package passes.

Validation should include, when approved:

- `open -W -n <app>.app`
- `-psn_*` argument handling
- `CFBundleExecutable` check
- `/tmp` launcher log review if Finder launch fails
- Apple Silicon architecture check when relevant

### UI-B10e: Release Or Desktop Handoff

Type: destructive or semi-destructive handoff.

Allowed only after explicit approval:

- writing repo `dist/**`
- replacing `/Users/changdali/Desktop/BioMedPilot.app`
- signing policy execution
- release handoff notes

## 5. Human Decisions Required

Before implementation starts, confirm these decisions:

1. D6 acceptance:
   - Accept all 16 D6 screenshots for packaging readiness, or list pages that need targeted polish before B10.
2. Icon source:
   - Use `assets/icons/app/biomedpilot_app_icon.icns`, regenerate from existing source PNGs, or provide a different approved asset.
3. Package target:
   - temp-only validation, repo `dist/**`, desktop bundle overwrite, or staged release directory.
4. Signing:
   - no signing, ad-hoc signing, or developer identity signing.
5. Finder validation:
   - whether LaunchServices validation is required in the first B10 execution or deferred.
6. Desktop replacement:
   - whether a successful B10 may overwrite an existing desktop app bundle.

## 6. Business And Safety Boundaries

UI-B10 must not:

- enable Bioinformatics or Meta executors
- enable DEG, ORA, GSEA, KM, Cox, clinical formal execution, Network Meta, or formal pooled effects
- enable report generation or formal export
- show fake report-ready packages, fake plots, fake formal result tables, or fake export success
- install or configure external engines
- download, upload, update, or configure cloud services
- treat icon availability as capability availability
- overwrite desktop app bundles without explicit approval

## 7. Proposed Implementation Checks After Approval

Smallest relevant checks for UI-B10b:

- focused package icon binding tests
- focused packaged entry metadata tests
- `python3 -m app.main --smoke-test`
- `git diff --check`
- `git diff --cached --check` before commit

Additional checks for UI-B10c or later:

- package smoke from generated launcher
- generated `Info.plist` inspection
- generated `Contents/Resources` inspection
- Finder / LaunchServices validation if approved
- signing verification if signing is approved

## 8. Recommendation

Do not execute package or icon changes yet.

Recommended next step: the product owner should review `docs/ui/runtime_screenshots/20260526_d6_runtime_review/` and answer the six decisions in section 5. After that, UI-B10 can proceed as a tightly scoped package/icon implementation stage.
