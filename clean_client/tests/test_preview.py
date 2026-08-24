"""Tests for recognition preview helpers."""

from __future__ import annotations

import numpy as np

from clean_client.ui.preview import (
    compose_preview_pixmap,
    frame_mean_luma,
    tip_for_preview,
)


def test_compose_preview_pixmap_draws_regions() -> None:
    frame = np.zeros((120, 200, 3), dtype=np.uint8)
    frame[:, :] = (30, 40, 50)
    pixmap = compose_preview_pixmap(
        frame,
        {"Skill": (10, 10, 80, 40)},
        max_width=100,
    )
    assert not pixmap.isNull()
    assert pixmap.width() <= 100


def test_tip_for_preview_cases() -> None:
    assert "方式一/二/三" in tip_for_preview(
        vision_mode="pixel",
        capture_backend="null",
        hwnd=None,
        regions={},
        frame=None,
    )
    assert "Skill" in tip_for_preview(
        vision_mode="pixel",
        capture_backend="mss",
        hwnd=1,
        regions={"Target": (1, 2, 3, 4)},
        frame=np.ones((10, 10, 3), dtype=np.uint8) * 40,
    )
    black = np.zeros((10, 10, 3), dtype=np.uint8)
    assert frame_mean_luma(black) < 1
    assert "全黑" in tip_for_preview(
        vision_mode="pixel",
        capture_backend="mss",
        hwnd=1,
        regions={"Skill": (1, 2, 3, 4)},
        frame=black,
    )
