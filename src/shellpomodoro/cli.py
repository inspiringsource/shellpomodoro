import os
import sys

def _detect_platform() -> str:
    """Detect the current platform (windows, unix)."""
    import platform
    return "windows" if platform.system().lower().startswith("win") else "unix"

def _read_key_windows(prompt: str) -> None:
    """Windows key reading implementation."""
    try:
        import msvcrt
        print(f"{prompt}", end="", flush=True)
        msvcrt.getch()
        print()  # Newline after keypress
    except ImportError:
        input(f"{prompt}")

def _read_key_unix(prompt: str) -> None:
    """Unix key reading implementation."""
    try:
        import termios
        import tty
        if not termios or not tty:
            input(f"{prompt}")
            return
        print(f"{prompt}", end="", flush=True)
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        print()  # Newline after keypress
    except (ImportError, OSError):
        input(f"{prompt}")

def _raw_terminal():
    """Context manager for safe terminal state management on Unix systems."""
    import contextlib
    
    @contextlib.contextmanager
    def _raw_context():
        try:
            import termios
            import tty
            if not termios or not tty:
                yield
                return
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                yield
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except (ImportError, OSError):
            yield
    
    return _raw_context()

def read_key(prompt: str) -> None:
    """Cross-platform key reading with non-interactive fallback."""
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

def mmss(seconds) -> str:
    """Convert seconds to MM:SS format."""
    try:
        seconds = int(seconds)
    except (ValueError, TypeError):
        seconds = 0
    if seconds < 0:
        seconds = 0
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def _signal_handler(signum, frame):
    """Signal handler for graceful interruption."""
    raise KeyboardInterrupt()

def setup_signal_handler():
    """Set up signal handler for graceful interruption."""
    import signal
    signal.signal(signal.SIGINT, _signal_handler)

def _supports_ansi() -> bool:
    """Return True if stdout likely supports ANSI control sequences."""
    try:
        return sys.stdout.isatty() and os.environ.get("TERM", "dumb") != "dumb"
    except Exception:
        return False

def _clear_and_repaint(line: str) -> None:
    """ANSI: clear current line and repaint with `line`, then flush."""
    sys.stdout.write("\x1b[2K\r" + line)
    sys.stdout.flush()
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

