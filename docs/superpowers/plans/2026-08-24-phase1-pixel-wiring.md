# Phase 1 Pixel Wiring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire calibrator save → regions_dir persistence, validate pixel startup, keep dry-run default, and allow live keypress only after explicit confirm.

**Architecture:** Extend existing `MainWindow` / `VisionPage` / `calibrator` with callbacks and start-time gates. Reuse `build_engine` + `PixelProtocolVision`; no new vision algorithm.

**Tech Stack:** Python, PySide6, pytest-qt (existing), clean_client engine/vision

**Spec:** `docs/superpowers/specs/2026-08-24-phase1-pixel-wiring-design.md`

---

## File map

| File | Change |
| --- | --- |
| `clean_client/ui/calibrator.py` | Add optional `on_saved(dir)` callback on successful save |
| `clean_client/ui/pages/vision_page.py` | `set_regions_dir()` helper |
| `clean_client/ui/main_window.py` | Confirm dry-run, session flag, start validation, calibrator save hook, persist regions |
| `clean_client/tests/test_main_window.py` | Tests for gates / confirm / regions set |
| `docs/使用手册-clean_client.md` | Phase 1 acceptance notes |

---

### Task 1: VisionPage set_regions_dir + calibrator on_saved

- [ ] Add `VisionPage.set_regions_dir(path)`
- [ ] Add `on_saved` callback to calibrator save path / `run_calibrator`
- [ ] Test or smoke that callback fires with output dir
- [ ] Commit

### Task 2: Guarded dry-run in MainWindow

- [ ] Add `_live_input_confirmed` flag
- [ ] Intercept dry_run checkbox toggle with confirm dialog
- [ ] On Start, block live mode without confirm
- [ ] Tests with qtbot / monkeypatch dialog
- [ ] Commit

### Task 3: Pixel start validation

- [ ] Refuse pixel + empty/missing Skill regions
- [ ] Refuse pixel + null capture
- [ ] Refuse printwindow pixel start without hwnd
- [ ] Log loaded region keys on successful start
- [ ] Tests
- [ ] Commit

### Task 4: Calibrator → persist regions_dir

- [ ] On save callback: set vision page dir, update cfg, save settings JSON
- [ ] Status/log Chinese message
- [ ] Commit

### Task 5: Docs + package note

- [ ] Update `docs/使用手册-clean_client.md` outdated “主界面不会读区域” claims
- [ ] Mentions confirm-before-keypress
- [ ] Commit / push
