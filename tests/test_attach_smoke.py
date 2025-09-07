"""Smoke test for attach functionality."""

import subprocess
import sys


def test_attach_no_session_exits_properly():
    """Test attach command behavior when no session exists."""
    result = subprocess.run(["shellpomodoro", "attach"], capture_output=True, text=True)

    # Should exit with non-zero code and show appropriate message
    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "No active shellpomodoro session" in output


def test_detach_message_string_exists():
    """Test that the detach message string is accessible."""
    # Import the attach_ui function to verify the detach message is available
    from shellpomodoro.cli import legend_line

    # The legend line should mention detach functionality
    legend = legend_line()
    assert "detach" in legend.lower()

    # Verify the expected detach message format exists in the codebase
    # This is a structural test to ensure the message hasn't been removed
    import shellpomodoro.cli as cli_module
    import inspect

    source = inspect.getsource(cli_module.attach_ui)
    assert "[detached] Viewer exited" in source
