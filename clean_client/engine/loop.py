"""Engine tick loop: grab → vision → select → (optional) press."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any

from clean_client.models.state import CombatState
from clean_client.rotation.selector import select_action


class EngineLoop:
    def __init__(
        self,
        *,
        grab: Callable[[], Any],
        read_state: Callable[[Any], CombatState],
        actions: list[dict],
        on_log: Callable[[str], None] | None = None,
        press: Callable[[str], None] | None = None,
        tick_ms: int = 30,
        dry_run: bool = True,
        prefer_highlighted: bool = True,
        cd_ready_window_ms: int = 30,
    ) -> None:
        self.grab = grab
        self.read_state = read_state
        self.actions = actions
        self.on_log = on_log or (lambda _m: None)
        self.press = press
        self.tick_ms = tick_ms
        self.dry_run = dry_run
        self.prefer_highlighted = prefer_highlighted
        self.cd_ready_window_ms = cd_ready_window_ms
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._vision_tip_sent = False

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._vision_tip_sent = False
        self._thread = threading.Thread(
            target=self._run, name="engine-loop", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def _maybe_vision_tip(self, state: CombatState) -> None:
        if self._vision_tip_sent:
            return
        debug = getattr(state, "raw_debug", None) or {}
        tip = None
        warning = debug.get("warning")
        bindings_error = debug.get("bindings_error")
        if warning:
            tip = f"提示: 识别警告={warning}。请检查区域目录与 Skill 框。"
        elif bindings_error:
            tip = f"提示: 绑定行解析失败={bindings_error}。请检查色块行是否完整。"
        elif not state.bindings and self.actions:
            tip = (
                "提示: 已截屏但未读到技能绑定。请确认 AutoPlayer 已启用，"
                "且 Skill 区域对准色块条。"
            )
        if tip is None:
            return
        self._vision_tip_sent = True
        self.on_log(tip)

    def _run(self) -> None:
        while not self._stop.is_set():
            started = time.perf_counter()
            try:
                frame = self.grab()
                state = self.read_state(frame)
                self._maybe_vision_tip(state)
                action = select_action(
                    state,
                    self.actions,
                    prefer_highlighted=self.prefer_highlighted,
                    cd_ready_window_ms=self.cd_ready_window_ms,
                )
                if action is None:
                    self.on_log("空闲")
                else:
                    msg = (
                        f"动作 法术ID={action.spell_id} 按键={action.key} "
                        f"只记日志={self.dry_run}"
                    )
                    self.on_log(msg)
                    if not self.dry_run and self.press is not None:
                        self.press(action.key)
            except Exception as exc:  # noqa: BLE001
                self.on_log(f"错误: {exc}")
            elapsed = (time.perf_counter() - started) * 1000.0
            delay = max(self.tick_ms - elapsed, 1.0) / 1000.0
            self._stop.wait(delay)
