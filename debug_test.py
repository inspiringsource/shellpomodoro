#!/usr/bin/env python3

import sys

sys.path.insert(0, "src")

from unittest.mock import patch, MagicMock


class FakeTimer:
    single_line = True

    def __init__(self):
        self.calls = 0

    def update(self, elapsed):
        self.calls += 1
        return f"[Focus] ⏳ 01:0{self.calls}"

    def close(self):
        pass


def test_minimal():
    fake_ticks = [
        {"phase_id": 1, "phase_label": "Focus", "left": 60, "total": 60},
        {"phase_id": 1, "phase_label": "Focus", "left": 59, "total": 60},
        None,
    ]

    call_count = [0]

    def fake_status(sock):
        if call_count[0] < len(fake_ticks):
            result = fake_ticks[call_count[0]]
            call_count[0] += 1
            print(f"Returning status: {result}")
            return result
        return None

    captured_prints = []

    def capture_print(*args, **kwargs):
        captured_prints.append(str(args))
        print(*args, **kwargs)  # Also actually print for debugging

    with patch(
        "src.shellpomodoro.cli.make_renderer", return_value=FakeTimer()
    ) as mock_make:
        with patch("src.shellpomodoro.cli._supports_ansi", return_value=False):
            with patch("src.shellpomodoro.ipc._connect", return_value=MagicMock()):
                with patch("src.shellpomodoro.ipc.hello", return_value=True):
                    with patch("src.shellpomodoro.ipc.status", side_effect=fake_status):
                        with patch(
                            "src.shellpomodoro.keypress.poll_hotkey", return_value=None
                        ):
                            with patch("time.sleep"):
                                with patch("builtins.print", side_effect=capture_print):
                                    from src.shellpomodoro.cli import attach_ui

                                    attach_ui({"port": 1234, "secret": "x"})

    print("Captured prints:", captured_prints)
    timer_calls = [call for call in captured_prints if "⏳ 01:0" in str(call)]
    print("Timer calls:", timer_calls)
    print("Should have >= 1 timer calls")


if __name__ == "__main__":
    test_minimal()
