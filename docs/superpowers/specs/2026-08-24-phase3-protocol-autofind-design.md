# Phase 3 Design: Cooldown Row (Minimal) + Skill Autofind

**Date:** 2026-08-24  
**Status:** Approved (scoped “shippable” slice)

## Goal

1. Parse a **minimal cooldown/highlight row** so `prefer_highlighted` / ready checks can use real `CooldownInfo`.
2. Offer **Skill-region autofind** from a preview frame by locating magenta START markers.

## Non-goals

- Full charge bar measurement / cd_remain_px geometry from original Nirvana
- Buff template matching
- Header / health-bar rows
- Multi-spec editors / card-key

## Cooldown row v1 wire format

BGR scanline (same marker vocabulary as bindings):

```
START | SPELL|ITEM | spell_rgb | flag_rgb | [SEP | ...] | END
```

`flag_rgb` (RGB channels):

| Channel | Meaning |
| --- | --- |
| R ≥ 128 | `unusable` |
| G ≥ 128 | `has_cooldown` |
| B ≥ 128 | `highlighted` |

`cd_remain_s` stays `None` in v1 unless a later pixel with marker `ETC` followed by a magnitude pixel is present:

```
ETC | (0, remain_byte, 0)   # remain_s ~= remain_byte / 10.0
```

## Autofind

- Scan frame rows for pixels matching START `#ff00ff` (tolerance configurable, default 8)
- Cluster consecutive rows with START hits; pick the band with most hits
- Suggest `Skill` rect: x from first..last START-ish span (expanded), y covering band + enough height for `bindings_row_index`/`cooldown` rows (default height ≥ 8px or `row_height * 6`)
- UI: button「自动建议 Skill 区域」writes `skill_region.txt` into current regions dir (create dir if needed) and refreshes preview

## Wiring

- `PixelProtocolVision.read_state`: parse bindings row + cooldown row (index configurable, default bindings=2, cooldowns=3)
- Selector unchanged — already consumes `state.cooldowns`

## Tests

- Synthetic cooldown row → CooldownInfo flags
- Autofind locates painted START band in a synthetic frame
- Protocol vision fills both bindings and cooldowns
