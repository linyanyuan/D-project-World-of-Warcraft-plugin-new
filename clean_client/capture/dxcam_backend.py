"""dxcam capture → BGR."""

from __future__ import annotations

import numpy as np


class DxcamCapture:
    def __init__(self) -> None:
        import dxcam  # type: ignore[import-not-found]

        self._cam = dxcam.create(output_color="BGR")

    def grab(self, hwnd: int | None = None) -> np.ndarray:
        frame = self._cam.grab()
        if frame is None:
            return np.zeros((64, 64, 3), dtype=np.uint8)
        return np.ascontiguousarray(frame)
