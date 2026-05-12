from __future__ import annotations

import pytest

from app.shared.qt_lifecycle import cleanup_qt_top_level_widgets as cleanup_qt_widgets


@pytest.fixture(autouse=True)
def cleanup_qt_top_level_widgets():
    yield
    cleanup_qt_widgets()
