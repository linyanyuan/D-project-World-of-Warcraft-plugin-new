"""PixelProtocolVision: crop Skill region and parse protocol rows.

v1 behaviour
------------
- Splits the Skill crop into horizontal strips of ``row_height``.
- Parses the bindings row at ``bindings_row_index`` (default 2).
- Other protocol rows (header / cooldowns / health / buffs) remain stubs
  until fixtures exist; prefer :func:`clean_client.vision.factory.create_vision`
  for construction from UI settings.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from clean_client.config.loader import (  # pyright: ignore[reportMissingImports]
    Region,
    crop_bgr,
)
from clean_client.models.state import (
    CombatState,  # pyright: ignore[reportMissingImports]
)
from clean_client.vision.parsers import (  # pyright: ignore[reportMissingImports]
    parse_key_bindings_row,
)


def _as_positive_int(value: object, default: int = 1) -> int:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


class PixelProtocolVision:
    """v1: parse key-binding row; other rows stubbed until more fixtures exist.

    Construct via :func:`clean_client.vision.factory.create_vision`
    (``mode="pixel"`` / ``"protocol"``) when switching from MockVision.
    """

    def __init__(
        self,
        regions: dict[str, Region] | None = None,
        *,
        row_height: int = 1,
        bindings_row_index: int = 2,
        default_key: str = "1",
    ) -> None:
        self.regions = regions or {}
        self.row_height = _as_positive_int(row_height, 1)
        try:
            self.bindings_row_index = int(bindings_row_index)
        except (TypeError, ValueError):
            self.bindings_row_index = 2
        self.default_key = default_key

    def split_rows(self, skill_bgr: np.ndarray) -> list[np.ndarray]:
        if skill_bgr.ndim != 3:
            raise ValueError("skill crop must be HxWxC")
        height = skill_bgr.shape[0]
        rows: list[np.ndarray] = []
        y = 0
        while y + self.row_height <= height:
            strip = skill_bgr[y : y + self.row_height]
            mid = strip[self.row_height // 2]
            rows.append(mid)
            y += self.row_height
        return rows

    def read_state(self, frame: Any) -> CombatState:
        state = CombatState()
        skill_region = self.regions.get("Skill")
        if skill_region is None:
            state.raw_debug["warning"] = "missing Skill region"
            return state
        crop = crop_bgr(frame, skill_region)
        rows = self.split_rows(crop)
        state.raw_debug["row_count"] = len(rows)
        if not rows:
            return state
        idx = min(max(self.bindings_row_index, 0), len(rows) - 1)
        try:
            state.bindings = parse_key_bindings_row(
                rows[idx], default_key=self.default_key
            )
        except ValueError as exc:
            state.raw_debug["bindings_error"] = str(exc)
        return state
