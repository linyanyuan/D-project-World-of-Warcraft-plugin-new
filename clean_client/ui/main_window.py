"""Fluent multi-page main window for clean_client."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMessageBox, QWidget
from qfluentwidgets import FluentIcon, FluentWindow, NavigationItemPosition

from clean_client.capture.backends import create_backend
from clean_client.capture.window import find_wow_hwnd
from clean_client.config.loader import load_json, load_regions_dir
from clean_client.engine.bootstrap import build_engine
from clean_client.engine.loop import EngineLoop
from clean_client.rotation.profile import load_profile
from clean_client.ui.pages import ControlPage, RotationPage, SettingsPage, VisionPage


class _LogBridge(QObject):
    """Marshal engine worker-thread log lines onto the UI thread."""

    message = Signal(str)


class MainWindow(FluentWindow):
    """Side-nav Fluent shell: Control / Rotation / Vision / Settings."""

    def __init__(self, root: Path | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        if root is not None:
            self.root = root
        else:
            from clean_client.paths import package_root

            self.root = package_root()

        self.setWindowTitle("CleanClient — 自动循环客户端")
        self.resize(1120, 740)
        self.setMinimumSize(960, 640)
        self.setObjectName("centralRoot")
        self.setMicaEffectEnabled(False)
        self._apply_window_icon()
        self.navigationInterface.setStyleSheet(
            """
            NavigationInterface {
                background-color: rgba(4, 7, 15, 230);
                border-right: 1px solid rgba(97, 216, 255, 0.18);
            }
            """
        )

        self._cfg: dict[str, Any] = load_json(self.root / "config" / "default.json")
        profile_rel = str(self._cfg.get("profile") or "profiles/unholy_default.json")
        self._profile = load_profile(self.root / profile_rel)
        self._engine: EngineLoop | None = None
        self._live_input_confirmed = False
        self._suppress_dry_run_guard = False
        self._log_bridge = _LogBridge(self)
        self._log_bridge.message.connect(self._append_log)

        self.control_page = ControlPage(self)
        self.rotation_page = RotationPage(self)
        self.vision_page = VisionPage(self)
        self.settings_page = SettingsPage(self)

        # Back-compat aliases used by smoke tests / external callers.
        self.start_btn = self.control_page.start_btn
        self.stop_btn = self.control_page.stop_btn
        self.dry_run_cb = self.control_page.dry_run_cb
        self.prefer_highlighted_cb = self.control_page.prefer_highlighted_cb
        self.capture_combo = self.control_page.capture_combo
        self.tick_spin = self.control_page.tick_spin
        self.hwnd_label = self.control_page.hwnd_label
        self.log_view = self.control_page.log_view

        self.addSubInterface(self.control_page, FluentIcon.PLAY, "控制台")
        self.addSubInterface(self.rotation_page, FluentIcon.LIBRARY, "循环")
        self.addSubInterface(self.vision_page, FluentIcon.VIEW, "识别")
        self.addSubInterface(
            self.settings_page,
            FluentIcon.SETTING,
            "系统设置",
            NavigationItemPosition.BOTTOM,
        )

        self.control_page.start_requested.connect(self._on_start)
        self.control_page.stop_requested.connect(self._on_stop)
        self.vision_page.calibrator_requested.connect(self._on_open_calibrator)
        self.vision_page.preview_requested.connect(self._on_preview)
        self.settings_page.save_btn.clicked.connect(self._on_save_settings)
        self.dry_run_cb.stateChanged.connect(self._on_dry_run_changed)

        self._apply_config_defaults()
        self.rotation_page.set_profile(self._profile)
        self.settings_page.load_from_config(self._cfg)
        self.control_page.set_running(False)
        self._append_log(
            f"已加载配置={self._profile.get('name', profile_rel)!r} "
            f"动作数={len(self._profile.get('actions') or [])}"
        )

    def _apply_window_icon(self) -> None:
        """Load app icon from package assets (works for source and frozen)."""
        candidates = [
            self.root / "assets" / "cleanclient.ico",
            self.root / "assets" / "cleanclient_icon.png",
            Path(__file__).resolve().parent.parent / "assets" / "cleanclient.ico",
            Path(__file__).resolve().parent.parent / "assets" / "cleanclient_icon.png",
        ]
        for path in candidates:
            if path.is_file():
                self.setWindowIcon(QIcon(str(path)))
                return

    def _apply_config_defaults(self) -> None:
        # Never treat a loaded dry_run=false as live-confirmed.
        self._live_input_confirmed = False
        self._suppress_dry_run_guard = True
        try:
            self.dry_run_cb.setChecked(bool(self._cfg.get("dry_run", True)))
        finally:
            self._suppress_dry_run_guard = False
        self.prefer_highlighted_cb.setChecked(
            bool(self._cfg.get("prefer_highlighted", True))
        )
        mode = str(self._cfg.get("capture_mode") or "null")
        self.control_page.set_capture_mode(mode)
        try:
            tick = int(self._cfg.get("tick_ms", 30))
        except (TypeError, ValueError):
            tick = 30
        self.tick_spin.setValue(max(1, tick))

        vision_mode = str(self._cfg.get("vision_mode") or "mock").lower()
        self.vision_page.set_vision_mode(vision_mode)

        regions_dir = str(self._cfg.get("regions_dir") or "").strip()
        if regions_dir:
            path = Path(regions_dir)
            if not path.is_absolute():
                path = self.root / path
            self.vision_page.set_regions_dir(path)
        else:
            regions_default = self.root / "regions"
            if regions_default.is_dir():
                self.vision_page.set_regions_dir(regions_default)

    def _collect_settings(self) -> dict[str, Any]:
        """Merge config + live UI controls into a settings dict for build_engine."""
        settings = dict(self._cfg)
        settings["root"] = str(self.root)
        settings["dry_run"] = self.dry_run_cb.isChecked()
        settings["prefer_highlighted"] = self.prefer_highlighted_cb.isChecked()
        settings["capture_mode"] = self.control_page.capture_mode()
        settings["tick_ms"] = self.tick_spin.value()
        settings["vision_mode"] = self.vision_page.vision_mode()
        regions = self.vision_page.regions_dir()
        settings["regions_dir"] = str(regions) if regions is not None else ""
        settings.update(self.settings_page.values())
        return settings

    def _confirm_live_input(self) -> bool:
        reply = QMessageBox.question(
            self,
            "确认关闭只记日志？",
            "关闭后将向系统发送真实按键，可能影响游戏操作。\n"
            "请确认魔兽窗口在前台，并已理解风险。\n\n"
            "是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    @Slot(int)
    def _on_dry_run_changed(self, _state: int = 0) -> None:
        if self._suppress_dry_run_guard:
            return
        if self.dry_run_cb.isChecked():
            self._live_input_confirmed = False
            return
        if self._confirm_live_input():
            self._live_input_confirmed = True
            self._append_log("已确认：允许真实按键（请谨慎使用）")
            return
        self._live_input_confirmed = False
        self._suppress_dry_run_guard = True
        try:
            self.dry_run_cb.setChecked(True)
        finally:
            self._suppress_dry_run_guard = False
        self._append_log("已取消：保持只记日志")

    def _normalize_vision_mode(self, mode: str) -> str:
        key = (mode or "mock").strip().lower()
        if key in {"pixel", "protocol"}:
            return "pixel"
        return "mock"

    def _validate_pixel_start(
        self, settings: dict[str, Any], hwnd: int | None
    ) -> str | None:
        vision_mode = self._normalize_vision_mode(
            str(settings.get("vision_mode") or "mock")
        )
        if vision_mode != "pixel":
            return None

        capture = str(settings.get("capture_mode") or "null").strip()
        capture_backend = self._map_capture_for_calibrator(capture)
        if capture_backend == "null":
            return (
                "像素协议需要真实截屏方式（方式一 / 方式二 / 方式三），"
                "不能使用空（测试）"
            )

        regions_dir = str(settings.get("regions_dir") or "").strip()
        if not regions_dir:
            return "像素协议需要先选择并保存区域目录（必须包含 Skill）"

        path = Path(regions_dir)
        if not path.is_absolute():
            path = self.root / path
        try:
            regions = load_regions_dir(path)
        except ValueError as exc:
            return f"区域目录读取失败: {exc}"
        if "Skill" not in regions:
            return f"区域目录缺少 Skill（技能）区域文件: {path}"

        if capture_backend == "printwindow" and hwnd is None:
            return "方式一（PrintWindow）需要先找到魔兽窗口，请确认游戏已打开"

        settings["_loaded_region_keys"] = ",".join(sorted(regions.keys()))
        return None

    @Slot()
    def _on_start(self) -> None:
        if self._engine is not None:
            return

        settings = self._collect_settings()
        settings["vision_mode"] = self._normalize_vision_mode(
            str(settings.get("vision_mode") or "mock")
        )
        mode = str(settings.get("capture_mode") or "null")
        keywords = tuple(settings.get("window_keywords") or ())
        hwnd: int | None = None
        try:
            hwnd = find_wow_hwnd(keywords)
        except (RuntimeError, OSError, TypeError, ValueError) as exc:
            self._append_log(f"查找游戏窗口已跳过: {exc}")
        self.hwnd_label.setText(f"窗口句柄: {hwnd if hwnd is not None else '—'}")

        error = self._validate_pixel_start(settings, hwnd)
        if error is not None:
            self._append_log(f"无法启动: {error}")
            self.vision_page.set_status(error)
            return

        dry_run = bool(settings.get("dry_run", True))
        if not dry_run and not self._live_input_confirmed:
            if not self._confirm_live_input():
                self._append_log("无法启动: 未确认真实按键，请勾选只记日志或确认后重试")
                self._suppress_dry_run_guard = True
                try:
                    self.dry_run_cb.setChecked(True)
                finally:
                    self._suppress_dry_run_guard = False
                return
            self._live_input_confirmed = True

        dry_run = bool(self.dry_run_cb.isChecked())
        settings["dry_run"] = dry_run
        press = None
        if not dry_run:
            from clean_client.input.sendinput import tap_key

            press = tap_key

        backend = create_backend(mode)

        def grab() -> Any:
            return backend.grab(hwnd)

        def on_log(message: str) -> None:
            self._log_bridge.message.emit(message)

        vision_mode = str(settings.get("vision_mode") or "mock")
        region_keys = str(settings.pop("_loaded_region_keys", "") or "")
        self._engine = build_engine(settings, on_log=on_log, press=press, grab=grab)
        self.control_page.set_running(True)
        extra = f" 区域={region_keys}" if region_keys else ""
        self._append_log(
            f"已启动 截屏={mode} 只记日志={dry_run} "
            f"周期ms={settings.get('tick_ms')} "
            f"识别={vision_mode} 窗口句柄={hwnd}{extra}"
        )
        self._engine.start()

    @Slot()
    def _on_stop(self) -> None:
        engine = self._engine
        self._engine = None
        if engine is not None:
            engine.stop()
            self._append_log("已停止")
        self.control_page.set_running(False)

    @staticmethod
    def _map_capture_for_calibrator(capture: str) -> str:
        """Map UI capture labels to calibrator/create_backend keys."""
        raw = (capture or "null").strip()
        key = raw.lower()
        mapping = {
            "null": "null",
            "mock": "null",
            "test": "null",
            "空": "null",
            "空（测试）": "null",
            "空（测试·不截屏）": "null",
            "方式一": "printwindow",
            "1": "printwindow",
            "printwindow": "printwindow",
            "方式二": "mss",
            "2": "mss",
            "mss": "mss",
            "方式三": "dxcam",
            "3": "dxcam",
            "dxcam": "dxcam",
        }
        if key in mapping:
            return mapping[key]
        if raw in mapping:
            return mapping[raw]
        if "printwindow" in key or raw.startswith("方式一"):
            return "printwindow"
        if "mss" in key or raw.startswith("方式二"):
            return "mss"
        if "dxcam" in key or "dxgi" in key or raw.startswith("方式三"):
            return "dxcam"
        if raw.startswith("空"):
            return "null"
        return "null"

    def _on_regions_saved(self, directory: Path) -> None:
        path = Path(directory)
        self.vision_page.set_regions_dir(path)
        self._cfg["regions_dir"] = str(path)
        self.vision_page.set_status(f"已载入区域目录: {path}")
        self._append_log(f"标定已保存并载入区域目录: {path}")
        self._persist_config(note_prefix="标定目录已写入")

    @Slot()
    def _on_preview(self) -> None:
        """Grab one frame for the Recognition page preview."""
        capture = self.control_page.capture_mode()
        backend_key = self._map_capture_for_calibrator(capture)
        keywords = tuple(self.settings_page.values().get("window_keywords") or ())
        hwnd: int | None = None
        try:
            hwnd = find_wow_hwnd(keywords)
        except (RuntimeError, OSError, TypeError, ValueError):
            hwnd = None

        try:
            backend = create_backend(capture)
            frame = backend.grab(hwnd)
        except Exception as exc:  # noqa: BLE001
            self.vision_page.show_preview(
                None,
                capture_label=capture,
                capture_backend=backend_key,
                hwnd=hwnd,
                error=str(exc),
            )
            self._append_log(f"预览失败: {exc}")
            return

        self.vision_page.show_preview(
            frame,
            capture_label=capture,
            capture_backend=backend_key,
            hwnd=hwnd,
        )

    @Slot()
    def _on_open_calibrator(self) -> None:
        """Open region calibrator in-process (works for frozen exe too)."""
        regions_dir = self.vision_page.regions_dir()
        capture = self.control_page.capture_mode()
        output = regions_dir if regions_dir is not None else (self.root / "regions")
        capture_arg = self._map_capture_for_calibrator(capture)

        try:
            from clean_client.ui.calibrator import run_calibrator

            run_calibrator(
                output_dir=output,
                capture_mode=capture_arg,
                on_saved=self._on_regions_saved,
            )
            self.vision_page.set_status(f"标定器已打开 → {output}")
            self._append_log(f"已打开标定器 截屏={capture_arg} 目录={output}")
        except Exception as exc:  # noqa: BLE001
            self.vision_page.set_status(f"标定器打开失败: {exc}")
            self._append_log(f"标定器错误: {exc}")

    def _persist_config(self, *, note_prefix: str | None = None) -> None:
        values = self.settings_page.values()
        self._cfg.update(values)
        self._cfg["dry_run"] = self.dry_run_cb.isChecked()
        self._cfg["prefer_highlighted"] = self.prefer_highlighted_cb.isChecked()
        self._cfg["capture_mode"] = self.control_page.capture_mode()
        self._cfg["tick_ms"] = self.tick_spin.value()
        self._cfg["vision_mode"] = self.vision_page.vision_mode()
        regions = self.vision_page.regions_dir()
        self._cfg["regions_dir"] = str(regions) if regions is not None else ""

        to_write = {k: v for k, v in self._cfg.items() if k != "root"}
        path = self.root / "config" / "default.json"
        try:
            path.write_text(
                json.dumps(to_write, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            prefix = note_prefix or "已保存到"
            note = (
                f"{prefix} {path.name}: 关键字={values['window_keywords']}, "
                f"区域目录={self._cfg.get('regions_dir') or '（空）'}"
            )
            self.settings_page.set_note(note)
            self._append_log(f"设置已保存 → {path}")
        except OSError as exc:
            self.settings_page.set_note(f"已应用到内存，但写入失败: {exc}")
            self._append_log(f"设置保存失败: {exc}")

    @Slot()
    def _on_save_settings(self) -> None:
        self._persist_config()

    @Slot(str)
    def _append_log(self, message: str) -> None:
        self.control_page.append_log(message)

    def closeEvent(self, event) -> None:  # noqa: N802
        self._on_stop()
        super().closeEvent(event)
