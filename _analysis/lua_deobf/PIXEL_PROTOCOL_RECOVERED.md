# AutoPlayer Pixel / RGB Protocol — Recovered Notes

Source of truth for this note: Nirvana client binary string dump
`_analysis/dump/mem_0x7ff631b62000_8388608_FluentPrototypeWindow_*.bin`
plus addon TOC / Lua symbol dumps.

Lua VM side is still Luraph-obfuscated; dynamic execution dies in anti-tamper
before `SetColorTexture` call sites run. Client-side parser names/strings are
complete enough to reconstruct the **wire format** the addon is expected to paint.

---

## 1. High-level model

The addon paints a **pixel row protocol** into a screen region. The external
client (`skill_recognition.py` / `SkillBotRuntimeCore`) captures the WoW window
and parses rows:

| Step | Name | Parser |
| --- | --- | --- |
| 1/5 | Header (Row 0) | `_parse_header_rgb_protocol` |
| 2/5 | Health Bars | `parse_dynamic_health_bars` |
| 3/5 | Key Bindings | `parse_row_data2_key_bindings` |
| 4/5 | Cooldowns | `parse_row_data3_cooldowns` |
| 5/5 | Buff/Debuff icons | `recognize_all_buffs_dynamic` (OpenCV template match) |

Debug visualizer: `visualize_pixel_row`.

Cycle selection logs: `default_cycle pixel_keys=...`.

---

## 2. Capture regions (client config files)

Client loads / saves rectangles:

```
skill_region.txt
target_region.txt
player_region.txt
buff_region.txt
```

Logical keys:

```python
{'Skill': (x1,y1,x2,y2), 'Target': ..., 'Player': ..., 'Buff': ...}
# order: ('Skill', 'Target', 'Player', 'Buff')
```

Saved via `save_regions_config`. Runtime vars: `region`, `target_region`,
`player_region`, `buff_region`, plus UI text helpers `_region_text`,
`_buff_region_text`, etc.

UI settings (recovered sample):

```json
{
  "capture_mode": "方式一",
  "tick_ms": 30,
  "cd_ready_window_ms": 30,
  "buff_match_threshold": 0.7
}
```

Addon TOC SavedVariables include `PixelPerfectUIScaleDB` — UI scale must stay
pixel-perfect for the RGB row to stay aligned.

---

## 3. Marker color vocabulary (hard finding)

From client constants co-located with `color_data` / key-binding parser:

| Constant | Hex | Role |
| --- | --- | --- |
| `_MARKER_START` | `#ff00ff` | magenta — record/stream start |
| `_MARKER_END` | `#ff8000` | orange — record/stream end |
| `_MARKER_SEP` | `#808080` | gray — field separator |
| `_MARKER_ITEM` | `#ffff00` | yellow — item action |
| `_MARKER_SPELL` | `#ffffff` | white — spell action |
| `_MARKER_ETC` | `#2a5938` | dark green — misc/etc |
| `_MARKER_RED` | `#ff0000` | red — error/flag |
| `_MARKER_RES` | `#ffff80` | light yellow — resource |

Parsers use `marker_at(row, ...)` / `_MARKER` while scanning a pixel row.

---

## 4. Spell-ID encoding (hard finding)

Client docstring example recovered verbatim:

```
RGB 12ca33 -> 0x12ca33 -> 1231411
```

So a pixel's 24-bit color packs an integer id:

```
spell_id = (R << 16) | (G << 8) | B
```

Example: `#12ca33` → spell id `1231411`.

This is the main “what skill?” channel; keybind row maps ids → key combos.

---

## 5. Row 0 — Header (`_parse_header_rgb_protocol`)

Parsed into `header` / `header_list` / `header_resources` / `header_hex`.

Observed field type stream (debug dump order, not yet named 1:1):

- several `bool`
- `team` (`team_type`)
- `int` (`member_count`, `spec`, …)
- `GCD`
- `spell` (likely last/current spell ids as RGB ints)
- more `bool` / `int`

Documented enum:

```
team_type: 0=solo, 1=party, 2=raid
```

Related layout helpers:

- `COLOR_PARTY`, `COLOR_RAID`
- `ROW_PARTY_START`, `UNIT_TOTAL_HEIGHT`
- `_is_retail_mode`
- `_gcd_exit_threshold`

Also feeds: `current_spec_id`, auto cycle switch (`spec_cycle_mapping`).

---

## 6. Row block — Health bars (`parse_dynamic_health_bars`)

Units: `player`, `target`, `focus` (+ party/raid via unit rows).

Per unit: `hp_data`, `exists`, `role` ∈ {`tank`,`healer`,`dps`,`none`},
bar length in px, percent.

Unit flags seen: `UNIT_FLAG_EXISTS`, `UNIT_FLAG_ALIVE`, `ROW_UNITS_DATA`.

---

## 7. Key bindings row (`parse_row_data2_key_bindings`)

- Scans markers; builds `bind_tokens`
- Modifiers: `Alt`, `Ctrl`, `Alt-Ctrl`
- Fields: `main_key`, `binding`, `combo`, `has_alt_ctrl`, `is_item`
- Output cached as `_row_cache_bindings`
- Skill entries printed as `ID:NNNNNN -> <key>`

`pixel_keys` from the active cycle are matched against this row to decide which
key to press.

---

