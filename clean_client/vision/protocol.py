"""PixelProtocolVision: crop Skill region and parse protocol rows.

Phase 3 behaviour
-----------------
- Splits the Skill crop into horizontal strips of ``row_height``.
- Parses key-bindings row (default index 2) and cooldown row (default index 3).
- Header / health / buffs remain out of scope for this phase.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from clean_client.config.loader import Region, crop_bgr
from clean_client.models.state import CombatState
from clean_client.vision.parsers import parse_cooldowns_row, parse_key_bindings_row


def _as_positive_int(value: object, default: int = 1) -> int:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _as_int(value: object, default: int) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


class PixelProtocolVision:
    """Parse bindings + cooldown rows from the Skill region."""

    def __init__(
        self,
        regions: dict[str, Region] | None = None,
        *,
        row_height: int = 1,
        bindings_row_index: int = 2,
        cooldown_row_index: int = 3,
        default_key: str = "1",
    ) -> None:
        self.regions = regions or {}
        self.row_height = _as_positive_int(row_height, 1)
        self.bindings_row_index = _as_int(bindings_row_index, 2)
        self.cooldown_row_index = _as_int(cooldown_row_index, 3)
        self.default_key = default_key

    def split_rows(self, skill_bgr: np.ndarray) -> list[np.ndarray]:
        if skill_bgr.ndim != 3:
            raise ValueError("skill crop must be HxWx3")
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

        bind_idx = min(max(self.bindings_row_index, 0), len(rows) - 1)
        try:
            state.bindings = parse_key_bindings_row(
                rows[bind_idx], default_key=self.default_key
            )
        except ValueError as exc:
            state.raw_debug["bindings_error"] = str(exc)

        if len(rows) > 0:
            cd_idx = min(max(self.cooldown_row_index, 0), len(rows) - 1)
            # Only parse cooldown row when it is a distinct index or same row has CD markers.
            try:
                state.cooldowns = parse_cooldowns_row(rows[cd_idx])
            except ValueError as exc:
                state.raw_debug["cooldowns_error"] = str(exc)
        return state
