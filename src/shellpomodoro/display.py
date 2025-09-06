from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
import time
import shutil
from typing import List, Optional


class Mode(str, Enum):
    TIMER_BACK = "timer-back"
    TIMER_FWD = "timer-forward"
    BAR = "bar"
    DOTS = "dots"


@dataclass
class PhaseRec:
    kind: str  # "WORK" or "BREAK"
    total_s: int
    ended_early: bool
    slots: str  # for dots (e.g., "••E") else ""


class Renderer:
    def start_phase(self, kind: str, total_s: int) -> None: ...
    def update(self, elapsed_s: int) -> str: ...  # return one-line status for top line
    def finalize_phase(self, ended_early: bool) -> None: ...
    def summary(self) -> str: ...  # multi-line string at session end
    def close(self) -> None: ...  # cleanup method


# ---- Timer back/forward ----
class TimerBackRenderer(Renderer):
    single_line = True

    def __init__(self):
        self._label = ""
        self._total = 0

    def start_phase(self, kind, total_s):
        self._label = kind
        self._total = total_s

    def frame(self, payload):
        # Use normalized MM:SS string
        return f"⏳ {payload.get('remaining_mmss', '00:00')}"

    def finalize_phase(self, ended_early):
        pass

    def summary(self):
        return ""

    def close(self):
        pass


class TimerFwdRenderer(Renderer):
    single_line = True

    def __init__(self):
        self._label = ""
        self._total = 0

    def start_phase(self, kind, total_s):
        self._label = kind
        self._total = total_s

    def frame(self, payload):
        # Use normalized MM:SS string
        return f"⏳ {payload.get('elapsed_mmss', '00:00')}"

    def finalize_phase(self, ended_early):
        pass

    def summary(self):
        return ""

    def close(self):
        pass


# ---- Progress bar ----
class BarRenderer(Renderer):
    single_line = True

    def __init__(self):
        self._label = ""
        self._total = 1

    def start_phase(self, kind, total_s):
        self._label = kind
        self._total = max(1, total_s)

    def frame(self, payload):
        progress = float(payload.get("progress", 0.0))
        cols = shutil.get_terminal_size((80, 24)).columns
        bar_w = max(10, min(40, cols - 30))
        filled = int(progress * bar_w)
        bar = "█" * filled + "░" * (bar_w - filled)
        percent = int(progress * 100)
        return f"[{bar}] {percent:>3}%"

    def finalize_phase(self, ended_early):
        pass

    def summary(self):
        return ""

    def close(self):
        pass


# ---- Dots (test-runner style) ----
class DotsRenderer(Renderer):
    single_line = True

    def __init__(self, dot_interval_s: Optional[int]):
        self._label = ""
        self._total = 0
        self._interval = dot_interval_s
        self._last_toggle = 0.0
        self._slots = []  # type: List[str]
        self._blink = False
        self.history = []  # type: List[PhaseRec]

    def start_phase(self, kind, total_s):
        self._label = kind
        self._total = max(1, total_s)
        if not self._interval:
            # Simple heuristic: minute dots for long, ~10 dots for short phases
            if self._total >= 60:
                self._interval = 60
            else:
                self._interval = max(1, self._total // 10)
        n_slots = max(1, self._total // self._interval)
        # Cap by terminal width to avoid wrapping
        cols = shutil.get_terminal_size((80, 24)).columns
        max_slots = max(10, cols - 20)
        if n_slots > max_slots:
            n_slots = max_slots
            self._interval = max(1, self._total // n_slots)
        self._slots = [" "] * n_slots
        self._last_toggle = time.time()

    def frame(self, payload):
        elapsed_s = int(payload.get("elapsed_s", 0))
        n = min(len(self._slots), max(0, int(elapsed_s // self._interval)))
        for i in range(n):
            self._slots[i] = "•"
        if n < len(self._slots):
            now = time.time()
            if now - self._last_toggle >= 0.5:
                self._blink = not self._blink
                self._last_toggle = now
            self._slots[n] = "•" if self._blink else "·"
        visual = "".join(self._slots)
        return visual

    def finalize_phase(self, ended_early: bool):
        # mark current slot if ended early
        if ended_early:
            for i, c in enumerate(self._slots):
                if c in {"·", "•", " "}:
                    self._slots[i] = "E"
                    break
        rec = PhaseRec(self._label, self._total, ended_early, "".join(self._slots))
        self.history.append(rec)

    def summary(self):
        if not self.history:
            return ""
        lines: List[str] = []
        for idx, (work, brk) in enumerate(
            zip(self.history[::2], self.history[1::2]), start=1
        ):
            w = f"WORK: {work.slots}"
            b = f"BREAK: {brk.slots}"
            lines.append(f"Iter {idx:<2} {w:<20} │ {b}")
        if len(self.history) % 2 == 1:
            work = self.history[-1]
            lines.append(f"Iter {len(self.history) // 2 + 1:<2} WORK: {work.slots}")
        lines.append("\nLegend: • done, · blinking, E ended early, │ phase separation")
        return "\n".join(lines)

    def close(self):
        pass


def make_renderer(mode: Mode, dot_interval_s: Optional[int]) -> Renderer:
    if mode == Mode.TIMER_FWD:
        return TimerFwdRenderer()
    if mode == Mode.BAR:
        return BarRenderer()
    if mode == Mode.DOTS:
        return DotsRenderer(dot_interval_s)
    return TimerBackRenderer()
