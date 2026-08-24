# Clean Auto-Unholy Client Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a maintainable PySide6 + dxcam Unholy DK full-auto client under `clean_client/`, protocol-driven against AutoPlayer RGB rows, with dry-run first and calibrated live path.

**Architecture:** Worker-thread tick loop captures WoW frames, `PixelProtocolVision` parses marker/spell-id rows into `CombatState`, thin Unholy profile selects first ready `spell_id`, SendInput presses unless dry-run. Region anchors are configurable placeholders until live calibration.

**Tech Stack:** Python 3.11, PySide6, numpy, OpenCV, dxcam, mss, pywin32, pytest

**Spec:** `docs/superpowers/specs/2026-08-21-clean-autounholy-client-design.md`  
**Protocol:** `_analysis/lua_deobf/PIXEL_PROTOCOL_RECOVERED.md`, `RGB_MARKERS.json`

---

## File map

| Path | Responsibility |
| --- | --- |
| `clean_client/pyproject.toml` / `requirements.txt` | deps |
| `clean_client/models/state.py` | Action, CooldownInfo, CombatState |
| `clean_client/config/default.json` | defaults |
| `clean_client/config/loader.py` | load/save settings + regions |
| `clean_client/vision/markers.py` | RGB marker constants |
| `clean_client/vision/encoding.py` | spell_id <-> RGB |
| `clean_client/vision/parsers.py` | row parsers |
| `clean_client/vision/protocol.py` | PixelProtocolVision |
| `clean_client/vision/mock.py` | MockVision |
| `clean_client/rotation/profile.py` | Unholy profile schema |
| `clean_client/rotation/selector.py` | ready predicate + first-match |
| `clean_client/capture/base.py` | CaptureBackend protocol |
| `clean_client/capture/backends.py` | dxcam/mss/printwindow |
| `clean_client/capture/window.py` | find WoW hwnd |
| `clean_client/input/sendinput.py` | key tap |
| `clean_client/engine/loop.py` | QThread tick loop |
| `clean_client/ui/main_window.py` | UI |
| `clean_client/app.py` | entry |
| `clean_client/profiles/unholy_default.json` | Unholy actions |
| `clean_client/tests/...` | unit tests |

---

### Task 1: Project scaffold + models

**Files:**

- Create: `clean_client/requirements.txt`
- Create: `clean_client/models/__init__.py`
- Create: `clean_client/models/state.py`
- Create: `clean_client/tests/test_models.py`

- [ ] **Step 1: Write failing test for CombatState construction**

```python
from clean_client.models.state import Action, CombatState

def test_action_fields():
    a = Action(spell_id=1231411, key="1", kind="spell", name="Outbreak")
    assert a.spell_id == 1231411
```

- [ ] **Step 2: Run test — expect fail (missing module)**

Run: `pytest clean_client/tests/test_models.py -v`

- [ ] **Step 3: Implement dataclasses in `models/state.py` per spec**

- [ ] **Step 4: Add requirements.txt (PySide6, numpy, opencv-python, dxcam, mss, pywin32, pytest)**

- [ ] **Step 5: Tests pass + commit**

```bash
git add clean_client && git commit -m "scaffold clean_client models"
```

---

### Task 2: Spell-id encoding + markers

**Files:**

- Create: `clean_client/vision/markers.py`
- Create: `clean_client/vision/encoding.py`
- Create: `clean_client/tests/test_encoding.py`

- [ ] **Step 1: Failing tests**

```python
from clean_client.vision.encoding import rgb_to_spell_id, spell_id_to_rgb

def test_doc_example():
    assert rgb_to_spell_id(0x12, 0xCA, 0x33) == 1231411
    assert spell_id_to_rgb(1231411) == (0x12, 0xCA, 0x33)
```

- [ ] **Step 2: Run — fail**

- [ ] **Step 3: Implement using `RGB_MARKERS.json` values in `markers.py`**

