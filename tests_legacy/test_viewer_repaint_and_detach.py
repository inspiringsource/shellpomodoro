"""Test viewer repaint discipline and Ctrl+O detach behavior."""

import io
import contextlib
from unittest.mock import patch, MagicMock
import sys


def test_single_line_repaint_and_legend_once():
    """Test that legend appears once and status repaints use ANSI sequences."""
    captured = io.StringIO()

    class FakeBar:
        single_line = True

        def __init__(self):
            self.calls = 0

        def frame(self, payload):
            self.calls += 1
            progress = payload.get("progress", 0.0)
            return f"[BAR {int(progress*100)}%]"

        def close(self):
            pass

    # Mock status calls to return different progress values
    status_calls = [
        {
            "phase_id": "1_Focus",
            "phase_label": "[1/1] Focus",
            "progress": 0.0,
            "remaining_s": 60,
            "elapsed_s": 0,
            "duration_s": 60,
            "display": "bar",
        },
        {
            "phase_id": "1_Focus",
            "phase_label": "[1/1] Focus",
            "progress": 0.5,
            "remaining_s": 30,
            "elapsed_s": 30,
            "duration_s": 60,
            "display": "bar",
        },
        {
            "phase_id": "1_Focus",
            "phase_label": "[1/1] Focus",
            "progress": 1.0,
            "remaining_s": 0,
            "elapsed_s": 60,
            "duration_s": 60,
            "display": "bar",
        },
        None,  # End session
    ]

    call_count = [0]

    def mock_status(sock):
        if call_count[0] < len(status_calls):
            result = status_calls[call_count[0]]
            call_count[0] += 1
            return result
        return None

    with patch("src.shellpomodoro.cli.make_renderer", return_value=FakeBar()):
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

    out = captured.getvalue()

    # Legend should appear exactly once
    legend_count = out.count("Hotkeys: Ctrl+C abort")
    assert legend_count == 1, f"Legend should appear exactly once, got {legend_count}"

    # Should contain ANSI clear sequences for status repaint
    assert (
        "\x1b[2K\r" in out
    ), "Should contain ANSI clear line sequences for status repaint"

    # Should contain cursor down sequence for cleanup
    assert "\x1b[1B\n" in out, "Should contain cursor down + newline for cleanup"


def test_ctrl_o_detach_no_exception():
    """Test that Ctrl+O detach exits cleanly without exceptions."""
    captured = io.StringIO()

    class FakeTimer:
        single_line = True

        def frame(self, payload):
            remaining = payload.get("remaining_s", 0)
            return f"⏳ 00:{remaining:02d}"

        def close(self):
            pass

    # Mock status calls
    status_calls = [
        {
            "phase_id": "1_Focus",
            "phase_label": "[1/1] Focus",
            "remaining_s": 60,
            "elapsed_s": 0,
            "duration_s": 60,
            "display": "timer-back",
        },
        {
            "phase_id": "1_Focus",
            "phase_label": "[1/1] Focus",
            "remaining_s": 59,
            "elapsed_s": 1,
            "duration_s": 60,
            "display": "timer-back",
        },
    ]

    call_count = [0]

    def mock_status(sock):
        if call_count[0] < len(status_calls):
            result = status_calls[call_count[0]]
            call_count[0] += 1
            return result
        return None

    # Mock poll_hotkey to return TOGGLE_HIDE on second call
    from src.shellpomodoro.keypress import Hotkey

    hotkey_calls = [None, Hotkey.TOGGLE_HIDE]
    hotkey_count = [0]

    def mock_poll():
        if hotkey_count[0] < len(hotkey_calls):
            result = hotkey_calls[hotkey_count[0]]
            hotkey_count[0] += 1
            return result
        return None

    with patch("src.shellpomodoro.cli.make_renderer", return_value=FakeTimer()):
        with patch("src.shellpomodoro.ipc._connect", return_value=MagicMock()):
            with patch("src.shellpomodoro.ipc.hello", return_value=True):
                with patch("src.shellpomodoro.ipc.status", side_effect=mock_status):
                    with patch(
                        "src.shellpomodoro.keypress.poll_hotkey", side_effect=mock_poll
                    ):
                        with patch("src.shellpomodoro.keypress.phase_key_mode"):
                            with patch("time.sleep"):
                                with contextlib.redirect_stdout(captured):
                                    from src.shellpomodoro.cli import attach_ui

                                    # Should not raise any exception
                                    attach_ui({"port": 1234, "secret": "x"})

    out = captured.getvalue()

    # Should contain legend
    assert "Hotkeys: Ctrl+C abort" in out, "Legend should be printed before detaching"

    # Should end cleanly with detach message
    assert out.endswith(
        "[detached] Viewer exited\n"
    ), "Should end cleanly with detach message"


def test_no_duplicate_status_lines():
    """Test that status lines don't appear duplicated (e.g., no '00:00' twice)."""
    captured = io.StringIO()

    class FakeTimer:
        single_line = True

        def __init__(self):
            self.call_count = 0

        def frame(self, payload):
            self.call_count += 1
            # Use normalized string if present
            mmss = payload.get("remaining_mmss")
            if mmss:
                return f"⏳ {mmss}"
            remaining = payload.get("remaining_s", 0)
            m, s = divmod(remaining, 60)
            return f"⏳ {m:02d}:{s:02d}"

        def close(self):
            pass

    # Mock status calls with same remaining time to test deduplication
    status_calls = [
        {
            "phase_id": "1_Focus",
            "phase_label": "[1/1] Focus",
            "remaining_s": 60,
            "elapsed_s": 0,
            "duration_s": 60,
            "display": "timer-back",
        },
        {
            "phase_id": "1_Focus",
            "phase_label": "[1/1] Focus",
            "remaining_s": 60,
            "elapsed_s": 0,
            "duration_s": 60,
            "display": "timer-back",
        },  # Same as before - should not repaint
        {
            "phase_id": "1_Focus",
            "phase_label": "[1/1] Focus",
            "remaining_s": 59,
            "elapsed_s": 1,
            "duration_s": 60,
            "display": "timer-back",
        },  # Different - should repaint
        None,  # End session
    ]

    call_count = [0]

    def mock_status(sock):
        if call_count[0] < len(status_calls):
            result = status_calls[call_count[0]]
            call_count[0] += 1
            return result
        return None

    fake_timer = FakeTimer()
    with patch("src.shellpomodoro.cli.make_renderer", return_value=fake_timer):
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

    out = captured.getvalue()

    # Should only show "⏳ 01:00" once in printed output (initial), then "⏳ 00:59" once (repaint)
    # The deduplication should prevent double-printing of "⏳ 01:00"
    lines = out.split("\n")
    timer_lines = [line for line in lines if "⏳" in line]

    # Should have exactly 2 timer lines: initial "01:00" and updated "00:59"
    assert (
        len(timer_lines) == 2
    ), f"Should have exactly 2 timer lines, got {len(timer_lines)}: {timer_lines}"
    assert "⏳ 01:00" in timer_lines[0], "First timer line should be 01:00"
    assert "⏳ 00:59" in timer_lines[1], "Second timer line should be 00:59"
