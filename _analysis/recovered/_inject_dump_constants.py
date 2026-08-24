import json
import os
import sys
import traceback

out = r"D:\project\World of Warcraft plugin new\_analysis\recovered"


def _write(path: str, text: str) -> None:
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    except OSError as exc:
        sys.stderr.write(f"write failed {path}: {exc}\n")


def _safe(obj):
    try:
        json.dumps(obj)
        return obj
    except Exception:
        return repr(obj)


try:
    targets = {
        "addon_update": [
            "BASE_SITE_URL",
            "ADDON_API_BASE",
            "PLUGIN_VERSION_URL",
        ],
        "update_checker": [
            "SOFTWARE_PACKAGE_NAME",
            "FALLBACK_VERSION",
        ],
        "fluent_ui.data_loader": [
            "CLASS_NAME_MAPPING",
        ],
        "fluent_ui.prototype_window": [
            "ADDON_PACKAGES",
            "CLASS_SPECS",
            "SPEC_NAMES",
            "LOGIN_URL_BASE",
        ],
        "fluent_ui.void_protocol_theme": [
            "BG_VOID",
            "BG_DEEP",
            "BG_PANEL",
            "CYAN_SIGNAL",
            "CYAN_BRIGHT",
            "BLUE_ACCENT",
            "ALERT_RED",
            "ALERT_AMBER",
            "TEXT_WHITE",
            "TEXT_PRIMARY",
            "TEXT_SECONDARY",
            "TEXT_MUTED",
            "BORDER_TRACE",
        ],
        "skill_conditions": [
            "ConditionType",
            "TargetType",
            "ComparisonOperator",
            "AuraConditionType",
            "ResourceType",
            "PlayerInfoField",
            "TargetInfoField",
        ],
    }
    result = {}
    for mod_name, attrs in targets.items():
        mod = sys.modules.get(mod_name)
        bucket = {"present": mod is not None, "values": {}}
        if mod is not None:
            for attr in attrs:
                if not hasattr(mod, attr):
                    bucket["values"][attr] = None
                    continue
                val = getattr(mod, attr)
                # Enum-like
                if hasattr(val, "__members__"):
                    bucket["values"][attr] = {
                        k: _safe(v.value) for k, v in val.__members__.items()
                    }
                else:
                    bucket["values"][attr] = _safe(val)
            # Also collect FluentPrototypeWindow method names if class exists
            cls = getattr(mod, "FluentPrototypeWindow", None)
            if cls is not None:
                methods = [n for n in dir(cls) if not n.startswith("__")]
                bucket["FluentPrototypeWindow_methods"] = methods
        result[mod_name] = bucket

    # prototype_window: dump class methods for main window and pages
    pw = sys.modules.get("fluent_ui.prototype_window")
    if pw:
        class_methods = {}
        for cname in [
            "FluentPrototypeWindow",
            "ControlPage",
            "DataRecogPage",
            "DebugPage",
            "BackgroundSettingsPage",
            "FluentSkillCycleDialog",
            "FluentLoginDialog",
            "KeyInfoNavWidget",
        ]:
            cls = getattr(pw, cname, None)
            if cls is None:
                continue
            class_methods[cname] = [n for n in dir(cls) if not n.startswith("__")]
        result["prototype_classes"] = class_methods

    fw = sys.modules.get("fluent_ui.fluent_windows")
    if fw:
        fw_classes = {}
        for cname in [
            "FluentConditionEditorDialog",
            "FluentConditionManagerDialog",
            "FluentOnlineCycleDialog",
            "ConditionType",
        ]:
            cls = getattr(fw, cname, None)
            if cls is None:
                continue
            fw_classes[cname] = [n for n in dir(cls) if not n.startswith("__")]
        result["fluent_windows_classes"] = fw_classes

    _write(
        os.path.join(out, "constants.json"),
        json.dumps(result, ensure_ascii=False, indent=2),
    )
    _write(os.path.join(out, "constants_done.txt"), "done")
except Exception:
    _write(os.path.join(out, "constants_error.txt"), traceback.format_exc())
