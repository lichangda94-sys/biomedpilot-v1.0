# UI-C5f Settings Hierarchy Polish

Date: 2026-05-25

## 1. Scope

This stage polishes the Settings runtime hierarchy identified by UI-C5a. It keeps Settings behavior unchanged and focuses on reducing first-viewport diagnostic noise.

Strictly not performed:

- no external capability install / update / download enablement
- no cloud configuration enablement
- no model invocation enablement
- no OCR / ImageJ / Fiji execution enablement
- no App icon / Finder icon / `.icns` / iconset / `Info.plist` / LaunchServices work
- no packaging or packaged app run

## 2. Changes

- `settingsContent` now carries:
  - `uiPrimitive=workbench_shell_content`
  - `layoutPolishNoOverlap=true`
- `settingsSecondaryNav` now carries:
  - `uiPrimitive=workbench_secondary_nav`
  - `layoutPolishNoOverlap=true`
- `settingsContentStack` now carries:
  - `uiPrimitive=workbench_content_stack`
  - `layoutPolishNoOverlap=true`
- The General page now shows only the summarized icon asset status.
- Detailed icon/resource inventory is moved into the collapsed Developer diagnostics panel.

## 3. Preserved Boundaries

- Detect-first semantics remain unchanged.
- Install / update buttons remain disabled.
- Cloud configuration remains disabled.
- ImageJ/Fiji remains an external capability marker, not a LabTools primary entry.
- Local model and Cloud AI remain not-configured / blocked as before.
- Developer diagnostics remain collapsed by default.

## 4. Screenshot

New source-runtime screenshot:

- `docs/ui/runtime_screenshots/20260525_c5f_settings_polish/settings_home.png`

The screenshot is `1600 x 1000` and non-empty.

## 5. Verification

Commands/checks run:

- `python3 -m pytest -q tests/ui/test_settings_shell.py tests/ui/test_ui_primitives.py tests/ui/test_workbench_layout_primitives.py`
  - Result: 12 passed
- `python3 -m app.main --smoke-test`
  - Result: passed
- Settings screenshot generation
  - Result: 1 non-empty PNG file created

No package smoke, packaged runtime, codesign, `dist/**` write, desktop app overwrite, or LaunchServices run was performed.
