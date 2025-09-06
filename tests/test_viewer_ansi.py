import io, sys
from unittest.mock import patch, MagicMock
import contextlib


def test_timer_single_line_with_legend_below():
    """Test timer updates in place with legend below using ANSI cursor movement."""

    class FakeTimer:
        single_line = True

        def __init__(self):
            self.calls = 0

        def update(self, elapsed):
            self.calls += 1
            m, s = divmod(max(0, int(60 - elapsed)), 60)
            return f"[Focus] ⏳ {m:02d}:{s:02d}"

        def close(self):
            pass

    # Mock sys.stdout.write to capture ANSI sequences
    captured_writes = []

    def mock_write(text):
        captured_writes.append(text)
        return len(text)

    with patch("src.shellpomodoro.cli.make_renderer", return_value=FakeTimer()):
        with patch("src.shellpomodoro.cli._supports_ansi", return_value=True):
            fake_ticks = [
                {"phase_id": 1, "phase_label": "Focus", "left": 60, "total": 60},
                {"phase_id": 1, "phase_label": "Focus", "left": 59, "total": 60},
                {"phase_id": 1, "phase_label": "Focus", "left": 58, "total": 60},
                {"phase_id": 1, "phase_label": "Focus", "left": 57, "total": 60},
                None,  # End the stream
            ]

            def fake_stream():
                for t in fake_ticks:
                    yield t

            stream = fake_stream()

            with patch("src.shellpomodoro.ipc._connect", return_value=object()):
                with patch("src.shellpomodoro.ipc.hello", return_value=True):
                    with patch(
                        "src.shellpomodoro.ipc.status",
                        side_effect=lambda sock: next(stream),
                    ):
                        with patch(
                            "src.shellpomodoro.keypress.poll_hotkey", return_value=None
                        ):
                            with patch("time.sleep", return_value=None):
                                with patch("sys.stdout.write", side_effect=mock_write):
                                    with patch("sys.stdout.flush"):
                                        with patch("builtins.print") as mock_print:
                                            from src.shellpomodoro.cli import attach_ui

                                            attach_ui({"port": 1234, "secret": "x"})

    # Check captured print calls for legend (should appear exactly once)
    print_calls = [str(call) for call in mock_print.call_args_list]
    legend_calls = [call for call in print_calls if "Hotkeys: Ctrl+C abort" in call]
    assert (
        len(legend_calls) == 1
    ), f"Legend should be printed exactly once, got: {legend_calls}"

    # Check captured writes for ANSI cursor movement sequences
    write_output = "".join(captured_writes)
    assert (
        "\x1b[1A" in write_output
    ), "Should contain cursor up sequences for in-place updates"
    assert (
        "\x1b[2K" in write_output
    ), "Should contain line clear sequences for in-place updates"
    assert (
        "\x1b[1B" in write_output
    ), "Should contain cursor down sequences to return to legend line"


def test_ansi_fallback_mode():
    """Test fallback behavior when ANSI is not supported."""

    class FakeTimer:
        single_line = True

        def __init__(self):
            self.calls = 0

        def update(self, elapsed):
            self.calls += 1
            return f"[Focus] ⏳ 01:0{self.calls}"

        def close(self):
            pass

    with patch("src.shellpomodoro.cli.make_renderer", return_value=FakeTimer()):
        with patch("src.shellpomodoro.cli._supports_ansi", return_value=False):
            fake_ticks = [
                {"phase_id": 1, "phase_label": "Focus", "left": 60, "total": 60},
                {"phase_id": 1, "phase_label": "Focus", "left": 59, "total": 60},
                None,  # End the stream
            ]

            def fake_stream():
                for t in fake_ticks:
                    yield t

            stream = fake_stream()

            with patch("src.shellpomodoro.ipc._connect", return_value=object()):
                with patch("src.shellpomodoro.ipc.hello", return_value=True):
                    with patch(
                        "src.shellpomodoro.ipc.status",
                        side_effect=lambda sock: next(stream),
                    ):
                        with patch(
                            "src.shellpomodoro.keypress.poll_hotkey", return_value=None
                        ):
                            with patch("time.sleep", return_value=None):
                                with patch("builtins.print") as mock_print:
                                    from src.shellpomodoro.cli import attach_ui

                                    attach_ui({"port": 1234, "secret": "x"})

    # In fallback mode, each distinct timer update should be printed
    print_calls = [str(call) for call in mock_print.call_args_list]
    timer_calls = [call for call in print_calls if "⏳ 01:0" in call]
    assert len(timer_calls) >= 1, "Should have printed timer updates in fallback mode"


def test_no_generator_renderers():
    """Defensive: ensure renderers aren't generators/contextmanagers."""
    import inspect
    from src.shellpomodoro import display

    bad = []
    for name in dir(display):
        obj = getattr(display, name)
        if name.lower().endswith("renderer") and inspect.isclass(obj):
            continue
        if inspect.isgeneratorfunction(obj):
            bad.append(name)
    assert not bad, f"Generator-based display functions not allowed: {bad}"
