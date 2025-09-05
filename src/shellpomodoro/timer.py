"""
Timer utilities for shellpomodoro, including hotkey-aware countdown.
"""

import os
import shutil
import sys
import time
from enum import Enum
from .keypress import phase_key_mode, poll_end_phase
from typing import Optional

_ERASE_LINE = "\x1b[2K"
_CR = "\r"


def _supports_ansi() -> bool:
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def _terminal_cols() -> int:
    try:
        return shutil.get_terminal_size(fallback=(80, 24)).columns
    except Exception:
        return 80


def _fit_to_width(s: str) -> str:
    cols = _terminal_cols()
    # keep 1 col free to avoid wrap on some terminals
    max_len = max(1, cols - 1)
    if len(s) <= max_len:
        return s
    # use an ellipsis when truncating
    if max_len >= 1:
        return s[: max_len - 1] + "…"
    return s[:max_len]


def _print_status(line: str):
    """Overwrite current line without newline; never let it wrap."""
    safe = _fit_to_width(line)
    if _supports_ansi():
        sys.stdout.write(_CR + _ERASE_LINE + safe)
    else:
        # fallback erase for non-ANSI
        last_len = getattr(_print_status, "_last_len", 0)
        pad = max(0, last_len - len(safe))
        sys.stdout.write(_CR + safe + (" " * pad))
        _print_status._last_len = len(safe)
    sys.stdout.flush()


def _println():
    sys.stdout.write("\n")
    sys.stdout.flush()


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
    # Determine if we use single-line mode
    use_single_line = bool(renderer) and getattr(renderer, "single_line", False)

    # Handle zero seconds case immediately
    if seconds <= 0:
        if renderer:
            renderer.start_phase(label, 0)
            status = renderer.update(0)
            status = f"{status}  (Ctrl+C abort • Ctrl+E end phase) "
            if use_single_line:
                _print_status(status)
                _println()
            else:
                print(f"\r{status}", end="", flush=True)
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
                    if use_single_line:
                        _println()
                    renderer.finalize_phase(True)
                if not use_single_line:
                    print()  # newline before leaving
                return PhaseResult.ENDED_EARLY

            if left < 0:
                if renderer:
                    if use_single_line:
                        status = renderer.update(seconds)
                        status = f"{status}  (Ctrl+C abort • Ctrl+E end phase) "
                        _print_status(status)
                        _println()
                        renderer.finalize_phase(False)
                    else:
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
                if use_single_line:
                    status = renderer.update(elapsed)
                    status = f"{status}  (Ctrl+C abort • Ctrl+E end phase) "
                    _print_status(status)
                else:
                    line = f"{renderer.update(elapsed)}  (Ctrl+C abort • Ctrl+E end phase) "
                    print(f"\r{line}", end="", flush=True)
            else:
                print(
                    f"\r{label}  ⏳ {fmt_mmss(left)}  (Ctrl+C abort • Ctrl+E end phase) ",
                    end="",
                    flush=True,
                )

            time.sleep(tick_ms / 1000.0)
