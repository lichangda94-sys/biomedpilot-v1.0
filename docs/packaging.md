# Packaging

BioMedPilot currently supports a local macOS `.app` launcher package.

## Current Package Mode

Command:

```bash
python3 scripts/package_app.py --smoke-test
```

For internal beta acceptance, keep the existing build directory and run:

```bash
python3 scripts/package_app.py --no-clean --smoke-test
```

Output:

```text
dist/BioMedPilot.app
```

For a scoped ReleaseBuild Integration Preview package, keep the preview bundle
separate from the generic desktop app:

```bash
python3 scripts/package_app.py --integration-preview --smoke-test
```

Output:

```text
dist/BioMedPilot Integration Preview.app
```

The preview bundle uses `CFBundleName=BioMedPilot Integration Preview` and the
space-free launcher executable `CFBundleExecutable=BioMedPilotIntegrationPreview`.
This keeps Finder-visible naming explicit while avoiding accidental overwrite of
`BioMedPilot.app` or `BioMedPilot Dev.app`.

The launcher bundle now writes a build marker at:

```text
dist/BioMedPilot.app/Contents/Resources/app/BUILD_INFO.json
```

The smoke test prints `app_version`, `launch_mode`, `app_root`, and `git_head`.
Use these fields to confirm whether you are testing the current source checkout
or a packaged app bundle. If the UI looks stale, rebuild the bundle with the
command above before opening `dist/BioMedPilot.app`.

The unified desktop testing entry on this machine is:

```text
/Users/changdali/Desktop/BioMedPilot.app
```

After rebuilding `dist/BioMedPilot.app`, refresh the desktop entry from the new
bundle and rerun:

```bash
/Users/changdali/Desktop/BioMedPilot.app/Contents/MacOS/BioMedPilot --smoke-test
```

The source smoke test should report `launch_mode=source`; the desktop bundle
should report `launch_mode=packaged-local-python`. Both should report the same
`app_version`, `app_channel`, and expected `git_head`.

This package mode:

- uses no network downloads
- does not install PyInstaller or py2app
- copies the active BioMedPilot project files into the app bundle
- creates a macOS launcher under `Contents/MacOS`
- runs `python -m app.main`
- records version/source metadata in `BUILD_INFO.json`
- records version/channel/git metadata in `Info.plist`
- stores runtime JSON under the copied `project_storage` directory inside the bundle

## Limitations

This is not yet a fully standalone distributable app. The target machine still
needs a Python interpreter with PySide6 available. The launcher first uses the
Python executable recorded during packaging, then falls back to `python3`.

For a portable release build, use a later dedicated packaging task to add either
PyInstaller or py2app after dependency installation is explicitly approved.
