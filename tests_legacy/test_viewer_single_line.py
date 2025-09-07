import io, sys
from unittest.mock import patch, MagicMock
import contextlib


def test_bar_mode_updates_in_place_and_prints_legend_once():
    from src.shellpomodoro.cli import attach_ui

    class FakeBar:
        single_line = True

        def __init__(self):
            self.calls = 0

        def frame(self, payload):
            self.calls += 1
            return f"[BAR {self.calls}]"

        def close(self):
            pass

    # Mock sys.stdout.write to capture single-line updates
    captured_writes = []
    original_write = sys.stdout.write
    original_flush = sys.stdout.flush

    def mock_write(text):
        captured_writes.append(text)
        return len(text)

    def mock_flush():
        pass

    with patch("src.shellpomodoro.cli.make_renderer", return_value=FakeBar()):
        with patch("src.shellpomodoro.cli._supports_ansi", return_value=True):
            fake_ticks = [
                {"phase_id": 1, "phase_label": "Focus", "left": 4, "total": 4},
                {"phase_id": 1, "phase_label": "Focus", "left": 3, "total": 4},
                {"phase_id": 1, "phase_label": "Focus", "left": 2, "total": 4},
                {"phase_id": 1, "phase_label": "Focus", "left": 1, "total": 4},
                {"phase_id": 1, "phase_label": "Focus", "left": 0, "total": 4},
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
                                    with patch(
                                        "sys.stdout.flush", side_effect=mock_flush
                                    ):
                                        with patch("builtins.print") as mock_print:
                                            attach_ui({"port": 1234, "secret": "x"})

    # Check captured print calls for legend
    print_calls = [str(call) for call in mock_print.call_args_list]
    legend_calls = [call for call in print_calls if "Hotkeys: Ctrl+C abort" in call]
    assert (
        len(legend_calls) == 1
    ), f"Legend should be printed exactly once, got: {legend_calls}"

    # Check captured writes for single-line updates
    write_output = "".join(captured_writes)
    carriage_returns = [w for w in captured_writes if "\x1b[2K\r[BAR " in w]
    assert (
        len(carriage_returns) >= 2
    ), f"Should have multiple carriage return updates, got: {carriage_returns}"  # Verify bar content appears
    assert "[BAR 1]" in write_output
    assert "[BAR 2]" in write_output


def test_no_generator_renderers():
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
