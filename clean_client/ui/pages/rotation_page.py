"""Rotation page: loaded Unholy profile (read-only)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView, QTableWidgetItem, QVBoxLayout
from qfluentwidgets import BodyLabel, TableWidget

from clean_client.ui.theme import (
    CYAN,
    TEXT_MUTED,
    add_page_header,
    make_card,
    section_label,
)
from clean_client.ui.widgets.void_page import VoidPage


class RotationPage(VoidPage):
    """Show the active Unholy profile and its actions."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("rotationPage")
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 22)
        root.setSpacing(14)

        add_page_header(
            root,
            self,
            "循环",
            "邪恶死亡骑士优先级列表（只读）。后续可接编辑器 / 云端循环。",
            badge="邪恶 DK",
        )

        card, card_layout = make_card(self)
        card_layout.addWidget(section_label("当前配置", card))
        self.profile_label = BodyLabel("配置: —", card)
        self.profile_label.setStyleSheet(
            f"color: {CYAN}; font-size: 14px; font-weight: 600;"
        )
        card_layout.addWidget(self.profile_label)
        hint = BodyLabel("按法术 ID 与像素协议绑定对齐；高亮技能优先。", card)
        hint.setStyleSheet(f"color: {TEXT_MUTED};")
        card_layout.addWidget(hint)

        self.actions_table = TableWidget(card)
        self.actions_table.setColumnCount(4)
        self.actions_table.setHorizontalHeaderLabels(
            ["法术 ID", "技能", "类型", "备用按键"]
        )
        self.actions_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.actions_table.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.actions_table.setSelectionBehavior(
            TableWidget.SelectionBehavior.SelectRows
        )
        self.actions_table.verticalHeader().setVisible(False)
        self.actions_table.setBorderVisible(True)
        self.actions_table.setBorderRadius(8)
        card_layout.addWidget(self.actions_table)
        root.addWidget(card, stretch=1)

    def set_profile(self, profile: dict[str, Any]) -> None:
        name = str(profile.get("name") or "未命名")
        actions = list(profile.get("actions") or [])
        self.profile_label.setText(f"{name}    ·    {len(actions)} 个动作")
        self.actions_table.setRowCount(len(actions))
        for row, action in enumerate(actions):
            values = [
                str(action.get("spell_id", "")),
                str(action.get("name", "")),
                str(action.get("kind", "")),
                str(action.get("fallback_key", "")),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.actions_table.setItem(row, col, item)
