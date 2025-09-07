# Test Suite for shellpomodoro v0.1.5

This is a minimal, fast test suite that validates the current behavior of shellpomodoro v0.1.5.

## Structure

- `test_version.py` - Tests version flag functionality
- `test_cli_smoke.py` - Smoke tests for CLI basic functionality
- `test_renderers.py` - Tests that all renderers return strings (never None)
- `test_attach_smoke.py` - Basic tests for attach functionality

## Design Principles

- **Fast**: No sleeps, minimal timeouts, designed for quick feedback
- **Deterministic**: Tests actual current behavior rather than imposing expectations
- **Tolerant**: Handles timing issues and real-world CLI behavior gracefully
- **Focused**: Only tests the core functionality that matters for v0.1.5

## Validated Behaviors

- Header format: `Pomodoro Session — work=X break=Y iterations=Z beeps=W display=MODE`
- Legend format: `Hotkeys: Ctrl+C abort • Ctrl+E end phase • Ctrl+O detach`
- All renderers return strings (timer-back, timer-forward, bar, dots)
- Version flag exits with code 0 and prints version
- Help flag exits with code 0
- Attach command handles no-session case properly

## Legacy Tests

All previous tests have been moved to `tests_legacy/` and are ignored via `pytest.ini`.
