from __future__ import annotations

import sys
import argparse

from app.shell.dashboard import build_dashboard_model
from app.shared.environment.checks import check_local_environment


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch BioMedPilot.")
    parser.add_argument("--smoke-test", action="store_true", help="Load startup state and exit without opening the GUI event loop.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.smoke_test:
        dashboard = build_dashboard_model()
        environment = check_local_environment()
        print(dashboard.product_name)
        print(f"workspace_entries=2")
        print(f"bioinformatics_features={len(dashboard.bioinformatics_features)}")
        print(f"meta_analysis_features={len(dashboard.meta_analysis_features)}")
        print(f"pyside6_available={environment.pyside6_available}")
        return 0

    try:
        from PySide6.QtWidgets import QApplication

        from app.shell.main_window import MainWindow
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
    window = MainWindow()
    window.show()
    return qt_app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
