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


def _safe_line(s) -> str:
    """Return a string for UI rendering; coerce None to empty string."""
    return s if isinstance(s, str) else ""


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

    Args:
        seconds: Duration of phase in seconds
        label: Phase label in format "[1/4] Focus"
        renderer: Optional renderer for display
        tick_ms: Tick interval in milliseconds
    """

    # Parse iteration info from label for renderer
    def _parse_label(lbl: str):
        """Parse '[1/4] Focus' -> (1, 4, 'Focus')"""
        if lbl.startswith("[") and "] " in lbl:
            bracket_part, phase_name = lbl.split("] ", 1)
            bracket_content = bracket_part[1:]  # Remove [
            if "/" in bracket_content:
                try:
                    i_str, n_str = bracket_content.split("/")
                    return int(i_str), int(n_str), phase_name
                except ValueError:
                    pass
        return 1, 1, lbl

    i, n, phase_name = _parse_label(label)

    # Determine if we use single-line mode
    use_single_line = bool(renderer) and getattr(renderer, "single_line", False)

    # Helper to create renderer status with phase info
    def _render_status(elapsed_s: int) -> str:
        """Get status line from renderer with phase info"""
        if not renderer:
            return ""
        remaining_s = max(0, seconds - elapsed_s)
        mm_remaining = remaining_s // 60
        ss_remaining = remaining_s % 60
        mm_elapsed = elapsed_s // 60
        ss_elapsed = elapsed_s % 60
        progress = elapsed_s / max(1, seconds)

        # Build payload with all needed info
        payload = {
            "phase_label": phase_name,
            "i": i,
            "n": n,
            "remaining_s": remaining_s,
            "elapsed_s": elapsed_s,
            "duration_s": seconds,
            "remaining_mmss": f"{mm_remaining:02d}:{ss_remaining:02d}",
            "elapsed_mmss": f"{mm_elapsed:02d}:{ss_elapsed:02d}",
            "progress": min(1.0, progress),
        }
        return renderer.frame(payload)

    # Handle zero seconds case immediately
    if seconds <= 0:
        if renderer:
            renderer.start_phase(phase_name, 0)
            status = _render_status(0)
            status = _safe_line(status)
            if use_single_line:
                _print_status(status)
                _println()
            else:
                print(f"\r{status}", end="", flush=True)
                print()
            renderer.finalize_phase(False)
        else:
            print(
                f"\r{label}  ⏳ {fmt_mmss(0)}",
                end="",
                flush=True,
            )
            print()
        return PhaseResult.COMPLETED

    end = time.time() + seconds
    if renderer:
        renderer.start_phase(phase_name, seconds)

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
                        status = _render_status(seconds)
                        status = _safe_line(status)
                        _print_status(status)
                        _println()
                        renderer.finalize_phase(False)
                    else:
                        status = _render_status(seconds)
                        status = _safe_line(status)
                        print(f"\r{status}", end="", flush=True)
                        print()
                        renderer.finalize_phase(False)
                else:
                    print(
                        f"\r{label}  ⏳ {fmt_mmss(0)}",
                        end="",
                        flush=True,
                    )
                    print()
                return PhaseResult.COMPLETED

            # status line
            if renderer:
                elapsed = seconds - max(0, left)
                if use_single_line:
                    status = _render_status(elapsed)
                    status = _safe_line(status)
                    _print_status(status)
                else:
                    status = _render_status(elapsed)
                    status = _safe_line(status)
                    print(f"\r{status}", end="", flush=True)
            else:
                print(
                    f"\r{label}  ⏳ {fmt_mmss(left)}",
                    end="",
                    flush=True,
                )

            time.sleep(tick_ms / 1000.0)
