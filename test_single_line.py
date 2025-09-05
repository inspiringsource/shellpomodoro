#!/usr/bin/env python3
"""Test script to verify single-line behavior for bar and dots displays."""

import subprocess
import sys
import time


def test_display_mode(mode, extra_args=[]):
    """Test a display mode with single-line behavior."""
    print(f"Testing {mode} display mode...")

    cmd = [
        sys.executable,
        "-m",
        "shellpomodoro",
        "--display",
        mode,
        "--work",
        "1",  # 1 minute for quick test
        "--iterations",
        "1",
    ] + extra_args

    # Start the process
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={"COLUMNS": "60"},  # Limit width to test truncation
    )

    # Let it run for a few seconds
    time.sleep(3)

    # Terminate it
    proc.terminate()
    stdout, stderr = proc.communicate(timeout=5)

    return stdout, stderr


def main():
    print("Testing single-line display implementations...")
    print("=" * 50)

    # Test bar display
    try:
        stdout, stderr = test_display_mode("bar")
        print(f"Bar display output (first few lines):")
        lines = stdout.split("\n")[:10]
        for i, line in enumerate(lines):
            print(f"  {i+1}: {repr(line)}")
        print()
    except Exception as e:
        print(f"Error testing bar display: {e}")

    # Test dots display
    try:
        stdout, stderr = test_display_mode("dots", ["--dot-interval", "2"])
        print(f"Dots display output (first few lines):")
        lines = stdout.split("\n")[:10]
        for i, line in enumerate(lines):
            print(f"  {i+1}: {repr(line)}")
        print()
    except Exception as e:
        print(f"Error testing dots display: {e}")

    # Test timer-back (should be multi-line)
    try:
        stdout, stderr = test_display_mode("timer-back")
        print(f"Timer-back display output (first few lines):")
        lines = stdout.split("\n")[:10]
        for i, line in enumerate(lines):
            print(f"  {i+1}: {repr(line)}")
        print()
    except Exception as e:
        print(f"Error testing timer-back display: {e}")


if __name__ == "__main__":
    main()
