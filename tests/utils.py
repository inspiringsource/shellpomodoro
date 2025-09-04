from contextlib import contextmanager
from unittest.mock import patch
from src.shellpomodoro.timer import PhaseResult


@contextmanager
def fast_session_patches():
    # never do real countdown - return COMPLETED immediately
    p_timer = patch(
        "src.shellpomodoro.timer.countdown", lambda *a, **k: PhaseResult.COMPLETED
    )
    # silence beeps
    p_beep = patch("src.shellpomodoro.cli.beep", lambda *a, **k: None)
    # never sleep for real time
    p_sleep = patch("time.sleep", lambda *a, **k: None)
    # mock read_key to never wait
    p_read_key = patch("src.shellpomodoro.cli.read_key", lambda *a, **k: None)
    with p_timer, p_beep, p_sleep, p_read_key:
        yield
