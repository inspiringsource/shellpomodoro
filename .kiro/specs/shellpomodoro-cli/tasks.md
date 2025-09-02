# Implementation Plan

- [x] 1. Set up project structure and packaging configuration
  - Create PEP 517/518 compliant directory structure with src-layout
  - Write pyproject.toml with setuptools backend and console script entry point
  - Create README.md with installation and usage instructions
  - Add MIT LICENSE file
  - _Requirements: 1.1, 1.2, 1.3, 8.1, 8.2, 8.4, 8.5_

- [x] 2. Implement core data models and configuration
- [x] 2.1 Create SessionConfig dataclass with validation
  - Write SessionConfig class with work_min, break_min, iterations, beeps fields
  - Implement validate() method to ensure positive values and reasonable ranges
  - Create unit tests for configuration validation edge cases
  - _Requirements: 2.2, 2.3, 2.4, 2.5, 8.6_

- [x] 2.2 Implement phase state management
  - Create PomodoroPhase enum for WORK, BREAK, DONE states
  - Write SessionState class to track current iteration and phase
  - Add unit tests for state transitions
  - _Requirements: 3.3, 6.1_

- [x] 3. Implement cross-platform input handling
- [x] 3.1 Create platform detection and keypress abstraction
  - Write platform detection logic for Windows vs Unix systems
  - Implement Windows keypress handling using msvcrt.getch()
  - Create unit tests with platform-specific mocking
  - _Requirements: 4.5, 4.6_

- [x] 3.2 Implement Unix keypress handling with terminal management
  - Write Unix keypress handling using termios and tty modules
  - Create context manager for safe terminal state restoration
  - Implement read_key function with proper cleanup
  - Add unit tests for terminal state management
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.6, 7.3_

- [x] 4. Implement timer and countdown functionality
- [x] 4.1 Create time formatting utilities
  - Write mmss() function to format seconds as MM:SS string
  - Handle edge cases like zero seconds and large values
  - Create unit tests for time formatting
  - _Requirements: 3.2_

- [x] 4.2 Implement countdown engine with real-time display
  - Write countdown() function with 200ms update intervals
  - Display phase label, remaining time, and abort instructions
  - Handle KeyboardInterrupt for graceful session abort
  - Create unit tests with mocked time.sleep for fast execution
  - _Requirements: 3.1, 3.2, 3.4, 3.5, 7.1, 7.2, 7.3_

- [x] 5. Implement audio notification system
- [x] 5.1 Create terminal bell notification system
  - Write beep() function using terminal bell character (\a)
  - Implement configurable beep count with 200ms spacing
  - Add unit tests to verify output and timing
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 6. Implement user interface and display management
- [x] 6.1 Create ASCII art reward system
  - Define GOOD_JOB ASCII art constant in cli module
  - Implement banner() function to return completion message
  - Add unit tests to verify message content and formatting
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 6.2 Implement session progress display
  - Create session header display with work/break/iteration summary
  - Implement iteration progress indicators during phases
  - Add unit tests for display formatting
  - _Requirements: 3.3_

- [x] 7. Implement signal handling and cleanup
- [x] 7.1 Create signal handler for graceful interruption
  - Write SIGINT handler that raises KeyboardInterrupt
  - Ensure proper cleanup and terminal state restoration
  - Implement "Aborted." message display and exit code 1
  - Add unit tests for signal handling behavior
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 8. Create comprehensive test suite for core components
- [x] 8.1 Write unit tests for all implemented components
  - Create tests for SessionConfig validation (95 tests total)
  - Write tests for cross-platform keypress handling
  - Add tests for timer countdown with mocked time
  - Create tests for audio notification system
  - Add tests for signal handling and UI components
  - _Requirements: All component-level requirements_

- [x] 9. Implement CLI interface and argument parsing
- [x] 9.1 Create command-line argument parser
  - Write parse_args() function with argparse for --work, --break, --iterations, --beeps
  - Set appropriate default values (25, 5, 4, 2)
  - Add input validation and error handling
  - Create unit tests for argument parsing and validation
  - _Requirements: 1.3, 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 9.2 Implement main CLI entry point
  - Write main() function that coordinates argument parsing and session execution
  - Handle configuration errors with appropriate exit codes
  - Integrate with setuptools entry point system
  - Add integration tests for complete CLI workflow
  - _Requirements: 1.1, 1.2, 8.5_

- [x] 10. Implement core session controller
- [x] 10.1 Create Pomodoro session orchestration
  - Write run() function that manages complete session flow
  - Implement work phase → beep → keypress → break phase cycle
  - Handle final iteration without break phase
  - Add integration tests with mocked components
  - _Requirements: 2.1, 4.1, 4.2, 5.1, 5.2, 6.4_

- [x] 10.2 Integrate all components into session flow
  - Wire together timer, keypress, beep, and display components
  - Implement proper error propagation and cleanup
  - Add end-to-end tests with fast execution (1-second phases)
  - Verify all EARS acceptance criteria are met
  - _Requirements: All requirements integration_

- [x] 11. Finalize package distribution and testing
- [x] 11.1 Verify installation and distribution
  - Test pip install -e . for development installation
  - Verify shellpomodoro command is available globally
  - Test package building with python -m build
  - Create installation verification tests
  - _Requirements: 1.1, 1.2, 8.1, 8.2, 8.4_

- [x] 11.2 Create integration and end-to-end tests
  - Create full session simulation tests with mocked I/O
  - Write CLI argument validation integration tests
  - Add cross-platform compatibility verification
  - Test complete workflow from CLI to session completion
  - _Requirements: Complete system behavior verification_