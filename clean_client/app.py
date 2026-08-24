"""Entry point for the clean Auto-Unholy client."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from clean_client.capture.backends import (
    create_backend,  # pyright: ignore[reportMissingImports]
)
from clean_client.capture.window import (
    find_wow_hwnd,  # pyright: ignore[reportMissingImports]
)
from clean_client.engine.loop import EngineLoop  # pyright: ignore[reportMissingImports]
from clean_client.rotation.profile import (
    load_profile,  # pyright: ignore[reportMissingImports]
)
from clean_client.vision.mock import MockVision  # pyright: ignore[reportMissingImports]


def _load_config(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"failed to load config {path}: {exc}") from exc


def _as_int(value: object, default: int) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def cli_main() -> int:
    """Headless dry-run stub (Ctrl+C to stop)."""
    from clean_client.paths import package_root

    root = package_root()
    cfg = _load_config(root / "config" / "default.json")
    profile = load_profile(root / cfg["profile"])
    backend = create_backend(str(cfg.get("capture_mode", "null")))
    hwnd = None
    try:
        hwnd = find_wow_hwnd(tuple(cfg.get("window_keywords") or ()))
    except (RuntimeError, OSError, TypeError, ValueError) as exc:
        print(f"查找游戏窗口已跳过: {exc}")

    vision = MockVision()

    def on_log(message: str) -> None:
        print(message)

    def grab():
        return backend.grab(hwnd)

    engine = EngineLoop(
        grab=grab,
        read_state=vision.read_state,
        actions=list(profile.get("actions") or []),
        on_log=on_log,
        tick_ms=_as_int(cfg.get("tick_ms"), 30),
        dry_run=bool(cfg.get("dry_run", True)),
        prefer_highlighted=bool(cfg.get("prefer_highlighted", True)),
        cd_ready_window_ms=_as_int(cfg.get("cd_ready_window_ms"), 30),
    )
    print("CleanClient 已启动（模拟识别，只记日志）。按 Ctrl+C 结束。")
    print(f"窗口句柄={hwnd} 截屏={cfg.get('capture_mode')}")
    engine.start()
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        engine.stop()
        print("已停止")
    return 0


def ui_main() -> int:
    """Launch the Fluent multi-page main window."""
    import os
    from pathlib import Path

    # Frozen builds: point Qt at bundled plugins before QApplication starts
    if getattr(sys, "frozen", False):
        meipass = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        plugin_candidates = [
            meipass / "PySide6" / "plugins",
            meipass / "plugins",
            Path(sys.executable).parent / "_internal" / "PySide6" / "plugins",
        ]
        for candidate in plugin_candidates:
            if (candidate / "platforms").exists():
                os.environ["QT_PLUGIN_PATH"] = str(candidate)
                break
        os.environ.setdefault("QT_OPENGL", "software")

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QMessageBox

    from clean_client.paths import package_root
    from clean_client.ui.main_window import MainWindow
    from clean_client.ui.theme import apply_app_theme

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    apply_app_theme()

    try:
        root = package_root()
        print(f"package_root={root}", flush=True)
        from PySide6.QtGui import QIcon
        from qfluentwidgets import FluentIcon, SplashScreen

        for icon_name in ("cleanclient.ico", "cleanclient_icon.png"):
            icon_path = root / "assets" / icon_name
            if icon_path.is_file():
                app.setWindowIcon(QIcon(str(icon_path)))
                break

        window = MainWindow(root=root)
        # SplashScreen has no setTitle/setSubTitle in current qfluentwidgets.
        splash = SplashScreen(FluentIcon.GAME, window)
        splash.setWindowTitle("CleanClient — 自动循环客户端")
        window.show()
        splash.show()
        app.processEvents()
        splash.finish()
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(None, "CleanClient 启动失败", str(exc))
        print(f"界面初始化错误: {exc}", file=sys.stderr)
        return 1

    window.raise_()
    window.activateWindow()
    try:
        return int(app.exec())
    except Exception as exc:  # noqa: BLE001
        print(f"界面退出错误: {exc}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CleanClient 自动循环客户端")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="以命令行模式运行（无界面，只记日志）",
    )
    args = parser.parse_args(argv)
    if args.cli:
        return cli_main()
    return ui_main()


if __name__ == "__main__":
    sys.exit(main())
