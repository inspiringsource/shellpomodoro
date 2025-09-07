"""Test renderer functionality with actual current behavior."""

from shellpomodoro.display import make_renderer, Mode


def test_timer_back_returns_string():
    """Test timer-back renderer returns string with correct format."""
    renderer = make_renderer(Mode.TIMER_BACK, None)

    payload = {"phase_label": "Focus", "i": 1, "n": 4, "remaining_mmss": "01:05"}

    line = renderer.frame(payload)
    assert isinstance(line, str)
    assert line == "[[1/4] Focus] 01:05"


def test_timer_forward_returns_string():
    """Test timer-forward renderer returns string with correct format."""
    renderer = make_renderer(Mode.TIMER_FWD, None)

    payload = {"phase_label": "Focus", "i": 1, "n": 4, "elapsed_mmss": "00:35"}

    line = renderer.frame(payload)
    assert isinstance(line, str)
    assert line == "[[1/4] Focus] 00:35"


def test_bar_returns_string():
    """Test bar renderer returns string with correct format."""
    renderer = make_renderer(Mode.BAR, None)

    payload = {
        "phase_label": "Focus",
        "i": 1,
        "n": 4,
        "progress": 0.35,
        "remaining_mmss": "01:05",
    }

    line = renderer.frame(payload)
    assert isinstance(line, str)
    assert line.strip() != ""
    # Should contain the phase header and progress elements
    assert "[[1/4] Focus]" in line
    assert "35%" in line
    assert "01:05" in line


def test_dots_returns_string():
    """Test dots renderer returns string (possibly empty at start)."""
    renderer = make_renderer(Mode.DOTS, 10)

    payload = {"phase_label": "Focus", "i": 1, "n": 4, "elapsed_s": 0}

    line = renderer.frame(payload)
    assert isinstance(line, str)
    # At t=0, should have header but no dots yet
    assert "[[1/4] Focus]" in line


def test_dots_with_elapsed_time():
    """Test dots renderer with some elapsed time."""
    renderer = make_renderer(Mode.DOTS, 10)

    payload = {
        "phase_label": "Focus",
        "i": 1,
        "n": 4,
        "elapsed_s": 35,  # Should show some dots
    }

    line = renderer.frame(payload)
    assert isinstance(line, str)
    assert "[[1/4] Focus]" in line


def test_all_renderers_return_strings_not_none():
    """Ensure all renderers return strings, never None."""
    test_payload = {
        "phase_label": "Focus",
        "i": 1,
        "n": 4,
        "remaining_s": 65,
        "elapsed_s": 35,
        "progress": 0.35,
        "remaining_mmss": "01:05",
        "elapsed_mmss": "00:35",
    }

    for mode in [Mode.TIMER_BACK, Mode.TIMER_FWD, Mode.BAR, Mode.DOTS]:
        renderer = make_renderer(mode, 10 if mode == Mode.DOTS else None)
        result = renderer.frame(test_payload)
        assert isinstance(
            result, str
        ), f"{mode} renderer returned {type(result)}, not str"
        assert result is not None, f"{mode} renderer returned None"
