"""Phase 3: cooldown row parsing + Skill autofind."""

from __future__ import annotations

import numpy as np

from clean_client.vision.autofind import find_skill_region
from clean_client.vision.encoding import rgb_to_spell_id
from clean_client.vision.markers import MARKERS
from clean_client.vision.parsers import (
    make_bindings_row,
    make_cooldowns_row,
    parse_cooldowns_row,
)
from clean_client.vision.protocol import PixelProtocolVision


def test_parse_cooldowns_row_flags_and_remain() -> None:
    spell_id = rgb_to_spell_id(0x12, 0xCA, 0x33)
    row = make_cooldowns_row(
        [
            {
                "spell_id": spell_id,
                "unusable": False,
                "has_cooldown": True,
                "highlighted": True,
                "cd_remain_s": 1.5,
            }
        ]
    )
    cds = parse_cooldowns_row(row)
    assert spell_id in cds
    info = cds[spell_id]
    assert not info.unusable
    assert info.has_cooldown
    assert info.highlighted
    assert info.cd_remain_s == 1.5


def test_pixel_protocol_reads_bindings_and_cooldowns() -> None:
    spell_id = rgb_to_spell_id(0x12, 0xCA, 0x33)
    bind = make_bindings_row([spell_id])
    cool = make_cooldowns_row(
        [
            {
                "spell_id": spell_id,
                "has_cooldown": False,
                "highlighted": True,
            }
        ]
    )
    width = max(bind.shape[0], cool.shape[0])
    frame = np.zeros((5, width, 3), dtype=np.uint8)
    frame[2, : bind.shape[0]] = bind
    frame[3, : cool.shape[0]] = cool
    vision = PixelProtocolVision(
        regions={"Skill": (0, 0, width, 5)},
        row_height=1,
        bindings_row_index=2,
        cooldown_row_index=3,
        default_key="q",
    )
    state = vision.read_state(frame)
    assert spell_id in state.bindings
    assert spell_id in state.cooldowns
    assert state.cooldowns[spell_id].highlighted


def test_find_skill_region_locates_start_band() -> None:
    frame = np.zeros((80, 120, 3), dtype=np.uint8)
    # paint START magenta as BGR
    r, g, b = MARKERS["START"]
    frame[20:24, 30:90] = (b, g, r)
    region = find_skill_region(frame, tol=0, prefer_rows=6)
    assert region is not None
    x1, y1, x2, y2 = region
    assert y1 <= 20
    assert y2 >= 24
    assert x1 <= 30
    assert x2 >= 90
