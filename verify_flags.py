#!/usr/bin/env python3
"""Verify that single_line flags are set correctly"""

from src.shellpomodoro.display import (
    TimerBackRenderer,
    TimerFwdRenderer,
    BarRenderer,
    DotsRenderer,
)


def check_single_line_flags():
    """Check that single_line flags are set correctly on all renderers"""

    # Timer renderers should have single_line = False
    timer_back = TimerBackRenderer()
    timer_fwd = TimerFwdRenderer()

    print(
        f"TimerBackRenderer.single_line = {getattr(timer_back, 'single_line', 'NOT SET')}"
    )
    print(
        f"TimerFwdRenderer.single_line = {getattr(timer_fwd, 'single_line', 'NOT SET')}"
    )

    # Bar and dots renderers should have single_line = True
    bar = BarRenderer()
    dots = DotsRenderer(dot_interval_s=60)

    print(f"BarRenderer.single_line = {getattr(bar, 'single_line', 'NOT SET')}")
    print(f"DotsRenderer.single_line = {getattr(dots, 'single_line', 'NOT SET')}")

    # Test the logic
    print("\nTesting single_line detection logic:")

    for name, renderer in [
        ("TimerBackRenderer", timer_back),
        ("TimerFwdRenderer", timer_fwd),
        ("BarRenderer", bar),
        ("DotsRenderer", dots),
    ]:
        use_single_line = bool(renderer) and getattr(renderer, "single_line", False)
        print(f"{name}: use_single_line = {use_single_line}")


if __name__ == "__main__":
    check_single_line_flags()
