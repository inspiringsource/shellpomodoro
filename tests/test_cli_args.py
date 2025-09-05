import sys
import pytest
from src.shellpomodoro.cli import parse_args


def test_dot_interval_must_be_positive(monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["shellpomodoro", "--display", "dots", "--dot-interval", "0"]
    )
    with pytest.raises(SystemExit):
        parse_args()
    monkeypatch.setattr(
        sys, "argv", ["shellpomodoro", "--display", "dots", "--dot-interval", "-5"]
    )
    with pytest.raises(SystemExit):
        parse_args()


def test_dot_interval_ignored_for_non_dots(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["shellpomodoro", "--display", "timer-back", "--dot-interval", "10"],
    )
    parse_args()
