#!/usr/bin/env python3
"""Probe obfuscated AutoPlayer Lua string tables."""

from __future__ import annotations

import base64
import re
from pathlib import Path

ADDON = Path(r"D:\project\World of Warcraft plugin new\addon\AutoPlayer")
OUT = Path(r"D:\project\World of Warcraft plugin new\_analysis\lua_deobf")
OUT.mkdir(parents=True, exist_ok=True)


def unescape_lua(s: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s):
            nxt = s[i + 1]
            if nxt.isdigit():
                j = i + 1
                while j < len(s) and j < i + 4 and s[j].isdigit():
                    j += 1
                # Lua \ddd uses decimal digits, not octal.
                out.append(chr(int(s[i + 1 : j], 10)))
                i = j
                continue
            mapping = {
                "n": "\n",
                "t": "\t",
                "r": "\r",
                '"': '"',
                "'": "'",
                "\\": "\\",
                "a": "\a",
                "b": "\b",
                "f": "\f",
                "v": "\v",
            }
            out.append(mapping.get(nxt, nxt))
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def probe(path: Path, limit: int = 120) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    head = text[:20000]
    strs = re.findall(r'"((?:\\.|[^"\\])*)"', head)
    decoded: list[str] = []
    lines: list[str] = [f"# {path.name} early strings {len(strs)}"]
    for raw in strs[:limit]:
        d = unescape_lua(raw)
        decoded.append(d)
        note = ""
        if re.fullmatch(r"[A-Za-z0-9+/]+=*", d or "") and len(d) >= 4:
            try:
                note = f" | b64={base64.b64decode(d)!r}"
            except Exception as exc:  # noqa: BLE001
                note = f" | b64-fail={exc}"
        lines.append(repr(d) + note)
    (OUT / f"{path.stem}_early_strings.txt").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return decoded


def main() -> int:
    all_decoded: list[str] = []
    for path in sorted(ADDON.glob("*.lua")):
        print("probe", path.name, path.stat().st_size)
        all_decoded.extend(probe(path))

    # interesting plaintext-ish
    interesting = sorted(
        {
            s
            for s in all_decoded
            if any(
                k in s.lower()
                for k in (
                    "pixel",
                    "frame",
                    "spell",
                    "buff",
                    "addon",
                    "auto",
                    "create",
                    "texture",
                    "color",
                    "hekili",
                    "wow",
                    "http",
                )
            )
            or (
                s.isascii()
                and any(c.isalpha() for c in s)
                and "\\" not in s
                and len(s) > 3
            )
        }
    )
    (OUT / "interesting_early.txt").write_text("\n".join(interesting), encoding="utf-8")
    print("interesting", len(interesting))
    for s in interesting[:80]:
        print(s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
