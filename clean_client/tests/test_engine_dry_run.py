import time

from clean_client.engine.loop import EngineLoop
from clean_client.models.state import Action, CombatState, CooldownInfo
from clean_client.vision.mock import MockVision


def test_engine_dry_run_logs_action() -> None:
    logs: list[str] = []
    pressed: list[str] = []
    state = CombatState(
        bindings={77575: Action(77575, "1", "spell", "Outbreak")},
        cooldowns={77575: CooldownInfo(77575, False, False, highlighted=True)},
    )
    vision = MockVision(state)
    engine = EngineLoop(
        grab=lambda: None,
        read_state=vision.read_state,
        actions=[{"spell_id": 77575, "name": "Outbreak", "fallback_key": "1"}],
        on_log=logs.append,
        press=pressed.append,
        tick_ms=20,
        dry_run=True,
        prefer_highlighted=True,
    )
    engine.start()
    time.sleep(0.08)
    engine.stop()
    assert any("法术ID=77575" in line for line in logs)
    assert pressed == []
