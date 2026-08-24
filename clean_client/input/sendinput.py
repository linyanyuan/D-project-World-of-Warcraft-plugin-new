"""Minimal SendInput key tap."""

from __future__ import annotations

import time
from ctypes import POINTER, Structure, Union, byref, c_ulong, sizeof, windll
from ctypes.wintypes import DWORD, WORD

MOD_MAP = {
    "shift": 0x10,
    "ctrl": 0x11,
    "control": 0x11,
    "alt": 0x12,
}


class KEYBDINPUT(Structure):
    _fields_ = [
        ("wVk", WORD),
        ("wScan", WORD),
        ("dwFlags", DWORD),
        ("time", DWORD),
        ("dwExtraInfo", POINTER(c_ulong)),
    ]


class INPUT_I(Union):
    _fields_ = [("ki", KEYBDINPUT)]


class INPUT(Structure):
    _fields_ = [("type", DWORD), ("ii", INPUT_I)]


KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1


def _vk_for_token(token: str) -> int:
    t = token.lower()
    if t in MOD_MAP:
        return MOD_MAP[t]
    if len(t) == 1:
        return windll.user32.VkKeyScanW(ord(t)) & 0xFF
    if t.startswith("f") and t[1:].isdigit():
        try:
            return 0x70 + int(t[1:]) - 1  # F1=0x70
        except ValueError as exc:
            raise ValueError(f"unsupported function key: {token}") from exc
    raise ValueError(f"unsupported key token: {token}")


def parse_key_combo(combo: str) -> list[int]:
    parts = [p.strip() for p in combo.lower().replace("+", "-").split("-") if p.strip()]
    if not parts:
        raise ValueError("empty key combo")
    return [_vk_for_token(p) for p in parts]


def tap_key(combo: str, *, press_ms: float = 30.0, sleeper=time.sleep) -> None:
    vks = parse_key_combo(combo)
    for vk in vks:
        inp = INPUT(
            type=INPUT_KEYBOARD,
            ii=INPUT_I(
                ki=KEYBDINPUT(wVk=vk, wScan=0, dwFlags=0, time=0, dwExtraInfo=None)
            ),
        )
        windll.user32.SendInput(1, byref(inp), sizeof(INPUT))
    sleeper(max(press_ms, 0) / 1000.0)
    for vk in reversed(vks):
        inp = INPUT(
            type=INPUT_KEYBOARD,
            ii=INPUT_I(
                ki=KEYBDINPUT(
                    wVk=vk, wScan=0, dwFlags=KEYEVENTF_KEYUP, time=0, dwExtraInfo=None
                )
            ),
        )
        windll.user32.SendInput(1, byref(inp), sizeof(INPUT))
