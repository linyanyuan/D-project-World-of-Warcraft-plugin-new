"""Vision page: backend choice, regions dir, calibrator, preview."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout
from qfluentwidgets import (
    BodyLabel,
    CheckBox,
    ComboBox,
    LineEdit,
    PrimaryPushButton,
    PushButton,
)

from clean_client.config.loader import Region, load_regions_dir
from clean_client.ui.preview import compose_preview_pixmap, tip_for_preview
from clean_client.ui.theme import TEXT_MUTED, add_page_header, make_card, section_label
from clean_client.ui.widgets.void_page import VoidPage

_VISION_CHOICES: tuple[tuple[str, str], ...] = (
    ("模拟识别（调试）", "mock"),
    ("像素协议（真实色块）", "pixel"),
)


class VisionPage(VoidPage):
    """Configure vision backend, regions, calibrator, and preview."""

    calibrator_requested = Signal()
    preview_requested = Signal()
    autofind_requested = Signal()
    regions_dir_changed = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("visionPage")
        self._last_frame: np.ndarray | None = None
        self._build_ui()
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self.preview_requested.emit)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 22)
        root.setSpacing(14)

        add_page_header(
            root,
            self,
            "识别",
            "视觉后端 · 区域标定 · 截屏预览 · 色块读取",
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

        self.autofind_btn = PushButton("自动建议 Skill 区域", card)
        self.autofind_btn.clicked.connect(self.autofind_requested.emit)
        card_layout.addWidget(self.autofind_btn)

        card_layout.addWidget(section_label("截屏预览", card))
        preview_btns = QHBoxLayout()
        self.preview_btn = PushButton("抓取预览", card)
        self.preview_btn.clicked.connect(self.preview_requested.emit)
        self.auto_preview_cb = CheckBox("自动刷新（约1秒）", card)
        self.auto_preview_cb.stateChanged.connect(self._on_auto_preview_changed)
        preview_btns.addWidget(self.preview_btn)
        preview_btns.addWidget(self.auto_preview_cb)
        preview_btns.addStretch(1)
        card_layout.addLayout(preview_btns)

        self.preview_meta = BodyLabel("尚未抓取预览", card)
        self.preview_meta.setStyleSheet(f"color: {TEXT_MUTED};")
        card_layout.addWidget(self.preview_meta)

        self.preview_label = QLabel(card)
        self.preview_label.setMinimumHeight(220)
        self.preview_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self.preview_label.setStyleSheet(
            "background: rgba(4,7,15,0.85); border: 1px solid rgba(97,216,255,0.18);"
            " border-radius: 10px; color: #8899aa;"
        )
        self.preview_label.setText("  点击「抓取预览」显示画面与区域框")
        self.preview_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        card_layout.addWidget(self.preview_label)

        self.tip_label = BodyLabel(
            "提示: 可先「自动建议 Skill 区域」，再抓取预览确认框选；也可手动打开标定器精修。",
            card,
        )
        self.tip_label.setWordWrap(True)
        self.tip_label.setStyleSheet("color: #9ad7ff;")
        card_layout.addWidget(self.tip_label)

        self.status_label = BodyLabel("", card)
        self.status_label.setStyleSheet(f"color: {TEXT_MUTED};")
        card_layout.addWidget(self.status_label)

        root.addWidget(card, stretch=1)

    def _browse_regions(self) -> None:
        start = self.regions_edit.text().strip() or str(Path.cwd())
        directory = QFileDialog.getExistingDirectory(self, "选择区域目录", start)
        if directory:
            self.regions_edit.setText(directory)
            self.regions_dir_changed.emit(directory)
            self.refresh_tip_only()

    def _on_auto_preview_changed(self, _state: int = 0) -> None:
        if self.auto_preview_cb.isChecked():
            self._timer.start()
            self.preview_requested.emit()
        else:
            self._timer.stop()

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

    def set_regions_dir(self, path: str | Path | None) -> None:
        if path is None:
            self.regions_edit.setText("")
        else:
            self.regions_edit.setText(str(path))
        self.refresh_tip_only()

    def loaded_regions(self) -> dict[str, Region]:
        path = self.regions_dir()
        if path is None:
            return {}
        try:
            return load_regions_dir(path)
        except ValueError:
            return {}

    def set_status(self, message: str) -> None:
        self.status_label.setText(message)

    def set_tip(self, message: str) -> None:
        self.tip_label.setText(message)

    def refresh_tip_only(
        self,
        *,
        capture_backend: str = "null",
        hwnd: int | None = None,
    ) -> None:
        tip = tip_for_preview(
            vision_mode=self.vision_mode(),
            capture_backend=capture_backend,
            hwnd=hwnd,
            regions=self.loaded_regions(),
            frame=self._last_frame,
            error=None,
        )
        self.set_tip(tip)

    def show_preview(
        self,
        frame: np.ndarray | None,
        *,
        capture_label: str,
        capture_backend: str,
        hwnd: int | None,
        error: str | None = None,
    ) -> None:
        regions = self.loaded_regions()
        if error is not None or frame is None:
            self._last_frame = None
            self.preview_label.clear()
            self.preview_label.setText("  预览失败 — 请更换截屏方式后重试")
            self.preview_meta.setText(f"预览失败 · 截屏={capture_label}")
            self.set_tip(
                tip_for_preview(
                    vision_mode=self.vision_mode(),
                    capture_backend=capture_backend,
                    hwnd=hwnd,
                    regions=regions,
                    frame=None,
                    error=error or "未获得画面",
                )
            )
            return

        self._last_frame = frame
        pixmap = compose_preview_pixmap(frame, regions, max_width=720)
        self.preview_label.setPixmap(pixmap)
        h, w = frame.shape[:2]
        self.preview_meta.setText(
            f"分辨率 {w}x{h} · 区域 {len(regions)} 个 · 截屏={capture_label}"
            + (f" · hwnd={hwnd}" if hwnd is not None else " · hwnd=—")
        )
        self.set_tip(
            tip_for_preview(
                vision_mode=self.vision_mode(),
                capture_backend=capture_backend,
                hwnd=hwnd,
                regions=regions,
                frame=frame,
                error=None,
            )
        )
