from __future__ import annotations

import os
import subprocess
import sys
import unittest


_QAPPLICATION = None
_QT_AVAILABLE: bool | None = None


def get_qapplication():
    global _QAPPLICATION, _QT_AVAILABLE
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise unittest.SkipTest("PySide6 is not installed.") from exc
    if _QT_AVAILABLE is None:
        _QT_AVAILABLE = _probe_qapplication_available()
    if not _QT_AVAILABLE:
        raise unittest.SkipTest("PySide6 QApplication cannot be created in this environment.")
    existing = QApplication.instance()
    if existing is not None:
        _QAPPLICATION = existing
        return existing
    os.environ.setdefault("QT_QPA_PLATFORM", "minimal")
    _QAPPLICATION = QApplication([])
    return _QAPPLICATION


def _probe_qapplication_available() -> bool:
    env = dict(os.environ)
    env.setdefault("QT_QPA_PLATFORM", "minimal")
    code = (
        "from PySide6.QtWidgets import QApplication\n"
        "app = QApplication([])\n"
        "print('ok')\n"
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0
