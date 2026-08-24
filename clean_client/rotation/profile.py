"""Load Unholy / rotation profiles from JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_profile(path: str | Path) -> dict[str, Any]:
    try:
        text = Path(path).read_text(encoding="utf-8")
        data = json.loads(text)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"failed to load profile {path}: {exc}") from exc
    if not isinstance(data, dict) or "actions" not in data:
        raise ValueError("profile must be an object with an actions list")
    return data
