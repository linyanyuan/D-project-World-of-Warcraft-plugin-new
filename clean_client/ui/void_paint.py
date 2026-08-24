"""Void Protocol painters — reimplemented from Nirvana theme signatures."""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen

BG_VOID = QColor("#04070F")
BG_DEEP = QColor("#0A1220")
BG_PANEL = QColor("#101B2F")
CYAN_SIGNAL = QColor("#61D8FF")
CYAN_BRIGHT = QColor("#B3F0FF")
BLUE_ACCENT = QColor("#5EA7FF")
ALERT_RED = QColor("#FF6E84")
BORDER_TRACE = QColor("#2C3F5E")


def paint_void_background(painter: QPainter, rect: QRectF) -> None:
    grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
    grad.setColorAt(0.0, BG_VOID)
    grad.setColorAt(0.45, BG_DEEP)
    grad.setColorAt(1.0, QColor("#0D1A33"))
    painter.fillRect(rect, grad)

    haze = QLinearGradient(rect.center(), rect.topRight())
    haze_color = QColor(CYAN_SIGNAL)
    haze_color.setAlpha(28)
    haze.setColorAt(0.0, QColor(0, 0, 0, 0))
    haze.setColorAt(1.0, haze_color)
    painter.fillRect(rect, haze)


def paint_hex_grid_background(
    painter: QPainter,
    rect: QRectF,
    *,
    color_rgb: QColor | None = None,
    opacity: float = 0.22,
    cell_size: float = 28.0,
) -> None:
    color = QColor(color_rgb or BORDER_TRACE)
    color.setAlphaF(max(0.0, min(opacity, 1.0)))
    pen = QPen(color)
    pen.setWidthF(1.0)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    r = cell_size / 2.0
    dx = cell_size * 1.5
    dy = math.sqrt(3) * cell_size
    row = 0
    y = rect.top() - dy
    while y < rect.bottom() + dy:
        offset_x = (cell_size * 0.75) if row % 2 else 0.0
        x = rect.left() - dx + offset_x
        while x < rect.right() + dx:
            path = QPainterPath()
            for i in range(6):
                angle = math.radians(60 * i - 30)
                px = x + r * math.cos(angle)
                py = y + r * math.sin(angle)
                if i == 0:
                    path.moveTo(QPointF(px, py))
                else:
                    path.lineTo(QPointF(px, py))
            path.closeSubpath()
            painter.drawPath(path)
            x += dx
        y += dy / 2.0
        row += 1


def paint_scan_line_overlay(
    painter: QPainter,
    rect: QRectF,
    *,
    opacity: float = 0.12,
    spacing: float = 4.0,
    phase: float = 0.0,
) -> None:
    color = QColor(CYAN_SIGNAL)
    color.setAlphaF(max(0.0, min(opacity, 1.0)))
    pen = QPen(color)
    pen.setWidthF(1.0)
    painter.setPen(pen)
    y = rect.top() + (phase % spacing)
    while y <= rect.bottom():
        painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
        y += spacing

    # bright moving sweep
    sweep = QColor(CYAN_BRIGHT)
    sweep.setAlpha(55)
    sy = rect.top() + ((phase * 3.0) % max(rect.height(), 1.0))
    painter.fillRect(QRectF(rect.left(), sy, rect.width(), 2.5), sweep)


def paint_corner_marks(
    painter: QPainter,
    rect: QRectF,
    *,
    color: QColor | None = None,
    size: float = 18.0,
    thickness: float = 2.0,
) -> None:
    pen = QPen(color or CYAN_SIGNAL)
    pen.setWidthF(thickness)
    pen.setCapStyle(Qt.PenCapStyle.SquareCap)
    painter.setPen(pen)
    left, top, right, bottom = rect.left(), rect.top(), rect.right(), rect.bottom()
    # TL
    painter.drawLine(QPointF(left, top + size), QPointF(left, top))
    painter.drawLine(QPointF(left, top), QPointF(left + size, top))
    # TR
    painter.drawLine(QPointF(right - size, top), QPointF(right, top))
    painter.drawLine(QPointF(right, top), QPointF(right, top + size))
    # BL
    painter.drawLine(QPointF(left, bottom - size), QPointF(left, bottom))
    painter.drawLine(QPointF(left, bottom), QPointF(left + size, bottom))
    # BR
    painter.drawLine(QPointF(right - size, bottom), QPointF(right, bottom))
    painter.drawLine(QPointF(right, bottom), QPointF(right, bottom - size))


def paint_data_strip(
    painter: QPainter,
    x: float,
    y: float,
    width: float,
    height: float,
    value_ratio: float,
) -> None:
    ratio = max(0.0, min(float(value_ratio), 1.0))
    track = QColor(BORDER_TRACE)
    track.setAlpha(120)
    painter.fillRect(QRectF(x, y, width, height), track)
    fill_w = width * ratio
    grad = QLinearGradient(x, y, x + fill_w, y)
    grad.setColorAt(0.0, CYAN_SIGNAL)
    grad.setColorAt(1.0, CYAN_BRIGHT)
    painter.fillRect(QRectF(x, y, fill_w, height), grad)
