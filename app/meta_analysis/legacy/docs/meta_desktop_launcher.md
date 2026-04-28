# BioMedPilot Meta macOS Launcher

This repository includes two local launch options for the Meta Analysis desktop app.

## Command Launcher

Run:

```bash
chmod +x packaging/meta_app_launcher.command
open packaging/meta_app_launcher.command
```

The launcher detects the repository root, activates `.venv` when available, checks that `PySide6` is installed, then runs:

```bash
python app_meta/main.py
```

If `PySide6` is missing, the launcher prints an actionable install message instead of failing silently.

## App Bundle

Create the local app bundle:

```bash
python packaging/create_meta_app_bundle.py
```

This generates:

```text
dist/BioMedPilot Meta.app/
  Contents/
    Info.plist
    MacOS/BioMedPilotMeta
    Resources/meta_app_icon.icns
```

Launch it with:

```bash
open "dist/BioMedPilot Meta.app"
```

You can also double-click `dist/BioMedPilot Meta.app` in Finder.

## Notes

- This bundle is local and unsigned.
- Code signing and notarization are not required for local development.
- Keep the app bundle inside this repository's `dist/` folder. The launcher resolves the project root relative to that location.
- If launch fails with a Qt `cocoa` platform plugin message, reinstall PySide6 in the project virtual environment:

```bash
./.venv/bin/python -m pip install --force-reinstall PySide6
```

- Normal command-line launch remains available:

```bash
python app_meta/main.py
```
