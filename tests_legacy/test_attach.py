import builtins
import sys
from unittest.mock import MagicMock, patch


# Helper: no-op sleep so loops don’t block
class NoSleep:
    def __enter__(self):
        self.p = patch("time.sleep", lambda *_args, **_kw: None)
        self.p.start()
        return self

    def __exit__(self, *a):
        self.p.stop()


def _make_status_iter():
    """Yield two status frames, then None (daemon ended)."""
    yield {
        "phase_label": "[1/1] Focus",
        "left": 10,
        "total": 60,
        "display": "bar",
        "dot_interval": None,
        "iter": 1,
        "iters": 1,
    }
    yield {
        "phase_label": "[1/1] Focus",
        "left": 9,
        "total": 60,
        "display": "bar",
        "dot_interval": None,
        "iter": 1,
        "iters": 1,
    }
    yield None


def test_attach_no_runtime(capsys):
    from src.shellpomodoro import cli

    with patch("src.shellpomodoro.runtime.read_runtime", return_value=None):
        with patch.object(sys, "exit") as mock_exit:
            cli.main = cli.main  # ensure import
            # Create a more complete mock args object
            mock_args = MagicMock()
            mock_args.subcommand = "attach"
            mock_args.version = False
            mock_args.work = 25
            setattr(mock_args, "break", 5)
            mock_args.iterations = 4
            mock_args.beeps = 2
            mock_args.display = "timer-back"
            mock_args.dot_interval = None

            cli.parse_args = MagicMock(return_value=mock_args)
            cli.main()
            captured = capsys.readouterr().out
            assert "No active shellpomodoro session" in captured
            mock_exit.assert_called()


def test_attach_happy_path():
    from src.shellpomodoro import cli

    info = {"port": 12345, "secret": "abc"}
    statuses = _make_status_iter()
    with (
        NoSleep(),
        patch("src.shellpomodoro.runtime.read_runtime", return_value=info),
        patch("src.shellpomodoro.ipc._connect", return_value=MagicMock()),
        patch("src.shellpomodoro.ipc.hello", return_value=True),
        patch("src.shellpomodoro.ipc.status", side_effect=lambda sock: next(statuses)),
        patch("src.shellpomodoro.keypress.phase_key_mode"),
        patch("src.shellpomodoro.keypress.poll_hotkey") as mock_keys,
    ):
        mock_keys.return_value = MagicMock(name="NONE")  # no keys pressed
        from src.shellpomodoro.cli import attach_ui

        attach_ui(info)  # should exit cleanly when status() returns None


def test_attach_detach_with_ctrl_o(capsys):
    from src.shellpomodoro import cli

    info = {"port": 12345, "secret": "abc"}
    statuses = _make_status_iter()
    from src.shellpomodoro.keypress import Hotkey

    key_seq = [Hotkey.TOGGLE_HIDE]  # detach immediately

    def keygen():
        if key_seq:
            return key_seq.pop(0)
        return Hotkey.NONE

    with (
        NoSleep(),
        patch("src.shellpomodoro.ipc._connect", return_value=MagicMock()),
        patch("src.shellpomodoro.ipc.hello", return_value=True),
        patch("src.shellpomodoro.ipc.status", side_effect=lambda sock: next(statuses)),
        patch("src.shellpomodoro.keypress.phase_key_mode"),
        patch("src.shellpomodoro.keypress.poll_hotkey", side_effect=keygen),
    ):
        from src.shellpomodoro.cli import attach_ui

        attach_ui(info)
    out = capsys.readouterr().out
    assert "[detached] Viewer exited" in out


def test_attach_end_phase_on_ctrl_e():
    from src.shellpomodoro import cli

    info = {"port": 12345, "secret": "abc"}
    statuses = _make_status_iter()
    from src.shellpomodoro.keypress import Hotkey

    key_seq = [Hotkey.END_PHASE, Hotkey.TOGGLE_HIDE]  # send end-phase then detach

    def keygen():
        if key_seq:
            return key_seq.pop(0)
        return Hotkey.NONE

    mock_end_phase = MagicMock()
    with (
        NoSleep(),
        patch("src.shellpomodoro.ipc._connect", return_value=MagicMock()),
        patch("src.shellpomodoro.ipc.hello", return_value=True),
        patch("src.shellpomodoro.ipc.status", side_effect=lambda sock: next(statuses)),
        patch("src.shellpomodoro.ipc.end_phase", mock_end_phase),
        patch("src.shellpomodoro.keypress.phase_key_mode"),
        patch("src.shellpomodoro.keypress.poll_hotkey", side_effect=keygen),
    ):
        from src.shellpomodoro.cli import attach_ui

        attach_ui(info)
    mock_end_phase.assert_called_once()