- [ ] **Step 4: Pass + commit**

---

### Task 3: Synthetic row helpers + binding parser

**Files:**

- Create: `clean_client/vision/parsers.py`
- Create: `clean_client/tests/test_parsers_bindings.py`

- [ ] **Step 1: Write test that builds a 1px-tall numpy row with START + SPELL marker + spell rgb + END and asserts parser returns binding spell_id→key stub**

(For v1 binding row: at minimum detect spell_id pixels between markers; key may come from a parallel encoding or fallback map in fixture.)

- [ ] **Step 2: Implement minimal `parse_key_bindings_row(row_bgr) -> dict[int, Action]`**

- [ ] **Step 3: Pass + commit**

---

### Task 4: Ready predicate + Unholy selector

**Files:**

- Create: `clean_client/rotation/selector.py`
- Create: `clean_client/rotation/profile.py`
- Create: `clean_client/profiles/unholy_default.json`
- Create: `clean_client/tests/test_selector.py`

- [ ] **Step 1: Failing tests for ready() and first-match with prefer_highlighted two-pass**

Use spec formulas exactly.

- [ ] **Step 2: Implement profile load + selector**

- [ ] **Step 3: Seed `unholy_default.json` with a few Midnight Unholy spell IDs from sibling UnholyAssist rules (names+ids only)

- [ ] **Step 4: Pass + commit**

---

### Task 5: Capture backends + window finder

**Files:**

- Create: `clean_client/capture/*.py`
- Create: `clean_client/tests/test_window_finder.py` (mock win32)

- [ ] **Step 1: Interface + hwnd finder tests with monkeypatched win32gui**

- [ ] **Step 2: Implement dxcam/mss/printwindow wrappers returning BGR arrays**

- [ ] **Step 3: Manual note in README for live grab smoke test**

- [ ] **Step 4: Commit**

---

### Task 6: SendInput + engine loop dry-run

**Files:**

- Create: `clean_client/input/sendinput.py`
- Create: `clean_client/engine/loop.py`
- Create: `clean_client/tests/test_engine_dry_run.py`

- [ ] **Step 1: Test engine with MockVision + fake capture yields logged actions, no press when dry_run=True**

- [ ] **Step 2: Implement QThread loop (or threading.Thread if UI not ready yet; switch to QThread in Task 7)

- [ ] **Step 3: Pass + commit**

---

### Task 7: PySide6 main window + app entry

**Files:**

- Create: `clean_client/ui/main_window.py`
- Create: `clean_client/app.py`
- Create: `clean_client/config/default.json`
- Create: `clean_client/config/loader.py`

- [ ] **Step 1: Wire Start/Stop, dry-run, capture mode, tick_ms, log pane to engine signals**

- [ ] **Step 2: `python -m clean_client.app` launches**

- [ ] **Step 3: Commit**

---

### Task 8: Region config + PixelProtocolVision shell

**Files:**

- Create: `clean_client/vision/protocol.py`
- Modify: config loader for `*_region.txt`
- Create: `clean_client/tests/test_protocol_regions.py`

- [ ] **Step 1: Load/save Skill/Target/Player/Buff rectangles**

- [ ] **Step 2: PixelProtocolVision crops skill region, splits rows by configurable `row_height`, calls parsers**

- [ ] **Step 3: Unit test with synthetic multi-row image**

- [ ] **Step 4: Commit**

---

### Task 9: Docs + manual checklist

**Files:**

- Create: `clean_client/README.md`
- Update: root `README.md` link

- [ ] **Step 1: Document run instructions, dry-run, calibration steps, ToS warning**

- [ ] **Step 2: Manual checklist for live AutoPlayer (optional)**

- [ ] **Step 3: Commit**

---

## Parallel note

Lua coordinate recovery remains open. If `skill_region.txt` from a live Nirvana install appears, drop it into `clean_client/config/regions/` and re-run live checklist—no engine rewrite.
