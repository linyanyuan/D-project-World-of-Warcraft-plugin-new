from pathlib import Path

import numpy as np

from clean_client.config.loader import (
    crop_bgr,
    load_region_file,
    load_regions_dir,
    parse_region_line,
    save_region_file,
)
from clean_client.vision.encoding import rgb_to_spell_id
from clean_client.vision.parsers import make_bindings_row
from clean_client.vision.protocol import PixelProtocolVision


def test_parse_region_line() -> None:
    region = parse_region_line("10,20,110,40")
    assert region[0] == 10
    assert region[1] == 20
    assert region[2] == 110
    assert region[3] == 40


def test_region_file_roundtrip(tmp_path: Path) -> None:
    fp = tmp_path / "skill_region.txt"
    save_region_file(fp, (1, 2, 3, 4))
    loaded = load_region_file(fp)
    assert loaded[0] == 1
    assert loaded[1] == 2
    assert loaded[2] == 3
    assert loaded[3] == 4


def test_load_regions_dir(tmp_path: Path) -> None:
    save_region_file(tmp_path / "skill_region.txt", (0, 0, 50, 5))
    save_region_file(tmp_path / "buff_region.txt", (0, 10, 20, 30))
    regions = load_regions_dir(tmp_path)
    assert regions["Skill"][2] == 50
    assert regions["Buff"][3] == 30


def test_pixel_protocol_vision_bindings_row() -> None:
    spell_id = rgb_to_spell_id(0x12, 0xCA, 0x33)
    bind_row = make_bindings_row([spell_id])
    width = bind_row.shape[0]
    frame = np.zeros((4, width, 3), dtype=np.uint8)
    frame[2] = bind_row
    vision = PixelProtocolVision(
        regions={"Skill": (0, 0, width, 4)},
        row_height=1,
        bindings_row_index=2,
        default_key="q",
    )
    state = vision.read_state(frame)
    assert spell_id in state.bindings
    action = state.bindings[spell_id]
    assert action.key == "q"


def test_crop_bgr() -> None:
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    frame[10:20, 5:15] = 255
    crop = crop_bgr(frame, (5, 10, 15, 20))
    assert crop.shape[0] == 10
    assert crop.shape[1] == 10
    assert int(crop.max()) == 255
