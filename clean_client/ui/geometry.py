"""Pure geometry helpers for region calibration (no Qt dependency)."""

from __future__ import annotations

from clean_client.config.loader import Region


def _as_int(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"expected int, got {value!r}") from exc


def normalize_rect(x1: object, y1: object, x2: object, y2: object) -> Region:
    """Ensure (x1,y1) is top-left and (x2,y2) is bottom-right."""
    a = _as_int(x1)
    b = _as_int(y1)
    c = _as_int(x2)
    d = _as_int(y2)
    if a > c:
        a, c = c, a
    if b > d:
        b, d = d, b
    return a, b, c, d


def clamp_region(region: Region, *, width: object, height: object) -> Region:
    """Clamp a region to [0,width] x [0,height], keeping order."""
    x1, y1, x2, y2 = normalize_rect(*region)
    w = max(0, _as_int(width))
    h = max(0, _as_int(height))
    x1 = max(0, min(w, x1))
    x2 = max(0, min(w, x2))
    y1 = max(0, min(h, y1))
    y2 = max(0, min(h, y2))
    return x1, y1, x2, y2


def rubber_band_to_region(
    start: tuple[object, object],
    end: tuple[object, object],
    *,
    width: object | None = None,
    height: object | None = None,
) -> Region:
    """Convert a drag from start→end into a normalized (optionally clamped) region."""
    region = normalize_rect(start[0], start[1], end[0], end[1])
    if width is not None and height is not None:
        return clamp_region(region, width=width, height=height)
    return region
