"""Void Protocol visual theme — dark HUD with cyan signal accents."""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, ElevatedCardWidget, Theme, setTheme, setThemeColor

# Exact recovered Nirvana void_protocol_theme palette
CYAN = "#61D8FF"
CYAN_BRIGHT = "#B3F0FF"
BG_VOID = "#04070F"
BG_DEEP = "#0A1220"
BG_PANEL = "#101B2F"
BG_CARD = "#121E33"
TEXT = "#E9EFF7"
TEXT_MUTED = "#7C8798"
ALERT = "#FF6E84"
OK = "#3DFFB5"
AMBER = "#FFC36B"


def apply_app_theme() -> None:
    """Force dark Fluent theme + cyan accent before windows open."""
    setTheme(Theme.DARK)
    setThemeColor(QColor(CYAN))


def add_page_header(
    layout: QVBoxLayout,
    parent: QWidget,
    title: str,
    subtitle: str,
    badge: str | None = None,
) -> None:
    """Large title + muted subtitle + optional status badge."""
    head = QHBoxLayout()
    titles = QVBoxLayout()
    titles.setSpacing(4)

    title_lbl = QLabel(title, parent)
    title_font = QFont("Segoe UI Semibold")
    title_font.setPointSize(20)
    title_font.setBold(True)
    title_lbl.setFont(title_font)
    title_lbl.setStyleSheet(
        f"color: {TEXT}; letter-spacing: 1px; background: transparent;"
    )
    titles.addWidget(title_lbl)

    sub = BodyLabel(subtitle, parent)
    sub.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
    titles.addWidget(sub)
    head.addLayout(titles, stretch=1)

    if badge:
        pill = QLabel(badge, parent)
        pill.setStyleSheet(
            f"""
            QLabel {{
                color: {BG_VOID};
                background: {CYAN};
                border-radius: 11px;
                padding: 5px 12px;
                font-weight: 700;
                font-size: 11px;
                letter-spacing: 1px;
            }}
            """
        )
        head.addWidget(pill)

    layout.addLayout(head)

    line = QWidget(parent)
    line.setFixedHeight(1)
    line.setStyleSheet("background: rgba(97, 216, 255, 0.22);")
    layout.addWidget(line)


def make_card(parent: QWidget):
    card = ElevatedCardWidget(parent)
    card.setStyleSheet(
        """
        ElevatedCardWidget {
            background-color: rgba(18, 30, 51, 230);
            border: 1px solid rgba(97, 216, 255, 0.22);
            border-radius: 14px;
        }
        """
    )
    lay = QVBoxLayout(card)
    lay.setContentsMargins(18, 16, 18, 16)
    lay.setSpacing(12)
    return card, lay


def section_label(text: str, parent: QWidget) -> QLabel:
    lbl = QLabel(text, parent)
    lbl.setStyleSheet(
        f"""
        color: {CYAN};
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 1.6px;
        background: transparent;
        """
    )
    return lbl
