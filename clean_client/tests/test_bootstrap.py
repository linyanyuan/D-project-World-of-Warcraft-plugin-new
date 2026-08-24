"""Tests for clean_client.engine.bootstrap.build_engine."""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np

from clean_client.config.loader import save_region_file
from clean_client.engine.bootstrap import build_engine, load_settings_regions
from clean_client.engine.loop import EngineLoop
from clean_client.models.state import Action, CombatState, CooldownInfo
from clean_client.paths import package_root
from clean_client.vision.encoding import rgb_to_spell_id
from clean_client.vision.factory import create_vision
from clean_client.vision.parsers import make_bindings_row


def test_build_engine_mock_dry_run() -> None:
    logs: list[str] = []
    pressed: list[str] = []
    seeded = CombatState(
        bindings={77575: Action(77575, "1", "spell", "Outbreak")},
        cooldowns={77575: CooldownInfo(77575, False, False, highlighted=True)},
    )
    vision = create_vision("mock", state=seeded)

    settings = {
        "root": str(package_root()),
        "vision_mode": "mock",
        "capture_mode": "null",
        "dry_run": True,
        "prefer_highlighted": True,
        "tick_ms": 20,
        "cd_ready_window_ms": 30,
        "profile": "profiles/unholy_default.json",
        "regions_dir": "",
    }
    engine = build_engine(
        settings,
        on_log=logs.append,
        press=pressed.append,
        grab=lambda: None,
        regions={},
    )
    # Replace vision after build so we control CombatState without touching UI.
    engine.read_state = vision.read_state
    assert isinstance(engine, EngineLoop)
    assert engine.dry_run

    engine.start()
    time.sleep(0.08)
    engine.stop()
    assert any("法术ID=77575" in line for line in logs)
    assert pressed == []


def test_load_settings_regions_from_dir(tmp_path: Path) -> None:
    save_region_file(tmp_path / "skill_region.txt", (0, 0, 40, 4))
    settings = {"regions_dir": str(tmp_path)}
    regions = load_settings_regions(settings)
    assert regions["Skill"] == (0, 0, 40, 4)


def test_build_engine_pixel_reads_synthetic_frame(tmp_path: Path) -> None:
    spell_id = rgb_to_spell_id(0x12, 0xCA, 0x33)
    bind_row = make_bindings_row([spell_id])
    width = int(bind_row.shape[0])
    frame = np.zeros((4, width, 3), dtype=np.uint8)
    frame[2] = bind_row
    save_region_file(tmp_path / "skill_region.txt", (0, 0, width, 4))

    settings = {
        "root": str(package_root()),
        "vision_mode": "pixel",
        "regions_dir": str(tmp_path),
        "row_height": 1,
        "bindings_row_index": 2,
        "default_key": "1",
        "capture_mode": "null",
        "dry_run": True,
        "tick_ms": 20,
        "profile": "profiles/unholy_default.json",
    }
    engine = build_engine(settings, on_log=lambda _m: None, grab=lambda: frame)
    state = engine.read_state(frame)
    assert spell_id in state.bindings
