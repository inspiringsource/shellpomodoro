"""Test version flag functionality."""

import subprocess
import sys


def test_version_flag_prints_and_exits_zero():
    """Test that --version prints version and exits with code 0."""
    result = subprocess.run(
        ["shellpomodoro", "--version"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert result.stdout.strip()  # Non-empty output
    # Should contain a version-like string (digits and dots)
    version_output = result.stdout.strip()
    assert any(char.isdigit() for char in version_output)
