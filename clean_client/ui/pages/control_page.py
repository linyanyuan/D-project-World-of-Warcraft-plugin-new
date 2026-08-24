"""控制页：启停、干跑、截屏、周期、日志。"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QVBoxLayout
from qfluentwidgets import (
    BodyLabel,
    CheckBox,
    ComboBox,
    IndeterminateProgressRing,
    PlainTextEdit,
    PrimaryPushButton,
    PushButton,
    SpinBox,
    StrongBodyLabel,
)

from clean_client.ui.theme import (
    ALERT,
    CYAN,
    OK,
    TEXT_MUTED,
    add_page_header,
    make_card,
    section_label,
)
from clean_client.ui.widgets.void_page import VoidPage

# (界面文案, 内部值) — 内部值交给 create_backend / 配置文件
# 方式一 PrintWindow / 方式二 MSS / 方式三 DXGI(dxcam)
CAPTURE_CHOICES: tuple[tuple[str, str], ...] = (
    ("空（测试·不截屏）", "null"),
    ("方式一 · 窗口打印（PrintWindow）", "方式一"),
    ("方式二 · 屏幕截取（MSS）", "方式二"),
    ("方式三 · 高速复制（DXGI）", "方式三"),
)


class ControlPage(VoidPage):
    """引擎控制与实时日志。"""

    start_requested = Signal()
    stop_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("controlPage")
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 22)
        root.setSpacing(14)

        add_page_header(
            root,
            self,
            "控制台",
            "启停引擎 · 截屏通道 · 实时日志（默认只记日志、不按键）",
            badge="安全模式",
        )

        card, card_layout = make_card(self)
        card_layout.addWidget(section_label("引擎连接", card))

        title_row = QHBoxLayout()
        title_row.addWidget(StrongBodyLabel("运行状态", card))
        title_row.addStretch(1)
        self.hwnd_label = BodyLabel("窗口句柄: —", card)
        self.hwnd_label.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        title_row.addWidget(self.hwnd_label)
        card_layout.addLayout(title_row)

        status_row = QHBoxLayout()
        self.ring = IndeterminateProgressRing(card)
        self.ring.setFixedSize(28, 28)
        self.ring.setStrokeWidth(3)
        self.ring.hide()
        status_row.addWidget(self.ring)
        self.status_pill = BodyLabel("● 待机", card)
        self.status_pill.setStyleSheet(
            f"color: {ALERT}; font-weight: 700; letter-spacing: 1px; background: transparent;"
        )
        status_row.addWidget(self.status_pill)
        status_row.addStretch(1)
        card_layout.addLayout(status_row)

        btn_row = QHBoxLayout()
        self.start_btn = PrimaryPushButton("▶  启动", card)
        self.stop_btn = PushButton("■  停止", card)
        self.start_btn.setMinimumHeight(42)
        self.stop_btn.setMinimumHeight(42)
        self.start_btn.setMinimumWidth(130)
        self.stop_btn.setMinimumWidth(130)
        self.start_btn.clicked.connect(self.start_requested.emit)
        self.stop_btn.clicked.connect(self.stop_requested.emit)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        btn_row.addStretch(1)
        card_layout.addLayout(btn_row)

        card_layout.addWidget(section_label("运行选项", card))
        opts = QHBoxLayout()
        self.dry_run_cb = CheckBox("只记日志，不按键", card)
        self.prefer_highlighted_cb = CheckBox("优先高亮技能", card)
        opts.addWidget(self.dry_run_cb)
        opts.addWidget(self.prefer_highlighted_cb)
        opts.addStretch(1)
        card_layout.addLayout(opts)

        capture_row = QHBoxLayout()
        capture_row.addWidget(BodyLabel("截屏方式", card))
        self.capture_combo = ComboBox(card)
        self.capture_combo.addItems([label for label, _ in CAPTURE_CHOICES])
        self.capture_combo.setMinimumWidth(260)
        capture_row.addWidget(self.capture_combo)
        capture_row.addSpacing(16)
        capture_row.addWidget(BodyLabel("周期(ms)", card))
        self.tick_spin = SpinBox(card)
        self.tick_spin.setRange(1, 5000)
        self.tick_spin.setSingleStep(5)
        capture_row.addWidget(self.tick_spin)
        capture_row.addStretch(1)
        card_layout.addLayout(capture_row)

        root.addWidget(card)

        log_card, log_layout = make_card(self)
        log_layout.addWidget(section_label("运行日志", log_card))
        self.log_view = PlainTextEdit(log_card)
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("等待引擎输出…")
        self.log_view.setMinimumHeight(260)
        self.log_view.setStyleSheet(
            f"""
            PlainTextEdit {{
                background: rgba(4, 7, 15, 0.92);
                border: 1px solid rgba(97, 216, 255, 0.18);
                border-radius: 10px;
                color: {CYAN};
                font-family: Consolas, 'Cascadia Mono', monospace;
                font-size: 12px;
                padding: 10px;
            }}
            """
        )
        self.log_view.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        log_layout.addWidget(self.log_view)
        root.addWidget(log_card, stretch=1)

    def capture_mode(self) -> str:
        label = self.capture_combo.currentText()
        for ui_label, mode in CAPTURE_CHOICES:
            if ui_label == label:
                return mode
        return "null"

    def set_capture_mode(self, mode: str) -> None:
        raw = (mode or "null").strip()
        key = raw.lower()
        aliases = {
            "null": "null",
            "mock": "null",
            "test": "null",
            "空": "null",
            "空（测试）": "null",
            "空（测试·不截屏）": "null",
            "方式一": "方式一",
            "方式一 · 窗口打印（printwindow）": "方式一",
            "方式一 · 窗口打印（PrintWindow）": "方式一",
            "1": "方式一",
            "printwindow": "方式一",
            "方式二": "方式二",
            "方式二 · 屏幕截取（mss）": "方式二",
            "方式二 · 屏幕截取（MSS）": "方式二",
            "2": "方式二",
            "mss": "方式二",
            "方式三": "方式三",
            "方式三 · 高速复制（dxgi）": "方式三",
            "方式三 · 高速复制（DXGI）": "方式三",
            "3": "方式三",
            "dxcam": "方式三",
        }
        target = aliases.get(key, aliases.get(raw, "null"))
        for i, (_label, value) in enumerate(CAPTURE_CHOICES):
            if value == target:
                self.capture_combo.setCurrentIndex(i)
                return
        self.capture_combo.setCurrentIndex(0)

    def set_running(self, running: bool) -> None:
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.dry_run_cb.setEnabled(not running)
        self.prefer_highlighted_cb.setEnabled(not running)
        self.capture_combo.setEnabled(not running)
        self.tick_spin.setEnabled(not running)
        if running:
            self.ring.show()
            self.ring.start()
            self.status_pill.setText("● 运行中")
            self.status_pill.setStyleSheet(
                f"color: {OK}; font-weight: 700; letter-spacing: 1px; background: transparent;"
            )
        else:
            self.ring.stop()
            self.ring.hide()
            self.status_pill.setText("● 待机")
            self.status_pill.setStyleSheet(
                f"color: {ALERT}; font-weight: 700; letter-spacing: 1px; background: transparent;"
            )

    def append_log(self, message: str) -> None:
        self.log_view.appendPlainText(message)
