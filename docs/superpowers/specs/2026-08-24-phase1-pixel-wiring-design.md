# Phase 1 Design: Calibration Wiring + Real Pixel Read + Guarded Keypress

**Date:** 2026-08-24  
**Status:** Approved by user for implementation  
**Goal:** Make the shortest real in-game loop work ASAP, without building preview/auto-detect/full protocol yet.

## Context

`clean_client` already contains most of the plumbing:

- UI can select `vision_mode` (`mock` / `pixel`) and `regions_dir`
- `build_engine()` loads regions from `regions_dir` and constructs `PixelProtocolVision`
- `PixelProtocolVision` crops `Skill` and parses the key-binding row
- `EngineLoop` can call `press(key)` when `dry_run=false`

What is missing is the **operator loop**: calibrator output does not reliably flow back into the main UI, startup validation/logging is weak, and disabling dry-run has no explicit safety gate.

## Non-goals (Phase 2 / 3)

- Live preview canvas of capture + overlays
- Automatic color-bar discovery
- Parsing cooldown / highlight / buff protocol rows beyond current stubs
- Card-key auth
- Multi-spec rotation editors

## Success criteria

1. After a successful calibrator save, the main UI **Recognition** page shows that directory, `_cfg["regions_dir"]` updates, and the value is persisted to `config/default.json` so the next launch restores it.
2. Starting with `vision_mode=pixel` without a loadable `Skill` region **refuses to start** and shows a Chinese error in the log / status.
3. Starting with `vision_mode=pixel` while capture is still `null` / 空（测试） **refuses to start** with a Chinese reason. PrintWindow also refuses when hwnd is missing.
4. Automated/synthetic path: existing bootstrap pixel fixture (or equivalent test) still produces an action log line containing `动作 法术ID=` under dry-run.
5. Live keypress is never enabled from a loaded config alone. Unchecking dry-run requires confirm; Start with `dry_run=false` also requires a session confirm flag (or the same dialog). Cancel keeps dry-run on.
6. Default remains safe: dry-run on; `vision_mode` Phase 1 values are only `mock` and `pixel` (`protocol` treated as alias of `pixel`).
7. Beginner docs mention the Phase 1 acceptance path.

## Design

### 1) Calibrator → UI regions_dir feedback

When the in-process calibrator finishes a successful save, `MainWindow` updates:

- `vision_page` regions dir state
- in-memory `_cfg["regions_dir"]`
- persist via the existing settings save path to `config/default.json`
- Chinese status: `已载入区域目录: ...`

If the calibrator API lacks a save callback, extend it with a minimal callback rather than rewriting the tool.

### 2) Startup validation

On Start, after collecting settings:

- Map capture UI values to backend modes (Chinese aliases kept).
- Normalize `protocol` → `pixel`.
- If `vision_mode == pixel`:
  - capture must be one of 方式一 / 方式二 / 方式三 (not null/空)
  - `regions_dir` must load and contain `Skill`
  - if capture resolves to printwindow, hwnd must be found
  - otherwise: do **not** start engine; log clear Chinese reason
- Log a one-line summary: capture mode, vision mode, dry_run, hwnd, region keys loaded

### 3) Real pixel dry-run path

No new vision algorithm in Phase 1. Use existing `PixelProtocolVision.read_state` + selector.
MSS/dxcam may start without hwnd; printwindow may not.

### 4) Guarded keypress

- Keep checkbox default checked (`dry_run=true`)
- Maintain a session flag `_live_input_confirmed` default false
- Unchecking dry-run shows confirm dialog; OK sets flag true, Cancel re-checks dry-run and keeps flag false
- Re-checking dry-run clears the flag
- On Start: if requested dry_run is false and flag is false, show the same confirm; Cancel forces dry-run start or aborts start (prefer abort with Chinese log)
- Never start live keypress merely because `default.json` has `dry_run: false`
- On Start with confirmed live mode, wire `press=tap_key`

### 5) Docs

Update:

- `docs/使用手册-clean_client.md` Phase 1 section
- regenerate or amend beginner DOCX acceptance checklist for pixel dry-run + guarded keypress

## Test plan

- Unit/UI: unchecking dry_run without confirm restores checked state
- Unit: start with pixel + empty regions_dir does not create/start engine
- Existing bootstrap pixel synthetic frame test still passes
- Manual: mock mode still idles; pixel+regions+capture can log actions in dry-run

## Rollout

1. Implement + tests
2. Update docs
3. Repackage `release/CleanClient` so friends get the wired build
4. User in-game acceptance before Phase 2 preview work
