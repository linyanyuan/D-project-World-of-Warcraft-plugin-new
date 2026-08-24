import dis
import json
import os
import sys
import traceback
import types

out = r"D:\project\World of Warcraft plugin new\_analysis\recovered"


def _write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


try:
    names = [
        "fluent_ui",
        "fluent_ui.prototype_window",
        "fluent_ui.fluent_windows",
        "fluent_ui.data_loader",
        "fluent_ui.void_protocol_theme",
        "addon_update",
        "skill_conditions",
        "skill_cycle_config",
        "update_checker",
        "window_capture",
        "AutoPlayer",
    ]
    report = {"markers": {}, "modules": {}}
    # Nuitka / freeze markers
    for k, v in list(sys.__dict__.items()):
        if any(s in k.lower() for s in ("nuitka", "frozen", "pyoxidizer", "cx_freeze", "pyinstaller")):
            report["markers"][k] = repr(v)[:200]
    for k in (
        "__nuitka_binary_dir__",
        "__compiled__",
        "frozen",
        "_MEIPASS",
    ):
        report["markers"][k] = getattr(sys, k, "MISSING")
    report["markers"]["executable"] = sys.executable
    report["markers"]["prefix"] = sys.prefix
    report["markers"]["version"] = sys.version

    decomp_dir = os.path.join(out, "disasm")
    os.makedirs(decomp_dir, exist_ok=True)

    for name in names:
        mod = sys.modules.get(name)
        info = {"present": mod is not None}
        if mod is None:
            report["modules"][name] = info
            continue
        info["type"] = type(mod).__name__
        info["type_repr"] = repr(type(mod))
        info["file"] = getattr(mod, "__file__", None)
        info["loader"] = repr(getattr(mod, "__loader__", None))[:300]
        info["spec"] = repr(getattr(mod, "__spec__", None))[:300]
        info["dict_keys"] = [k for k in getattr(mod, "__dict__", {}).keys()][:120]
        # find callables with __code__
        coded = []
        native = []
        for attr in info["dict_keys"]:
            try:
                obj = getattr(mod, attr)
            except Exception:
                continue
            if isinstance(obj, type):
                # class methods
                for mname, member in list(obj.__dict__.items())[:80]:
                    func = member
                    if isinstance(member, (staticmethod, classmethod)):
                        func = member.__func__
                    if isinstance(func, types.FunctionType) and hasattr(func, "__code__"):
                        coded.append(f"{attr}.{mname}")
                        try:
                            path = os.path.join(decomp_dir, f"{name.replace('.','_')}__{attr}__{mname}.dis.txt")
                            with open(path, "w", encoding="utf-8") as fh:
                                fh.write(f"# {name}.{attr}.{mname}\n")
                                fh.write(f"co_filename={func.__code__.co_filename}\n")
                                fh.write(f"co_names={func.__code__.co_names}\n")
                                fh.write(f"co_varnames={func.__code__.co_varnames}\n")
                                fh.write(f"co_consts={[c for c in func.__code__.co_consts if not hasattr(c,'co_code')][:50]!r}\n")
                                dis.dis(func, file=fh)
                        except Exception as e:
                            native.append(f"{attr}.{mname}:disfail:{e!r}")
                    elif callable(member):
                        native.append(f"{attr}.{mname}:{type(member)}")
            elif isinstance(obj, types.FunctionType) and hasattr(obj, "__code__"):
                coded.append(attr)
                try:
                    path = os.path.join(decomp_dir, f"{name.replace('.','_')}__{attr}.dis.txt")
                    with open(path, "w", encoding="utf-8") as fh:
                        fh.write(f"# {name}.{attr}\n")
                        fh.write(f"co_filename={obj.__code__.co_filename}\n")
                        fh.write(f"co_names={obj.__code__.co_names}\n")
                        fh.write(f"co_varnames={obj.__code__.co_varnames}\n")
                        fh.write(
                            f"co_consts={[c for c in obj.__code__.co_consts if not hasattr(c,'co_code')][:80]!r}\n"
                        )
                        dis.dis(obj, file=fh)
                except Exception as e:
                    native.append(f"{attr}:disfail:{e!r}")
            elif callable(obj):
                native.append(f"{attr}:{type(obj)}")
        info["coded_funcs"] = coded[:100]
        info["native_or_other"] = [str(x) for x in native[:100]]
        report["modules"][name] = info

    _write(os.path.join(out, "module_probe.json"), json.dumps(report, ensure_ascii=False, indent=2))
    _write(os.path.join(out, "module_probe_done.txt"), "done")
except Exception:
    _write(os.path.join(out, "module_probe_error.txt"), traceback.format_exc())
