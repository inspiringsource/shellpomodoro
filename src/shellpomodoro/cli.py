"""
Cross-platform Pomodoro timer CLI implementation.
"""

import sys
import time
import platform
import signal
import argparse
from contextlib import contextmanager
from typing import List, Optional
import importlib.metadata
from .timer import countdown, PhaseResult
import os
from .display import Mode, make_renderer


# ASCII art for completion message
GOOD_JOB = """
 ██████╗  ██████╗  ██████╗ ██████╗      ██╗ ██████╗ ██████╗ ██╗
██╔════╝ ██╔═══██╗██╔═══██╗██╔══██╗     ██║██╔═══██╗██╔══██╗██║
██║  ███╗██║   ██║██║   ██║██║  ██║     ██║██║   ██║██████╔╝██║
██║   ██║██║   ██║██║   ██║██║  ██║██   ██║██║   ██║██╔══██╗╚═╝
╚██████╔╝╚██████╔╝╚██████╔╝██████╔╝╚█████╔╝╚██████╔╝██████╔╝██╗
 ╚═════╝  ╚═════╝  ╚═════╝ ╚═════╝  ╚════╝  ╚═════╝ ╚═════╝ ╚═╝
"""

CSI = "\x1b["


def _supports_ansi() -> bool:
    """Check if the terminal supports ANSI escape sequences."""
    import os
    import sys

    # CI environment or explicit override
    if os.getenv("SHELLPOMODORO_NO_ANSI"):
        return False
    if os.getenv("FORCE_COLOR") or os.getenv("SHELLPOMODORO_FORCE_ANSI"):
        return True

    # Windows terminals
    if os.name == "nt":
        return (
            os.getenv("TERM_PROGRAM") in ("vscode", "mintty") or "ANSICON" in os.environ
        )

    # Unix-like systems
    if not sys.stdout.isatty():
        return False

    term = os.getenv("TERM", "").lower()
    return "color" in term or term.startswith("xterm") or term in ("screen", "tmux")


def _csi_up(lines: int = 1) -> str:
    """Return ANSI escape sequence to move cursor up."""
    return f"\x1b[{lines}A"


def _csi_down(lines: int = 1) -> str:
    """Return ANSI escape sequence to move cursor down."""
    return f"\x1b[{lines}B"


def _csi_clear_line() -> str:
    """Return ANSI escape sequence to clear current line."""
    return "\x1b[2K"


def _clear_and_repaint(status_line: str):
    """Clear current line and repaint with new status (used when cursor is parked on status line)."""
    import sys

    sys.stdout.write("\x1b[2K\r" + status_line)
    sys.stdout.flush()


def _signal_handler(signum: int, frame) -> None:
    """
    Signal handler for graceful interruption.

    Args:
        signum: Signal number (should be SIGINT)
        frame: Current stack frame (unused)

    Raises:
        KeyboardInterrupt: Always raises to trigger graceful cleanup
    """
    # Raise KeyboardInterrupt to trigger existing cleanup logic
    raise KeyboardInterrupt


def setup_signal_handler() -> None:
    """
    Set up SIGINT handler for graceful session interruption.

    This function registers a signal handler that converts SIGINT (Ctrl+C)
    into a KeyboardInterrupt exception, allowing for proper cleanup and
    terminal state restoration.
    """
    signal.signal(signal.SIGINT, _signal_handler)


def mmss(seconds: int) -> str:
    """
    Format seconds as MM:SS string with zero padding.

    Args:
        seconds: Number of seconds to format

    Returns:
        str: Formatted time string in MM:SS format

    Examples:
        >>> mmss(0)
        '00:00'
        >>> mmss(65)
        '01:05'
        >>> mmss(3661)
        '61:01'
    """
    # Ensure non-negative value
    seconds = max(0, int(seconds))

    # Calculate minutes and remaining seconds
    minutes, remaining_seconds = divmod(seconds, 60)

    # Return zero-padded format
    return f"{minutes:02d}:{remaining_seconds:02d}"


def _detect_platform() -> str:
    """
    Detect the current platform for input handling.

    Returns:
        str: 'windows' for Windows systems, 'unix' for Unix-like systems
    """
    return "windows" if platform.system() == "Windows" else "unix"