def attach_ui(info: dict) -> None:
    """
    Connect to daemon and render UI.

    - Header once per phase (e.g., "[1/4] Focus")
    - Status repaints in place (ANSI) or prints-on-change (fallback)
    - Legend once per phase below status
    - Ctrl+O detaches → "[detached] Viewer exited"
    - Ctrl+E end phase; Ctrl+C abort session
    - Accept both (remaining_s/elapsed_s/duration_s) and (left/elapsed/total)
    """
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
        renderer = make_renderer(info)  # keep existing factory
    except Exception as e:
        print(f"Unable to create UI renderer: {e}", flush=True)
        return

    last_phase_id = None
    last_key = None
    last_status_line = None
    ansi = _supports_ansi()

    def _mmss(s):
        try:
            s = 0 if s is None else max(0, int(s))
        except Exception:
            s = 0
        return f"{s//60:02d}:{s%60:02d}"

    def _fingerprint(st: dict) -> tuple:
        disp = st.get("display", "")
        if disp == "timer-back":
            return ("tb", int(st.get("remaining_s", 0)))
        if disp == "timer-forward":
            return ("tf", int(st.get("elapsed_s", 0)))
        if disp in ("bar", "dots"):
            # fallback dedup ~0.1% step
            p = st.get("progress", 0.0)
            try: p = float(p)
            except: p = 0.0
            return ("p", int(p * 1000))
        return ("raw", st.get("phase_id"))

    # Non-TTY-safe context
    from contextlib import contextmanager
    try:
        ctx = phase_key_mode()
    except Exception:
        @contextmanager
        def _noop(): yield
        ctx = _noop()

    try:
        with ctx:
            while True:
                st = status(sock)
                if st is None:
                    # Session ended
                    if renderer and hasattr(renderer, "close"):
                        renderer.close()
                    if ansi:
                        sys.stdout.write("\x1b[1B\n"); sys.stdout.flush()
                    else:
                        print("", flush=True)
                    print("[✓] Session finished", flush=True)
                    return

                # Key normalization
                remaining_s = st.get("remaining_s", st.get("left"))
                elapsed_s   = st.get("elapsed_s",   st.get("elapsed"))
                duration_s  = st.get("duration_s",  st.get("total"))
                display     = st.get("display", "")
                phase_id    = st.get("phase_id")
                phase_label = st.get("phase_label", "")

                payload = {
                    "phase_id": phase_id,
                    "phase_label": phase_label,
                    "display": display,
                    "progress": st.get("progress", 0.0),
                    "remaining_s": remaining_s,
                    "elapsed_s": elapsed_s,
                    "duration_s": duration_s,
                    "remaining_mmss": _mmss(remaining_s),
                    "elapsed_mmss": _mmss(elapsed_s),
                    "duration_mmss": _mmss(duration_s),
                }

                # Phase change
                if phase_id != last_phase_id:
                    last_phase_id = phase_id
                    last_key = None
                    last_status_line = None

                    print(f"{phase_label} phase begins", flush=True)

                    # initial status
                    status_line = (renderer.frame(payload)
                                   if hasattr(renderer, "frame")
                                   else renderer.update(payload))
                    if ansi:
                        _clear_and_repaint(status_line)
                    else:
                        print(status_line, flush=True)
                        last_status_line = status_line

                    # legend once
                    print("Hotkeys: Ctrl+C abort • Ctrl+E end phase • Ctrl+O detach", flush=True)

                    # park cursor on status line (ANSI)
                    if ansi:
                        sys.stdout.write("\x1b[1A"); sys.stdout.flush()

                # hotkeys
                hk = poll_hotkey()
                if hk == Hotkey.TOGGLE_HIDE:
                    if renderer and hasattr(renderer, "close"):
                        renderer.close()
                    if ansi:
                        sys.stdout.write("\x1b[1B\n"); sys.stdout.flush()
                    else:
                        print("", flush=True)
                    print("[detached] Viewer exited", flush=True)
                    return
                elif hk == Hotkey.END_PHASE:
                    try: end_phase(sock)
                    except Exception: pass
                elif hk == Hotkey.ABORT:
                    try: abort(sock)
                    except Exception: pass
                    if renderer and hasattr(renderer, "close"):
                        renderer.close()
                    if ansi:
                        sys.stdout.write("\x1b[1B\n"); sys.stdout.flush()
                    else:
                        print("", flush=True)
                    print("[✗] Session aborted", flush=True)
                    return

                # repaint/print
                status_line = (renderer.frame(payload)
                               if hasattr(renderer, "frame")
                               else renderer.update(payload))
                if ansi:
                    _clear_and_repaint(status_line)
                else:
                    key = _fingerprint(payload)
                    if key != last_key or status_line != last_status_line:
                        print(status_line, flush=True)
                        last_key = key
                        last_status_line = status_line

                time.sleep(0.2)
    finally:
        try:
            if renderer and hasattr(renderer, "close"):
                renderer.close()
        except Exception:
            pass

