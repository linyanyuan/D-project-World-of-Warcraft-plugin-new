"""Settings page: window keywords and match thresholds."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QVBoxLayout
from qfluentwidgets import (
    BodyLabel,
    DoubleSpinBox,
    LineEdit,
    PrimaryPushButton,
    SpinBox,
)

from clean_client.ui.theme import TEXT_MUTED, add_page_header, make_card, section_label
from clean_client.ui.widgets.void_page import VoidPage


class SettingsPage(VoidPage):
    """Editable runtime settings (applied to in-memory config)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("settingsPage")
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 22)
        root.setSpacing(14)

        add_page_header(
            root,
            self,
            "系统设置",
            "窗口关键字 · 识别阈值 · 写入本地 default.json",
            badge="本地",
        )

        card, card_layout = make_card(self)
        card_layout.addWidget(section_label("匹配参数", card))

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.keywords_edit = LineEdit(card)
        self.keywords_edit.setPlaceholderText("World of Warcraft, 魔兽世界")
        form.addRow(BodyLabel("窗口关键字", card), self.keywords_edit)

        self.cd_ready_spin = SpinBox(card)
        self.cd_ready_spin.setRange(0, 5000)
        self.cd_ready_spin.setSuffix(" ms")
        form.addRow(BodyLabel("CD 就绪窗口", card), self.cd_ready_spin)

        self.buff_threshold_spin = DoubleSpinBox(card)
        self.buff_threshold_spin.setRange(0.0, 1.0)
        self.buff_threshold_spin.setSingleStep(0.05)
        self.buff_threshold_spin.setDecimals(2)
        form.addRow(BodyLabel("Buff 匹配阈值", card), self.buff_threshold_spin)

        card_layout.addLayout(form)
        root.addWidget(card)

        btn_row = QHBoxLayout()
        self.save_btn = PrimaryPushButton("保存设置", self)
        self.save_btn.setMinimumHeight(38)
        self.save_btn.setMinimumWidth(140)
        btn_row.addWidget(self.save_btn)
        btn_row.addStretch(1)
        root.addLayout(btn_row)

        self.note_label = BodyLabel("尚未保存。", self)
        self.note_label.setStyleSheet(f"color: {TEXT_MUTED};")
        root.addWidget(self.note_label)
        root.addStretch(1)

    def load_from_config(self, cfg: dict[str, Any]) -> None:
        keywords = cfg.get("window_keywords") or []
        if isinstance(keywords, (list, tuple)):
            self.keywords_edit.setText(", ".join(str(k) for k in keywords))
        else:
            self.keywords_edit.setText(str(keywords))
        try:
            self.cd_ready_spin.setValue(int(cfg.get("cd_ready_window_ms", 30)))
        except (TypeError, ValueError):
            self.cd_ready_spin.setValue(30)
        try:
            self.buff_threshold_spin.setValue(
                float(cfg.get("buff_match_threshold", 0.7))
            )
        except (TypeError, ValueError):
            self.buff_threshold_spin.setValue(0.7)

    def values(self) -> dict[str, Any]:
        raw = self.keywords_edit.text().strip()
        keywords = [part.strip() for part in raw.split(",") if part.strip()]
        try:
            cd_ready = int(self.cd_ready_spin.value())
        except (TypeError, ValueError):
            cd_ready = 30
        try:
            buff_threshold = float(self.buff_threshold_spin.value())
        except (TypeError, ValueError):
            buff_threshold = 0.7
        return {
            "window_keywords": keywords,
            "cd_ready_window_ms": cd_ready,
            "buff_match_threshold": buff_threshold,
        }

    def set_note(self, message: str) -> None:
        self.note_label.setText(message)
