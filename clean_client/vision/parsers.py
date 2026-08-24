"""Pixel-row parsers for AutoPlayer RGB protocol (v1 minimal)."""

from __future__ import annotations

from typing import Any

import numpy as np

from clean_client.models.state import Action, CooldownInfo
from clean_client.vision.encoding import rgb_to_spell_id, spell_id_to_rgb
from clean_client.vision.markers import MARKERS, rgb_matches


def _pixel_bgr_to_rgb(pix: Any) -> tuple[int, int, int]:
    # OpenCV/dxcam frames are BGR
    try:
        b, g, r = (int(pix[0]), int(pix[1]), int(pix[2]))
    except (TypeError, ValueError, IndexError) as exc:
        raise ValueError(f"invalid BGR pixel: {pix!r}") from exc
    return r, g, b


def parse_key_bindings_row(
    row_bgr: np.ndarray,
    *,
    default_key: str = "1",
    tol: int = 0,
) -> dict[int, Action]:
    """Parse a single BGR scanline for SPELL-marked spell-id pixels.

    Layout (v1):
      START | SPELL | <spell_rgb> | [SEP | SPELL | <spell_rgb> ...] | END

    Key chords are not fully recovered yet; ``default_key`` is used as placeholder
    unless callers remap via profile fallbacks.
    """
    if row_bgr.ndim != 2 or row_bgr.shape[1] < 3:
        raise ValueError("row_bgr must be shape (width, 3|4)")

    width = row_bgr.shape[0]
    bindings: dict[int, Action] = {}
    i = 0
    while i < width:
        rgb = _pixel_bgr_to_rgb(row_bgr[i])
        if rgb_matches(rgb, MARKERS["START"], tol=tol):
            i += 1
            break
        i += 1
    else:
        return bindings

    while i < width:
        rgb = _pixel_bgr_to_rgb(row_bgr[i])
        if rgb_matches(rgb, MARKERS["END"], tol=tol):
            break
        if rgb_matches(rgb, MARKERS["SEP"], tol=tol):
            i += 1
            continue
        if rgb_matches(rgb, MARKERS["SPELL"], tol=tol) or rgb_matches(
            rgb, MARKERS["ITEM"], tol=tol
        ):
            kind = "spell" if rgb_matches(rgb, MARKERS["SPELL"], tol=tol) else "item"
            if i + 1 >= width:
                break
            sid_rgb = _pixel_bgr_to_rgb(row_bgr[i + 1])
            if rgb_matches(sid_rgb, MARKERS["END"], tol=tol) or rgb_matches(
                sid_rgb, MARKERS["SEP"], tol=tol
            ):
                i += 1
                continue
            spell_id = rgb_to_spell_id(*sid_rgb)
            bindings[spell_id] = Action(
                spell_id=spell_id,
                key=default_key,
                kind=kind,
            )
            i += 2
            continue
        i += 1
    return bindings


def make_bindings_row(
    spell_ids: list[int],
    *,
    kind: str = "spell",
) -> np.ndarray:
    """Build a synthetic BGR row for tests."""
    marker = MARKERS["SPELL"] if kind == "spell" else MARKERS["ITEM"]
    pixels: list[tuple[int, int, int]] = [MARKERS["START"]]
    for idx, spell_id in enumerate(spell_ids):
        if idx:
            pixels.append(MARKERS["SEP"])
        pixels.append(marker)
        r, g, b = spell_id_to_rgb(spell_id)
        pixels.append((r, g, b))
    pixels.append(MARKERS["END"])
    # store as BGR
    row = np.zeros((len(pixels), 3), dtype=np.uint8)
    for i, (r, g, b) in enumerate(pixels):
        row[i] = (b, g, r)
    return row


def _flag_from_rgb(rgb: tuple[int, int, int]) -> tuple[bool, bool, bool]:
    r, g, b = rgb
    return (r >= 128, g >= 128, b >= 128)


