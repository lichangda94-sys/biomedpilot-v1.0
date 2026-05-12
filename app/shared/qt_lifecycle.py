from __future__ import annotations


def cleanup_qt_top_level_widgets(app=None) -> None:
    try:
        from PySide6.QtCore import QEvent
        from PySide6.QtWidgets import QApplication
    except Exception:  # pragma: no cover
        return

    qt_app = app or QApplication.instance()
    if qt_app is None:
        return
    for widget in list(qt_app.topLevelWidgets()):
        try:
            widget.close()
            widget.deleteLater()
        except RuntimeError:
            continue
    qt_app.sendPostedEvents(None, QEvent.DeferredDelete)
    qt_app.processEvents()
