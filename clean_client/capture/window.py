"""Find WoW client hwnd by title keywords."""

from __future__ import annotations

from collections.abc import Callable

try:
    import win32gui
except ImportError:  # pragma: no cover
    win32gui = None  # type: ignore


DEFAULT_KEYWORDS = ("World of Warcraft", "魔兽世界", "Warcraft")


def find_wow_hwnd(
    keywords: tuple[str, ...] = DEFAULT_KEYWORDS,
    *,
    enum_windows: Callable | None = None,
    get_title: Callable | None = None,
) -> int | None:
    if enum_windows is None or get_title is None:
        if win32gui is None:
            raise RuntimeError("pywin32 is required for window discovery")
        enum_windows = win32gui.EnumWindows
        get_title = win32gui.GetWindowText

    found: list[int] = []

    def _callback(hwnd: object, _extra: object) -> None:
        try:
            title = str(get_title(hwnd) or "")
        except (TypeError, ValueError, OSError):
            return
        for kw in keywords:
            if kw.lower() in title.lower():
                try:
                    found.append(int(hwnd))  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    return
                return

    enum_windows(_callback, None)
    return found[0] if found else None
