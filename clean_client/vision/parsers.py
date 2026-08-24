"""Pixel-row parsers for AutoPlayer RGB protocol (v1 minimal)."""

from __future__ import annotations

from typing import Any

import numpy as np

from clean_client.models.state import Action
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
