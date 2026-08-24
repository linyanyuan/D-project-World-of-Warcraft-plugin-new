#!/usr/bin/env python3
"""Static triage for Nirvana.exe once it is readable on disk."""

from __future__ import annotations

import argparse
import collections
import hashlib
import math
import re
import struct
from pathlib import Path

EXPECTED_SHA256 = "8ed3e725a7b3b44337c60d914308de2ad0f26fdf2c0ad8371405330d48c2a42d"


def entropy(blob: bytes) -> float:
    if not blob:
        return 0.0
    n = len(blob)
    counts = collections.Counter(blob)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def parse_pe(raw: bytes):
    e_lfanew = struct.unpack_from("<I", raw, 0x3C)[0]
    machine, numsec, timedate, _, _, sizeopt = struct.unpack_from(
        "<HHIIIH", raw, e_lfanew + 4
    )
    magic = struct.unpack_from("<H", raw, e_lfanew + 24)[0]
    sec_off = e_lfanew + 24 + sizeopt
    sections = []
    for i in range(numsec):
        off = sec_off + i * 40
        name = raw[off : off + 8].split(b"\x00")[0]
        vsize, vaddr, rsize, raddr, _, _, _, _, chars = struct.unpack_from(
            "<IIIIIIHHI", raw, off + 8
        )
        sections.append(
            {
                "name": name,
                "vsize": vsize,
                "vaddr": vaddr,
                "rsize": rsize,
                "raddr": raddr,
                "chars": chars,
            }
        )
    ep = struct.unpack_from("<I", raw, e_lfanew + 24 + 16)[0]
    return {
        "e_lfanew": e_lfanew,
        "machine": machine,
        "timedate": timedate,
        "magic": magic,
        "sections": sections,
        "ep": ep,
        "sizeopt": sizeopt,
    }


def rva_to_off(sections, rva: int):
    for s in sections:
        span = max(s["vsize"], s["rsize"])
        if s["vaddr"] <= rva < s["vaddr"] + span:
            return s["raddr"] + (rva - s["vaddr"])
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "path",
        nargs="?",
        default=r"D:\project\_nirv_extract\Nirvana.exe",
    )
    ap.add_argument(
        "--out", default=r"D:\project\World of Warcraft plugin new\_analysis"
    )
    args = ap.parse_args()

    path = Path(args.path)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    print(f"path={path}")
    print(f"size={len(raw)}")
    print(f"sha256={digest}")
    print(f"sha256_match={digest == EXPECTED_SHA256}")
    if raw[:2] != b"MZ":
        raise SystemExit("not an MZ file")

    pe = parse_pe(raw)
    print(f"sections={len(pe['sections'])} ep_rva=0x{pe['ep']:x}")
    for i, s in enumerate(pe["sections"]):
        blob = raw[s["raddr"] : s["raddr"] + s["rsize"]]
        print(
            f"  [{i}] name={s['name']!r:10} ent={entropy(blob):.3f} "
            f"raddr=0x{s['raddr']:x} rsize=0x{s['rsize']:x}"
        )

    # Enigma taggant marker
    tagg = raw.find(b"TAGG")
    enigma = raw.find(b"Enigma Protector")
    print(f"TAGG_off={tagg} EnigmaProtector_off={enigma}")

    # Extract printable strings that may survive partial dumps later
    ascii_strings = sorted(
        {m.decode("ascii", "ignore") for m in re.findall(rb"[\x20-\x7e]{8,}", raw)}
    )
    interesting = [
        s
        for s in ascii_strings
        if any(
            k in s.lower()
            for k in (
                "enigma",
                "python",
                "fluent",
                "nirvana",
                "autoplay",
                "dxcam",
                "pyside",
                "tagg",
                "addon",
                ".py",
                ".lua",
                ".toc",
                "wow",
            )
        )
    ]
    (out / "interesting_strings.txt").write_text(
        "\n".join(interesting), encoding="utf-8"
    )
    print(
        f"interesting_strings={len(interesting)} -> {out / 'interesting_strings.txt'}"
    )

    # Save section map
    lines = [
        f"sha256={digest}",
        f"ep_rva=0x{pe['ep']:x}",
        f"tagg={tagg}",
        f"enigma={enigma}",
    ]
    for i, s in enumerate(pe["sections"]):
        blob = raw[s["raddr"] : s["raddr"] + s["rsize"]]
        lines.append(
            f"{i}\t{s['name']!r}\tva=0x{s['vaddr']:x}\tvsz=0x{s['vsize']:x}\t"
            f"ra=0x{s['raddr']:x}\trsz=0x{s['rsize']:x}\tent={entropy(blob):.3f}"
        )
    (out / "section_map.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out / 'section_map.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
