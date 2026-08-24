"""Capture backends returning BGR uint8 arrays."""

from __future__ import annotations

from typing import Protocol

import numpy as np


class CaptureBackend(Protocol):
    def grab(self, hwnd: int | None = None) -> np.ndarray: ...


class NullCapture:
    """Test double that returns a solid frame."""

    def __init__(self, shape: tuple[int, int, int] = (64, 64, 3)) -> None:
        self.shape = shape

    def grab(self, hwnd: int | None = None) -> np.ndarray:
        return np.zeros(self.shape, dtype=np.uint8)


def create_backend(mode: str) -> CaptureBackend:
    """Provisional mapping: 方式一 printwindow, 方式二 mss, 方式三 dxcam."""
    key = mode.strip().lower()
    if key in {"null", "mock", "test"}:
        return NullCapture()
    if key in {"方式二", "mss", "2"}:
        from clean_client.capture.mss_backend import (
            MssCapture,  # type: ignore[import-not-found]
        )

        return MssCapture()
    if key in {"方式三", "dxcam", "3"}:
        from clean_client.capture.dxcam_backend import (
            DxcamCapture,  # type: ignore[import-not-found]
        )

        return DxcamCapture()
    # default / 方式一
    from clean_client.capture.printwindow_backend import (  # type: ignore[import-not-found]
        PrintWindowCapture,
    )

    return PrintWindowCapture()
