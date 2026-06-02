# Phase 1 Preview Boot and Shell Validation

- date: `2026-06-02`
- branch: `integration/release-bio-c1-ui-shell`
- source_head_before_commit: `1a80c648b429c9d1bbb3a3baae72a84a2fbe6bc4`
- app: `/Users/changdali/Developer/biomedpilot v1.0/Integration/dist/BioMedPilot Integration Preview.app`

## Scope

Phase 1 only restores the packaged Preview launch path and captures Shell baseline evidence. It does not migrate Bioinformatics, Meta Analysis, or LabTools deep functional pages.

Validated surfaces:

- Welcome
- About
- Home / Dashboard
- Settings
- Sidebar
- Bioinformatics entry
- Meta Analysis entry
- LabTools entry

## Launch Finding

The previous packaged Preview used a POSIX shell launcher that executed Framework Python. LaunchServices started the bundle, but the runtime process appeared as `Python -m app.main`, which made double-click behavior and foreground window visibility unreliable.

Phase 1 changes the packager to prefer a native Mach-O launcher. The bundle executable is now:

`dist/BioMedPilot Integration Preview.app/Contents/MacOS/BioMedPilot Integration Preview`

The native launcher embeds Python in the bundle executable process, sets the packaged runtime environment, enters `Contents/Resources/app`, and invokes `python -m app.main`.

## Validation Commands

- `python3 -m py_compile app/main.py app/shared/macos_activation.py scripts/package_app.py`
- `python3 -m pytest -q tests/test_app_main.py tests/test_package_app.py tests/test_unified_entry.py`
- `QT_QPA_PLATFORM=offscreen python3 scripts/package_app.py --app-name 'BioMedPilot Integration Preview' --smoke-test`
- `file 'dist/BioMedPilot Integration Preview.app/Contents/MacOS/BioMedPilot Integration Preview'`
- `codesign --verify --deep --strict --verbose=2 'dist/BioMedPilot Integration Preview.app'`
- `open -W -n 'dist/BioMedPilot Integration Preview.app' --args --smoke-test`
- `open -W -n 'dist/BioMedPilot Integration Preview.app' --args --gui-startup-check --gui-startup-check-output /tmp/biomedpilot_gui_startup_native2.json`
- `open -n 'dist/BioMedPilot Integration Preview.app'`

## Results

- Package mode: `local-python-native-launcher`
- Bundle executable type: `Mach-O 64-bit executable arm64`
- Codesign: passed
- LaunchServices smoke: passed
- GUI startup check: passed
- MainWindow visible in GUI startup check: `true`
- MainWindow size: `1120 x 720`
- Real `open -n` hold time: `10s`
- Runtime process after real open: `BioMedPilot Integration Preview`
- Launcher log: no traceback
- Crash reports during validation: none found

Known observation:

- `open -W` GUI startup check reports `window_active=false` and `activation_policy_rejected`; however the MainWindow is created and visible, and the real app process remains alive without crash. This remains a follow-up foreground activation polish item, not a startup crash blocker.

## Screenshot Evidence

### Welcome

![Welcome](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_boot_shell/01_welcome.png)

### About

![About](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_boot_shell/02_about.png)

### Home / Dashboard

![Home Dashboard](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_boot_shell/03_home_dashboard.png)

### Settings

![Settings](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_boot_shell/04_settings.png)

### Sidebar / Dashboard

![Sidebar Dashboard](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_boot_shell/05_sidebar_dashboard.png)

### Bioinformatics Entry

![Bioinformatics Entry](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_boot_shell/06_bio_entry.png)

### Meta Analysis Entry

![Meta Analysis Entry](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_boot_shell/07_meta_entry.png)

### LabTools Entry

![LabTools Entry](/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_phase1_preview_boot_shell/08_labtools_entry.png)

## Phase 1 Conclusion

The first-stage Preview launch blocker is resolved for the local release build path. The app now packages with a native macOS launcher, passes LaunchServices smoke, creates a visible MainWindow in GUI startup check, and stays alive during a real 10-second open test.

The screenshots confirm the current Shell surfaces are renderable. Visual baseline disagreements, including whether Home or module pages match the final UIShell high-fidelity target, should be handled in the next UI scoped migration batch rather than mixed into the startup repair.
