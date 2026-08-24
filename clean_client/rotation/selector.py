"""Ready predicate + ordered Unholy/profile selector."""

from __future__ import annotations

from clean_client.models.state import Action, CombatState, CooldownInfo


def is_ready(
    cd: CooldownInfo | None,
    *,
    cd_ready_window_ms: int = 30,
) -> bool:
    """Spec ready rule.

    ready = (not unusable) and ((not has_cooldown) or near_ready or highlighted)
    """
    if cd is None:
        # Binding present without CD row → treat as ready
        return True
    if cd.unusable:
        return False
    near_ready = cd.cd_remain_s is not None and cd.cd_remain_s <= (
        cd_ready_window_ms / 1000.0
    )
    return (not cd.has_cooldown) or near_ready or cd.highlighted


def select_action(
    state: CombatState,
    actions: list[dict],
    *,
    prefer_highlighted: bool = True,
    cd_ready_window_ms: int = 30,
    allow_fallback_keys: bool = False,
) -> Action | None:
    """Two-pass selection per spec.

    1) If prefer_highlighted: first ready+highlighted in profile order
    2) Else / fallback: first ready in profile order

    ``allow_fallback_keys`` synthesizes Actions from profile ``fallback_key``
    when a spell_id is absent from ``state.bindings`` (fixture/dry-run only).
    """

    def _walk(*, require_highlighted: bool) -> Action | None:
        for entry in actions:
            try:
                spell_id = int(entry["spell_id"])
            except (KeyError, TypeError, ValueError):
                continue
            binding = state.bindings.get(spell_id)
            if binding is None:
                if not allow_fallback_keys:
                    continue
                fallback = entry.get("fallback_key")
                if fallback is None:
                    continue
                binding = Action(
                    spell_id=spell_id,
                    key=str(fallback),
                    kind=str(entry.get("kind") or "spell"),
                    name=entry.get("name"),
                )
            # Prefer profile fallback_key when present — pixel bindings often
            # only carry a placeholder key until chord recovery is complete.
            profile_key = entry.get("fallback_key")
            if profile_key is not None and str(profile_key).strip():
                binding = Action(
                    spell_id=binding.spell_id,
                    key=str(profile_key),
                    kind=str(entry.get("kind") or binding.kind),
                    name=entry.get("name") or binding.name,
                )
            cd = state.cooldowns.get(spell_id)
            if not is_ready(cd, cd_ready_window_ms=cd_ready_window_ms):
                continue
            if require_highlighted and (cd is None or not cd.highlighted):
                continue
            return binding
        return None

    if prefer_highlighted:
        hit = _walk(require_highlighted=True)
        if hit is not None:
            return hit
    return _walk(require_highlighted=False)
