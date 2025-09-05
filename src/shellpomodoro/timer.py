"""
Timer utilities for shellpomodoro, including hotkey-aware countdown.
"""

import time
from enum import Enum
from .keypress import phase_key_mode, poll_end_phase
from typing import Optional

try:
    # Renderer is optional at runtime; avoid hard dependency in type context
    from .display import Renderer  # type: ignore
except Exception:  # pragma: no cover - fallback for editable installs without display

    class Renderer:  # type: ignore
        pass


class PhaseResult(Enum):
    COMPLETED = "completed"
    ENDED_EARLY = "ended_early"


def fmt_mmss(total_s: int) -> str:
    m, s = divmod(max(0, int(total_s)), 60)
    return f"{m:02d}:{s:02d}"


def countdown(
    seconds: int,
    label: str,
    renderer: Optional[Renderer] = None,
    tick_ms: int = 200,
) -> PhaseResult:
    """
    Display a live countdown, polling for Ctrl+E to end the phase early.

    Returns PhaseResult.COMPLETED on natural completion, or
    PhaseResult.ENDED_EARLY if Ctrl+E is detected.
    """
    # Handle zero seconds case immediately
    if seconds <= 0:
        if renderer:
            renderer.start_phase(label, 0)
            # show one line
            line = f"{renderer.update(0)}  (Ctrl+C abort • Ctrl+E end phase) "
            print(f"\r{line}", end="", flush=True)
            print()
            renderer.finalize_phase(False)
        else:
            print(
                f"\r{label}  ⏳ {fmt_mmss(0)}  (Ctrl+C abort • Ctrl+E end phase) ",
                end="",
                flush=True,
            )
            print()
        return PhaseResult.COMPLETED

    end = time.time() + seconds
    if renderer:
        renderer.start_phase(label, seconds)
    with phase_key_mode():  # enable per-key reads during this phase
        while True:
            left = int(round(end - time.time()))

            # hotkey check first
            if poll_end_phase():
                if renderer:
                    renderer.finalize_phase(True)
                print()  # newline before leaving
                return PhaseResult.ENDED_EARLY

            if left < 0:
                if renderer:
                    line = f"{renderer.update(seconds)}  (Ctrl+C abort • Ctrl+E end phase) "
                    print(f"\r{line}", end="", flush=True)
                    print()
                    renderer.finalize_phase(False)
                else:
                    print(
                        f"\r{label}  ⏳ {fmt_mmss(0)}  (Ctrl+C abort • Ctrl+E end phase) ",
                        end="",
                        flush=True,
                    )
                    print()
                return PhaseResult.COMPLETED

            # status line
            if renderer:
                elapsed = seconds - max(0, left)
                line = f"{renderer.update(elapsed)}  (Ctrl+C abort • Ctrl+E end phase) "
                print(f"\r{line}", end="", flush=True)
            else:
                print(
                    f"\r{label}  ⏳ {fmt_mmss(left)}  (Ctrl+C abort • Ctrl+E end phase) ",
                    end="",
                    flush=True,
                )

            time.sleep(tick_ms / 1000.0)
