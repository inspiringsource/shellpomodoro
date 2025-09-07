"""Smoke tests for CLI functionality."""

import subprocess
import sys
import os


def test_header_and_legend_present_default_invocation():
    """Test that header and legend are present in default invocation."""
    # Use environment variables to make it non-interactive and fast
    env = os.environ.copy()
    env["SHELLPOMODORO_NONINTERACTIVE"] = "1"
    env["SHELLPOMODORO_CI"] = "1"

    try:
        result = subprocess.run(
            [
                "shellpomodoro",
                "--work",
                "1",
                "--break",
                "1",
                "--iterations",
                "1",
                "--display",
                "timer-back",
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=2,
            input="\n",  # Send newline in case it's waiting for input
        )
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired as e:
        # Extract partial output from timeout exception
        stdout = e.stdout.decode("utf-8") if e.stdout else ""
        stderr = e.stderr.decode("utf-8") if e.stderr else ""
        output = stdout + stderr

    # Check for the actual header format we observed
    assert "Pomodoro Session — work=1 break=1 iterations=1" in output
    assert "Hotkeys: Ctrl+C abort • Ctrl+E end phase • Ctrl+O detach" in output


def test_help_exits_zero():
    """Test that --help exits with code 0."""
    result = subprocess.run(["shellpomodoro", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Pomodoro timer CLI" in result.stdout


def test_attach_no_session_message():
    """Test attach command when no session is running."""
    result = subprocess.run(["shellpomodoro", "attach"], capture_output=True, text=True)
    assert result.returncode == 1
    assert "No active shellpomodoro session" in result.stdout
