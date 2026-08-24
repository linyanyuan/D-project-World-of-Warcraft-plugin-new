#!/usr/bin/env python3
"""Attach to running Nirvana.exe and dump Python modules via CPython C API."""

from __future__ import annotations

import json
import time
from pathlib import Path

import frida

PID = 22872
REC = Path(r"D:\project\World of Warcraft plugin new\_analysis\recovered")
INJECT = REC / "_inject_payload.py"


def main() -> int:
    runner = (
        "exec(open(r'"
        + str(INJECT).replace("\\", "/")
        + "', encoding='utf-8').read(), {'__name__':'__inject__'})"
    )
    session = frida.attach(PID)
    s0 = session.create_script(
        "rpc.exports={x:function(m,n){return Process.findModuleByName(m).findExportByName(n).toString();}}"
    )
    s0.load()
    ex = s0.exports_sync
    pygil = ex.x("python311.dll", "PyGILState_Ensure")
    pyrel = ex.x("python311.dll", "PyGILState_Release")
    pyrun = ex.x("python311.dll", "PyRun_SimpleString")
    print("resolved", pygil, pyrel, pyrun)

    js = f"""
'use strict';
const PyGILState_Ensure = new NativeFunction(ptr('{pygil}'), 'int', []);
const PyGILState_Release = new NativeFunction(ptr('{pyrel}'), 'void', ['int']);
const PyRun_SimpleString = new NativeFunction(ptr('{pyrun}'), 'int', ['pointer']);
rpc.exports = {{
  run: function(code) {{
    const gil = PyGILState_Ensure();
    try {{
      const buf = Memory.allocUtf8String(code);
      return PyRun_SimpleString(buf);
    }} finally {{
      PyGILState_Release(gil);
    }}
  }}
}};
"""
    script = session.create_script(js)
    script.load()
    rc = script.exports_sync.run(runner)
    print("rc", rc)
    time.sleep(2)

    for name in [
        "inject_started.txt",
        "inject_done.txt",
        "inject_error.txt",
        "sys_modules_app.txt",
        "module_files.json",
        "source_report.json",
        "sys_path.txt",
        "module_attrs.json",
    ]:
        p = REC / name
        print(name, "OK" if p.exists() else "NO", p.stat().st_size if p.exists() else 0)

    err = REC / "inject_error.txt"
    if err.exists():
        print("ERROR:\n", err.read_text(encoding="utf-8")[:3000])

    mods = REC / "sys_modules_app.txt"
    if mods.exists():
        print("MODULES:\n", mods.read_text(encoding="utf-8")[:4000])

    report = REC / "source_report.json"
    if report.exists():
        rep = json.loads(report.read_text(encoding="utf-8"))
        print("source report entries", len(rep))
        for row in rep:
            print(row["ok"], row["name"], row["file"], str(row.get("err", ""))[:100])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
