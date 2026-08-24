"""Vision page: backend choice, regions dir, calibrator launch."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QVBoxLayout
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    LineEdit,
    PrimaryPushButton,
    PushButton,
)

from clean_client.ui.theme import TEXT_MUTED, add_page_header, make_card, section_label
from clean_client.ui.widgets.void_page import VoidPage

_VISION_CHOICES: tuple[tuple[str, str], ...] = (
    ("模拟识别（调试）", "mock"),
    ("像素协议（真实色块）", "pixel"),
)


class VisionPage(VoidPage):
    """Configure vision backend and region calibration."""

    calibrator_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("visionPage")
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 22)
        root.setSpacing(14)

        add_page_header(
            root,
            self,
            "识别",
            "视觉后端 · 技能/目标/玩家/增益 区域标定 · 色块读取",
            badge="像素",
        )

        card, card_layout = make_card(self)
        card_layout.addWidget(section_label("识别后端", card))

        backend_row = QHBoxLayout()
        backend_row.addWidget(BodyLabel("模式", card))
        self.vision_combo = ComboBox(card)
        self.vision_combo.addItems([label for label, _ in _VISION_CHOICES])
        self.vision_combo.setMinimumWidth(240)
        backend_row.addWidget(self.vision_combo)
        backend_row.addStretch(1)
        card_layout.addLayout(backend_row)

        tip = BodyLabel(
            "模拟识别：不读屏，日志多为空闲。像素协议：读取 AutoPlayer 色块行。",
            card,
        )
        tip.setStyleSheet(f"color: {TEXT_MUTED};")
        tip.setWordWrap(True)
        card_layout.addWidget(tip)

        card_layout.addWidget(section_label("区域文件", card))
        dir_row = QHBoxLayout()
        self.regions_edit = LineEdit(card)
        self.regions_edit.setPlaceholderText("选择包含 *_region.txt 的目录")
        self.browse_btn = PushButton("浏览…", card)
        self.browse_btn.clicked.connect(self._browse_regions)
        dir_row.addWidget(self.regions_edit, stretch=1)
        dir_row.addWidget(self.browse_btn)
        card_layout.addLayout(dir_row)

        self.calibrator_btn = PrimaryPushButton("打开区域标定器", card)
        self.calibrator_btn.setMinimumHeight(38)
        self.calibrator_btn.clicked.connect(self.calibrator_requested.emit)
        card_layout.addWidget(self.calibrator_btn)

        self.status_label = BodyLabel("", card)
        self.status_label.setStyleSheet(f"color: {TEXT_MUTED};")
        card_layout.addWidget(self.status_label)

        root.addWidget(card)
        root.addStretch(1)

    def _browse_regions(self) -> None:
        start = self.regions_edit.text().strip() or str(Path.cwd())
        directory = QFileDialog.getExistingDirectory(self, "选择区域目录", start)
        if directory:
            self.regions_edit.setText(directory)

    def vision_mode(self) -> str:
        label = self.vision_combo.currentText()
        for ui_label, mode in _VISION_CHOICES:
            if ui_label == label:
                return mode
        return "mock"

    def set_vision_mode(self, mode: str) -> None:
        key = (mode or "mock").strip().lower()
        for i, (_label, value) in enumerate(_VISION_CHOICES):
            if value == key or (key == "protocol" and value == "pixel"):
                self.vision_combo.setCurrentIndex(i)
                return
        self.vision_combo.setCurrentIndex(0)

    def regions_dir(self) -> Path | None:
        text = self.regions_edit.text().strip()
        if not text:
            return None
        return Path(text)

    def set_status(self, message: str) -> None:
        self.status_label.setText(message)
