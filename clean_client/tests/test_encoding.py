from clean_client.vision.encoding import rgb_to_spell_id, spell_id_to_rgb
from clean_client.vision.markers import MARKERS, rgb_matches


def test_doc_example() -> None:
    assert rgb_to_spell_id(0x12, 0xCA, 0x33) == 1231411
    assert spell_id_to_rgb(1231411) == (0x12, 0xCA, 0x33)


def test_roundtrip() -> None:
    for spell_id in (77575, 85948, 0, 0xFFFFFF):
        assert rgb_to_spell_id(*spell_id_to_rgb(spell_id)) == spell_id


def test_marker_start() -> None:
    assert rgb_matches((255, 0, 255), MARKERS["START"])
