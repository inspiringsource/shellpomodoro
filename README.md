# Shellpomodoro

---

[![PyPI version](https://img.shields.io/pypi/v/shellpomodoro.svg)](https://pypi.org/project/shellpomodoro/) [![Python versions](https://img.shields.io/pypi/pyversions/shellpomodoro.svg)](https://pypi.org/project/shellpomodoro/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

`shellpomodoro` = Shell + Pomodoro timer. Built for my own use; sharing in case it helps others too.

A cross-platform terminal-based Pomodoro timer CLI application with multiple display modes, session detach/reattach capabilities, and background session management. Installable via pip and runs anywhere with zero external dependencies.

## Features

- 🍅 Classic Pomodoro technique with customizable work and break durations
- 📊 **Multiple modes**: countdown timer, count-up timer, progress bar, or test-runner style dots
- ⏱️ Real-time countdown display with MM:SS format
- 🔔 Terminal bell notifications at phase transitions
- ⌨️ Keypress-controlled phase transitions (no need to wait) \
~~- 🔌 **Detach/reattach sessions**: Run sessions in background with `Ctrl+O`, reattach from any terminal~~
- 🎨 ASCII art congratulations upon session completion
- 🖥️ Cross-platform support (Windows, macOS, Linux)
- 📦 Zero external dependencies (Python stdlib only)
- 🚀 Fast installation via pip

## Installation

### From PyPI (Recommended)

```bash
pip install shellpomodoro
```

Or using `uv` (even faster):

```bash
uv pip install shellpomodoro
````

### Development Installation (from source)

```bash
git clone https://github.com/inspiringsource/shellpomodoro.git
cd shellpomodoro
#python3 -m venv .venv
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# Windows CMD
.\.venv\Scripts\activate.bat
pip install -U pip
pip install -e .
```

## Usage

### Basic Usage

Start a default Pomodoro session (25min work, 5min break, 4 iterations):

```bash
shellpomodoro
```

### Customization Options

```bash
# Custom work and break durations
shellpomodoro --work 30 --break 10

# Custom number of iterations
shellpomodoro --iterations 6

# Custom notification beeps
shellpomodoro --beeps 3

# Different display modes
shellpomodoro --display bar          # Progress bar
shellpomodoro --display dots         # Test-runner style dots
shellpomodoro --display timer-forward # Count up from 00:00

# Combine all options
shellpomodoro --work 45 --break 15 --iterations 3 --beeps 1 --display bar
```

### Command Line Options

- `--work N`: Set work period duration in minutes (default: 25)
- `--break N`: Set break period duration in minutes (default: 5)
- `--iterations N`: Set number of Pomodoro cycles (default: 4)
- `--beeps N`: Set number of notification beeps (default: 2)
- `--display MODE`: Set display mode: `timer-back` (default), `timer-forward`, `bar`, or `dots`
- `--dot-interval N`: Dot emission interval in seconds (only for dots mode)
- `--version`, `-v`: Show version and exit
- `--help`: Show help message and exit

### Display modes

By default, shellpomodoro shows a countdown timer. You can pick other displays:

```bash
# default behavior (countdown)
shellpomodoro --display timer-back

# count up from 00:00
shellpomodoro --display timer-forward

# progress bar
shellpomodoro --display bar

# test-runner style dots
shellpomodoro --display dots --dot-interval 60   # one dot per minute
```

- `--dot-interval` (seconds) is optional and only used with dots.
  If omitted, shellpomodoro uses a sensible default (one dot per minute for long phases; ~10 dots for short ones).

### Screenshots

**Default Timer (timer-back)**
![Shellpomodoro Default](screenshots/shellpomodoro-default.png)

**Progress Bar**
![Shellpomodoro Bar](screenshots/shellpomodoro-bar.png)

**Dots Mode**
![Shellpomodoro Dots](screenshots/shellpomodoro-dots.png)

## How It Works

1. **Work Phase**: Focus on your task while the timer counts down
2. **Notification**: Terminal bell sounds when work phase ends
3. **Keypress Transition**: Press any key when ready for break
4. **Break Phase**: Take a break while the timer counts down
5. **Repeat**: Continue until all iterations are complete
6. **Completion**: Enjoy ASCII art congratulations!

### Session Control

- **Check Version**: Run `shellpomodoro --version` or `shellpomodoro -v`
- **Abort Session**: Press `Ctrl+C` at any time to abort the current session
- **Phase Transitions**: Press `Ctrl+E` to end the current phase early (WORK → BREAK, BREAK → next WORK)
- **Detach Session**: Press `Ctrl+O` to detach the UI while keeping the session running in background
- **Real-time Display**: See countdown timer, current phase, and hotkey instructions

## Detach / Reattach

- Press `Ctrl+O` to **detach** the UI; the session continues in the background.
- Run `shellpomodoro attach` to **reattach** from the same or another terminal and resume viewing.
- Hotkeys are shown once per phase on a separate line under the timer/progress line.
- Beeps continue while detached: Windows (winsound), macOS/Linux best-effort via terminal bell.

Example legend placement:

```bash
[[1/4] Focus] 24:57
Hotkeys: Ctrl+C abort • Ctrl+E end phase • Ctrl+O detach
```

## Requirements

- Python 3.9 or higher
- No external dependencies required

## Cross-Platform Compatibility

Shellpomodoro works seamlessly across different operating systems:

- **Windows**: Uses `msvcrt` for keypress detection
- **Unix/Linux/macOS**: Uses `termios` and `tty` for terminal control
- **Terminal Bell**: Uses standard `\a` character (may require terminal configuration)

### Troubleshooting: No Beep in VS Code

If you don't hear the terminal bell when running in the VS Code integrated terminal, you may need to enable audio cues in your VS Code settings. Add the following to your `settings.json`:

```json
{
  "terminal.integrated.enableVisualBell": true,
  "accessibility.signals.terminalBell": {
    "sound": "on"
  },
  "audioCues.enabled": "on",
  "audioCues.terminalBell": "on"
}
```

This enables the audible bell and ensures `\a` is played as a sound when Shellpomodoro triggers notifications.

## Examples

### Quick 15-minute session

```bash
shellpomodoro --work 15 --break 5 --iterations 1
```

### Extended deep work session

```bash
shellpomodoro --work 50 --break 10 --iterations 3
```

### Different display modes

```bash
# Progress bar mode
shellpomodoro --display bar

# Dots mode with custom interval
shellpomodoro --display dots --dot-interval 30

# Count-up timer
shellpomodoro --display timer-forward
```

### Background session management

```bash
# Start a session, detach with Ctrl+O, then reattach later
shellpomodoro --work 25 --break 5
# ... press Ctrl+O to detach ...
shellpomodoro attach  # reattach from same or different terminal
```

### Silent mode (no beeps)

```bash
shellpomodoro --beeps 0
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please open an issue on the GitHub repository.

## What's New in v0.1.5

- **🎯 Multiple Display Modes**: Choose from countdown timer (default), count-up timer, progress bar, or test-runner style dots
- **🔌 Session Detach/Reattach**: Start a session, detach with `Ctrl+O`, and reattach from any terminal with `shellpomodoro attach`
- **⌨️ Enhanced Hotkeys**: `Ctrl+C` to abort, `Ctrl+E` to end phase early, `Ctrl+O` to detach
- **📊 Visual Progress Tracking**: Progress bars show completion percentage and remaining time
- **🔄 Background Session Management**: Sessions continue running even when detached
- **🎨 Improved UI**: Better formatted status lines with phase indicators `[[1/4] Focus] 24:57`

## Development History

This project was initiated using Kiro, which helped establish the initial structure and core functionality of the Pomodoro timer (the original `design.md`, `requirements.md`, and `tasks.md` are included in the repo). Later, the codebase was optimized and refined using Grok code / Claude Sonnet 4 to improve performance, code quality, and maintainability.
