"""Offscreen smoke for calibrator helpers that touch Qt."""

from __future__ import annotations

import os

import numpy as np
import pytest

# Must set before QApplication for headless CI / servers.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from clean_client.ui.calibrator import bgr_to_qimage
from clean_client.ui.geometry import rubber_band_to_region


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    existing = QApplication.instance()
    if isinstance(existing, QApplication):
        return existing
    return QApplication([])


def test_bgr_to_qimage_size(qapp: QApplication) -> None:
    frame = np.zeros((40, 60, 3), dtype=np.uint8)
    frame[:, :, 0] = 255  # B
    image = bgr_to_qimage(frame)
    assert image.width() == 60
    assert image.height() == 40


def test_rubber_band_matches_loader_format(qapp: QApplication) -> None:
    # Ensure geometry helper stays compatible with save_region_file ints.
    region = rubber_band_to_region((15, 25), (5, 10), width=100, height=100)
    assert isinstance(region[0], int)
    assert region[0] == 5
    assert region[1] == 10
    assert region[2] == 15
    assert region[3] == 25
