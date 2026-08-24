from clean_client.models.state import Action, CombatState, CooldownInfo


def test_action_fields() -> None:
    action = Action(spell_id=1231411, key="1", kind="spell", name="Outbreak")
    assert action.spell_id == 1231411
    assert action.key == "1"
    assert action.kind == "spell"
    assert action.name == "Outbreak"


def test_combat_state_defaults() -> None:
    state = CombatState()
    assert state.bindings == {}
    assert state.cooldowns == {}
    assert state.buffs == []


def test_cooldown_info() -> None:
    cd = CooldownInfo(
        spell_id=77575,
        unusable=False,
        has_cooldown=True,
        highlighted=True,
        cd_remain_s=0.02,
    )
    assert cd.highlighted is True
    assert cd.cd_remain_s == 0.02
