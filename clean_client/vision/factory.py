"""Vision backend factory for MockVision ↔ PixelProtocolVision.

Public API
----------
create_vision(mode, regions=None, **opts) -> object with ``read_state(frame)``

Modes
-----
- ``"mock"``: returns :class:`~clean_client.vision.mock.MockVision`.
  Optional ``state=`` CombatState override via ``opts``.
- ``"pixel"`` / ``"protocol"``: returns
  :class:`~clean_client.vision.protocol.PixelProtocolVision` using ``regions``
  and opts ``row_height``, ``bindings_row_index``, ``default_key``.

UI / bootstrap call this to switch backends without importing concrete classes.
"""

from __future__ import annotations

from typing import Any, Protocol

from clean_client.config.loader import Region  # pyright: ignore[reportMissingImports]
from clean_client.models.state import (
    CombatState,  # pyright: ignore[reportMissingImports]
)
from clean_client.vision.mock import MockVision  # pyright: ignore[reportMissingImports]
from clean_client.vision.protocol import (  # pyright: ignore[reportMissingImports]
    PixelProtocolVision,
)


class VisionBackend(Protocol):
    """Minimal contract shared by MockVision and PixelProtocolVision."""

    def read_state(self, frame: Any) -> CombatState: ...


def create_vision(
    mode: str,
    regions: dict[str, Region] | None = None,
    **opts: Any,
) -> VisionBackend:
    """Build a vision backend.

    Parameters
    ----------
    mode:
        ``"mock"``, ``"pixel"``, or ``"protocol"`` (case-insensitive).
    regions:
        Capture rectangles keyed by ``Skill`` / ``Target`` / ``Player`` / ``Buff``.
        Required for meaningful pixel/protocol reads; ignored by mock.
    **opts:
        Forwarded to the concrete backend. Common keys:
        ``state`` (mock), ``row_height``, ``bindings_row_index``, ``default_key``.
    """
    key = (mode or "mock").strip().lower()
    if key in {"mock", "test", "null"}:
        state = opts.get("state")
        if state is not None and not isinstance(state, CombatState):
            raise TypeError("opts['state'] must be a CombatState or None")
        return MockVision(state=state)

    if key in {"pixel", "protocol"}:
        return PixelProtocolVision(
            regions=regions,
            row_height=opts.get("row_height", 1),
            bindings_row_index=opts.get("bindings_row_index", 2),
            cooldown_row_index=opts.get("cooldown_row_index", 3),
            default_key=str(opts.get("default_key") or "1"),
        )

    raise ValueError(f"unknown vision mode {mode!r}; expected mock|pixel|protocol")
