from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

from app.ui_style_tokens import COLORS, ICON_SIZE


def biomed_icon(name: str, size: int = ICON_SIZE["nav"]) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    stroke = max(1.4, size / 14)
    primary = QColor(COLORS["bio"])
    accent = QColor(COLORS["bio_accent"])
    muted = QColor("#8B98A8")
    rect = QRectF(stroke, stroke, size - stroke * 2, size - stroke * 2)
    painter.setPen(QPen(primary, stroke, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(Qt.NoBrush)

    if name == "home":
        roof = QPainterPath()
        roof.moveTo(rect.left() + rect.width() * 0.16, rect.center().y())
        roof.lineTo(rect.center().x(), rect.top() + rect.height() * 0.18)
        roof.lineTo(rect.right() - rect.width() * 0.16, rect.center().y())
        painter.drawPath(roof)
        painter.drawRoundedRect(rect.adjusted(rect.width() * 0.22, rect.height() * 0.42, -rect.width() * 0.22, 0), 2, 2)
    elif name == "search":
        painter.drawEllipse(rect.adjusted(1, 1, -size * 0.26, -size * 0.26))
        painter.drawLine(QPointF(size * 0.67, size * 0.67), QPointF(size * 0.86, size * 0.86))
    elif name == "assets":
        for offset in [0.0, 0.18, 0.36]:
            y = rect.top() + rect.height() * offset
            painter.drawRoundedRect(QRectF(rect.left() + size * 0.12, y + size * 0.08, rect.width() * 0.72, size * 0.2), 2, 2)
    elif name == "groups":
        for x, y in [(0.32, 0.32), (0.68, 0.32), (0.5, 0.68)]:
            painter.drawEllipse(QPointF(size * x, size * y), size * 0.09, size * 0.09)
        painter.drawLine(QPointF(size * 0.37, size * 0.37), QPointF(size * 0.47, size * 0.61))
        painter.drawLine(QPointF(size * 0.63, size * 0.37), QPointF(size * 0.53, size * 0.61))
    elif name == "deg":
        for x, y, color in [(0.32, 0.68, "#2F80ED"), (0.52, 0.44, "#B9C1CA"), (0.72, 0.28, "#E53935")]:
            painter.setBrush(QColor(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(size * x, size * y), size * 0.07, size * 0.07)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(primary, stroke, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(QPointF(size * 0.18, size * 0.82), QPointF(size * 0.84, size * 0.82))
        painter.drawLine(QPointF(size * 0.18, size * 0.82), QPointF(size * 0.18, size * 0.18))
    elif name == "enrichment":
        for idx, width in enumerate([0.64, 0.48, 0.72]):
            y = size * (0.28 + idx * 0.22)
            painter.drawLine(QPointF(size * 0.24, y), QPointF(size * (0.24 + width), y))
        painter.setBrush(accent)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(size * 0.22, size * 0.28), size * 0.045, size * 0.045)
    elif name == "correlation":
        painter.drawLine(QPointF(size * 0.18, size * 0.76), QPointF(size * 0.82, size * 0.24))
        for t in [0.24, 0.42, 0.62, 0.78]:
            painter.drawEllipse(QPointF(size * t, size * (0.88 - t * 0.75)), size * 0.04, size * 0.04)
    elif name == "survival":
        painter.drawArc(rect.adjusted(1, 1, -1, -1), 20 * 16, 300 * 16)
        painter.drawLine(QPointF(size * 0.50, size * 0.50), QPointF(size * 0.50, size * 0.24))
        painter.drawLine(QPointF(size * 0.50, size * 0.50), QPointF(size * 0.70, size * 0.50))
    elif name == "visualization":
        for idx, height in enumerate([0.36, 0.58, 0.44]):
            x = size * (0.24 + idx * 0.2)
            painter.drawRoundedRect(QRectF(x, size * (0.78 - height), size * 0.1, size * height), 2, 2)
    elif name == "reporting":
        painter.drawRoundedRect(rect.adjusted(size * 0.18, size * 0.05, -size * 0.12, -size * 0.05), 2, 2)
        painter.drawLine(QPointF(size * 0.34, size * 0.36), QPointF(size * 0.68, size * 0.36))
        painter.drawLine(QPointF(size * 0.34, size * 0.52), QPointF(size * 0.70, size * 0.52))
        painter.drawLine(QPointF(size * 0.34, size * 0.68), QPointF(size * 0.58, size * 0.68))
    elif name == "tasks":
        painter.drawRoundedRect(rect.adjusted(size * 0.12, size * 0.08, -size * 0.08, -size * 0.08), 2, 2)
        painter.drawLine(QPointF(size * 0.34, size * 0.38), QPointF(size * 0.72, size * 0.38))
        painter.drawLine(QPointF(size * 0.34, size * 0.60), QPointF(size * 0.68, size * 0.60))
        painter.drawLine(QPointF(size * 0.24, size * 0.38), QPointF(size * 0.27, size * 0.42))
        painter.drawLine(QPointF(size * 0.27, size * 0.42), QPointF(size * 0.31, size * 0.34))
    elif name == "project":
        painter.drawRoundedRect(rect.adjusted(size * 0.08, size * 0.24, -size * 0.08, -size * 0.08), 3, 3)
        painter.drawLine(QPointF(size * 0.28, size * 0.24), QPointF(size * 0.72, size * 0.24))
    elif name == "samples":
        for x, y in [(0.35, 0.34), (0.65, 0.34)]:
            painter.drawEllipse(QPointF(size * x, size * y), size * 0.08, size * 0.08)
        painter.drawArc(QRectF(size * 0.18, size * 0.50, size * 0.3, size * 0.26), 0, 180 * 16)
        painter.drawArc(QRectF(size * 0.52, size * 0.50, size * 0.3, size * 0.26), 0, 180 * 16)
    elif name == "running":
        painter.setPen(QPen(accent, stroke, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawArc(rect.adjusted(2, 2, -2, -2), 30 * 16, 280 * 16)
    elif name == "completed":
        painter.setPen(QPen(QColor(COLORS["success"]), stroke, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(QPointF(size * 0.24, size * 0.52), QPointF(size * 0.42, size * 0.70))
        painter.drawLine(QPointF(size * 0.42, size * 0.70), QPointF(size * 0.78, size * 0.30))
    elif name == "attention":
        painter.setPen(QPen(QColor(COLORS["warning"]), stroke, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(QPointF(size * 0.50, size * 0.20), QPointF(size * 0.50, size * 0.60))
        painter.drawPoint(QPointF(size * 0.50, size * 0.78))
    elif name == "locked":
        painter.setPen(QPen(muted, stroke, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawRoundedRect(rect.adjusted(size * 0.18, size * 0.44, -size * 0.18, -size * 0.08), 2, 2)
        painter.drawArc(QRectF(size * 0.32, size * 0.16, size * 0.36, size * 0.42), 0, 180 * 16)
    else:
        painter.drawEllipse(rect.adjusted(size * 0.18, size * 0.18, -size * 0.18, -size * 0.18))

    painter.end()
    return QIcon(pixmap)


def icon_size(kind: str) -> QSize:
    value = ICON_SIZE[kind]
    return QSize(value, value)
