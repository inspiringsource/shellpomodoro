from contextlib import contextmanager
from unittest.mock import patch

@contextmanager
def fast_session_patches():
    # never do real countdown
    p_timer = patch("shellpomodoro.cli.countdown", lambda *a, **k: None)
    # silence beeps
    p_beep = patch("shellpomodoro.cli.beep", lambda *a, **k: None)
    # never sleep for real time
    p_sleep = patch("time.sleep", lambda *a, **k: None)
    with p_timer, p_beep, p_sleep:
        yield