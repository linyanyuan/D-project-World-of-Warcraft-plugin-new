"""Offscreen smoke test for the Fluent multi-page main window."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")
pytest.importorskip("qfluentwidgets")

from PySide6.QtWidgets import QApplication

from clean_client.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    existing = QApplication.instance()
    if isinstance(existing, QApplication):
        return existing
    return QApplication([])


def test_main_window_constructs(qapp: QApplication) -> None:
    win = MainWindow()
    try:
        title = win.windowTitle()
        assert (
            ("CleanClient" in title)
            or ("clean_client" in title)
            or ("自动循环" in title)
        )
        assert win.dry_run_cb.isChecked()
        assert win.prefer_highlighted_cb.isChecked()
        assert win.control_page.capture_mode() == "null"
        assert win.capture_combo.currentText().startswith("空（测试")
        assert win.tick_spin.value() == 30
        assert win.start_btn.isEnabled()
        assert not win.stop_btn.isEnabled()
        assert "unholy_default" in win.log_view.toPlainText()
        assert win.control_page is not None
        assert win.rotation_page is not None
        assert win.vision_page is not None
        assert win.settings_page is not None
        assert win.vision_page.vision_mode() == "mock"
        assert "unholy_default" in win.rotation_page.profile_label.text()
    finally:
        win.close()


def test_collect_settings_includes_vision(qapp: QApplication) -> None:
    win = MainWindow()
    try:
        win.vision_page.set_vision_mode("pixel")
        win.vision_page.set_regions_dir("C:/tmp/regions")
        settings = win._collect_settings()
        assert settings["vision_mode"] == "pixel"
        assert settings["regions_dir"].replace("\\", "/").endswith("tmp/regions")
        assert settings["dry_run"]
    finally:
        win.close()


def test_dry_run_uncheck_requires_confirm(qapp: QApplication, monkeypatch) -> None:
    win = MainWindow()
    try:
        from PySide6.QtWidgets import QMessageBox

        monkeypatch.setattr(
            MainWindow,
            "_confirm_live_input",
            lambda self: False,
        )
        win.dry_run_cb.setChecked(False)
        assert win.dry_run_cb.isChecked()
        assert win._live_input_confirmed is False

        monkeypatch.setattr(MainWindow, "_confirm_live_input", lambda self: True)
        win.dry_run_cb.setChecked(False)
        assert not win.dry_run_cb.isChecked()
        assert win._live_input_confirmed is True
        _ = QMessageBox  # keep import used for type presence in env
    finally:
        win.close()


def test_pixel_start_rejects_null_capture(qapp: QApplication, tmp_path) -> None:
    win = MainWindow()
    try:
        skill = tmp_path / "skill_region.txt"
        skill.write_text("10 10 100 40\n", encoding="utf-8")
        win.vision_page.set_vision_mode("pixel")
        win.vision_page.set_regions_dir(tmp_path)
        win.control_page.set_capture_mode("null")
        win._on_start()
        assert win._engine is None
        assert "无法启动" in win.log_view.toPlainText()
        assert "真实截屏" in win.log_view.toPlainText()
    finally:
        win.close()


def test_pixel_start_rejects_missing_skill(qapp: QApplication, tmp_path) -> None:
    win = MainWindow()
    try:
        win.vision_page.set_vision_mode("pixel")
        win.vision_page.set_regions_dir(tmp_path)
        win.control_page.set_capture_mode("方式二")
        win._on_start()
        assert win._engine is None
        text = win.log_view.toPlainText()
        assert "无法启动" in text
        assert "Skill" in text
    finally:
        win.close()


def test_regions_saved_updates_ui(qapp: QApplication, tmp_path) -> None:
    win = MainWindow()
    try:
        target = tmp_path / "regions_out"
        target.mkdir()
        (target / "skill_region.txt").write_text("1 2 3 4\n", encoding="utf-8")
        win._on_regions_saved(target)
        assert win.vision_page.regions_dir() == target
        assert "已载入区域目录" in win.vision_page.status_label.text()
    finally:
        win.close()
