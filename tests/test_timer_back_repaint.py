"""Test timer-back repaints once per second, no duplicate first print."""

import io
import contextlib
from unittest.mock import patch, MagicMock
from src.shellpomodoro.display import Mode


def test_timer_back_single_print_per_second():
    """Test that timer-back prints exactly once per second change."""
    captured = io.StringIO()

    # Mock a sequence of status frames with decreasing remaining_s
    status_frames = [
        {
            "phase_id": "1_Focus",
            "phase_label": "[1/1] Focus",
            "remaining_s": 59,
            "elapsed_s": 1,
            "duration_s": 60,
            "display": "timer-back",
        },
        {
            "phase_id": "1_Focus",
            "phase_label": "[1/1] Focus",
            "remaining_s": 58,
            "elapsed_s": 2,
            "duration_s": 60,
            "display": "timer-back",
        },
        {
            "phase_id": "1_Focus",
            "phase_label": "[1/1] Focus",
            "remaining_s": 57,
            "elapsed_s": 3,
            "duration_s": 60,
            "display": "timer-back",
        },
        None,  # Session ended
    ]

    call_count = [0]

    def mock_status(sock):
        if call_count[0] < len(status_frames):
            result = status_frames[call_count[0]]
            call_count[0] += 1
            return result
        return None

    class FakeTimerBack:
        single_line = True

        def frame(self, payload):
            remaining = int(payload.get("remaining_s", 0))
            m, s = divmod(remaining, 60)
            return f"⏳ {m:02d}:{s:02d}"

        def close(self):
            pass

        def start_phase(self, kind, total_s):
            pass

    with patch("src.shellpomodoro.cli.make_renderer", return_value=FakeTimerBack()):
        with patch("src.shellpomodoro.cli._supports_ansi", return_value=True):
            with patch("src.shellpomodoro.ipc._connect", return_value=MagicMock()):
                with patch("src.shellpomodoro.ipc.hello", return_value=True):
                    with patch("src.shellpomodoro.ipc.status", side_effect=mock_status):
                        with patch(
                            "src.shellpomodoro.keypress.poll_hotkey", return_value=None
                        ):
                            with patch("src.shellpomodoro.keypress.phase_key_mode"):
                                with patch("time.sleep"):
                                    with contextlib.redirect_stdout(captured):
                                        from src.shellpomodoro.cli import attach_ui

                                        attach_ui({"port": 1234, "secret": "x"})

    output = captured.getvalue()

    # Should have exactly one header line
    assert (
        output.count("[1/1] Focus") == 1
    ), f"Expected 1 Focus header, got: {output.count('[1/1] Focus')}"

    # Should have exactly one instance of each timer value (no duplicates)
    assert (
        output.count("⏳ 00:59") == 1
    ), f"Expected 1 instance of 00:59, got: {output.count('⏳ 00:59')}"
    assert (
        output.count("⏳ 00:58") == 1
    ), f"Expected 1 instance of 00:58, got: {output.count('⏳ 00:58')}"
    assert (
        output.count("⏳ 00:57") == 1
    ), f"Expected 1 instance of 00:57, got: {output.count('⏳ 00:57')}"

    # Should have exactly one legend
    assert (
        output.count("Hotkeys:") == 1
    ), f"Expected 1 legend, got: {output.count('Hotkeys:')}"

    # Should contain ANSI clear sequences for repaint
    assert (
        "\x1b[2K\r" in output
    ), "Should contain ANSI clear sequences for status repaint"


def test_timer_back_no_double_first_frame():
    """Test that there's no duplicate first frame like ⏳ 00:00 before the real frame."""
    captured = io.StringIO()

    # Start with a real remaining_s value, not 0
    status_frames = [
        {
            "phase_id": "1_Focus",
            "phase_label": "[1/1] Focus",
            "remaining_s": 25,  # Start at 25 seconds
            "elapsed_s": 0,
            "duration_s": 25,
            "display": "timer-back",
        },
        None,  # End quickly
    ]

    call_count = [0]

    def mock_status(sock):
        if call_count[0] < len(status_frames):
            result = status_frames[call_count[0]]
            call_count[0] += 1
            return result
        return None

    class FakeTimerBack:
        single_line = True

        def frame(self, payload):
            remaining = int(payload.get("remaining_s", 0))
            m, s = divmod(remaining, 60)
            return f"⏳ {m:02d}:{s:02d}"

        def close(self):
            pass

        def start_phase(self, kind, total_s):
            pass

    with patch("src.shellpomodoro.cli.make_renderer", return_value=FakeTimerBack()):
        with patch("src.shellpomodoro.cli._supports_ansi", return_value=True):
            with patch("src.shellpomodoro.ipc._connect", return_value=MagicMock()):
                with patch("src.shellpomodoro.ipc.hello", return_value=True):
                    with patch("src.shellpomodoro.ipc.status", side_effect=mock_status):
                        with patch(
                            "src.shellpomodoro.keypress.poll_hotkey", return_value=None
                        ):
                            with patch("src.shellpomodoro.keypress.phase_key_mode"):
                                with patch("time.sleep"):
                                    with contextlib.redirect_stdout(captured):
                                        from src.shellpomodoro.cli import attach_ui

                                        attach_ui({"port": 1234, "secret": "x"})

    output = captured.getvalue()

    # Should not contain any ⏳ 00:00 "boot frame"
    assert (
        "⏳ 00:00" not in output
    ), f"Should not contain boot frame ⏳ 00:00, got: {output}"

    # Should contain the actual remaining time
    assert (
        "⏳ 00:25" in output
    ), f"Should contain actual remaining time ⏳ 00:25, got: {output}"

    # Should have exactly one instance of the timer value
    assert (
        output.count("⏳ 00:25") == 1
    ), f"Expected exactly 1 instance of ⏳ 00:25, got: {output.count('⏳ 00:25')}"
