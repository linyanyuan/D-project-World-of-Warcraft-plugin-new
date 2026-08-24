"""Page base with animated Void Protocol backdrop."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from clean_client.ui.void_paint import (
    paint_corner_marks,
    paint_hex_grid_background,
    paint_scan_line_overlay,
    paint_void_background,
)


class VoidPage(QWidget):
    """Dark hex-grid + scanline backdrop used by all main pages."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._phase = 0.0
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self) -> None:
        self._phase += 1.0
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        paint_void_background(painter, rect)
        paint_hex_grid_background(painter, rect, opacity=0.20, cell_size=26.0)
        paint_scan_line_overlay(
            painter, rect, opacity=0.08, spacing=5.0, phase=self._phase
        )
        paint_corner_marks(
            painter, rect.adjusted(10, 10, -10, -10), size=16.0, thickness=1.6
        )
        painter.end()
        super().paintEvent(event)
