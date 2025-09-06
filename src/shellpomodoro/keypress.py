# src/shellpomodoro/keypress.py
from __future__ import annotations
import contextlib
import platform
import sys
from enum import Enum
from io import UnsupportedOperation

IS_WIN = platform.system().lower().startswith("win")
CTRL_E = "\x05"  # Ctrl+E
CTRL_O = "\x0f"  # Ctrl+O
CTRL_C = "\x03"  # Ctrl+C

class Hotkey(Enum):
    """Hotkey enumeration for phase control."""
    NONE = "none"
    END_PHASE = "end_phase"     # Ctrl+E
    TOGGLE_HIDE = "toggle_hide" # Ctrl+O 
    ABORT = "abort"             # Ctrl+C

# --- Windows implementation ---
if IS_WIN:
    try:
        import msvcrt  # type: ignore
    except Exception:  # very rare
        msvcrt = None  # type: ignore

    def _poll_ctrl_e_win() -> bool:
        if msvcrt and msvcrt.kbhit():
            ch = msvcrt.getwch()
            return ch == CTRL_E
        return False


# --- Unix implementation ---
else:
    import select
    import termios
    import tty

    @contextlib.contextmanager
    def _cbreak(fd: int):
        old = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)  # keep Ctrl+C working
            yield
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    def _poll_ctrl_e_unix(timeout: float = 0.0) -> bool:
        try:
            r, _, _ = select.select([sys.stdin], [], [], timeout)
            if r:
                ch = sys.stdin.read(1)
                return ch == CTRL_E
        except (OSError, ValueError):
            # stdin is not selectable or redirected
            pass
        return False


@contextlib.contextmanager
def phase_key_mode():
    """
    Enable per-key reads while a phase runs; restore terminal on exit.
    On Windows this is a no-op; on Unix we enter cbreak mode when possible.
    In non-TTY / redirected stdin, gracefully no-op.
    """
    if IS_WIN:
        yield
        return
    try:
        # stdin must be a TTY and expose fileno()
        fileno = sys.stdin.fileno()
        # If not a real TTY, just no-op
        if not sys.stdin.isatty():
            yield
            return
    except Exception:
        # No fileno or other issue: no-op
        yield
        return

    if not termios or not tty:
        yield
        return

    try:
        old = termios.tcgetattr(fileno)
        try:
            tty.setcbreak(fileno)
            yield
        finally:
            termios.tcsetattr(fileno, termios.TCSADRAIN, old)
    except Exception:
        # Any issue setting terminal mode: no-op
        yield


def poll_end_phase() -> bool:
    """
    Return True if Ctrl+E was pressed (non-blocking).
    """
    if IS_WIN:
        return _poll_ctrl_e_win()
    else:
        return _poll_ctrl_e_unix(0.0)

def poll_hotkey() -> Hotkey:
    """
    Poll for hotkeys (non-blocking). Returns first hotkey found or NONE.
    """
    if IS_WIN:
        if msvcrt and msvcrt.kbhit():
            ch = msvcrt.getwch()
            if ch == CTRL_E:
                return Hotkey.END_PHASE
            elif ch == CTRL_O:
                return Hotkey.TOGGLE_HIDE
            elif ch == CTRL_C:
                return Hotkey.ABORT
    else:
        try:
            r, _, _ = select.select([sys.stdin], [], [], 0.0)
            if r:
                ch = sys.stdin.read(1)
                if ch == CTRL_E:
                    return Hotkey.END_PHASE
                elif ch == CTRL_O:
                    return Hotkey.TOGGLE_HIDE
                elif ch == CTRL_C:
                    return Hotkey.ABORT
        except (OSError, ValueError):
            # stdin is not selectable or redirected
            pass
    return Hotkey.NONE
