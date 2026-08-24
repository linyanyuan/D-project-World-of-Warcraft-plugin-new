"""Suggest a Skill region by locating magenta START marker bands."""

from __future__ import annotations

from typing import Any

import numpy as np

from clean_client.config.loader import Region
from clean_client.vision.markers import MARKERS, rgb_matches


def _bgr_to_rgb(pix: Any) -> tuple[int, int, int]:
    try:
        b, g, r = (int(pix[0]), int(pix[1]), int(pix[2]))
    except (TypeError, ValueError, IndexError) as exc:
        raise ValueError(f"invalid BGR pixel: {pix!r}") from exc
    return r, g, b


def find_skill_region(
    frame_bgr: np.ndarray,
    *,
    tol: int = 8,
    min_hits_per_row: int = 1,
    pad_x: int = 4,
    min_height: int = 8,
    prefer_rows: int = 6,
) -> Region | None:
    """Return a suggested Skill (x1,y1,x2,y2) or None if no START band found.

    Scans for START magenta pixels, clusters consecutive rows with hits, and
    picks the densest band.
    """
    if frame_bgr.ndim != 3 or frame_bgr.shape[2] < 3:
        raise ValueError("frame must be HxWx3 BGR")
    height, width = frame_bgr.shape[:2]
    start = MARKERS["START"]

    row_hits: list[list[int]] = [[] for _ in range(height)]
    for y in range(height):
        xs: list[int] = []
        for x in range(width):
            try:
                rgb = _bgr_to_rgb(frame_bgr[y, x])
            except ValueError:
                continue
            if rgb_matches(rgb, start, tol=tol):
                xs.append(x)
        row_hits[y] = xs

    best: tuple[int, int, int, int, int] | None = None
    # score, y1, y2, x1, x2
    y = 0
    while y < height:
        if len(row_hits[y]) < min_hits_per_row:
            y += 1
            continue
        y1 = y
        xs_all = list(row_hits[y])
        y += 1
        while y < height and len(row_hits[y]) >= min_hits_per_row:
            xs_all.extend(row_hits[y])
            y += 1
        y2 = y  # exclusive
        if not xs_all:
            continue
        x1 = max(0, min(xs_all) - pad_x)
        x2 = min(width, max(xs_all) + pad_x + 1)
        score = len(xs_all)
        band_h = max(y2 - y1, min_height, prefer_rows)
        y2_pref = min(height, y1 + band_h)
        cand = (score, y1, y2_pref, x1, x2)
        if best is None or cand[0] > best[0]:
            best = cand

    if best is None:
        return None
    _score, y1, y2, x1, x2 = best
    if x2 <= x1 or y2 <= y1:
        return None
    try:
        return int(x1), int(y1), int(x2), int(y2)
    except (TypeError, ValueError):
        return None
