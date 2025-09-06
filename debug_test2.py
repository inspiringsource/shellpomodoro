import unittest.mock
from contextlib import contextmanager


def _noop_cm():
    @contextmanager
    def cm():
        yield

    return cm()


class FakeTimer:
    def __init__(self):
        self.calls = []

    def update(self, elapsed_s):
        self.calls.append(elapsed_s)
        return f"⏳ {elapsed_s:02.0f}:00"


def test_minimal():
    print("Setting up mocks...")

    # Mock all needed functions
    with (
        unittest.mock.patch("src.shellpomodoro.cli.status") as mock_status,
        unittest.mock.patch("src.shellpomodoro.cli.renderer") as mock_renderer,
        unittest.mock.patch("src.shellpomodoro.cli._supports_ansi", return_value=False),
        unittest.mock.patch(
            "src.shellpomodoro.keypress.phase_key_mode", side_effect=lambda: _noop_cm()
        ),
    ):

        # Set up the mock objects
        mock_status.return_value = None  # End immediately
        fake_timer = FakeTimer()
        mock_renderer.return_value = fake_timer

        print(f"After patching - hasattr check: {hasattr(fake_timer, 'update')}")

        from src.shellpomodoro.cli import attach_ui

        attach_ui({"port": 1234, "secret": "x"})

        print(f"Timer calls: {fake_timer.calls}")


test_minimal()
