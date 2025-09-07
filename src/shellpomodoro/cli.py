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
from .runtime import read_runtime, cleanup_stale_runtime
import shellpomodoro.runtime as runtime


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
    import sys

    # Check for non-interactive override first
    if os.getenv("SHELLPOMODORO_NONINTERACTIVE") == "1":
        print(f"{prompt} [auto-continue: non-interactive]")
        return

    # Check if we're in a non-TTY environment
    if not sys.stdin.isatty():
        print(f"{prompt} [auto-continue: non-TTY]")
        return

    try:
        import msvcrt

        # Check if msvcrt was mocked to None (for testing)
        if msvcrt is None:
            raise ImportError("msvcrt mocked to None")
        print(prompt, end="", flush=True)
        # Wait for keypress using msvcrt
        msvcrt.getch()
        print()  # Add newline after keypress
    except (ImportError, OSError):
        # Fallback to standard input if msvcrt fails
        input(prompt)


@contextmanager
def _raw_terminal():
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
    Unix-specific keypress handling using termios.

    Args:
        prompt: Message to display to user
    """
    import sys

    # Check for non-interactive override first
    if os.getenv("SHELLPOMODORO_NONINTERACTIVE") == "1":
        print(f"{prompt} [auto-continue: non-interactive]")
        return

    # Check if we're in a non-TTY environment
    if not sys.stdin.isatty():
        print(f"{prompt} [auto-continue: non-TTY]")
        return

    try:
        import termios
        import tty

        print(prompt, end="", flush=True)
        # Get current terminal settings
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            # Set terminal to raw mode for single character input
            tty.setraw(sys.stdin.fileno())
            # Read single character
            sys.stdin.read(1)
        finally:
            # Restore original terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        print()  # Add newline after keypress
    except (ImportError, OSError):
        # Fallback to standard input if termios fails
        input(prompt)
    except Exception:
        # Catch any other termios-related errors
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


def session_header(
    work: int,
    break_minutes: int,
    iterations: int,
    beeps: int = None,
    display: str = None,
) -> str:
    """Return a single-line header used by tests and manual runs."""
    if beeps is None and display is None:
        # Legacy 3-argument format for tests
        iter_text = "iteration" if iterations == 1 else "iterations"
        return f"Pomodoro Session: {work}min work, {break_minutes}min break, {iterations} {iter_text}"
    else:
        # New 5-argument format for main flow
        return (
            f"Pomodoro Session — work={work} break={break_minutes} "
            f"iterations={iterations} beeps={beeps} display={display}"
        )


def legend_line() -> str:
    return "Hotkeys: Ctrl+C abort • Ctrl+E end phase • Ctrl+O detach"


def _safe_line(s) -> str:
    """Return a string for UI rendering; coerce None to empty string."""
    return s if isinstance(s, str) else ""


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
    p = argparse.ArgumentParser(
        prog="shellpomodoro",
        description="Pomodoro timer CLI for focused work sessions",
        add_help=True,
    )
    p.add_argument(
        "--work",
        type=int,
        default=25,
        dest="work",
        metavar="MINUTES",
        help="Work duration in minutes",
    )
    p.add_argument(
        "--break",
        type=int,
        default=5,
        metavar="MINUTES",
        help="Break duration in minutes",
    )
    p.add_argument(
        "--iterations",
        type=int,
        default=4,
        metavar="COUNT",
        help="Number of work/break cycles",
    )
    p.add_argument(
        "--beeps",
        type=int,
        default=2,
        metavar="COUNT",
        help="Number of notification beeps",
    )
    p.add_argument(
        "--display",
        choices=("timer-back", "timer-forward", "bar", "dots"),
        default="timer-back",
        help="Display mode for timer",
    )
    p.add_argument(
        "--dot-interval",
        type=int,
        default=None,
        dest="dot_interval",
        help="Dot interval in seconds for dots mode",
    )
    p.add_argument("--version", "-v", action="store_true", help="Show version and exit")
    p.add_argument(
        "subcommand",
        nargs="?",
        choices=("attach",),
        default=None,
        help="Attach to existing session",
    )

    # Add examples to help
    p.epilog = """
