"""
Timer utilities for shellpomodoro, including hotkey-aware countdown.
"""

import time
from enum import Enum
from .keypress import phase_key_mode, poll_end_phase


class PhaseResult(Enum):
    COMPLETED = "completed"
    ENDED_EARLY = "ended_early"


def fmt_mmss(total_s: int) -> str:
    m, s = divmod(max(0, int(total_s)), 60)
    return f"{m:02d}:{s:02d}"


def countdown(seconds: int, label: str, tick_ms: int = 200) -> PhaseResult:
    """
    Display a live countdown, polling for Ctrl+E to end the phase early.

    Returns PhaseResult.COMPLETED on natural completion, or
    PhaseResult.ENDED_EARLY if Ctrl+E is detected.
    """
    # Handle zero seconds case immediately
    if seconds <= 0:
        print(
            f"\r{label}  ⏳ {fmt_mmss(0)}  (Ctrl+C abort • Ctrl+E end phase) ",
            end="",
            flush=True,
        )
        print()
        return PhaseResult.COMPLETED

    end = time.time() + seconds
    with phase_key_mode():  # enable per-key reads during this phase
        while True:
            left = int(round(end - time.time()))

            # hotkey check first
            if poll_end_phase():
                print()  # newline before leaving
                return PhaseResult.ENDED_EARLY

            if left < 0:
                print(
                    f"\r{label}  ⏳ {fmt_mmss(0)}  (Ctrl+C abort • Ctrl+E end phase) ",
                    end="",
                    flush=True,
                )
                print()
                return PhaseResult.COMPLETED

            # status line
            print(
                f"\r{label}  ⏳ {fmt_mmss(left)}  (Ctrl+C abort • Ctrl+E end phase) ",
                end="",
                flush=True,
            )

            time.sleep(tick_ms / 1000.0)
