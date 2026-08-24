"""Load settings and capture regions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

Region = tuple[int, int, int, int]  # x1,y1,x2,y2
REGION_KEYS = ("Skill", "Target", "Player", "Buff")
REGION_FILES: dict[str, str] = {
    "Skill": "skill_region.txt",
    "Target": "target_region.txt",
    "Player": "player_region.txt",
    "Buff": "buff_region.txt",
}


def load_json(path: str | Path) -> dict[str, Any]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"failed to load json {path}: {exc}") from exc


def parse_region_line(text: str) -> Region:
    parts = [p.strip() for p in text.replace(",", " ").split() if p.strip()]
    if len(parts) != 4:
        raise ValueError(f"region needs 4 ints, got {text!r}")
    try:
        x1, y1, x2, y2 = (int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]))
    except ValueError as exc:
        raise ValueError(f"invalid region ints: {text!r}") from exc
    return x1, y1, x2, y2


def load_region_file(path: str | Path) -> Region:
    try:
        text = Path(path).read_text(encoding="utf-8").strip().splitlines()[0]
    except (OSError, IndexError) as exc:
        raise ValueError(f"failed to read region file {path}: {exc}") from exc
    return parse_region_line(text)


def save_region_file(path: str | Path, region: Region) -> None:
    x1, y1, x2, y2 = region
    Path(path).write_text(f"{x1} {y1} {x2} {y2}\n", encoding="utf-8")


def load_regions_dir(directory: str | Path) -> dict[str, Region]:
    """Load skill/target/player/buff_region.txt from a folder."""
    base = Path(directory)
    out: dict[str, Region] = {}
    for key, filename in REGION_FILES.items():
        fp = base / filename
        if fp.exists():
            out[key] = load_region_file(fp)
    return out


def save_regions_dir(directory: str | Path, regions: dict[str, Region]) -> None:
    """Write Skill/Target/Player/Buff rectangles as *_region.txt files."""
    base = Path(directory)
    base.mkdir(parents=True, exist_ok=True)
    for key in REGION_KEYS:
        if key not in regions:
            continue
        filename = REGION_FILES[key]
        save_region_file(base / filename, regions[key])


def crop_bgr(frame, region: Region):
    import numpy as np

    x1, y1, x2, y2 = region
    h, w = frame.shape[:2]
    x1 = max(0, min(w, x1))
    x2 = max(0, min(w, x2))
    y1 = max(0, min(h, y1))
    y2 = max(0, min(h, y2))
    if x2 <= x1 or y2 <= y1:
        return np.zeros((1, 1, 3), dtype=frame.dtype)
    return frame[y1:y2, x1:x2]
