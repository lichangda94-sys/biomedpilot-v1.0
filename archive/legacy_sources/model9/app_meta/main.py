from __future__ import annotations

import os
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QCoreApplication, QLibraryInfo
from PySide6.QtWidgets import QApplication

from app_meta.main_window import MetaMainWindow


def _configure_qt_plugin_path() -> None:
    plugins_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
    if plugins_path:
        os.environ.setdefault("QT_PLUGIN_PATH", plugins_path)
        os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(Path(plugins_path) / "platforms"))
        QCoreApplication.addLibraryPath(plugins_path)


def main() -> int:
    _configure_qt_plugin_path()
    app = QApplication(sys.argv)
    app.setApplicationName("BioMedPilot")
    app.setApplicationDisplayName("BioMedPilot · Meta分析")
    app.setOrganizationName("BioMedPilot")
    window = MetaMainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
