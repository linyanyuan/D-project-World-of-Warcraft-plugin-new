"""Mock vision for dry-run / unit tests."""

from __future__ import annotations

from typing import Any

from clean_client.models.state import CombatState  # type: ignore[import-not-found]


class MockVision:
    def __init__(self, state: CombatState | None = None) -> None:
        self.state = state or CombatState()

    def read_state(self, frame: Any) -> CombatState:
        return self.state
