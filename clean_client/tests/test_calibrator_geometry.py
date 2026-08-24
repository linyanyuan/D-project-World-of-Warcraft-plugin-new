"""Pure helpers for region calibration geometry and dir save."""

from __future__ import annotations

from pathlib import Path

from clean_client.config.loader import load_regions_dir, save_regions_dir
from clean_client.ui.geometry import (
    clamp_region,
    normalize_rect,
    rubber_band_to_region,
)


def test_normalize_rect_swaps_inverted_corners() -> None:
    region = normalize_rect(100, 50, 10, 20)
    assert region[0] == 10
    assert region[1] == 20
    assert region[2] == 100
    assert region[3] == 50
    same = normalize_rect(5, 5, 5, 5)
    assert same[0] == 5
    assert same[1] == 5
    assert same[2] == 5
    assert same[3] == 5


def test_clamp_region_to_frame_bounds() -> None:
    clamped = clamp_region((-10, -5, 200, 150), width=100, height=80)
    assert clamped[0] == 0
    assert clamped[1] == 0
    assert clamped[2] == 100
    assert clamped[3] == 80
    inside = clamp_region((10, 20, 30, 40), width=100, height=80)
    assert inside[0] == 10
    assert inside[1] == 20
    assert inside[2] == 30
    assert inside[3] == 40


def test_clamp_region_degenerate_stays_ordered() -> None:
    # After clamp, x1 <= x2 and y1 <= y2 still hold.
    region = clamp_region((90, 70, 120, 100), width=100, height=80)
    x1, y1, x2, y2 = region
    assert 0 <= x1 <= x2 <= 100
    assert 0 <= y1 <= y2 <= 80


def test_rubber_band_to_region() -> None:
    region = rubber_band_to_region((80, 60), (20, 10))
    assert region[0] == 20
    assert region[1] == 10
    assert region[2] == 80
    assert region[3] == 60
    clamped = rubber_band_to_region((0, 0), (50, 25), width=40, height=20)
    assert clamped[0] == 0
    assert clamped[1] == 0
    assert clamped[2] == 40
    assert clamped[3] == 20


def test_save_regions_dir_roundtrip(tmp_path: Path) -> None:
    regions = {
        "Skill": (1, 2, 3, 4),
        "Target": (10, 20, 30, 40),
        "Player": (5, 6, 7, 8),
        "Buff": (100, 110, 120, 130),
    }
    save_regions_dir(tmp_path, regions)
    skill_text = (tmp_path / "skill_region.txt").read_text(encoding="utf-8").strip()
    target_text = (tmp_path / "target_region.txt").read_text(encoding="utf-8").strip()
    assert skill_text == "1 2 3 4"
    assert target_text == "10 20 30 40"
    loaded = load_regions_dir(tmp_path)
    assert loaded == regions
