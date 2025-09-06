#!/usr/bin/env python3
"""Clean up any stale shellpomodoro daemon processes and runtime files."""

import json
import os
import signal
import sys
import tempfile
import time


def cleanup_daemon():
    """Find and kill stale daemon, remove runtime file."""
    base = (
        os.environ.get("XDG_RUNTIME_DIR")
        or os.environ.get("TMPDIR")
        or tempfile.gettempdir()
    )
    runtime_file = os.path.join(base, "shellpomodoro", "shellpomodoro-runtime.json")

    if not os.path.exists(runtime_file):
        print("No runtime file found")
        return

    try:
        with open(runtime_file, "r") as f:
            data = json.load(f)

        pid = data.get("pid")
        if pid:
            try:
                # Check if process exists
                os.kill(pid, 0)
                print(f"Killing daemon process {pid}")
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.3)
            except ProcessLookupError:
                print(f"Process {pid} already gone")
            except Exception as e:
                print(f"Error dealing with process {pid}: {e}")

    except Exception as e:
        print(f"Error reading runtime file: {e}")

    # Remove runtime file
    try:
        os.remove(runtime_file)
        print("Removed runtime file")
    except FileNotFoundError:
        print("Runtime file already gone")
    except Exception as e:
        print(f"Error removing runtime file: {e}")


if __name__ == "__main__":
    cleanup_daemon()
