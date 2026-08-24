from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Action:
    spell_id: int | None
    key: str
    kind: str  # spell|item|etc
    name: str | None = None


@dataclass
class CooldownInfo:
    spell_id: int
    unusable: bool
    has_cooldown: bool
    highlighted: bool
    cd_remain_s: float | None = None
    charge_count: int | None = None
    kind: str = "spell"


@dataclass
class CombatState:
    header: dict[str, object] = field(default_factory=dict)
    health: dict[str, dict] = field(default_factory=dict)
    bindings: dict[int, Action] = field(default_factory=dict)
    cooldowns: dict[int, CooldownInfo] = field(default_factory=dict)
    buffs: list[dict] = field(default_factory=list)
    pixel_keys: list[str] = field(default_factory=list)
    raw_debug: dict[str, object] = field(default_factory=dict)
