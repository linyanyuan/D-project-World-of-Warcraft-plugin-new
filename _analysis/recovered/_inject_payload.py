import inspect
import json
import os
import shutil
import sys
import traceback


def _write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


out = r"D:\project\World of Warcraft plugin new\_analysis\recovered"
os.makedirs(out, exist_ok=True)
_write(os.path.join(out, "inject_started.txt"), "ok")

try:
    prefixes = (
        "fluent_ui",
        "AutoPlayer",
        "capture",
        "skill",
        "addon",
        "update",
        "dxcam",
    )
    interesting = []
    for name, mod in list(sys.modules.items()):
        if not mod:
            continue
        fn = getattr(mod, "__file__", None)
        low_fn = str(fn).replace("\\", "/").lower() if fn else ""
        if name.startswith(prefixes) or any(
            k in low_fn
            for k in ("fluent_ui", "autoplayer", "capture", "skill_", "addon_", "update_")
        ):
            interesting.append((name, str(fn)))

    interesting = sorted(set(interesting), key=lambda x: x[0])
    _write(
        os.path.join(out, "module_files.json"),
        json.dumps(interesting, ensure_ascii=False, indent=2),
    )
    _write(
        os.path.join(out, "sys_modules_app.txt"),
        "\n".join(n for n, _ in interesting) + f"\n\nALL_COUNT={len(sys.modules)}\n",
    )
    _write(os.path.join(out, "sys_path.txt"), "\n".join(map(str, sys.path)))

    src_dir = os.path.join(out, "sources")
    os.makedirs(src_dir, exist_ok=True)
    report = []
    for name, fn in interesting:
        mod = sys.modules.get(name)
        path = os.path.join(src_dir, name.replace(".", "_") + ".py")
        ok = False
        err = ""
        try:
            src = inspect.getsource(mod)
            _write(path, src)
            ok = True
        except Exception as e:
            err = repr(e)
            try:
                if fn and os.path.isfile(fn):
                    ext = os.path.splitext(fn)[1] or ".bin"
                    shutil.copy2(fn, path + ".orig" + ext)
                    ok = "copied"
            except Exception as e2:
                err += " | " + repr(e2)
        if ok is False and fn and str(fn).endswith(".py") and os.path.isfile(fn):
            try:
                shutil.copy2(fn, path)
                ok = "copied_py"
            except Exception as e3:
                err += " | " + repr(e3)
        report.append({"name": name, "file": fn, "ok": ok, "err": err})

    _write(
        os.path.join(out, "source_report.json"),
        json.dumps(report, ensure_ascii=False, indent=2),
    )

    meta = []
    for name, fn in interesting:
        mod = sys.modules.get(name)
        if not mod:
            continue
        try:
            attrs = [a for a in dir(mod) if not a.startswith("__")][:80]
        except Exception:
            attrs = []
        meta.append({"name": name, "file": fn, "attrs": attrs})
    _write(
        os.path.join(out, "module_attrs.json"),
        json.dumps(meta, ensure_ascii=False, indent=2),
    )
    _write(os.path.join(out, "inject_done.txt"), "done")
except Exception:
    _write(os.path.join(out, "inject_error.txt"), traceback.format_exc())
