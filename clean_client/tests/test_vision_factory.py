"""Tests for clean_client.vision.factory.create_vision."""

from __future__ import annotations

import numpy as np
import pytest

from clean_client.models.state import CombatState
from clean_client.vision.encoding import rgb_to_spell_id
from clean_client.vision.factory import create_vision
from clean_client.vision.mock import MockVision
from clean_client.vision.parsers import make_bindings_row
from clean_client.vision.protocol import PixelProtocolVision


def test_create_vision_mock_default() -> None:
    vision = create_vision("mock")
    assert isinstance(vision, MockVision)
    state = vision.read_state(None)
    assert isinstance(state, CombatState)
    assert state.bindings == {}


def test_create_vision_mock_with_state() -> None:
    seeded = CombatState(raw_debug={"source": "seed"})
    vision = create_vision("mock", state=seeded)
    assert vision.read_state(object()) is seeded


def test_create_vision_pixel_parses_bindings() -> None:
    spell_id = rgb_to_spell_id(0x12, 0xCA, 0x33)
    bind_row = make_bindings_row([spell_id])
    width = bind_row.shape[0]
    frame = np.zeros((4, width, 3), dtype=np.uint8)
    frame[2] = bind_row

    vision = create_vision(
        "pixel",
        regions={"Skill": (0, 0, width, 4)},
        row_height=1,
        bindings_row_index=2,
        default_key="q",
    )
    assert isinstance(vision, PixelProtocolVision)
    state = vision.read_state(frame)
    assert spell_id in state.bindings
    assert state.bindings[spell_id].key == "q"


def test_create_vision_protocol_alias() -> None:
    vision = create_vision("protocol", regions={})
    assert isinstance(vision, PixelProtocolVision)


def test_create_vision_unknown_mode() -> None:
    with pytest.raises(ValueError, match="unknown vision mode"):
        create_vision("laser")
