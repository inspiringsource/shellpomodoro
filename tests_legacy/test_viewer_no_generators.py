"""Test to ensure no generator-based renderers are used."""

import inspect
from src.shellpomodoro import display


def test_no_generator_renderers():
    """Ensure no generator functions exist in the display module."""
    bad = []
    for name in dir(display):
        obj = getattr(display, name)
        if inspect.isgeneratorfunction(obj):
            bad.append(name)
    assert not bad, f"Generator-based display functions not allowed: {bad}"


def test_all_renderers_have_frame_method():
    """Ensure all renderer classes have frame method returning string."""
    renderer_classes = [
        display.TimerBackRenderer,
        display.TimerFwdRenderer,
        display.BarRenderer,
        display.DotsRenderer,
    ]

    for cls in renderer_classes:
        renderer = cls() if cls != display.DotsRenderer else cls(60)
        assert hasattr(renderer, "frame"), f"{cls.__name__} missing frame method"
        assert hasattr(renderer, "close"), f"{cls.__name__} missing close method"
        assert hasattr(
            renderer, "single_line"
        ), f"{cls.__name__} missing single_line attribute"
        assert (
            renderer.single_line is True
        ), f"{cls.__name__}.single_line should be True"


def test_frame_method_returns_string():
    """Ensure frame methods return strings, not generators."""
    payload = {"remaining_s": 30, "elapsed_s": 30, "duration_s": 60, "progress": 0.5}

    renderers = [
        display.TimerBackRenderer(),
        display.TimerFwdRenderer(),
        display.BarRenderer(),
        display.DotsRenderer(60),
    ]

    for renderer in renderers:
        if hasattr(renderer, "start_phase"):
            renderer.start_phase("Test", 60)

        result = renderer.frame(payload)
        assert isinstance(
            result, str
        ), f"{type(renderer).__name__}.frame() should return string, got {type(result)}"
        assert not inspect.isgenerator(
            result
        ), f"{type(renderer).__name__}.frame() should not return generator"
