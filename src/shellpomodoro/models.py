"""
Core data models for shellpomodoro application.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


@dataclass
class SessionConfig:
    """Configuration for a Pomodoro session with validation."""
    
    work_min: int = 25
    break_min: int = 5
    iterations: int = 4
    beeps: int = 2
    
    def validate(self) -> None:
        """
        Validate configuration parameters to ensure positive values and reasonable ranges.
        
        Raises:
            ValueError: If any parameter is invalid
        """
        if self.work_min <= 0:
            raise ValueError("Work minutes must be positive")
        if self.break_min <= 0:
            raise ValueError("Break minutes must be positive")
        if self.iterations <= 0:
            raise ValueError("Iterations must be positive")
        if self.beeps < 0:
            raise ValueError("Beeps must be non-negative")
            
        # Reasonable range validation
        if self.work_min > 120:  # 2 hours max
            raise ValueError("Work minutes should not exceed 120 minutes")
        if self.break_min > 60:  # 1 hour max
            raise ValueError("Break minutes should not exceed 60 minutes")
        if self.iterations > 20:  # Reasonable daily limit
            raise ValueError("Iterations should not exceed 20")
        if self.beeps > 10:  # Avoid excessive beeping
            raise ValueError("Beeps should not exceed 10")


class PomodoroPhase(Enum):
    """Enumeration of Pomodoro session phases."""
    
    WORK = "Focus"
    BREAK = "Break"
    DONE = "Done"


@dataclass
class SessionState:
    """Tracks the current state of a Pomodoro session."""
    
    current_iteration: int
    total_iterations: int
    current_phase: PomodoroPhase
    
    def __post_init__(self):
        """Validate session state after initialization."""
        if self.current_iteration < 1:
            raise ValueError("Current iteration must be at least 1")
        if self.total_iterations < 1:
            raise ValueError("Total iterations must be at least 1")
        if self.current_iteration > self.total_iterations:
            raise ValueError("Current iteration cannot exceed total iterations")
    
    def is_final_iteration(self) -> bool:
        """Check if this is the final iteration of the session."""
        return self.current_iteration == self.total_iterations
    
    def advance_to_break(self) -> None:
        """Advance from work phase to break phase."""
        if self.current_phase != PomodoroPhase.WORK:
            raise ValueError("Can only advance to break from work phase")
        self.current_phase = PomodoroPhase.BREAK
    
    def advance_to_next_work(self) -> None:
        """Advance to the next work iteration."""
        if self.current_phase != PomodoroPhase.BREAK:
            raise ValueError("Can only advance to work from break phase")
        self.current_iteration += 1
        if self.current_iteration <= self.total_iterations:
            self.current_phase = PomodoroPhase.WORK
        else:
            self.current_phase = PomodoroPhase.DONE
    
    def complete_session(self) -> None:
        """Mark the session as complete."""
        self.current_phase = PomodoroPhase.DONE