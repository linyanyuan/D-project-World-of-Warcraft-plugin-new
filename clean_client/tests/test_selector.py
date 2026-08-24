from pathlib import Path

from clean_client.models.state import Action, CombatState, CooldownInfo
from clean_client.rotation.profile import load_profile
from clean_client.rotation.selector import is_ready, select_action

PROFILE = Path(__file__).resolve().parents[1] / "profiles" / "unholy_default.json"


def test_ready_near_window() -> None:
    cd = CooldownInfo(
        spell_id=77575,
        unusable=False,
        has_cooldown=True,
        highlighted=False,
        cd_remain_s=0.02,
    )
    assert is_ready(cd, cd_ready_window_ms=30) == True


def test_not_ready_long_cd() -> None:
    cd = CooldownInfo(
        spell_id=77575,
        unusable=False,
        has_cooldown=True,
        highlighted=False,
        cd_remain_s=1.5,
    )
    assert is_ready(cd, cd_ready_window_ms=30) == False


def test_highlighted_overrides_cd() -> None:
    cd = CooldownInfo(
        spell_id=77575,
        unusable=False,
        has_cooldown=True,
        highlighted=True,
        cd_remain_s=3.0,
    )
    assert is_ready(cd) == True


def test_prefer_highlighted_pass() -> None:
    state = CombatState(
        bindings={
            77575: Action(77575, "1", "spell", "Outbreak"),
            85948: Action(85948, "2", "spell", "FesteringStrike"),
        },
        cooldowns={
            77575: CooldownInfo(77575, False, False, highlighted=False),
            85948: CooldownInfo(85948, False, False, highlighted=True),
        },
    )
    profile = load_profile(PROFILE)
    # Outbreak is earlier but not highlighted; prefer_highlighted should pick FesteringStrike
    chosen = select_action(state, profile["actions"], prefer_highlighted=True)
    assert chosen is not None
    assert chosen.spell_id == 85948


def test_fallback_pass_without_highlight() -> None:
    state = CombatState(
        bindings={77575: Action(77575, "1", "spell", "Outbreak")},
        cooldowns={77575: CooldownInfo(77575, False, False, highlighted=False)},
    )
    profile = load_profile(PROFILE)
    chosen = select_action(state, profile["actions"], prefer_highlighted=True)
    assert chosen is not None
    assert chosen.spell_id == 77575
