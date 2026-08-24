"""Spell-id packing: RGB 12ca33 -> 0x12ca33 -> 1231411."""

from __future__ import annotations


def _byte(value: object) -> int:
    try:
        return int(value) & 0xFF  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise TypeError(f"expected int-compatible channel, got {value!r}") from exc


def rgb_to_spell_id(r: object, g: object, b: object) -> int:
    return (_byte(r) << 16) | (_byte(g) << 8) | _byte(b)


def spell_id_to_rgb(spell_id: object) -> tuple[int, int, int]:
    try:
        sid = int(spell_id) & 0xFFFFFF  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise TypeError(f"spell_id must be int-compatible, got {spell_id!r}") from exc
    return (sid >> 16) & 0xFF, (sid >> 8) & 0xFF, sid & 0xFF
