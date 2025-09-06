def _read_one_char_if_available():
    """
    Non-blocking single-char read. Assumes phase_key_mode() already set the TTY into
    cbreak/raw (POSIX). On Windows, uses msvcrt.
    Returns a 1-char string or None if no input available.
    """
    import os

    if os.name == "nt":
        try:
            import msvcrt  # type: ignore
        except Exception:
            return None
        if msvcrt.kbhit():
            ch = msvcrt.getwch()
            return ch if ch else None
        return None
    else:
        import sys, select

        try:
            r, _, _ = select.select([sys.stdin], [], [], 0)
        except Exception:
            return None
        if not r:
            return None
        try:
            ch = sys.stdin.read(1)
            return ch if ch else None
        except (IOError, OSError, EOFError):
            return None


from enum import Enum, auto

CTRL_E = "\x05"  # Ctrl+E
CTRL_O = "\x0f"  # Ctrl+O


class Hotkey(Enum):
    NONE = auto()
    END_PHASE = auto()
    TOGGLE_HIDE = auto()  # For Ctrl+O detach


def poll_hotkey() -> "Hotkey":
    ch = _read_one_char_if_available()
    if not ch:
        return Hotkey.NONE
    if ch == CTRL_E:
        return Hotkey.END_PHASE
    if ch == CTRL_O:
        return Hotkey.TOGGLE_HIDE
    return Hotkey.NONE


import contextlib
import platform
import sys
from io import UnsupportedOperation

IS_WIN = platform.system().lower().startswith("win")
CTRL_E = "\x05"  # Ctrl+E

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