Examples:
  shellpomodoro                                 # Default: 25min work, 5min break, 4 cycles
  shellpomodoro --work 50 --break 10           # Custom work/break duration
  shellpomodoro --iterations 6 --beeps 0       # 6 cycles with no beeps
  shellpomodoro --display bar                  # Use progress bar display
  shellpomodoro attach                         # Attach to existing session
    """

    args = p.parse_args(argv)

    # Handle version flag manually to match test expectations
    if args.version:
        import importlib.metadata

        version = importlib.metadata.version("shellpomodoro")
        print(version)
        sys.exit(0)

    # Validate argument ranges
    if args.work <= 0:
        p.error("Work duration must be positive")
    if getattr(args, "break") <= 0:
        p.error("Break duration must be positive")
    if args.iterations <= 0:
        p.error("Iterations must be positive")
    if args.beeps < 0:
        p.error("Beeps must be non-negative")

    # Validate upper limits
    if args.work > 180:
        p.error("Work duration cannot exceed 180 minutes")
    if getattr(args, "break") > 60:
        p.error("Break duration cannot exceed 60 minutes")
    if args.iterations > 20:
        p.error("Iterations cannot exceed 20")
    if args.beeps > 10:
        p.error("Beeps cannot exceed 10")

    return args


def _is_ci_mode() -> bool:
    """
    Check if running in CI/non-interactive mode.

    Returns:
        bool: True if CI mode or stdin is not a TTY
    """
    # CI/non-interactive if env var set or stdin not a TTY
    return os.getenv("SHELLPOMODORO_CI") == "1" or not sys.stdin.isatty()


def _existing_session_info() -> Optional[dict]:
    """
    Get connection info for existing session daemon.

    Returns:
        dict: Connection info with port/secret, or None if no active session
    """
    cleanup_stale_runtime()  # Clean up dead sessions first
    runtime = read_runtime()
    if not runtime:
        return None

    # Check if we have the required connection info
    if "port" not in runtime or "secret" not in runtime:
        return None

    return {
        "port": runtime["port"],
        "secret": runtime["secret"],
        "display": runtime.get("display", "timer-back"),
    }


def run(
    work: int,
    break_: int = None,
    iterations: int = None,
    beeps: int = 2,
    display: str = "timer-back",
    dot_interval: int | None = None,
    # Legacy parameter names for backward compatibility
    brk: int = None,
    iters: int = None,
) -> bool:
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
        bool: True on successful completion, False on abort/interrupt
    """
    # Handle legacy parameter names for backward compatibility
    if brk is not None:
        break_ = brk
    if iters is not None:
        iterations = iters

    # (existing implementation continues here)
    try:
        # Convert minutes to seconds for countdown
        work_seconds = work * 60
        break_seconds = break_ * 60

        # Build renderer
        mode = Mode(display)
        renderer = make_renderer(mode, dot_interval)

        # Execute each Pomodoro iteration
        for iteration in range(1, iterations + 1):
            # Work phase
            work_label = iteration_progress(iteration, iterations, "Focus")
            work_result = countdown(work_seconds, work_label, renderer)

            # Play notification beeps after work phase
            if not _is_ci_mode():
                beep(beeps)

            # Check if this is the final iteration
            if iteration == iterations:
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
                break_label = iteration_progress(iteration, iterations, "Break")
                # Separate phases visually for DOTS
                if mode == Mode.DOTS:
                    print("\n│")
                break_result = countdown(break_seconds, break_label, renderer)

                # Play notification beeps after break phase
                if not _is_ci_mode():
                    beep(beeps)

                # Wait for keypress before next work phase (except after final break)
                if iteration < iterations:
                    if break_result == PhaseResult.ENDED_EARLY or _is_ci_mode():
                        # Skip the keypress wait if break was ended early
                        pass
                    else:
                        read_key(
                            "Break complete! Press any key to start next work phase..."
                        )

        return True

    except KeyboardInterrupt:
        # Re-raise to be handled by caller
        raise


def main():
    """
    CLI entry point with no arguments for setuptools compatibility.
    Returns an int exit code for normal flow.
    Uses sys.exit() for error conditions to match test expectations.
    """
    return _main_impl(None)