def _read_key_windows(prompt: str = "Press any key to continue...") -> None:
    """
    Windows-specific keypress handling using msvcrt.

    Args:
        prompt: Message to display to user
    """
    """
    Execute the complete Pomodoro session with the specified parameters.

    Args:
        work: Work duration in minutes.
        break_: Break duration in minutes (name uses underscore to avoid keyword).
        iterations: Number of work/break cycles.
        beeps: Number of beeps to play on phase transitions.
        display: One of {"timer-back", "timer-forward", "bar", "dots"}.
        dot_interval: Dot interval in seconds for "dots" mode, or None.

    Returns:
        None
    """
    Context manager for safe terminal state management on Unix systems.

    Yields:
        None: Context for raw terminal mode

    Raises:
        ImportError: If termios/tty modules are not available
        OSError: If terminal operations fail
    """
    try:
        import termios
        import tty

        # Save original terminal settings
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            # Set terminal to raw mode
            tty.setraw(fd)
            yield
        finally:
            # Always restore original settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    except (ImportError, OSError):
        # Fallback if terminal operations are not supported
        yield


def _read_key_unix(prompt: str = "Press any key to continue...") -> None:
    """
    Unix-specific keypress handling using termios and tty modules.

    Args:
        prompt: Message to display to user
    """
    import sys

    if not sys.stdin.isatty():
        print(f"{prompt} [auto-continue: non-TTY]")
        return

    try:
        print(prompt, end="", flush=True)

        with _raw_terminal():
            # Read single character without Enter requirement
            char = sys.stdin.read(1)

        print()  # Add newline after keypress

    except (ImportError, OSError):
        # Fallback to standard input if raw terminal mode fails
        input(prompt)


def read_key(prompt: str = "Press any key to continue...") -> None:
    """
    Cross-platform single keypress input without Enter requirement.

    Args:
        prompt: Message to display to user
    """
    import os

    # Global kill-switch for tests and automation
    if os.getenv("SHELLPOMODORO_NONINTERACTIVE") == "1":
        print(f"{prompt} [auto-continue: non-interactive]")
        return

    # Safety guard: prevent blocking in non-TTY environments
    if not sys.stdin.isatty():
        print(f"{prompt} [auto-continue: non-TTY]")
        return

    current_platform = _detect_platform()

    if current_platform == "windows":
        _read_key_windows(prompt)
    else:
        _read_key_unix(prompt)


def beep(times: int = 1, interval: float = 0.2) -> None:
    """
    Play terminal bell notifications with configurable count and spacing.

    Args:
        times: Number of beeps to play (default: 1)
        interval: Time interval between beeps in seconds (default: 0.2)
    """
    for i in range(times):
        # Print terminal bell character
        print("\a", end="", flush=True)

        # Add interval between beeps (except after the last beep)
        if i < times - 1:
            time.sleep(interval)


def banner() -> str:
    """
    Return completion message with ASCII art congratulations.

    Returns:
        str: Complete banner message with ASCII art and completion text
    """
    return f"{GOOD_JOB}\nshellpomodoro — great work!\nSession complete"


def session_header(work_min: int, break_min: int, iterations: int) -> str:
    """
    Create session header display with work/break/iteration summary.

    Args:
        work_min: Work period duration in minutes
        break_min: Break period duration in minutes
        iterations: Total number of Pomodoro cycles

    Returns:
        str: Formatted session header with configuration summary
    """
    return (
        f"Pomodoro Session: {work_min}min work, {break_min}min break, "
        f"{iterations} iteration{'s' if iterations != 1 else ''}"
    )


def iteration_progress(current: int, total: int, phase: str) -> str:
    """
    Create iteration progress indicators during phases.

    Args:
        current: Current iteration number (1-based)
        total: Total number of iterations
        phase: Current phase ("Focus" or "Break")

    Returns:
        str: Formatted progress indicator showing current iteration and phase
    """
    return f"[{current}/{total}] {phase}"


def parse_args(argv: List[str] = None) -> argparse.Namespace:
    """
    Parse command line arguments with validation.

    Args:
        argv: List of command line arguments (defaults to sys.argv[1:])

    Returns:
        argparse.Namespace: Parsed arguments with validated values

    Raises:
        SystemExit: If arguments are invalid or help is requested
    import argparse
    def parse_args(argv=None) -> argparse.Namespace:
        p = argparse.ArgumentParser(prog="shellpomodoro", add_help=True)
        p.add_argument("--work", type=int, default=25, dest="work")
        p.add_argument("--break", type=int, default=5, dest="break_")
        p.add_argument("--iterations", type=int, default=4)
        p.add_argument("--beeps", type=int, default=2)
        p.add_argument("--display", choices=("timer-back","timer-forward","bar","dots"), default="timer-back")
        p.add_argument("--dot-interval", type=int, default=None, dest="dot_interval")
        p.add_argument("--version", "-v", action="store_true")
        p.add_argument("subcommand", nargs="?", choices=("attach",), default=None)
        return p.parse_args(argv)


