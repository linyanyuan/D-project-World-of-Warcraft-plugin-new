from clean_client.vision.encoding import rgb_to_spell_id
from clean_client.vision.parsers import make_bindings_row, parse_key_bindings_row


def test_parse_single_spell_binding() -> None:
    spell_id = rgb_to_spell_id(0x12, 0xCA, 0x33)
    row = make_bindings_row([spell_id])
    bindings = parse_key_bindings_row(row, default_key="q")
    assert spell_id in bindings
    assert bindings[spell_id].kind == "spell"
    assert bindings[spell_id].key == "q"


def test_parse_multiple_spells() -> None:
    ids = [77575, 85948, 47541]
    row = make_bindings_row(ids)
    bindings = parse_key_bindings_row(row)
    assert set(bindings) == set(ids)