def _main_impl(argv: list[str] | None = None) -> int:
    """
    Main implementation that can take argv parameter for testing.
    """
    try:
        args = parse_args(argv)

        work = int(args.work)
        break_minutes = int(getattr(args, "break"))
        iterations = int(args.iterations)
        beeps = int(args.beeps)
        display = args.display
        dot_interval = int(args.dot_interval) if args.dot_interval else None

        # Subcommands
        if getattr(args, "subcommand", None) == "attach":
            try:
                # Check for existing session
                info = _existing_session_info()
                if not info:
                    print("No active shellpomodoro session")
                    sys.exit(1)

                # Attach to existing session
                attach_ui(info)
                return 0
            except KeyboardInterrupt:
                print("\nAborted.")
                sys.exit(1)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

        setup_signal_handler()

        print(
            session_header(work, break_minutes, iterations, beeps, display), flush=True
        )
        legend = legend_line()
        if legend:
            print(legend, flush=True)

        ok = run(work, break_minutes, iterations, beeps, display, dot_interval)
        return 0 if ok else 1
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(1)
    except SystemExit as e:
        # Re-raise SystemExit to preserve exit codes (e.g., version flag)
        raise e
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def attach_ui(info: dict) -> None:
    """
    Connect to the background session daemon and render the live UI in the terminal.

    Features:
      - Prints a phase header once, a status line that repaints in place, and a legend line.
      - Ctrl+O detaches the viewer (daemon keeps running).
      - Ctrl+E ends the current phase.
      - Ctrl+C aborts the whole session.

    Args:
        info: Connection metadata, e.g., {"port": int, "secret": str}.

    Returns:
        None
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
        display_mode = info.get("display", "timer-back")
        mode = Mode(display_mode)
        dot_interval = info.get("dot_interval")
        renderer = make_renderer(mode, dot_interval)
    except Exception as e:
        print(f"Unable to create UI renderer: {e}", flush=True)
        return

    last_phase_id = None
    last_key = None
    ansi = _supports_ansi()

    def _mmss(s: int | None) -> str:
        s = 0 if s is None else int(max(0, s))
        return f"{s//60:02d}:{s%60:02d}"

    def _fingerprint(st: dict):
        d = st.get("display", "")
        if d == "timer-back":
            return ("tb", int(st.get("remaining_s") or 0))
        if d == "timer-forward":
            return ("tf", int(st.get("elapsed_s") or 0))
        if d in ("bar", "dots"):
            return ("p", int(round(st.get("progress", 0.0) * 1000)))
        # Default: use remaining_s as fallback for timer modes
        return ("def", int(st.get("remaining_s") or 0))

    try:
        # Safe phase_key_mode for non-TTY environments
        try:
            cm = phase_key_mode()
        except Exception:

            class _Noop:
                def __enter__(self):
                    return None

                def __exit__(self, *a):
                    return False

            cm = _Noop()

        with cm:
            while True:
                # Check for hotkeys first
                hk = poll_hotkey()
                if hk == Hotkey.TOGGLE_HIDE:
                    if ansi:
                        sys.stdout.write("\x1b[1B\n")
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

                # Normalize payload keys for test compatibility
                remaining_s = st.get("remaining_s", st.get("left"))
                elapsed_s = st.get("elapsed_s", st.get("elapsed"))
                duration_s = st.get("duration_s", st.get("total"))

                # Extract phase info for status line formatting
                phase_parts = st.get("phase_label", "").split("] ")
                if len(phase_parts) == 2 and phase_parts[0].startswith("["):
                    # Extract "[1/4] Focus" -> i=1, n=4, phase_label="Focus"
                    bracket_part = phase_parts[0][1:]  # Remove [
                    if "/" in bracket_part:
                        i_str, n_str = bracket_part.split("/")
                        try:
                            i, n = int(i_str), int(n_str)
                            phase_label = phase_parts[1]
                        except ValueError:
                            i, n, phase_label = 1, 1, st.get("phase_label", "")
                    else:
                        i, n, phase_label = 1, 1, st.get("phase_label", "")
                else:
                    i, n, phase_label = 1, 1, st.get("phase_label", "")

                payload = {
                    "phase_id": st.get("phase_id"),
                    "phase_label": phase_label,
                    "i": i,
                    "n": n,
                    "display": st.get("display", ""),
                    "progress": st.get("progress", 0.0),
                    "remaining_s": remaining_s,
                    "elapsed_s": elapsed_s,
                    "duration_s": duration_s,
                    "remaining_mmss": _mmss(remaining_s),
                    "elapsed_mmss": _mmss(elapsed_s),
                    "duration_mmss": _mmss(duration_s),
                }
                phase_id = payload["phase_id"]
                phase_label = payload["phase_label"]
                cur_key = _fingerprint(payload)

                new_phase = (last_phase_id is None) or (phase_id != last_phase_id)
                if new_phase:
                    last_phase_id = phase_id
                    last_key = cur_key
                    status_line = renderer.frame(payload)
                    status_line = _safe_line(status_line)

                    if ansi:
                        # Print status line, then legend below, then move cursor back to status line
                        sys.stdout.write("\x1b[2K\r" + status_line + "\n")
                        legend = legend_line()
                        if legend:
                            print(legend, flush=True)
                        sys.stdout.write("\x1b[1A")
                        sys.stdout.flush()
                    else:
                        print(status_line, flush=True)
                        legend = legend_line()
                        if legend:
                            print(legend, flush=True)
                    continue

                # Decide whether to repaint based on display mode
                force_repaint = ansi and (payload["display"] in {"bar", "dots"})
                should_repaint = force_repaint or (cur_key != last_key)
                if not should_repaint:
                    time.sleep(0.1)
                    continue

                last_key = cur_key
                status_line = renderer.frame(payload)
                status_line = _safe_line(status_line)
                if ansi:
                    # ANSI: clear line and repaint in place
                    sys.stdout.write("\x1b[2K\r" + status_line)
                    sys.stdout.flush()
                else:
                    # Fallback: only print if changed
                    print(status_line, flush=True)

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
