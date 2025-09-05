# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project adheres to Semantic Versioning.

## [0.1.3] - 2025-09-05

### Added

- Pluggable display modes via `--display`:
	- `timer-back` (default): countdown MM:SS remaining
	- `timer-forward`: timer counts up from 00:00
	- `bar`: progress bar with percentage
	- `dots`: test-runner style dot slots; supports `--dot-interval SECS`
- Non-blocking CI mode: when `SHELLPOMODORO_CI=1` or stdin is not a TTY, beeps and key waits are skipped to avoid hangs.

### Changed

- `timer.countdown` now accepts an optional renderer to produce the one-line status display and records per-phase summaries for `dots`.

## [0.1.2] - 2025-09-04

### Added

- `--version` / `-v` flag to print installed version.
- Ctrl+E to end current phase early (WORK → BREAK, BREAK → next WORK).

### Docs

- Help and README mention hotkeys and bell troubleshooting.

## [0.1.1] - 2025-09-03

### Added

- Ctrl+E hotkey to end current phase early (WORK → BREAK, BREAK → next WORK).
- Status line now shows “Ctrl+C abort • Ctrl+E end phase”.

## [0.1.0] - 2025-09-02

### Added

- First public release on PyPI via Trusted Publishing (OIDC).
- Cross-platform terminal Pomodoro timer (macOS/Linux/Windows).
- Stdlib-only, zero runtime dependencies.
- Real-time countdown, beeps, any-key transitions.
- ASCII “GOOD JOB” banner at session end.