def parse_cooldowns_row(
    row_bgr: np.ndarray,
    *,
    tol: int = 0,
) -> dict[int, CooldownInfo]:
    """Parse minimal cooldown/highlight row (Phase 3 v1).

    Layout:
      START | SPELL|ITEM | spell_rgb | flag_rgb
          [| ETC | (0, remain_byte, 0)]
          [SEP | ...] | END

    flag_rgb: R>=128 unusable, G>=128 has_cooldown, B>=128 highlighted.
    Optional ETC + magnitude pixel: cd_remain_s ~= remain_byte / 10.0
    """
    if row_bgr.ndim != 2 or row_bgr.shape[1] < 3:
        raise ValueError("row_bgr must be shape (width, 3|4)")

    width = row_bgr.shape[0]
    out: dict[int, CooldownInfo] = {}
    i = 0
    while i < width:
        rgb = _pixel_bgr_to_rgb(row_bgr[i])
        if rgb_matches(rgb, MARKERS["START"], tol=tol):
            i += 1
            break
        i += 1
    else:
        return out

    while i < width:
        rgb = _pixel_bgr_to_rgb(row_bgr[i])
        if rgb_matches(rgb, MARKERS["END"], tol=tol):
            break
        if rgb_matches(rgb, MARKERS["SEP"], tol=tol):
            i += 1
            continue
        if rgb_matches(rgb, MARKERS["SPELL"], tol=tol) or rgb_matches(
            rgb, MARKERS["ITEM"], tol=tol
        ):
            kind = "spell" if rgb_matches(rgb, MARKERS["SPELL"], tol=tol) else "item"
            if i + 2 >= width:
                break
            sid_rgb = _pixel_bgr_to_rgb(row_bgr[i + 1])
            flag_rgb = _pixel_bgr_to_rgb(row_bgr[i + 2])
            if rgb_matches(sid_rgb, MARKERS["END"], tol=tol) or rgb_matches(
                sid_rgb, MARKERS["SEP"], tol=tol
            ):
                i += 1
                continue
            spell_id = rgb_to_spell_id(*sid_rgb)
            unusable, has_cooldown, highlighted = _flag_from_rgb(flag_rgb)
            cd_remain_s = None
            j = i + 3
            if j + 1 < width:
                maybe_etc = _pixel_bgr_to_rgb(row_bgr[j])
                if rgb_matches(maybe_etc, MARKERS["ETC"], tol=tol):
                    mag = _pixel_bgr_to_rgb(row_bgr[j + 1])
                    try:
                        cd_remain_s = float(mag[1]) / 10.0
                    except (TypeError, ValueError):
                        cd_remain_s = None
                    j += 2
            out[spell_id] = CooldownInfo(
                spell_id=spell_id,
                unusable=unusable,
                has_cooldown=has_cooldown,
                highlighted=highlighted,
                cd_remain_s=cd_remain_s,
                kind=kind,
            )
            i = j
            continue
        i += 1
    return out


def make_cooldowns_row(
    entries: list[dict[str, Any]],
) -> np.ndarray:
    """Build a synthetic BGR cooldown row for tests.

    Each entry: spell_id, optional unusable/has_cooldown/highlighted/cd_remain_s/kind.
    """
    pixels: list[tuple[int, int, int]] = [MARKERS["START"]]
    for idx, entry in enumerate(entries):
        if idx:
            pixels.append(MARKERS["SEP"])
        kind = str(entry.get("kind") or "spell")
        marker = MARKERS["SPELL"] if kind == "spell" else MARKERS["ITEM"]
        pixels.append(marker)
        try:
            spell_id = int(entry["spell_id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid cooldown entry spell_id: {entry!r}") from exc
        pixels.append(spell_id_to_rgb(spell_id))
        unusable = bool(entry.get("unusable", False))
        has_cooldown = bool(entry.get("has_cooldown", False))
        highlighted = bool(entry.get("highlighted", False))
        pixels.append(
            (
                255 if unusable else 0,
                255 if has_cooldown else 0,
                255 if highlighted else 0,
            )
        )
        remain = entry.get("cd_remain_s")
        if remain is not None:
            pixels.append(MARKERS["ETC"])
            try:
                remain_byte = max(0, min(255, round(float(remain) * 10.0)))
            except (TypeError, ValueError):
                remain_byte = 0
            pixels.append((0, remain_byte, 0))
    pixels.append(MARKERS["END"])
    row = np.zeros((len(pixels), 3), dtype=np.uint8)
    for i, (r, g, b) in enumerate(pixels):
        row[i] = (b, g, r)
    return row
