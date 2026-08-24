"""Assemble an :class:`~clean_client.engine.loop.EngineLoop` from settings.

Public API
----------
build_engine(settings, on_log=None, press=None, *, grab=None, regions=None)
    -> EngineLoop

Settings keys (see ``config/default.json``)
------------------------------------------
- ``vision_mode``: ``"mock"`` | ``"pixel"`` | ``"protocol"``
- ``regions_dir``: folder with ``*_region.txt`` (empty string = no regions)
- ``row_height``, ``bindings_row_index``: pixel-protocol geometry
- ``capture_mode``, ``tick_ms``, ``dry_run``, ``prefer_highlighted``
- ``cd_ready_window_ms``
- ``profile``: relative/absolute path to rotation JSON
- ``window_keywords``: list used by :func:`find_wow_hwnd`
- ``root``: optional base path for relative ``profile`` / ``regions_dir``

The UI agent should call this instead of wiring capture/vision/engine by hand.
Login / card-key auth remains deferred.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from clean_client.capture.backends import (
    create_backend,  # pyright: ignore[reportMissingImports]
)
from clean_client.capture.window import (
    find_wow_hwnd,  # pyright: ignore[reportMissingImports]
)
from clean_client.config.loader import (  # pyright: ignore[reportMissingImports]
    Region,
    load_regions_dir,
)
from clean_client.engine.loop import EngineLoop  # pyright: ignore[reportMissingImports]
from clean_client.rotation.profile import (
    load_profile,  # pyright: ignore[reportMissingImports]
)
from clean_client.vision.factory import (
    create_vision,  # pyright: ignore[reportMissingImports]
)


def _as_int(value: object, default: int) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _resolve_path(raw: str | Path, root: Path | None) -> Path:
    path = Path(raw)
    if path.is_absolute() or root is None:
        return path
    return root / path


def load_settings_regions(
    settings: dict[str, Any],
    *,
    regions: dict[str, Region] | None = None,
    root: Path | None = None,
) -> dict[str, Region]:
    """Return explicit ``regions`` or load from ``settings['regions_dir']``."""
    if regions is not None:
        return regions
    regions_dir = str(settings.get("regions_dir") or "").strip()
    if not regions_dir:
        return {}
    return load_regions_dir(_resolve_path(regions_dir, root))


def build_engine(
    settings: dict[str, Any],
    on_log: Callable[[str], None] | None = None,
    press: Callable[[str], None] | None = None,
    *,
    grab: Callable[[], Any] | None = None,
    regions: dict[str, Region] | None = None,
) -> EngineLoop:
    """Build a fully wired :class:`EngineLoop` from a config dict.

    Parameters
    ----------
    settings:
        Config mapping (typically ``config/default.json`` plus UI overrides).
    on_log:
        Optional log sink; defaults to a no-op.
    press:
        Optional key press callback used when ``dry_run`` is false.
    grab:
        Optional frame provider. When omitted, a capture backend is created from
        ``capture_mode`` and bound to the first matching WoW hwnd.
    regions:
        Optional in-memory region map. When omitted, ``regions_dir`` is loaded.
    """
    root_raw = settings.get("root")
    root = Path(root_raw) if root_raw else None
    if root is None:
        try:
            from clean_client.paths import package_root

            root = package_root()
        except Exception:  # noqa: BLE001
            root = Path.cwd()

    profile_rel = str(settings.get("profile") or "profiles/unholy_default.json")
    profile = load_profile(_resolve_path(profile_rel, root))
    actions = list(profile.get("actions") or [])

    loaded_regions = load_settings_regions(settings, regions=regions, root=root)
    vision = create_vision(
        str(settings.get("vision_mode") or "mock"),
        loaded_regions,
        row_height=_as_int(settings.get("row_height"), 1),
        bindings_row_index=_as_int(settings.get("bindings_row_index"), 2),
        default_key=str(settings.get("default_key") or "1"),
    )

    if grab is None:
        backend = create_backend(str(settings.get("capture_mode") or "null"))
        hwnd: int | None = None
        try:
            hwnd = find_wow_hwnd(tuple(settings.get("window_keywords") or ()))
        except (RuntimeError, OSError, TypeError, ValueError) as exc:
            hwnd = None
            if on_log is not None:
                on_log(f"window find skipped: {exc}")

        def grab() -> Any:
            return backend.grab(hwnd)

    dry_run = bool(settings.get("dry_run", True))
    return EngineLoop(
        grab=grab,
        read_state=vision.read_state,
        actions=actions,
        on_log=on_log,
        press=press,
        tick_ms=_as_int(settings.get("tick_ms"), 30),
        dry_run=dry_run,
        prefer_highlighted=bool(settings.get("prefer_highlighted", True)),
        cd_ready_window_ms=_as_int(settings.get("cd_ready_window_ms"), 30),
    )
