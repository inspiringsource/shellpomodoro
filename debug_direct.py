#!/usr/bin/env python3

import sys
import unittest.mock

# Test direct import and call
try:
    from src.shellpomodoro.cli import attach_ui

    print("Successfully imported attach_ui")

    # Add a simple debug call
    with unittest.mock.patch("src.shellpomodoro.ipc._connect") as mock_connect:
        mock_connect.side_effect = ConnectionRefusedError("Test error")

        print("About to call attach_ui...")
        attach_ui({"port": 1234, "secret": "x"})
        print("attach_ui call completed")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
