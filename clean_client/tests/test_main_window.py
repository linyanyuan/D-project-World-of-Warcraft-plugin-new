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
        win.vision_page.regions_edit.setText("C:/tmp/regions")
        settings = win._collect_settings()
        assert settings["vision_mode"] == "pixel"
        assert settings["regions_dir"].replace("\\", "/").endswith("tmp/regions")
        assert settings["dry_run"]
    finally:
        win.close()
