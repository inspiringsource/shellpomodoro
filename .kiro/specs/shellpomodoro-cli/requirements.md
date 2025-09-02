# Requirements Document

## Introduction

Shellpomodoro is a cross-platform terminal-based Pomodoro timer CLI application that can be installed via pip and run anywhere. The application provides a clean, zero-dependency implementation using only Python's standard library, featuring keypress-based phase transitions, terminal bell notifications, and ASCII art rewards upon completion.

## Requirements

### Requirement 1

**User Story:** As a developer, I want to install shellpomodoro via pip so that I can use it as a global CLI tool on any system.

#### Acceptance Criteria

1. WHEN the user runs `pip install shellpomodoro` THEN the system SHALL install the package successfully
2. WHEN the installation is complete THEN the system SHALL make the `shellpomodoro` command available globally
3. WHEN the user runs `shellpomodoro --help` THEN the system SHALL display usage information and available options
4. IF the user has Python 3.9 or higher THEN the system SHALL support the installation

### Requirement 2

**User Story:** As a user, I want to run Pomodoro sessions with customizable work and break durations so that I can adapt the timer to my workflow.

#### Acceptance Criteria

1. WHEN the user runs `shellpomodoro` without arguments THEN the system SHALL start a session with 25-minute work periods and 5-minute breaks
2. WHEN the user specifies `--work N` THEN the system SHALL use N minutes for work periods
3. WHEN the user specifies `--break N` THEN the system SHALL use N minutes for break periods
4. WHEN the user specifies `--iterations N` THEN the system SHALL run N Pomodoro cycles
5. WHEN the user specifies `--beeps N` THEN the system SHALL play N terminal bell sounds at phase transitions

### Requirement 3

**User Story:** As a user, I want to see a real-time countdown display so that I can track my remaining time in the current phase.

#### Acceptance Criteria

1. WHEN a work or break phase is active THEN the system SHALL display a countdown timer in MM:SS format
2. WHEN the countdown is running THEN the system SHALL update the display every 200ms
3. WHEN displaying the countdown THEN the system SHALL show the current phase label (Focus/Break)
4. WHEN displaying the countdown THEN the system SHALL show abort instructions (Ctrl+C to abort)
5. WHEN the countdown reaches zero THEN the system SHALL advance to the next phase

### Requirement 4

**User Story:** As a user, I want to control phase transitions with keypress so that I can take breaks when I'm ready.

#### Acceptance Criteria

1. WHEN a work phase completes THEN the system SHALL wait for any keypress before starting the break
2. WHEN a break phase completes THEN the system SHALL wait for any keypress before starting the next work phase
3. WHEN waiting for keypress THEN the system SHALL display appropriate prompt text
4. WHEN the user presses any key THEN the system SHALL immediately advance to the next phase
5. IF the system is Windows THEN the system SHALL use msvcrt for keypress detection
6. IF the system is Unix-like THEN the system SHALL use termios/tty for keypress detection

### Requirement 5

**User Story:** As a user, I want audio notifications at phase transitions so that I'm alerted when it's time to switch activities.

#### Acceptance Criteria

1. WHEN a work phase ends THEN the system SHALL play terminal bell sounds
2. WHEN a break phase ends THEN the system SHALL play terminal bell sounds
3. WHEN playing notification sounds THEN the system SHALL use the number of beeps specified by --beeps parameter
4. WHEN playing multiple beeps THEN the system SHALL space them 200ms apart
5. WHEN playing beeps THEN the system SHALL use the terminal bell character (\a)

### Requirement 6

**User Story:** As a user, I want to see a congratulatory message when I complete all iterations so that I feel rewarded for my productivity.

#### Acceptance Criteria

1. WHEN all Pomodoro iterations are completed THEN the system SHALL display ASCII art congratulations
2. WHEN displaying the completion message THEN the system SHALL include "shellpomodoro — great work!" text
3. WHEN displaying the completion message THEN the system SHALL show "Session complete" confirmation
4. WHEN the session completes THEN the system SHALL exit gracefully

### Requirement 7

**User Story:** As a user, I want to abort the session at any time so that I can stop the timer when needed.

#### Acceptance Criteria

1. WHEN the user presses Ctrl+C during any phase THEN the system SHALL display "Aborted." message
2. WHEN the user aborts the session THEN the system SHALL exit with status code 1
3. WHEN aborting THEN the system SHALL handle the interruption gracefully without errors
4. WHEN aborting THEN the system SHALL not display the completion ASCII art

### Requirement 8

**User Story:** As a developer, I want the package to follow Python packaging standards so that it integrates well with the Python ecosystem.

#### Acceptance Criteria

1. WHEN examining the project structure THEN the system SHALL use PEP 517/518 compliant pyproject.toml
2. WHEN examining the project structure THEN the system SHALL use src-layout with shellpomodoro package under src/
3. WHEN examining dependencies THEN the system SHALL have zero external dependencies (stdlib only)
4. WHEN building the package THEN the system SHALL use setuptools>=68 as build backend
5. WHEN installing THEN the system SHALL register the CLI entry point correctly
6. WHEN examining metadata THEN the system SHALL include proper project description, version, and author information