def _is_ci_mode() -> bool:
    # CI/non-interactive if env var set or stdin not a TTY
    return os.getenv("SHELLPOMODORO_CI") == "1" or not sys.stdin.isatty()


def run(work: int, break_: int, iterations: int, beeps: int, display: str, dot_interval: int | None) -> None:
    """
    Execute the complete Pomodoro session with the specified parameters.

    Args:
        work: Work duration in minutes.
        break_: Break duration in minutes (name uses underscore to avoid keyword).
        iterations: Number of work/break cycles.
        beeps: Number of beeps to play on phase transitions.
        display: One of {"timer-back", "timer-forward", "bar", "dots"}.
        dot_interval: Dot emission interval in seconds (only for "dots"), or None.

    Returns:
        None
    """
    # (existing implementation continues here)
    try:
        # Convert minutes to seconds for countdown
        work_seconds = work * 60
        break_seconds = brk * 60

        # Build renderer
        mode = Mode(display)
        renderer = make_renderer(mode, dot_interval)

        # Execute each Pomodoro iteration
        for iteration in range(1, iters + 1):
            # Work phase
            work_label = iteration_progress(iteration, iters, "Focus")
            work_result = countdown(work_seconds, work_label, renderer)

            # Play notification beeps after work phase
            if not _is_ci_mode():
                beep(beeps)

            # Check if this is the final iteration
            if iteration == iters:
                # Final iteration - no break phase, show completion
                print()
                print(banner())
                # Print renderer summary if available
                summary = getattr(renderer, "summary", lambda: "")()
                if summary:
                    print()
                    print(summary)
                break
            else:
                # Wait for keypress before break (except final iteration)
                if work_result == PhaseResult.ENDED_EARLY or _is_ci_mode():
                    # Skip the keypress wait if work was ended early
                    pass
                else:
                    read_key("Work phase complete! Press any key to start break...")

                # Break phase
                break_label = iteration_progress(iteration, iters, "Break")
                # Separate phases visually for DOTS
                if mode == Mode.DOTS:
                    print("\n│")
                break_result = countdown(break_seconds, break_label, renderer)

                # Play notification beeps after break phase
                if not _is_ci_mode():
                    beep(beeps)

                # Wait for keypress before next work phase (except after final break)
                if iteration < iters:
                    if break_result == PhaseResult.ENDED_EARLY or _is_ci_mode():
                        # Skip the keypress wait if break was ended early
                        pass
                    else:
                        read_key(
                            "Break complete! Press any key to start next work phase..."
                        )

    except KeyboardInterrupt:
        # Re-raise to be handled by caller
        raise


def main() -> None:
            """
            CLI entry point: parse arguments, handle version/help, attach or start a session.

            Behavior:
                - `--version` / `-v` prints package version and exits(0).
                - `--help` is handled by argparse (exits 0).
                - `attach` subcommand reattaches to an existing session if available.
                - Otherwise starts a new session with parsed args.

            Returns:
                    None
            """
        # (existing implementation continues here)
    import sys
    from importlib import metadata

    args = parse_args()  # uses sys.argv[1:]
    if args.version:
        print(metadata.version("shellpomodoro"))
        sys.exit(0)

    if args.subcommand == "attach":
        info = _existing_session_info()
        if not info:
            print("No active shellpomodoro session to attach.", flush=True)
            sys.exit(1)
        return attach_ui(info)

    # normal start
    work = int(args.work)
    brk = int(args.break_)
    iters = int(args.iterations)
    beeps = int(args.beeps)
    display = str(args.display)
    dot_interval = None if args.dot_interval is None else int(args.dot_interval)

    setup_signal_handler()
    run(work, brk, iters, beeps, display, dot_interval)


