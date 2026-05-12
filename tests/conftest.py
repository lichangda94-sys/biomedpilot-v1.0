from __future__ import annotations

import pytest

try:
    from PySide6.QtCore import QEvent
    from PySide6.QtWidgets import QApplication
except Exception:  # pragma: no cover
    QApplication = None  # type: ignore[assignment]
    QEvent = None  # type: ignore[assignment]


@pytest.fixture(autouse=True)
def cleanup_qt_top_level_widgets():
    yield
    if QApplication is None or QEvent is None:
        return
    app = QApplication.instance()
    if app is None:
        return
    for widget in list(app.topLevelWidgets()):
        widget.close()
        widget.deleteLater()
    app.sendPostedEvents(None, QEvent.DeferredDelete)
    app.processEvents()
