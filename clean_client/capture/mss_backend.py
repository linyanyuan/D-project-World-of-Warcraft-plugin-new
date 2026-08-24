"""mss full-screen / monitor capture → BGR."""

from __future__ import annotations

import numpy as np


class MssCapture:
    def __init__(self) -> None:
        import mss  # type: ignore[import-not-found]

        self._mss = mss.mss()

    def grab(self, hwnd: int | None = None) -> np.ndarray:
        # hwnd ignored for v1 full-monitor grab; region crop happens in Vision
        shot = self._mss.grab(self._mss.monitors[1])
        frame = np.asarray(shot)[:, :, :3]  # BGRA -> BGR
        return np.ascontiguousarray(frame)
