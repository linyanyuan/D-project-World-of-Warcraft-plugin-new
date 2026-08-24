# clean_client

Protocol-driven Unholy DK auto client (clean rewrite).

## Status

- Models / RGB encoding / binding-row parser / ready selector: **done + tested**
- Capture backends / SendInput / engine dry-run loop: **scaffolded**
- Vision factory (`mock` / `pixel`) + `engine.bootstrap.build_engine`: **done**
- Fluent multi-page UI (qfluentwidgets): **Control / Rotation / Vision / Settings**
- Live auto requires AutoPlayer addon + calibrated `*_region.txt`
- Card-key login: **deferred** (see `docs/auth-cardkey-plan.md`)

## Run tests

```bash
cd "D:/project/World of Warcraft plugin new"
pip install -r clean_client/requirements.txt
python -m pytest clean_client/tests -v
```

## Launch UI

```bash
python -m clean_client.app
```

Opens a **Fluent** side-nav window:

| Page | Contents |
| --- | --- |
| 控制 Control | Start/Stop, dry_run, capture, tick_ms, hwnd, log |
| 循环 Rotation | Loaded Unholy profile + actions table (read-only) |
| 识别 Vision | Mock vs PixelProtocol, regions dir, open calibrator |
| 设置 Settings | window_keywords, cd_ready_window_ms, buff_match_threshold |

`dry_run` defaults to **checked** — no SendInput unless you uncheck it.
Start/Stop wires through `clean_client.engine.bootstrap.build_engine`.

Dependency note: install **`PySide6-Fluent-Widgets`** (import name `qfluentwidgets`).

## Run headless dry-run stub

```bash
python -m clean_client.app --cli
```

Uses `MockVision` and `dry_run=true` by default — logs only, no keypresses.

## Region calibrator

Select Skill / Target / Player / Buff rectangles and save `*_region.txt` files
(`x1 y1 x2 y2`) compatible with `clean_client.config.loader`.

```bash
cd "D:/project/World of Warcraft plugin new"
python -m clean_client.tools.calibrate_regions
# optional:
python -m clean_client.tools.calibrate_regions --dir ./regions --capture null
```

Or use **识别 → Open calibrator** in the UI (spawns the same module).

Workflow:

1. Choose capture backend (`null` synthetic, or `mss` / `dxcam` / `printwindow` live).
2. Click **Grab frame**.
3. Pick the active region key, then drag on the image (or edit x1/y1/x2/y2 spins).
4. **Save regions…** writes `skill_region.txt`, `target_region.txt`,
   `player_region.txt`, `buff_region.txt` into the chosen folder.
5. **Load regions…** reloads an existing folder.

## Safety

Full-auto may violate game ToS. Use only for private research on accounts you own.