def run_attach_from_runtime():
    """Placeholder for attach runtime resolution."""
    print("Attach command not yet implemented")
    return


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
    """
    parser = argparse.ArgumentParser(
        prog="shellpomodoro",
        description="A cross-platform terminal-based Pomodoro timer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Hotkeys: Ctrl+C abort • Ctrl+E end phase
If no sound, see README troubleshooting (VS Code/macOS)

Examples:
  shellpomodoro                    # Use default settings (25min work, 5min break, 4 iterations)
  shellpomodoro --work 30 --break 10  # Custom work and break durations
  shellpomodoro --iterations 6     # Run 6 Pomodoro cycles
  shellpomodoro --beeps 3          # Play 3 beeps at phase transitions
  shellpomodoro --display dots --dot-interval 60  # Dots mode, one dot per minute

Display modes (--display): timer-back (default), timer-forward, bar, dots
Note: --dot-interval applies only to --display dots
        """,
    )

    parser.add_argument(
        "--work",
        type=int,
        default=25,
        metavar="MINUTES",
        help="Work period duration in minutes (default: 25)",
    )

    parser.add_argument(
        "--break",
        type=int,
        default=5,
        metavar="MINUTES",
        help="Break period duration in minutes (default: 5)",
    )

    parser.add_argument(
        "--iterations",
        type=int,
        default=4,
        metavar="COUNT",
        help="Number of Pomodoro cycles to run (default: 4)",
    )

    parser.add_argument(
        "--beeps",
        type=int,
        default=2,
        metavar="COUNT",
        help="Number of beeps to play at phase transitions (default: 2)",
    )

    parser.add_argument(
        "-v", "--version", action="store_true", help="Show version and exit"
    )

    parser.add_argument(
        "--display",
        type=str,
        choices=[m.value for m in Mode],
        default=Mode.TIMER_BACK.value,
        help="Display mode: timer-back, timer-forward, bar, dots (default: timer-back)",
    )

    parser.add_argument(
        "--dot-interval",
        type=int,
        default=None,
        metavar="SECS",
        help="Dot update interval in seconds (only for --display dots)",
    )

    parser.add_argument(
        "cmd", nargs="*", help="Subcommand (e.g., 'attach')"
    )

    # Parse arguments
    if argv is None:
        argv = sys.argv[1:]

    args = parser.parse_args(argv)

    # Validate arguments
    if args.work <= 0:
        parser.error("Work duration must be a positive integer")

    if getattr(args, "break") <= 0:
        parser.error("Break duration must be a positive integer")

    if args.iterations <= 0:
        parser.error("Number of iterations must be a positive integer")

    if args.beeps < 0:
        parser.error("Number of beeps must be non-negative")

    # Reasonable upper limits to prevent accidental very long sessions
    if args.work > 180:  # 3 hours
        parser.error("Work duration cannot exceed 180 minutes")

    if getattr(args, "break") > 60:  # 1 hour
        parser.error("Break duration cannot exceed 60 minutes")

    if args.iterations > 20:
        parser.error("Number of iterations cannot exceed 20")

    if args.beeps > 10:
        parser.error("Number of beeps cannot exceed 10")

    # dot-interval validation (when provided)
    if args.dot_interval is not None and args.dot_interval <= 0:
        parser.error("--dot-interval must be a positive integer")

    return args


def _is_ci_mode() -> bool:
    # CI/non-interactive if env var set or stdin not a TTY
    return os.getenv("SHELLPOMODORO_CI") == "1" or not sys.stdin.isatty()


def run(
    work: int,
    brk: int,
    iters: int,
    beeps: int,
    display: str = Mode.TIMER_BACK.value,
    dot_interval: Optional[int] = None,
) -> None:
    """
    Execute complete Pomodoro session with specified parameters.

    Args:
        work: Work period duration in minutes
        brk: Break period duration in minutes
        iters: Number of Pomodoro cycles to run
        beeps: Number of beeps to play at phase transitions

    Raises:
        KeyboardInterrupt: When user aborts session with Ctrl+C
    """
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
    Main entry point for shellpomodoro command.

    Handles command-line argument parsing, configuration validation,
    and session execution with appropriate exit codes.
    """
    try:
        # Parse command line arguments
        args = parse_args()

        # Handle version flag - must exit before any other output
        if args.version:
            print(importlib.metadata.version("shellpomodoro"))
            sys.exit(0)

        # Handle attach subcommand
        if hasattr(args, 'cmd') and args.cmd and args.cmd[0] == "attach":
            return run_attach_from_runtime()

        # Set up signal handler for graceful interruption
        setup_signal_handler()

        # Display session configuration
        header = session_header(args.work, getattr(args, "break"), args.iterations)
        print(header)
        print()  # Add blank line for readability

        # Execute Pomodoro session
        run(
            args.work,
            getattr(args, "break"),
            args.iterations,
            args.beeps,
            getattr(args, "display"),
            getattr(args, "dot_interval"),
        )

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\nAborted.")
        sys.exit(1)
    except Exception as e:
        # Handle unexpected errors
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
