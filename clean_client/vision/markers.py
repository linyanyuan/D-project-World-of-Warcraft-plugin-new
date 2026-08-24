"""RGB marker vocabulary recovered from Nirvana client dumps."""

from __future__ import annotations

MARKERS: dict[str, tuple[int, int, int]] = {
    "START": (0xFF, 0x00, 0xFF),
    "END": (0xFF, 0x80, 0x00),
    "SEP": (0x80, 0x80, 0x80),
    "ITEM": (0xFF, 0xFF, 0x00),
    "SPELL": (0xFF, 0xFF, 0xFF),
    "ETC": (0x2A, 0x59, 0x38),
    "RED": (0xFF, 0x00, 0x00),
    "RES": (0xFF, 0xFF, 0x80),
}

MARKER_HEX: dict[str, str] = {
    name: f"{r:02x}{g:02x}{b:02x}" for name, (r, g, b) in MARKERS.items()
}


def rgb_matches(
    pixel: tuple[int, int, int],
    expected: tuple[int, int, int],
    tol: int = 0,
) -> bool:
    try:
        return all(
            abs(int(a) - int(b)) <= tol for a, b in zip(pixel, expected, strict=True)
        )
    except (TypeError, ValueError):
        return False