def attach_ui(info: dict) -> None:
    """
    Connect to the background session daemon and render the live UI in the terminal.

    Features:
      - Prints a phase header once, a status line that repaints in place, and a legend line.
      - Ctrl+O detaches the viewer (daemon keeps running).
      - Ctrl+E ends the current phase.
      - Ctrl+C aborts the whole session.

    """
    Connect to the background session daemon and render the live UI.

    Features:
      - One header line per phase, a status line that repaints, and a legend line.
      - Ctrl+O detaches the viewer (daemon keeps running).
      - Ctrl+E ends the current phase.
      - Ctrl+C aborts the session.

    Args:
        info: Connection metadata, e.g., {"port": int, "secret": str}.

    Returns:
        None
    """
    # existing implementation continues...
    import time
    from .ipc import _connect, hello, status, end_phase, abort
    from .keypress import phase_key_mode, poll_hotkey, Hotkey

    port, secret = info["port"], info["secret"]
    try:
        sock = _connect(port)
    except (ConnectionRefusedError, OSError) as e:
        print(f"Unable to connect to session daemon: {e}", flush=True)
        return

    try:
        if not hello(sock, secret):
            print("Authentication failed", flush=True)
            return
    except (ConnectionResetError, BrokenPipeError, OSError):
        print("Connection lost during authentication", flush=True)
        return

    try:
        renderer = make_renderer(info)
    except Exception as e:
        print(f"Unable to create UI renderer: {e}", flush=True)
        return

    last_phase_id = None
    last_key = None
    ansi = _supports_ansi()

    def _mmss(seconds: int) -> str:
        s = max(0, int(seconds))
        return f"{s // 60:02d}:{s % 60:02d}"

    def _fingerprint(st: dict):
        d = st.get("display")
        if d == "timer-back":
            return ("tb", int(st["remaining_s"] or 0))
        if d == "timer-forward":
            return ("tf", int(st["elapsed_s"] or 0))
        if d in ("bar","dots"):
            return ("p", int(round(st.get("progress", 0.0)*1000)))
        return ("raw", st.get("phase_id"))

    try:
        try:
            cm = phase_key_mode()
        except Exception:
            class _Noop:
                def __enter__(self): return None
                def __exit__(self, *a): return False
            cm = _Noop()
        with cm:
            while True:
                st = status(sock)
                if st is None:
                    if ansi:
                        sys.stdout.write("\x1b[1B\n")
                        sys.stdout.flush()
                    else:
                        print("", flush=True)
                    if renderer and hasattr(renderer, "close"):
                        renderer.close()
                    print("[✓] Session finished", flush=True)
                    return

                # Normalize payload for test compatibility
                remaining_s = st.get("remaining_s", st.get("left"))
                elapsed_s   = st.get("elapsed_s", st.get("elapsed"))
                duration_s  = st.get("duration_s", st.get("total"))

                payload = {
                    "phase_id":    st.get("phase_id"),
                    "phase_label": st.get("phase_label"),
                    "display":     st.get("display", ""),
                    "progress":    st.get("progress", 0.0),
                    "remaining_s": remaining_s,
                    "elapsed_s":   elapsed_s,
                    "duration_s":  duration_s,
                    "remaining_mmss": _mmss(remaining_s or 0),
                    "elapsed_mmss":   _mmss(elapsed_s or 0),
                    "duration_mmss":  _mmss(duration_s or 0),
                }
                phase_id = payload["phase_id"]
                phase_label = payload["phase_label"]
                cur_key = _fingerprint(payload)

                new_phase = (last_phase_id is None) or (phase_id != last_phase_id)
                if new_phase:
                    last_phase_id = phase_id
                    last_key = cur_key
                    status_line = renderer.frame(payload)
                    print(f"{phase_label} phase begins", flush=True)
                    if ansi:
                        sys.stdout.write("\x1b[2K\r" + status_line + "\n")
                        print("Hotkeys: Ctrl+C abort • Ctrl+E end phase • Ctrl+O detach", flush=True)
                        sys.stdout.write("\x1b[1A")
                        sys.stdout.flush()
                    else:
                        print(status_line, flush=True)
                        print("Hotkeys: Ctrl+C abort • Ctrl+E end phase • Ctrl+O detach", flush=True)
                    continue

                force_repaint = ansi and (payload["display"] in {"bar", "dots"})
                should_repaint = force_repaint or (cur_key != last_key)
                if not should_repaint:
                    continue
                last_key = cur_key
                status_line = renderer.frame(payload)
                if ansi:
                    sys.stdout.write("\x1b[2K\r" + status_line)
                    sys.stdout.flush()
                else:
                    print(status_line, flush=True)

                hk = poll_hotkey()
                if hk == Hotkey.TOGGLE_HIDE:
                    print("[detached] Viewer exited", flush=True)
                    return
                elif hk == Hotkey.END_PHASE:
                    try:
                        end_phase(sock)
                    except (ConnectionResetError, BrokenPipeError, OSError):
                        print("Connection lost while sending end-phase", flush=True)
                        return
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n[✓] Viewer interrupted", flush=True)
    except (ConnectionResetError, BrokenPipeError, OSError):
        print("Connection to daemon lost", flush=True)
    finally:
        if renderer and hasattr(renderer, "close"):
            renderer.close()
        try:
            sock.close()
        except Exception:
            pass
        print(f"Unable to connect to session daemon: {e}", flush=True)
        return

    try:
        if not hello(sock, secret):
            print("Authentication failed", flush=True)
            return
    except (ConnectionResetError, BrokenPipeError, OSError):
        print("Connection lost during authentication", flush=True)
        return

    try:
        renderer = make_renderer(info)
    except Exception as e:
        print(f"Unable to create UI renderer: {e}", flush=True)
        return

    last_phase_id = None
    last_key = None
    ansi = _supports_ansi()

    def _mmss(seconds: int) -> str:
        s = max(0, int(seconds))
        return f"{s // 60:02d}:{s % 60:02d}"

    def _fingerprint(st: dict):
        d = st.get("display")
        if d == "timer-back":
            return ("tb", int(st["remaining_s"]))
        if d == "timer-forward":
            return ("tf", int(st["elapsed_s"]))
        if d in ("bar","dots"):
            return ("p", int(round(st.get("progress", 0.0)*1000)))
        return ("raw", st.get("phase_id"))

    def _norm(st: dict) -> dict:
        rem = st.get("remaining_s", st.get("left"))
        dur = st.get("duration_s", st.get("total"))
        el  = st.get("elapsed_s")
        if el is None and rem is not None and dur is not None:
            try:
                el = max(0, int(dur) - int(rem))
            except Exception:
                el = 0
        disp = st.get("display") or "timer-back"
        return {
            "phase_id": st.get("phase_id"),
            "phase_label": st.get("phase_label") or "",
            "remaining_s": 0 if rem is None else int(rem),
            "elapsed_s": 0 if el is None else int(el),
            "duration_s": 0 if dur is None else int(dur),
            "progress": st.get("progress", 0.0),
            "display": disp,
        }

    try:
        with phase_key_mode():
            while True:
                st = status(sock)
                if st is None:
                    # Session ended - move cursor down and emit one newline (ANSI)
                    if ansi:
                        sys.stdout.write("\x1b[1B\n")
                        sys.stdout.flush()
                    else:
                        print("", flush=True)
                    if renderer and hasattr(renderer, "close"):
                        renderer.close()
                    print("[✓] Session finished", flush=True)
                    return

                st = _norm(status(sock))
                payload = {
                    **st,
                    "remaining_mmss": _mmss(st["remaining_s"]),
                    "elapsed_mmss": _mmss(st["elapsed_s"]),
                    "duration_mmss": _mmss(st["duration_s"]),
                }
                phase_id = payload["phase_id"]
                phase_label = payload["phase_label"]
                cur_key = _fingerprint(payload)

                new_phase = (last_phase_id is None) or (phase_id != last_phase_id)
                if new_phase:
                    last_phase_id = phase_id
                    last_key = cur_key
                    status_line = renderer.frame(payload)
                    # Header
                    print(f"{phase_label} phase begins", flush=True)
                    if ansi:
                        sys.stdout.write(_csi_clear_line() + "\r" + status_line + "\n")
                        print("Hotkeys: Ctrl+C abort • Ctrl+E end phase • Ctrl+O detach", flush=True)
                        sys.stdout.write(_csi_up(1))
                        sys.stdout.flush()
                    else:
                        print(status_line, flush=True)
                        print("Hotkeys: Ctrl+C abort • Ctrl+E end phase • Ctrl+O detach", flush=True)
                    continue

                force_repaint = ansi and (payload["display"] in {"bar", "dots"})
                should_repaint = force_repaint or (cur_key != last_key)
                if not should_repaint:
                    continue
                last_key = cur_key
                status_line = renderer.frame(payload)
                if ansi:
                    sys.stdout.write(_csi_clear_line() + "\r" + status_line)
                    sys.stdout.flush()
                else:
                    print(status_line, flush=True)

                hk = poll_hotkey()
                if hk == Hotkey.TOGGLE_HIDE:
                    if ansi:
                        sys.stdout.write(_csi_down(1) + "\n")
                        sys.stdout.flush()
                    if renderer and hasattr(renderer, "close"):
                        renderer.close()
                    print("[detached] Viewer exited", flush=True)
                    return
                elif hk == Hotkey.END_PHASE:
                    try:
                        end_phase(sock)
                    except (ConnectionResetError, BrokenPipeError, OSError):
                        print("Connection lost while sending end-phase", flush=True)
                        return
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n[✓] Viewer interrupted", flush=True)
    except (ConnectionResetError, BrokenPipeError, OSError):
        print("Connection to daemon lost", flush=True)
    finally:
        if renderer and hasattr(renderer, "close"):
            renderer.close()
        try:
            sock.close()
        except Exception:
            pass
