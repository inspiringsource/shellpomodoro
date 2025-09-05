from unittest.mock import patch
from src.shellpomodoro.cli import run
from shellpomodoro.timer import PhaseResult


def test_ci_mode_skips_beep_and_key():
    with (
        patch("src.shellpomodoro.cli._is_ci_mode", return_value=True),
        patch("src.shellpomodoro.cli.countdown", return_value=PhaseResult.COMPLETED),
        patch("src.shellpomodoro.cli.beep") as mock_beep,
        patch("src.shellpomodoro.cli.read_key") as mock_read_key,
    ):
        run(work=1, brk=1, iters=1, beeps=2)
        mock_beep.assert_not_called()
        mock_read_key.assert_not_called()
