from clean_client.capture.window import find_wow_hwnd


def test_find_wow_hwnd_with_stub() -> None:
    windows = {1: "Notepad", 2: "World of Warcraft", 3: "Chrome"}

    def enum_windows(cb, _extra):
        for hwnd in windows:
            cb(hwnd, None)

    def get_title(hwnd):
        return windows[hwnd]

    hwnd = find_wow_hwnd(enum_windows=enum_windows, get_title=get_title)
    assert hwnd == 2
