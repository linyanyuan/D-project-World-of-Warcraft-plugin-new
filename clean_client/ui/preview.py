"""Preview helpers: BGR frame → QPixmap with region overlays."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap

from clean_client.config.loader import Region

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
    if frame.ndim != 3 or frame.shape[2] < 3:
        raise ValueError("frame must be HxWx3 BGR")
    rgb = np.ascontiguousarray(frame[:, :, ::-1])
    height, width, _ = rgb.shape
    bytes_per_line = 3 * width
    image = QImage(rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
    return image.copy()


def frame_mean_luma(frame: np.ndarray) -> float:
    """Rough brightness 0..255 for black-frame tip."""
    if frame.size == 0:
        return 0.0
    try:
        # BGR approximate luma
        b = frame[:, :, 0].astype(np.float32)
        g = frame[:, :, 1].astype(np.float32)
        r = frame[:, :, 2].astype(np.float32)
        return float((0.114 * b + 0.587 * g + 0.299 * r).mean())
    except (TypeError, ValueError, IndexError):
        return 0.0


def compose_preview_pixmap(
    frame: np.ndarray,
    regions: Mapping[str, Region] | None = None,
    *,
    max_width: int = 640,
) -> QPixmap:
    image = bgr_to_qimage(frame)
    pixmap = QPixmap.fromImage(image)
    painter = QPainter(pixmap)
    for key, region in (regions or {}).items():
        color = REGION_COLORS.get(key, QColor(255, 255, 255, 80))
        x1, y1, x2, y2 = region
        rect = QRect(x1, y1, max(0, x2 - x1), max(0, y2 - y1))
        painter.fillRect(rect, color)
        pen = QPen(QColor(255, 255, 255))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(rect)
        painter.drawText(x1 + 4, y1 + 16, REGION_LABELS.get(key, key))
    painter.end()

    if pixmap.width() > max_width and pixmap.width() > 0:
        pixmap = pixmap.scaledToWidth(max_width, Qt.TransformationMode.SmoothTransformation)
    return pixmap


def tip_for_preview(
    *,
    vision_mode: str,
    capture_backend: str,
    hwnd: int | None,
    regions: Mapping[str, Region] | None,
    frame: np.ndarray | None,
    error: str | None = None,
) -> str:
    if error:
        return f"预览失败: {error}。可尝试更换截屏方式一/二/三。"
    if vision_mode == "pixel" and capture_backend == "null":
        return "提示: 像素协议请改用方式一/二/三，空（测试）无法读真实色块。"
    if capture_backend == "printwindow" and hwnd is None:
        return "提示: 方式一需要先打开魔兽世界（未找到窗口句柄）。"
    if not regions:
        return "提示: 尚未载入区域文件。请先标定并保存 Skill 等区域。"
    if "Skill" not in (regions or {}):
        return "提示: 区域目录缺少 Skill（技能）框，像素协议无法工作。"
    if frame is None:
        return "点击「抓取预览」查看截屏与区域框。"
    if frame_mean_luma(frame) < 5.0:
        return "提示: 画面几乎全黑。可换截屏方式，或检查游戏是否在前台/是否全屏独占。"
    return f"预览正常 · 已叠加 {len(regions)} 个区域框。若仍读不到技能，请检查 AutoPlayer 与 Skill 框是否对准色块。"