## 8. Cooldown row (`parse_row_data3_cooldowns`)

Marker-oriented status bars. Important helpers:

- `_is_cd_bar_pixel`
- `_measure_cd_bar`
- `_measure_charge_after_marker`
- `_count_black_pixels`
- `_has_tail_kind_after`
- `_read_spell_id_bar`
- `_read_dispel_color`

Kind encoding comment fragments:

```
(R=1,G=...) + (R=2,G=...) + (R=3,G=...) + ETC ff8000
```

i.e. **R channel selects record kind**; G/B carry magnitude / secondary data.
Orange `#ff8000` appears both as `_MARKER_END` and in CD-bar measurement notes.

Lua side paints bars with black base:

```
statusBarTemplate.color = {0,0,0}
```

Per-skill cooldown struct (client fields):

| Field | Meaning |
| --- | --- |
| `unusable` | cannot cast |
| `has_cooldown` | on CD |
| `cd_remain_px` / `cd_remain_ratio` / `cd_remain_s` | remaining |
| `cd_fill_px` / `cd_fill_ratio` | fill bar |
| `has_charges` / `charge_count` | charges |
| `charge_fill_px` / `charge_fill_ratio` | charge bar |
| `channel_remain_s` | channel |
| `highlighted` | matches addon `judgeItIsLighted` |
| `is_override` | override spell |
| `cd_eta_s` / `cd_pred_ready` | prediction |
| `kind` ∈ {`spell`,`item`,…} | from markers |

Ready window uses `cd_ready_window_ms` / `near_ready_window_s`.

---

## 9. Buff region (not RGB-row; icon match)

Separate from the RGB rows. Uses OpenCV `matchTemplate`
(`TM_CCOEFF_NORMED`) against icon templates.

Layout constants (names recovered; numeric values not yet pinned):

- `BUFF_ICON_OFFSET`, `BUFF_ICON_SIZE`
- `AURA_ICON_SIZE`, `AURAS_PER_ROW`, `AURA_SLOT_STEP`
- `BUFF_ICON_SPACING`, `_BUFF_POSSIBLE_X_POSITIONS`
- `UNIT_SPACING`, `BUFF_ROW_OFFSET`
- `BUFF_DURATION_BAR_OFFSET`, `BUFF_STACK_BAR_OFFSET`
- `BLOOD_BAR_HEIGHT`, `BLOOD_BAR_INTERVAL`
- `_BUFF_SCALE_STEP`, `_BUFF_TEMPLATE_SCALE_PRECISION`
- `ROLE_COLOR_TOLERANCE`

Debug mentions `20x20` icon crops. Threshold: `buff_match_threshold` (default 0.7).

---

## 10. Addon-side symbols that paint the protocol

From Lua string dumps (execution still aborts pre-call):

| Symbol | File hits | Role |
| --- | --- | --- |
| `SetColorTexture` | Macro, Tools | write RGB pixels |
| `SetVertexColor` | AutoPlayer | tint |
| `CreateTexture` | AutoPlayer, Tools, Laminar | pixel cells |
| `initPositionIcon` | AutoPlayer, Tools | place protocol textures |
| `HexToRGB` | General, Macro | color parse |
| `judgeItIsLighted` | CLEAN_symbols | highlight / usable |
| `getSpellCD` | Macro | CD source |
| `LoadFramePosition` | Tools, AutoPlayer | saved anchors |
| `ChangeSimpleActionBar` / `initializeTheActionBar` | Simple, AutoPlayer | action bar sync |
| `CreateCenterMessageFrame` | AutoPlayer | UI |

Likely flow:

1. `initPositionIcon` creates 1px (or small) textures anchored to a fixed corner
2. On update, judgment engine calls `judgeItIsLighted` / `getSpellCD`
3. Results encoded via `SetColorTexture(r,g,b[,a])` using the marker + spell-id scheme above
4. Client samples the Skill region rows every `tick_ms`

Exact frame names / anchor offsets still require either:

- surviving VM anti-tamper far enough to log `CreateTexture`/`SetPoint` args, or
- reading in-game `/fstack` over the pixel strip, or
- dumping `skill_region.txt` from a live Nirvana install.

---

## 11. Improved dumper

`scripts/lua51_pixel_trace.lua` — hooks CreateFrame/CreateTexture/SetPoint/
SetSize/SetColorTexture/SetVertexColor, dumps strings/upvalues, attempts
nil-local neutralization for anti-tamper.

Outputs: `*_pixel_strings.txt`, `*_pixel_calls.txt`, `*_pixel_frames.txt`.

Current result: still dies inside Macro/Tools decrypt (`attempt to call local
'B' (a number value)` / prior nil-arith). Neutralizing nils to `0` breaks
function registers; neutralizing to callable stubs breaks numeric `for` loops.
Need a smarter per-register poison or bytecode-level unwrap.

---

## 12. Remaining blockers

1. Luraph anti-tamper prevents full Lua execution → no live `SetPoint`/`SetColorTexture` arg trace yet
2. Exact Skill-region pixel coordinates / texture frame names unknown
3. Header field order ↔ meaning map incomplete (types known, names partial)
4. Numeric values for `BUFF_ICON_*` / `AURA_*` layout constants not pinned
5. Kind encoding `(R=1/2/3,G=…)` full G/B dictionary unknown
