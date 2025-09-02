"""
Shellpomodoro - A cross-platform terminal-based Pomodoro timer CLI application.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("shellpomodoro")
except PackageNotFoundError:
    # Package not installed (e.g., running from source)
    __version__ = "0.0.0"
