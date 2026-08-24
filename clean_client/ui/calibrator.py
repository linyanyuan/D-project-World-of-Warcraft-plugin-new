"""区域标定界面：框选/编辑 技能/目标/玩家/增益 矩形。"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np
from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from clean_client.capture.backends import CaptureBackend, NullCapture, create_backend
from clean_client.capture.window import find_wow_hwnd
from clean_client.config.loader import (
    REGION_KEYS,
    Region,
    load_regions_dir,
    save_regions_dir,
)
from clean_client.ui.geometry import clamp_region, rubber_band_to_region

# 各区域叠加色（RGBA）
REGION_COLORS: dict[str, QColor] = {
    "Skill": QColor(0, 200, 255, 90),
    "Target": QColor(255, 80, 80, 90),
    "Player": QColor(80, 255, 120, 90),
    "Buff": QColor(255, 220, 0, 90),
}

REGION_LABELS: dict[str, str] = {
    "Skill": "技能",
    "Target": "目标",
    "Player": "玩家",
    "Buff": "增益",
}


def bgr_to_qimage(frame: np.ndarray) -> QImage:
    """Convert a BGR uint8 HxWx3 array to QImage (RGB888, copied)."""
    if frame.ndim != 3 or frame.shape[2] < 3:
        raise ValueError("frame must be HxWx3 BGR")
    rgb = np.ascontiguousarray(frame[:, :, ::-1])
    height, width, _ = rgb.shape
    bytes_per_line = 3 * width
    image = QImage(rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
    return image.copy()


class FrameCanvas(QLabel):
    """可拖拽框选区域的图像画布。"""

    def __init__(self, on_region_drawn: Callable[[Region], None] | None = None) -> None:
        super().__init__()
        self.setMinimumSize(640, 360)
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setStyleSheet("background:#1e1e1e; color:#aaa;")
        self.setText("请先抓取画面")
        self._on_region_drawn = on_region_drawn
        self._base_pixmap: QPixmap | None = None
        self._regions: dict[str, Region] = {}
        self._active_key = "Skill"
        self._dragging = False
        self._origin = QPoint()
        self._current = QPoint()
        self._frame_size = (0, 0)

    def set_frame(self, frame: np.ndarray) -> None:
        image = bgr_to_qimage(frame)
        self._base_pixmap = QPixmap.fromImage(image)
        self._frame_size = (frame.shape[1], frame.shape[0])
        self.setFixedSize(self._base_pixmap.size())
        self._redraw()

    def set_regions(self, regions: dict[str, Region]) -> None:
        self._regions = dict(regions)
        self._redraw()

    def set_active_key(self, key: str) -> None:
        self._active_key = key

    def frame_size(self) -> tuple[int, int]:
        return self._frame_size

    def _redraw(self) -> None:
        if self._base_pixmap is None:
            return
        composed = QPixmap(self._base_pixmap)
        painter = QPainter(composed)
        for key, region in self._regions.items():
            color = REGION_COLORS.get(key, QColor(255, 255, 255, 80))
            x1, y1, x2, y2 = region
            rect = QRect(x1, y1, max(0, x2 - x1), max(0, y2 - y1))
            painter.fillRect(rect, color)
            pen = QPen(
                color.darker(150) if hasattr(color, "darker") else QColor(255, 255, 255)
            )
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(rect)
            painter.drawText(x1 + 4, y1 + 14, REGION_LABELS.get(key, key))
        if self._dragging:
            band = QRect(self._origin, self._current).normalized()
            painter.setPen(QPen(QColor(255, 255, 255), 1, Qt.PenStyle.DashLine))
            painter.drawRect(band)
        painter.end()
        self.setPixmap(composed)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if self._base_pixmap is None or event.button() != Qt.MouseButton.LeftButton:
            return
        self._dragging = True
        self._origin = event.position().toPoint()
        self._current = self._origin
        self._redraw()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if not self._dragging:
            return
        self._current = event.position().toPoint()
        self._redraw()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if not self._dragging or event.button() != Qt.MouseButton.LeftButton:
            return
        self._dragging = False
        self._current = event.position().toPoint()
        width, height = self._frame_size
        region = rubber_band_to_region(
            (self._origin.x(), self._origin.y()),
            (self._current.x(), self._current.y()),
            width=width,
            height=height,
        )
        self._regions[self._active_key] = region
        self._redraw()
        if self._on_region_drawn is not None:
            self._on_region_drawn(region)


class RegionCalibratorWindow(QMainWindow):
    """选择并保存截屏区域的主窗口。"""

    def __init__(
        self,
        *,
        output_dir: Path | None = None,
        capture: CaptureBackend | None = None,
        grab_hwnd: bool = True,
        on_saved: Callable[[Path], None] | None = None,
    ) -> None:
        super().__init__()
        self.setWindowTitle("区域标定器")
        self.resize(960, 720)

        self._output_dir = Path(output_dir) if output_dir else Path.cwd()
        self._capture: CaptureBackend = (
            capture if capture is not None else NullCapture((720, 1280, 3))
        )
        self._grab_hwnd = grab_hwnd
        self._on_saved = on_saved
        self._hwnd: int | None = None
        self._frame: np.ndarray | None = None
        self._regions: dict[str, Region] = {
            "Skill": (20, 20, 220, 80),
            "Target": (240, 20, 440, 80),
            "Player": (20, 100, 220, 180),
            "Buff": (240, 100, 440, 180),
        }
        self._updating_spins = False
        self._key_labels = [REGION_LABELS[k] for k in REGION_KEYS]
        self._label_to_key = {REGION_LABELS[k]: k for k in REGION_KEYS}

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        toolbar = QHBoxLayout()
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(
            [
                "空（测试·不截屏）",
                "方式一 · 窗口打印（PrintWindow）",
                "方式二 · 屏幕截取（MSS）",
                "方式三 · 高速复制（DXGI）",
            ]
        )
        self._mode_values = {
            "空（测试·不截屏）": "null",
            "空（测试）": "null",
            "方式一 · 窗口打印（PrintWindow）": "printwindow",
            "方式一": "printwindow",
            "方式二 · 屏幕截取（MSS）": "mss",
            "方式二": "mss",
            "方式三 · 高速复制（DXGI）": "dxcam",
            "方式三": "dxcam",
            "null": "null",
            "mss": "mss",
            "dxcam": "dxcam",
            "printwindow": "printwindow",
        }
        toolbar.addWidget(QLabel("截屏:"))
        toolbar.addWidget(self._mode_combo)

        grab_btn = QPushButton("抓取画面")
        grab_btn.clicked.connect(self._on_grab)
        toolbar.addWidget(grab_btn)

        load_btn = QPushButton("加载区域…")
        load_btn.clicked.connect(self._on_load)
        toolbar.addWidget(load_btn)

        save_btn = QPushButton("保存区域…")
        save_btn.clicked.connect(self._on_save)
        toolbar.addWidget(save_btn)
        toolbar.addStretch(1)
        layout.addLayout(toolbar)

        body = QHBoxLayout()
        self._canvas = FrameCanvas(on_region_drawn=self._on_canvas_region)
        self._canvas.set_regions(self._regions)
        body.addWidget(self._canvas, stretch=1)

        side = QVBoxLayout()
        side.addWidget(QLabel("当前区域"))
        self._key_combo = QComboBox()
        self._key_combo.addItems(self._key_labels)
        self._key_combo.currentTextChanged.connect(self._on_key_changed)
        side.addWidget(self._key_combo)

        form = QFormLayout()
        self._spins: dict[str, QSpinBox] = {}
        for name, label in (
            ("x1", "左"),
            ("y1", "上"),
            ("x2", "右"),
            ("y2", "下"),
        ):
            spin = QSpinBox()
            spin.setRange(0, 100000)
            spin.valueChanged.connect(self._on_spin_changed)
            self._spins[name] = spin
            form.addRow(label, spin)
        side.addLayout(form)

        apply_btn = QPushButton("应用数值")
        apply_btn.clicked.connect(self._on_apply_numeric)
        side.addWidget(apply_btn)

        self._dir_label = QLabel(f"目录: {self._output_dir}")
        self._dir_label.setWordWrap(True)
        side.addWidget(self._dir_label)
        side.addStretch(1)
        body.addLayout(side)
        layout.addLayout(body)

        self._status = QLabel("就绪 — 先抓取画面，选择区域类型，再在图上拖拽框选。")
        layout.addWidget(self._status)

        self._sync_spins_from_region(self._regions["Skill"])

    def _active_key(self) -> str:
        label = self._key_combo.currentText()
        return self._label_to_key.get(label, "Skill")

    def _capture_mode(self) -> str:
        label = self._mode_combo.currentText()
        return self._mode_values.get(label, "null")

    def _on_key_changed(self, label: str) -> None:
        key = self._label_to_key.get(label, "Skill")
        self._canvas.set_active_key(key)
        region = self._regions.get(key)
        if region is not None:
            self._sync_spins_from_region(region)

    def _on_canvas_region(self, region: Region) -> None:
        key = self._active_key()
        self._regions[key] = region
        self._sync_spins_from_region(region)
        label = REGION_LABELS.get(key, key)
        self._status.setText(
            f"{label} = {region[0]} {region[1]} {region[2]} {region[3]}"
        )

    def _sync_spins_from_region(self, region: Region) -> None:
        self._updating_spins = True
        try:
            self._spins["x1"].setValue(region[0])
            self._spins["y1"].setValue(region[1])
            self._spins["x2"].setValue(region[2])
            self._spins["y2"].setValue(region[3])
        finally:
            self._updating_spins = False

    def _on_spin_changed(self, _value: int = 0) -> None:
        if self._updating_spins:
            return
        self._on_apply_numeric()

    def _on_apply_numeric(self) -> None:
        key = self._active_key()
        region = (
            self._spins["x1"].value(),
            self._spins["y1"].value(),
            self._spins["x2"].value(),
            self._spins["y2"].value(),
        )
        width, height = self._canvas.frame_size()
        if width > 0 and height > 0:
            region = clamp_region(region, width=width, height=height)
        self._regions[key] = region
        self._canvas.set_regions(self._regions)
        self._sync_spins_from_region(region)

    def _on_grab(self) -> None:
        mode = self._capture_mode()
        try:
            if mode == "null":
                self._capture = NullCapture((720, 1280, 3))
                frame = self._capture.grab()
                frame[:, :] = (40, 40, 40)
                frame[::40, :, :] = (70, 70, 90)
                frame[:, ::40, :] = (70, 90, 70)
            else:
                self._capture = create_backend(mode)
                hwnd = None
                if self._grab_hwnd:
                    try:
                        hwnd = find_wow_hwnd()
                    except (RuntimeError, OSError, TypeError, ValueError) as exc:
                        self._status.setText(f"查找游戏窗口已跳过: {exc}")
                self._hwnd = hwnd
                frame = self._capture.grab(hwnd)
        except Exception as exc:  # noqa: BLE001 — surface any capture failure in UI
            QMessageBox.warning(self, "抓取失败", str(exc))
            self._status.setText(f"抓取失败: {exc}")
            return

        self._frame = frame
        self._canvas.set_frame(frame)
        self._canvas.set_regions(self._regions)
        self._status.setText(f"画面 {frame.shape[1]}x{frame.shape[0]}，来源 {mode}")

    def _on_load(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "从目录加载区域文件…", str(self._output_dir)
        )
        if not directory:
            return
        path = Path(directory)
        try:
            loaded = load_regions_dir(path)
        except ValueError as exc:
            QMessageBox.warning(self, "加载失败", str(exc))
            return
        if not loaded:
            QMessageBox.information(self, "加载", "未找到 *_region.txt 文件。")
            return
        self._regions.update(loaded)
        self._output_dir = path
        self._dir_label.setText(f"目录: {self._output_dir}")
        self._canvas.set_regions(self._regions)
        key = self._active_key()
        if key in self._regions:
            self._sync_spins_from_region(self._regions[key])
        self._status.setText(f"已从 {path} 加载 {len(loaded)} 个区域")

    def _on_save(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "保存区域文件到…", str(self._output_dir)
        )
        if not directory:
            return
        path = Path(directory)
        try:
            save_regions_dir(path, self._regions)
        except OSError as exc:
            QMessageBox.warning(self, "保存失败", str(exc))
            return
        self._output_dir = path
        self._dir_label.setText(f"目录: {self._output_dir}")
        self._status.setText(f"已保存 4 个区域文件到 {path}")
        if self._on_saved is not None:
            self._on_saved(path)


def run_calibrator(
    *,
    output_dir: str | Path | None = None,
    capture_mode: str = "null",
    on_saved: Callable[[Path], None] | None = None,
) -> int:
    """启动标定器；若已有 QApplication 则不阻塞。"""
    app = QApplication.instance()
    owns_app = app is None
    if owns_app:
        app = QApplication([])

    capture: CaptureBackend | None = None
    if capture_mode:
        try:
            capture = create_backend(capture_mode)
        except Exception:  # noqa: BLE001
            capture = NullCapture((720, 1280, 3))

    window = RegionCalibratorWindow(
        output_dir=Path(output_dir) if output_dir else None,
        capture=capture,
        on_saved=on_saved,
    )
    # 预选截屏方式
    raw_mode = (capture_mode or "null").strip()
    display_map = {
        "null": "空（测试·不截屏）",
        "mock": "空（测试·不截屏）",
        "test": "空（测试·不截屏）",
        "空（测试）": "空（测试·不截屏）",
        "空（测试·不截屏）": "空（测试·不截屏）",
        "printwindow": "方式一 · 窗口打印（PrintWindow）",
        "方式一": "方式一 · 窗口打印（PrintWindow）",
        "1": "方式一 · 窗口打印（PrintWindow）",
        "mss": "方式二 · 屏幕截取（MSS）",
        "方式二": "方式二 · 屏幕截取（MSS）",
        "2": "方式二 · 屏幕截取（MSS）",
        "dxcam": "方式三 · 高速复制（DXGI）",
        "方式三": "方式三 · 高速复制（DXGI）",
        "3": "方式三 · 高速复制（DXGI）",
    }
    display = display_map.get(
        raw_mode.lower(), display_map.get(raw_mode, "空（测试·不截屏）")
    )
    idx = window._mode_combo.findText(display)  # noqa: SLF001
    if idx >= 0:
        window._mode_combo.setCurrentIndex(idx)  # noqa: SLF001
    window.show()
    window._on_grab()  # noqa: SLF001
    if not owns_app:
        return 0
    try:
        return int(app.exec())
    except (TypeError, ValueError):
        return 1
