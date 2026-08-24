# Nirvana30 Reverse Notes

## Package layout

Source package: `D:\project\Nirvana30.zip` → `Nirvana30/`

| Component | Role |
| --- | --- |
| `Nirvana.exe` (~21 MB) | Main client, **Enigma Protector** + **Nuitka** |
| `python311.dll` + stdlib `.pyd` | Adjacent CPython 3.11 runtime |
| `PySide6` / `shiboken6` / Qt6 | Fluent-style desktop UI |
| `cv2` / `numpy` / `dxcam` / `PIL` | Screen capture + image match |
| `win32*.pyd` | Windows API (window find / input) |
| `AutoPlayer/ui_settings.json` | Runtime UI/capture settings |
| `user_config.json` | Tracks package versions |
| `ada92cb5d92a588d1b93__mypyc.pyd` | charset_normalizer mypyc wheel (not app code) |

SHA256(`Nirvana.exe`) = `8ed3e725a7b3b44337c60d914308de2ad0f26fdf2c0ad8371405330d48c2a42d`

## Protection / compilation

- Outer: **Enigma Protector** (`TAGG` / enigmaprotector.com taggant)
- Inner: **Nuitka** (`nuitka_module_loader`, module `__compiled__`)
- Nuitka stubs expose `co_varnames` / `co_names` but bytecode only raises `RuntimeError('Compiled function bytecode used')`
- Real logic is native → **cannot restore full Python source** without original project

## Runtime recovery performed

1. Defender exclude + restore exe
2. Frida attach after Enigma unpack
3. `PyGILState_Ensure` + `PyRun_SimpleString` injection
4. Dumped module list, class/method names, constants/enums, co_varnames
5. Downloaded update packages from `http://36.138.222.171:3000`

## Update channels

| Package | Version API | Actual content |
| --- | --- | --- |
| `Nirvana.zip` | v30 | Client `Nirvana.exe` |
| `retail.zip` | v31 | In-game `AutoPlayer` addon |
| Login/API | `http://36.138.222.171:124/prod-api/third` | Auth / notices |

## In-game addon

- Path recovered: `_analysis/remote/retail/AutoPlayer` → copied to `addon/AutoPlayer`
- TOC: AutoPlayer, Interface 120000+, OptionalDeps Hekili
- Lua files are **VM-obfuscated** (escaped string table + custom VM), not simple Base64
- `Media/obfuscator.py` is a Base64 obfuscator helper (not what the shipped Lua currently uses)

## Crash note

Original crash:

`FluentPrototypeWindow._on_auto_update_result` missing `_do_quit_for_update`

Recovered truth: `_do_quit_for_update` lives on **`BackgroundSettingsPage`**, not the main window.

## ui_settings.json

```json
{
  "capture_mode": "方式一",
  "tick_ms": 30,
  "cd_ready_window_ms": 30,
  "buff_match_threshold": 0.7,
  "hotkey_enabled": false,
  "hotkey_key": "F8",
  "background_strength": 60,
  "card_opacity": 88,
  "background_image": "",
  "custom_font": "",
  "font_family": "Microsoft YaHei UI"
}
```

## Reconstruction outputs

- `client/` — API stubs with constants + method names + co_varnames
- `_analysis/recovered/constants.json` — enums/URLs/class maps
- `_analysis/recovered/signature_index.json` — function local-name index
- `_analysis/recovered/disasm/` — Nuitka stub disassemblies
