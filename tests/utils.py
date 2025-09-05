from contextlib import contextmanager
from unittest.mock import patch
import time
import itertools
from src.shellpomodoro.timer import PhaseResult


def _noop_cm():
    from contextlib import contextmanager

    @contextmanager
    def cm():
        yield

    return cm()


@contextmanager
def fast_session_patches(silence_beep=True, silence_key=True):
    """
    Make runs non-blocking in tests:
    - Don't wait for keypress (optional)
    - Don't sleep
    - Don't beep (optional)
    - Don't touch real terminal modes
    - Force CI mode so run() skips waits/beeps (unless overridden)
    """
    patches = [
        patch("src.shellpomodoro.cli.time.sleep", lambda s: None),
        patch("src.shellpomodoro.timer.time.sleep", lambda s: None),
        patch("src.shellpomodoro.keypress.phase_key_mode", _noop_cm),
        patch.dict("os.environ", {"SHELLPOMODORO_CI": "1"}, clear=False),
        # Make time.time() progress fast to complete countdown immediately
        patch(
            "src.shellpomodoro.timer.time.time",
            side_effect=itertools.count(time.time() + 10000).__next__,
        ),
    ]

    if silence_beep:
        patches.append(patch("src.shellpomodoro.cli.beep", lambda count=1: None))
    if silence_key:
        patches.append(
            patch("src.shellpomodoro.cli.read_key", lambda prompt=None: None)
        )
        patches.append(
            patch("src.shellpomodoro.keypress.poll_end_phase", lambda: False)
        )

    # Apply all patches using context managers
    cm_patches = []
    for p in patches:
        cm_patches.append(p.__enter__())

    try:
        yield
    finally:
        for i, p in enumerate(patches):
            try:
                p.__exit__(None, None, None)
            except:
                pass
