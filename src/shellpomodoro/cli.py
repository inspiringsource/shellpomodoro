"""
Cross-platform Pomodoro timer CLI implementation.
"""

import sys
import time
import platform
import signal
import argparse
from contextlib import contextmanager
from typing import List


# ASCII art for completion message
GOOD_JOB = """
 ██████╗  ██████╗  ██████╗ ██████╗      ██╗ ██████╗ ██████╗ ██╗
██╔════╝ ██╔═══██╗██╔═══██╗██╔══██╗     ██║██╔═══██╗██╔══██╗██║
██║  ███╗██║   ██║██║   ██║██║  ██║     ██║██║   ██║██████╔╝██║
██║   ██║██║   ██║██║   ██║██║  ██║██   ██║██║   ██║██╔══██╗╚═╝
╚██████╔╝╚██████╔╝╚██████╔╝██████╔╝╚█████╔╝╚██████╔╝██████╔╝██╗
 ╚═════╝  ╚═════╝  ╚═════╝ ╚═════╝  ╚════╝  ╚═════╝ ╚═════╝ ╚═╝
"""


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
    return 'windows' if platform.system() == 'Windows' else 'unix'


def _read_key_windows(prompt: str = "Press any key to continue...") -> None:
    """
    Windows-specific keypress handling using msvcrt.
    
    Args:
        prompt: Message to display to user
    """
    try:
        import msvcrt
        print(prompt, end='', flush=True)
        msvcrt.getch()
        print()  # Add newline after keypress
    except ImportError:
        # Fallback to standard input if msvcrt is not available
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
    Unix-specific keypress handling using termios and tty modules.
    
    Args:
        prompt: Message to display to user
    """
    import sys
    if not sys.stdin.isatty():
        print(f"{prompt} [auto-continue: non-TTY]")
        return
        
    try:
        print(prompt, end='', flush=True)
        
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
    
    if current_platform == 'windows':
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
        print('\a', end='', flush=True)
        
        # Add interval between beeps (except after the last beep)
        if i < times - 1:
            time.sleep(interval)


def countdown(seconds: int, label: str) -> None:
    """
    Display real-time countdown with abort capability.
    
    Args:
        seconds: Duration of countdown in seconds
        label: Phase label to display (e.g., "Focus", "Break")
        
    Raises:
        KeyboardInterrupt: When user presses Ctrl+C to abort
    """
    try:
        remaining = seconds
        
        while remaining > 0:
            # Clear line and display countdown
            print(f"\r{label}: {mmss(remaining)} (Ctrl+C to abort)", end='', flush=True)
            
            # Sleep for 200ms update interval
            time.sleep(0.2)
            remaining -= 0.2
            
            # Ensure we don't go below zero due to floating point precision
            remaining = max(0, remaining)
        
        # Final display showing completion
        print(f"\r{label}: {mmss(0)} (Ctrl+C to abort)", end='', flush=True)
        print()  # Add newline after countdown completes
        
    except KeyboardInterrupt:
        # Clean up display and re-raise for caller to handle
        print("\nAborted.")
        raise


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
    return (f"Pomodoro Session: {work_min}min work, {break_min}min break, "
            f"{iterations} iteration{'s' if iterations != 1 else ''}")


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
        prog='shellpomodoro',
        description='A cross-platform terminal-based Pomodoro timer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  shellpomodoro                    # Use default settings (25min work, 5min break, 4 iterations)
  shellpomodoro --work 30 --break 10  # Custom work and break durations
  shellpomodoro --iterations 6     # Run 6 Pomodoro cycles
  shellpomodoro --beeps 3          # Play 3 beeps at phase transitions
        """
    )
    
    parser.add_argument(
        '--work',
        type=int,
        default=25,
        metavar='MINUTES',
        help='Work period duration in minutes (default: 25)'
    )
    
    parser.add_argument(
        '--break',
        type=int,
        default=5,
        metavar='MINUTES',
        help='Break period duration in minutes (default: 5)'
    )
    
    parser.add_argument(
        '--iterations',
        type=int,
        default=4,
        metavar='COUNT',
        help='Number of Pomodoro cycles to run (default: 4)'
    )
    
    parser.add_argument(
        '--beeps',
        type=int,
        default=2,
        metavar='COUNT',
        help='Number of beeps to play at phase transitions (default: 2)'
    )
    
    # Parse arguments
    if argv is None:
        argv = sys.argv[1:]
    
    args = parser.parse_args(argv)
    
    # Validate arguments
    if args.work <= 0:
        parser.error("Work duration must be a positive integer")
    
    if getattr(args, 'break') <= 0:
        parser.error("Break duration must be a positive integer")
    
    if args.iterations <= 0:
        parser.error("Number of iterations must be a positive integer")
    
    if args.beeps < 0:
        parser.error("Number of beeps must be non-negative")
    
    # Reasonable upper limits to prevent accidental very long sessions
    if args.work > 180:  # 3 hours
        parser.error("Work duration cannot exceed 180 minutes")
    
    if getattr(args, 'break') > 60:  # 1 hour
        parser.error("Break duration cannot exceed 60 minutes")
    
    if args.iterations > 20:
        parser.error("Number of iterations cannot exceed 20")
    
    if args.beeps > 10:
        parser.error("Number of beeps cannot exceed 10")
    
    return args


def run(work: int, brk: int, iters: int, beeps: int) -> None:
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
        
        # Execute each Pomodoro iteration
        for iteration in range(1, iters + 1):
            # Work phase
            work_label = iteration_progress(iteration, iters, "Focus")
            countdown(work_seconds, work_label)
            
            # Play notification beeps after work phase
            beep(beeps)
            
            # Check if this is the final iteration
            if iteration == iters:
                # Final iteration - no break phase, show completion
                print()
                print(banner())
                break
            else:
                # Wait for keypress before break (except final iteration)
                read_key("Work phase complete! Press any key to start break...")
                
                # Break phase
                break_label = iteration_progress(iteration, iters, "Break")
                countdown(break_seconds, break_label)
                
                # Play notification beeps after break phase
                beep(beeps)
                
                # Wait for keypress before next work phase (except after final break)
                if iteration < iters:
                    read_key("Break complete! Press any key to start next work phase...")
                    
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
        
        # Set up signal handler for graceful interruption
        setup_signal_handler()
        
        # Display session configuration
        header = session_header(args.work, getattr(args, 'break'), args.iterations)
        print(header)
        print()  # Add blank line for readability
        
        # Execute Pomodoro session
        run(args.work, getattr(args, 'break'), args.iterations, args.beeps)
        
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\nAborted.")
        sys.exit(1)
    except Exception as e:
        # Handle unexpected errors
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)