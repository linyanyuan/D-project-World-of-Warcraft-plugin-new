#!/usr/bin/env python3
"""Spawn Nirvana.exe under Frida, wait for unpack, dump interesting memory."""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

import frida

NEEDLES = [
    b"fluent_ui",
    b"prototype_window",
    b"FluentPrototypeWindow",
    b"AutoPlayer",
    b"skill_cycles",
    b"buff_match_threshold",
    b"capture_mode",
    b"dxcam",
    b"PySide6",
    b"qfluentwidgets",
    b"Nirvana",
    b".toc",
    b"Interface\\AddOns",
    b"SendInput",
    b"keybd_event",
]

JS = r"""
'use strict';
rpc.exports = {
  modules: function () {
    return Process.enumerateModules().map(m => ({
      name: m.name,
      base: m.base.toString(),
      size: m.size,
      path: m.path
    }));
  },
  scan: function (patterns) {
    const hits = [];
    const ranges = Process.enumerateRanges('r--');
    for (let i = 0; i < patterns.length; i++) {
      const pat = patterns[i];
      for (let r = 0; r < ranges.length; r++) {
        const range = ranges[r];
        if (range.size > 64 * 1024 * 1024) continue;
        try {
          const found = Memory.scanSync(range.base, range.size, pat);
          for (let f = 0; f < found.length; f++) {
            hits.push({
              pattern: pat,
              address: found[f].address.toString(),
              base: range.base.toString(),
              size: range.size,
              protection: range.protection
            });
          }
        } catch (e) {}
      }
    }
    return hits;
  },
  read: function (address, size) {
    return Memory.readByteArray(ptr(address), size);
  },
  dumpRange: function (address, size) {
    return Memory.readByteArray(ptr(address), size);
  },
  ranges: function () {
    return Process.enumerateRanges('r--').map(r => ({
      base: r.base.toString(),
      size: r.size,
      protection: r.protection
    }));
  }
};
"""


def to_frida_pattern(data: bytes) -> str:
    return " ".join(f"{b:02x}" for b in data)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--exe",
        default=r"D:\project\Nirvana30\Nirvana30\Nirvana.exe",
    )
    ap.add_argument(
        "--cwd",
        default=r"D:\project\Nirvana30\Nirvana30",
    )
    ap.add_argument(
        "--out",
        default=r"D:\project\World of Warcraft plugin new\_analysis\dump",
    )
    ap.add_argument("--wait", type=float, default=8.0)
    ap.add_argument("--kill", action="store_true", default=True)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    print(f"spawning {args.exe}")
    pid = frida.spawn([args.exe], cwd=args.cwd)
    session = frida.attach(pid)
    script = session.create_script(JS)
    script.load()
    frida.resume(pid)
    print(f"pid={pid}, waiting {args.wait}s for Enigma unpack / Python init")
    time.sleep(args.wait)

    api = script.exports_sync
    modules = api.modules()
    (out / "modules.txt").write_text(
        "\n".join(f"{m['name']}\t{m['base']}\t{m['size']}\t{m['path']}" for m in modules),
        encoding="utf-8",
    )
    print(f"modules={len(modules)}")
    interesting_mods = [
        m
        for m in modules
        if any(
            k in m["name"].lower()
            for k in ("python", "pyside", "shiboken", "cv2", "dxcam", "nirvana", "qt6")
        )
    ]
    for m in interesting_mods:
        print(" ", m["name"], m["base"], m["size"])

    patterns = [to_frida_pattern(n) for n in NEEDLES]
    print("scanning memory for needles...")
    hits = api.scan(patterns)
    print(f"hits={len(hits)}")
    hit_lines = []
    dumped_bases = set()
    for h in hits:
        hit_lines.append(
            f"{h['pattern']}\t{h['address']}\tbase={h['base']}\tsize={h['size']}\t{h['protection']}"
        )
        base = h["base"]
        if base in dumped_bases:
            continue
        # dump surrounding page-ish window around hit, and full range if modest
        size = min(int(h["size"]), 8 * 1024 * 1024)
        try:
            # dump from range base
            blob = api.dump_range(base, size)
            if blob:
                dumped_bases.add(base)
                fp = out / f"range_{base}_{size}.bin"
                Path(fp).write_bytes(bytes(blob))
                print("dumped", fp, size)
        except Exception as exc:  # noqa: BLE001
            print("dump fail", base, exc)
            # fallback: small window around hit
            try:
                addr = int(h["address"], 16)
                start = max(addr - 0x1000, 0)
                blob = api.read(hex(start), 0x4000)
                if blob:
                    fp = out / f"win_{h['address']}.bin"
                    Path(fp).write_bytes(bytes(blob))
                    print("window", fp)
            except Exception as exc2:  # noqa: BLE001
                print("window fail", exc2)

    (out / "hits.txt").write_text("\n".join(hit_lines), encoding="utf-8")

    # Also dump Nirvana.exe module image if present
    for m in modules:
        if m["name"].lower() == "nirvana.exe":
            size = min(int(m["size"]), 96 * 1024 * 1024)
            try:
                blob = api.dump_range(m["base"], size)
                if blob:
                    fp = out / f"module_Nirvana_exe_{m['base']}_{size}.bin"
                    Path(fp).write_bytes(bytes(blob))
                    print("module dump", fp, len(blob))
                    # quick string extract
                    text = re.findall(rb"[\x20-\x7e]{8,}", bytes(blob))
                    keys = (
                        b"fluent",
                        b"AutoPlay",
                        b"prototype",
                        b"skill",
                        b"dxcam",
                        b".lua",
                        b".toc",
                        b"PySide",
                        b"qfluent",
                    )
                    uniq = []
                    seen = set()
                    for s in text:
                        if any(k.lower() in s.lower() for k in keys):
                            t = s.decode("ascii", "ignore")
                            if t not in seen:
                                seen.add(t)
                                uniq.append(t)
                    (out / "module_interesting_strings.txt").write_text(
                        "\n".join(uniq[:500]), encoding="utf-8"
                    )
                    print("module interesting strings", len(uniq))
            except Exception as exc:  # noqa: BLE001
                print("module dump fail", exc)

    if args.kill:
        try:
            frida.kill(pid)
            print("killed", pid)
        except Exception as exc:  # noqa: BLE001
            print("kill fail", exc)

    return 0


if __name__ == "__main__":
    sys.exit(main())
