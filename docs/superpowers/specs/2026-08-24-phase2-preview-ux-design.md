# Phase 2 Design: Recognition Preview + Failure Tips

**Date:** 2026-08-24  
**Status:** Approved  
**Depends on:** Phase 1 pixel wiring

## Goal

Make calibration and capture problems visible without guessing: show a live/manual preview with region overlays, and clearer Chinese tips when something is wrong.

## Non-goals

- Auto-detect color bars
- Full cooldown/highlight protocol parsing
- Redesigning Control/Rotation pages

## Success criteria

1. Recognition page can grab a preview frame using the current capture mode from Control page (or a local capture combo synced with settings).
2. Preview draws Skill/Target/Player/Buff rectangles when region files are present.
3. Optional auto-refresh (~1s) while enabled; default off or on with low cost — default **off**, user can enable.
4. Common failures show Chinese tips: no window (printwindow), grab error, missing Skill region, empty/black-looking frame, pixel mode with null capture.
5. When pixel engine returns empty bindings with a vision warning, log a one-shot Chinese tip (not spam every tick).
6. Tests cover overlay/load helpers and/or UI smoke for preview controls.

## Design

### Preview panel on VisionPage

- Image label (letterboxed) + buttons: `抓取预览`, checkbox `自动刷新`
- On grab: ask MainWindow for a frame via callback/signal (`preview_requested`) so capture mode + hwnd stay consistent with Control page
- Paint region overlays from `load_regions_dir(regions_dir)` using existing colors
- Show meta line: `分辨率 WxH · 区域 n 个 · 截屏=...`

### Failure tips

Static tip box + dynamic status:

| Condition | Tip |
| --- | --- |
| regions_dir empty | 先标定并保存 Skill 区域 |
| pixel + null capture | 请改用方式一/二/三 |
| grab exception | 显示异常摘要 + 换截屏方式 |
| printwindow & no hwnd | 先打开魔兽世界 |
| frame ok but no regions loaded | 预览无框：检查区域目录 |
| engine raw_debug warning missing Skill | already blocked at start |
| bindings empty after rows parsed | 提示检查 AutoPlayer / 框选是否对准色块 |

### Engine tip (light touch)

In `EngineLoop`, if `read_state` result has `raw_debug` warning/bindings_error or empty bindings while actions exist, emit at most one tip per start session (reset on stop/start) to avoid log spam.

## Files

- `clean_client/ui/pages/vision_page.py` — preview UI
- `clean_client/ui/main_window.py` — provide grab for preview, wire tips
- `clean_client/ui/preview.py` (optional helper) — bgr→pixmap + overlay
- `clean_client/engine/loop.py` — one-shot idle/vision tips
- tests + short doc note
