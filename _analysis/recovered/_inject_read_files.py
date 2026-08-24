import json
import os
import traceback

out = r"D:\project\World of Warcraft plugin new\_analysis\recovered"
src_dir = os.path.join(out, "virtual_files")
os.makedirs(src_dir, exist_ok=True)

files = [
    r"D:\project\Nirvana30\Nirvana30\fluent_ui\__init__.py",
    r"D:\project\Nirvana30\Nirvana30\fluent_ui\data_loader.py",
    r"D:\project\Nirvana30\Nirvana30\fluent_ui\fluent_windows.py",
    r"D:\project\Nirvana30\Nirvana30\fluent_ui\prototype_window.py",
    r"D:\project\Nirvana30\Nirvana30\fluent_ui\void_protocol_theme.py",
    r"D:\project\Nirvana30\Nirvana30\fluent_ui\general_settings.py",
    r"D:\project\Nirvana30\Nirvana30\AutoPlayer\__init__.py",
    r"D:\project\Nirvana30\Nirvana30\AutoPlayer\ui_settings.py",
    r"D:\project\Nirvana30\Nirvana30\addon_update.py",
    r"D:\project\Nirvana30\Nirvana30\skill_conditions.py",
    r"D:\project\Nirvana30\Nirvana30\skill_cycle_config.py",
    r"D:\project\Nirvana30\Nirvana30\skill_recognition.py",
    r"D:\project\Nirvana30\Nirvana30\update_checker.py",
    r"D:\project\Nirvana30\Nirvana30\window_capture.py",
    r"D:\project\Nirvana30\Nirvana30\capture.py",
    r"D:\project\Nirvana30\Nirvana30\capture_loop.py",
    r"D:\project\Nirvana30\Nirvana30\capture_runtime.py",
    r"D:\project\Nirvana30\Nirvana30\updates.py",
    r"D:\project\Nirvana30\Nirvana30\main.py",
    r"D:\project\Nirvana30\Nirvana30\app.py",
    r"D:\project\Nirvana30\Nirvana30\__main__.py",
]


def _write(path: str, data: bytes | str) -> None:
    if isinstance(data, str):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(data)
    else:
        with open(path, "wb") as fh:
            fh.write(data)


report = []
try:
    # Also list virtual directory
    root = r"D:\project\Nirvana30\Nirvana30"
    listing = []
    try:
        for name in sorted(os.listdir(root)):
            p = os.path.join(root, name)
            listing.append(
                {
                    "name": name,
                    "isdir": os.path.isdir(p),
                    "isfile": os.path.isfile(p),
                    "size": (os.path.getsize(p) if os.path.isfile(p) else None),
                }
            )
    except Exception as e:
        listing.append({"error": repr(e)})
    _write(os.path.join(out, "virtual_listdir.json"), json.dumps(listing, ensure_ascii=False, indent=2))

    # recursive py listing under fluent_ui / AutoPlayer
    py_files = []
    for sub in ("fluent_ui", "AutoPlayer", "dxcam"):
        base = os.path.join(root, sub)
        if not os.path.isdir(base):
            continue
        for dirpath, _, filenames in os.walk(base):
            for fn in filenames:
                if fn.endswith((".py", ".pyc", ".pyo", ".json", ".txt", ".lua", ".toc")):
                    fp = os.path.join(dirpath, fn)
                    py_files.append(fp)
                    if fp not in files:
                        files.append(fp)
    _write(os.path.join(out, "virtual_py_list.json"), json.dumps(py_files, ensure_ascii=False, indent=2))

    for fp in files:
        item = {"path": fp, "exists": os.path.exists(fp), "isfile": os.path.isfile(fp)}
        try:
            if os.path.isfile(fp):
                with open(fp, "rb") as fh:
                    data = fh.read()
                item["size"] = len(data)
                rel = fp.split("Nirvana30\\Nirvana30\\", 1)[-1].replace("\\", "__")
                out_path = os.path.join(src_dir, rel)
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                # write bytes; also utf-8 text copy if decodable
                _write(out_path, data)
                try:
                    text = data.decode("utf-8")
                    _write(out_path + ".txt", text)
                    item["utf8"] = True
                    item["preview"] = text[:200]
                except Exception:
                    item["utf8"] = False
                    item["preview"] = data[:40].hex()
                item["ok"] = True
            else:
                item["ok"] = False
        except Exception as e:
            item["ok"] = False
            item["err"] = repr(e)
        report.append(item)

    _write(os.path.join(out, "virtual_read_report.json"), json.dumps(report, ensure_ascii=False, indent=2))
    _write(os.path.join(out, "virtual_read_done.txt"), "done")
except Exception:
    _write(os.path.join(out, "virtual_read_error.txt"), traceback.format_exc())
