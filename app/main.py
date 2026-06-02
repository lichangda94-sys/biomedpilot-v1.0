from __future__ import annotations

import sys
import argparse
import json
from pathlib import Path

from app.shell.dashboard import build_dashboard_model
from app.shared.macos_activation import activate_macos_app
from app.shared.environment.checks import check_local_environment
from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets
from app.version import app_version_summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch BioMedPilot.")
    parser.add_argument("--smoke-test", action="store_true", help="Load startup state and exit without opening the GUI event loop.")
    parser.add_argument("--gui-startup-check", action="store_true", help="Open the GUI, verify the main window is visible, and exit.")
    parser.add_argument("--gui-startup-check-output", default="", help="Optional JSON output path for --gui-startup-check.")
    parser.add_argument("--bio-formal-deg-runtime-check", action="store_true", help="Validate formal DEG runtime dependencies and fixture execution.")
    parser.add_argument("--bio-formal-deg-runtime-check-output", default="", help="Optional JSON output path for --bio-formal-deg-runtime-check.")
    normalized_argv = list(sys.argv[1:] if argv is None else argv)
    filtered_argv = [arg for arg in normalized_argv if not arg.startswith("-psn_")]
    return parser.parse_args(filtered_argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.bio_formal_deg_runtime_check:
        from app.bioinformatics.deg_engine.runtime_validation import run_formal_deg_runtime_validation

        output_path = Path(args.bio_formal_deg_runtime_check_output) if args.bio_formal_deg_runtime_check_output else None
        payload = run_formal_deg_runtime_validation(output_path=output_path)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["status"] in {"passed", "blocked_missing_dependency"} else 1

    if args.smoke_test:
        dashboard = build_dashboard_model()
        environment = check_local_environment()
        version = app_version_summary()
        print(dashboard.product_name)
        print(f"app_version={version.version}")
        print(f"app_channel={version.channel}")
        print(f"launch_mode={version.launch_mode}")
        print(f"app_root={version.app_root}")
        print(f"git_head={version.git_head}")
        print(f"workspace_entries=3")
        print(f"bioinformatics_features={len(dashboard.bioinformatics_features)}")
        print(f"meta_analysis_features={len(dashboard.meta_analysis_features)}")
        print(f"labtools_features={len(dashboard.labtools_features)}")
        print(f"pyside6_available={environment.pyside6_available}")
        return 0

    try:
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication

        from app.app_identity import apply_app_identity
        from app.labtools.workspace import LABTOOLS_WORKSPACE_IMPORT_ERROR
        from app.shell.main_window import MainWindow
        from app.ui_theme import apply_light_app_theme
    except Exception as exc:
        dashboard = build_dashboard_model()
        environment = check_local_environment()
        print(f"{dashboard.product_name}")
        print("Desktop UI unavailable; running console smoke mode.")
        print(f"reason={exc.__class__.__name__}: {exc}")
        print(f"bioinformatics_features={len(dashboard.bioinformatics_features)}")
        print(f"meta_analysis_features={len(dashboard.meta_analysis_features)}")
        print(f"python={environment.python_executable}")
        return 0

    qt_app = QApplication([sys.argv[0], *[arg for arg in sys.argv[1:] if not arg.startswith("-psn_")]])
    first_activation = activate_macos_app()
    apply_light_app_theme(qt_app)
    apply_app_identity(qt_app)
    if LABTOOLS_WORKSPACE_IMPORT_ERROR:
        print(f"LabTools workspace fallback active: {LABTOOLS_WORKSPACE_IMPORT_ERROR}", file=sys.stderr)
    window = MainWindow()
    window.show()
    window.setWindowState(window.windowState() & ~window.windowState().WindowMinimized | window.windowState().WindowActive)
    window.raise_()
    window.activateWindow()
    second_activation = activate_macos_app()
    QTimer.singleShot(0, window.raise_)
    QTimer.singleShot(0, window.activateWindow)
    if args.gui_startup_check:
        def finish_startup_check() -> None:
            qt_app.processEvents()
            payload = _gui_startup_payload(window, qt_app, first_activation, second_activation)
            output_path = Path(args.gui_startup_check_output) if args.gui_startup_check_output else None
            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            window.close()
            qt_app.quit()

        QTimer.singleShot(400, finish_startup_check)
        try:
            qt_app.exec()
        finally:
            cleanup_qt_top_level_widgets(qt_app)
        return 0
    try:
        return qt_app.exec()
    finally:
        window.close()
        cleanup_qt_top_level_widgets(qt_app)


def _gui_startup_payload(window, qt_app, first_activation, second_activation) -> dict[str, object]:
    active_window = qt_app.activeWindow()
    top_level_widgets = [
        {
            "type": type(widget).__name__,
            "title": widget.windowTitle(),
            "visible": widget.isVisible(),
            "width": widget.size().width(),
            "height": widget.size().height(),
        }
        for widget in qt_app.topLevelWidgets()
        if widget.isWindow()
    ]
    return {
        "status": "passed" if window.isVisible() and window.size().width() > 0 and window.size().height() > 0 else "failed",
        "window_title": window.windowTitle(),
        "window_visible": window.isVisible(),
        "window_active": window.isActiveWindow(),
        "active_window_title": active_window.windowTitle() if active_window is not None else "",
        "window_size": {"width": window.size().width(), "height": window.size().height()},
        "macos_activation": {
            "before_show": first_activation.__dict__,
            "after_show": second_activation.__dict__,
        },
        "top_level_widgets": top_level_widgets,
    }


if __name__ == "__main__":
    raise SystemExit(main())
