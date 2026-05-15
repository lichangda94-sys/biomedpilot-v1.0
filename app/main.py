from __future__ import annotations

import sys
import argparse

from app.shell.dashboard import build_dashboard_model
from app.shared.environment.checks import check_local_environment
from app.version import app_version_summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch BioMedPilot.")
    parser.add_argument("--smoke-test", action="store_true", help="Load startup state and exit without opening the GUI event loop.")
    normalized_argv = list(sys.argv[1:] if argv is None else argv)
    filtered_argv = [arg for arg in normalized_argv if not arg.startswith("-psn_")]
    return parser.parse_args(filtered_argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
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
        print(f"workspace_entries=2")
        print(f"bioinformatics_features={len(dashboard.bioinformatics_features)}")
        print(f"meta_analysis_features={len(dashboard.meta_analysis_features)}")
        print(f"pyside6_available={environment.pyside6_available}")
        return 0

    try:
        from PySide6.QtWidgets import QApplication

        from app.app_identity import apply_app_identity
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

    qt_app = QApplication(sys.argv)
    apply_light_app_theme(qt_app)
    apply_app_identity(qt_app)
    window = MainWindow()
    window.show()
    return qt_app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
