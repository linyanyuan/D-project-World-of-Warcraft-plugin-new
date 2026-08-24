#!/usr/bin/env python3
"""Generate reconstructed Python stubs from Nuitka disasm metadata + constants."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

REC = Path(r"D:\project\World of Warcraft plugin new\_analysis\recovered")
DIS = REC / "disasm"
CLIENT = Path(r"D:\project\World of Warcraft plugin new\client")

STUB_HEADER = '''"""
Reconstructed API stub from Nirvana30 Nuitka runtime metadata.
NOTE: Bodies are not recovered (Nuitka native). Signatures/locals come from co_varnames.
"""
from __future__ import annotations

from typing import Any
'''


def parse_tuple(s: str) -> list:
    try:
        return list(eval(s, {}))  # noqa: S307 - controlled disasm headers
    except Exception:
        return []


def emit_func(name: str, meta: dict, indent: int = 0) -> str:
    vars_ = meta.get("varnames") or []
    pad = " " * indent
    lines = [
        f"{pad}def {name}(*args: Any, **kwargs: Any) -> Any:",
        f'{pad}    """co_varnames={vars_!r}"""',
    ]
    if meta.get("names"):
        lines.append(f"{pad}    # co_names={meta['names'][:40]!r}")
    lines.append(
        f"{pad}    raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')"
    )
    return "\n".join(lines)


def mod_to_path(mod: str) -> Path:
    return CLIENT.joinpath(*mod.split(".")).with_suffix(".py")


def main() -> int:
    try:
        constants = json.loads((REC / "constants.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"failed to load constants.json: {exc}") from exc
    modules: dict = defaultdict(
        lambda: {"functions": {}, "methods": defaultdict(dict), "file": None}
    )

    skip_prefixes = (
        "Path.",
        "Enum.",
        "Q",
        "ComboBox.",
        "InfoBar.",
        "BodyLabel.",
        "Any.",
        "Dict.",
        "List.",
        "Optional.",
        "Callable.",
        "Buffered",
        "TextIO",
        "BytesIO",
        "WeakSet.",
        "HTTP",
    )

    for path in DIS.glob("*.txt"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "Compiled function bytecode used" not in text:
            continue
        m = re.search(r"^# (?P<qual>.+)$", text, re.M)
        if not m:
            continue
        qual = m.group("qual").strip()
        if any(qual.startswith(pref) for pref in skip_prefixes):
            continue

        def grab_from(src: str, key: str) -> str:
            mm = re.search(rf"^{key}=(.*)$", src, re.M)
            return mm.group(1).strip() if mm else ""

        co_file = grab_from(text, "co_filename")
        names = parse_tuple(grab_from(text, "co_names"))
        varnames = parse_tuple(grab_from(text, "co_varnames"))
        meta = {"varnames": varnames, "names": names, "file": co_file}

        parts = qual.split(".")
        if len(parts) == 2:
            mod, func = parts
            modules[mod]["functions"][func] = meta
            modules[mod]["file"] = co_file
        elif len(parts) >= 3:
            if parts[0] == "fluent_ui":
                mod = parts[0] + "." + parts[1]
                rest = parts[2:]
            else:
                mod = parts[0]
                rest = parts[1:]
            if len(rest) == 1:
                modules[mod]["functions"][rest[0]] = meta
            else:
                cls = rest[0]
                method = ".".join(rest[1:])
                modules[mod]["methods"][cls][method] = meta
            modules[mod]["file"] = co_file

    for mod in [
        "window_capture",
        "addon_update",
        "update_checker",
        "skill_conditions",
        "skill_cycle_config",
        "fluent_ui.data_loader",
        "fluent_ui.fluent_windows",
        "fluent_ui.prototype_window",
        "fluent_ui.void_protocol_theme",
    ]:
        _ = modules[mod]

    CLIENT.mkdir(parents=True, exist_ok=True)
    (CLIENT / "fluent_ui").mkdir(exist_ok=True)
    (CLIENT / "fluent_ui" / "__init__.py").write_text(
        "from . import data_loader, fluent_windows, prototype_window, void_protocol_theme\n",
        encoding="utf-8",
    )

    written = []
    for mod, data in sorted(modules.items()):
        if mod.startswith("dxcam") or mod in {"json", "os", "sys", "re", "pathlib"}:
            continue
        path = mod_to_path(mod)
        path.parent.mkdir(parents=True, exist_ok=True)
        parts = [STUB_HEADER, f"# original_file: {data.get('file')}\n"]

        const_bucket = None
        if isinstance(constants.get(mod), dict):
            const_bucket = constants[mod].get("values")
        if const_bucket:
            parts.append("# --- recovered constants ---")
            for key, value in const_bucket.items():
                parts.append(f"{key} = {json.dumps(value, ensure_ascii=False)}")
            parts.append("")

        for fname, meta in sorted(data["functions"].items()):
            parts.append(emit_func(fname, meta))
            parts.append("")

        for cls, methods in sorted(data["methods"].items()):
            parts.append(f"class {cls}:")
            if not methods:
                parts.append("    pass")
            else:
                for mname, meta in sorted(methods.items()):
                    parts.append(emit_func(mname, meta, indent=4))
                    parts.append("")
            parts.append("")

        if mod == "fluent_ui.prototype_window":
            pcs = constants.get("prototype_classes", {})
            for cname, methods in pcs.items():
                if cname in data["methods"]:
                    continue
                parts.append(f"class {cname}:")
                parts.append(
                    f'    """Recovered method names only ({len(methods)} attrs)."""'
                )
                custom = [
                    m
                    for m in methods
                    if (m.startswith("_") or m[:1].islower())
                    and not m.startswith("_pyside6_workaround")
                    and not m.endswith(
                        (
                            "Event",
                            "Color",
                            "Ratio",
                            "Focus",
                            "Timer",
                            "Geometry",
                            "Enabled",
                            "Level",
                            "Keyboard",
                        )
                    )
                ]
                for method_name in sorted(set(custom))[:120]:
                    parts.append(
                        f"    def {method_name}(self, *args: Any, **kwargs: Any) -> Any: ..."
                    )
                parts.append("")

        if mod == "fluent_ui.fluent_windows":
            fwc = constants.get("fluent_windows_classes", {})
            for cname, methods in fwc.items():
                if cname == "ConditionType":
                    continue
                parts.append(f"class {cname}:")
                custom = [
                    m
                    for m in methods
                    if (m.startswith("_") or m == "query_online_cycles")
                    and not m.startswith("_pyside6")
                ]
                for method_name in sorted(set(custom))[:80]:
                    parts.append(
                        f"    def {method_name}(self, *args: Any, **kwargs: Any) -> Any: ..."
                    )
                parts.append("")

        path.write_text("\n".join(parts) + "\n", encoding="utf-8")
        written.append((mod, str(path), path.stat().st_size))

    index = {
        mod: {
            "file": data.get("file"),
            "functions": {k: v["varnames"] for k, v in data["functions"].items()},
            "methods": {
                c: {m: meta["varnames"] for m, meta in ms.items()}
                for c, ms in data["methods"].items()
            },
        }
        for mod, data in modules.items()
    }
    (REC / "signature_index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("wrote", len(written), "modules")
    for row in written:
        print(row)
    print("signature_index modules", len(index))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
