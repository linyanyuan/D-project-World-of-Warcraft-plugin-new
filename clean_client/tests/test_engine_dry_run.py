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


def test_engine_emits_one_vision_tip_when_bindings_empty() -> None:
    from clean_client.engine.loop import EngineLoop
    from clean_client.models.state import CombatState
    import time

    logs: list[str] = []
    frame = object()

    def grab():
        return frame

    def read_state(_frame):
        return CombatState()

    engine = EngineLoop(
        grab=grab,
        read_state=read_state,
        actions=[{"spell_id": 1, "fallback_key": "1"}],
        on_log=logs.append,
        dry_run=True,
        tick_ms=20,
    )
    engine.start()
    time.sleep(0.12)
    engine.stop()
    tips = [line for line in logs if line.startswith("提示:")]
    assert len(tips) == 1
    assert "未读到技能绑定" in tips[0]
