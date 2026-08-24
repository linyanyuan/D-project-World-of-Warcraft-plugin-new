"""PrintWindow capture of a specific hwnd → BGR (best-effort v1)."""

from __future__ import annotations

import numpy as np


class PrintWindowCapture:
    def grab(self, hwnd: int | None = None) -> np.ndarray:
        if hwnd is None:
            return np.zeros((64, 64, 3), dtype=np.uint8)
        try:
            from ctypes import windll

            import win32gui
            import win32ui
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("pywin32 required for PrintWindow") from exc

        left, top, right, bottom = win32gui.GetClientRect(hwnd)
        width, height = right - left, bottom - top
        if width <= 0 or height <= 0:
            return np.zeros((64, 64, 3), dtype=np.uint8)

        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(bitmap)
        windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 3)
        bmpinfo = bitmap.GetInfo()
        bmpstr = bitmap.GetBitmapBits(True)
        img = np.frombuffer(bmpstr, dtype=np.uint8)
        img.shape = (bmpinfo["bmHeight"], bmpinfo["bmWidth"], 4)
        bgr = np.ascontiguousarray(img[:, :, :3])
        win32gui.DeleteObject(bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)
        return bgr
