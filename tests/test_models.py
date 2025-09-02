"""
Unit tests for shellpomodoro data models.
"""

import unittest
from src.shellpomodoro.models import SessionConfig, PomodoroPhase, SessionState


class TestSessionConfig(unittest.TestCase):
    """Test cases for SessionConfig dataclass and validation."""
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        config = SessionConfig()
        self.assertEqual(config.work_min, 25)
        self.assertEqual(config.break_min, 5)
        self.assertEqual(config.iterations, 4)
        self.assertEqual(config.beeps, 2)
    
    def test_custom_values(self):
        """Test that custom values can be set."""
        config = SessionConfig(work_min=30, break_min=10, iterations=6, beeps=3)
        self.assertEqual(config.work_min, 30)
        self.assertEqual(config.break_min, 10)
        self.assertEqual(config.iterations, 6)
        self.assertEqual(config.beeps, 3)
    
    def test_valid_configuration(self):
        """Test that valid configurations pass validation."""
        config = SessionConfig(work_min=25, break_min=5, iterations=4, beeps=2)
        # Should not raise any exception
        config.validate()
    
    def test_zero_work_minutes_invalid(self):
        """Test that zero work minutes is invalid."""
        config = SessionConfig(work_min=0)
        with self.assertRaises(ValueError) as cm:
            config.validate()
        self.assertIn("Work minutes must be positive", str(cm.exception))
    
    def test_negative_work_minutes_invalid(self):
        """Test that negative work minutes is invalid."""
        config = SessionConfig(work_min=-5)
        with self.assertRaises(ValueError) as cm:
            config.validate()
        self.assertIn("Work minutes must be positive", str(cm.exception))
    
    def test_zero_break_minutes_invalid(self):
        """Test that zero break minutes is invalid."""
        config = SessionConfig(break_min=0)
        with self.assertRaises(ValueError) as cm:
            config.validate()
        self.assertIn("Break minutes must be positive", str(cm.exception))
    
    def test_negative_break_minutes_invalid(self):
        """Test that negative break minutes is invalid."""
        config = SessionConfig(break_min=-3)
        with self.assertRaises(ValueError) as cm:
            config.validate()
        self.assertIn("Break minutes must be positive", str(cm.exception))
    
    def test_zero_iterations_invalid(self):
        """Test that zero iterations is invalid."""
        config = SessionConfig(iterations=0)
        with self.assertRaises(ValueError) as cm:
            config.validate()
        self.assertIn("Iterations must be positive", str(cm.exception))
    
    def test_negative_iterations_invalid(self):
        """Test that negative iterations is invalid."""
        config = SessionConfig(iterations=-1)
        with self.assertRaises(ValueError) as cm:
            config.validate()
        self.assertIn("Iterations must be positive", str(cm.exception))
    
    def test_negative_beeps_invalid(self):
        """Test that negative beeps is invalid."""
        config = SessionConfig(beeps=-1)
        with self.assertRaises(ValueError) as cm:
            config.validate()
        self.assertIn("Beeps must be non-negative", str(cm.exception))
    
    def test_zero_beeps_valid(self):
        """Test that zero beeps is valid (silent mode)."""
        config = SessionConfig(beeps=0)
        # Should not raise any exception
        config.validate()
    
    def test_excessive_work_minutes_invalid(self):
        """Test that work minutes over 120 is invalid."""
        config = SessionConfig(work_min=121)
        with self.assertRaises(ValueError) as cm:
            config.validate()
        self.assertIn("Work minutes should not exceed 120 minutes", str(cm.exception))
    
    def test_excessive_break_minutes_invalid(self):
        """Test that break minutes over 60 is invalid."""
        config = SessionConfig(break_min=61)
        with self.assertRaises(ValueError) as cm:
            config.validate()
        self.assertIn("Break minutes should not exceed 60 minutes", str(cm.exception))
    
    def test_excessive_iterations_invalid(self):
        """Test that iterations over 20 is invalid."""
        config = SessionConfig(iterations=21)
        with self.assertRaises(ValueError) as cm:
            config.validate()
        self.assertIn("Iterations should not exceed 20", str(cm.exception))
    
    def test_excessive_beeps_invalid(self):
        """Test that beeps over 10 is invalid."""
        config = SessionConfig(beeps=11)
        with self.assertRaises(ValueError) as cm:
            config.validate()
        self.assertIn("Beeps should not exceed 10", str(cm.exception))
    
    def test_boundary_values_valid(self):
        """Test that boundary values are valid."""
        # Test maximum valid values
        config = SessionConfig(work_min=120, break_min=60, iterations=20, beeps=10)
        config.validate()  # Should not raise
        
        # Test minimum valid values
        config = SessionConfig(work_min=1, break_min=1, iterations=1, beeps=0)
        config.validate()  # Should not raise


class TestPomodoroPhase(unittest.TestCase):
    """Test cases for PomodoroPhase enum."""
    
    def test_phase_values(self):
        """Test that phase enum values are correct."""
        self.assertEqual(PomodoroPhase.WORK.value, "Focus")
        self.assertEqual(PomodoroPhase.BREAK.value, "Break")
        self.assertEqual(PomodoroPhase.DONE.value, "Done")


class TestSessionState(unittest.TestCase):
    """Test cases for SessionState class."""
    
    def test_valid_initialization(self):
        """Test that valid session state can be initialized."""
        state = SessionState(current_iteration=1, total_iterations=4, current_phase=PomodoroPhase.WORK)
        self.assertEqual(state.current_iteration, 1)
        self.assertEqual(state.total_iterations, 4)
        self.assertEqual(state.current_phase, PomodoroPhase.WORK)
    
    def test_invalid_current_iteration_zero(self):
        """Test that current iteration cannot be zero."""
        with self.assertRaises(ValueError) as cm:
            SessionState(current_iteration=0, total_iterations=4, current_phase=PomodoroPhase.WORK)
        self.assertIn("Current iteration must be at least 1", str(cm.exception))
    
    def test_invalid_current_iteration_negative(self):
        """Test that current iteration cannot be negative."""
        with self.assertRaises(ValueError) as cm:
            SessionState(current_iteration=-1, total_iterations=4, current_phase=PomodoroPhase.WORK)
        self.assertIn("Current iteration must be at least 1", str(cm.exception))
    
    def test_invalid_total_iterations_zero(self):
        """Test that total iterations cannot be zero."""
        with self.assertRaises(ValueError) as cm:
            SessionState(current_iteration=1, total_iterations=0, current_phase=PomodoroPhase.WORK)
        self.assertIn("Total iterations must be at least 1", str(cm.exception))
    
    def test_invalid_total_iterations_negative(self):
        """Test that total iterations cannot be negative."""
        with self.assertRaises(ValueError) as cm:
            SessionState(current_iteration=1, total_iterations=-1, current_phase=PomodoroPhase.WORK)
        self.assertIn("Total iterations must be at least 1", str(cm.exception))
    
    def test_current_exceeds_total_invalid(self):
        """Test that current iteration cannot exceed total iterations."""
        with self.assertRaises(ValueError) as cm:
            SessionState(current_iteration=5, total_iterations=4, current_phase=PomodoroPhase.WORK)
        self.assertIn("Current iteration cannot exceed total iterations", str(cm.exception))
    
    def test_is_final_iteration_true(self):
        """Test is_final_iteration returns True for final iteration."""
        state = SessionState(current_iteration=4, total_iterations=4, current_phase=PomodoroPhase.WORK)
        self.assertTrue(state.is_final_iteration())
    
    def test_is_final_iteration_false(self):
        """Test is_final_iteration returns False for non-final iteration."""
        state = SessionState(current_iteration=2, total_iterations=4, current_phase=PomodoroPhase.WORK)
        self.assertFalse(state.is_final_iteration())
    
    def test_advance_to_break_from_work(self):
        """Test advancing from work phase to break phase."""
        state = SessionState(current_iteration=1, total_iterations=4, current_phase=PomodoroPhase.WORK)
        state.advance_to_break()
        self.assertEqual(state.current_phase, PomodoroPhase.BREAK)
    
    def test_advance_to_break_from_break_invalid(self):
        """Test that advancing to break from break phase is invalid."""
        state = SessionState(current_iteration=1, total_iterations=4, current_phase=PomodoroPhase.BREAK)
        with self.assertRaises(ValueError) as cm:
            state.advance_to_break()
        self.assertIn("Can only advance to break from work phase", str(cm.exception))
    
    def test_advance_to_break_from_done_invalid(self):
        """Test that advancing to break from done phase is invalid."""
        state = SessionState(current_iteration=4, total_iterations=4, current_phase=PomodoroPhase.DONE)
        with self.assertRaises(ValueError) as cm:
            state.advance_to_break()
        self.assertIn("Can only advance to break from work phase", str(cm.exception))
    
    def test_advance_to_next_work_from_break(self):
        """Test advancing from break phase to next work iteration."""
        state = SessionState(current_iteration=1, total_iterations=4, current_phase=PomodoroPhase.BREAK)
        state.advance_to_next_work()
        self.assertEqual(state.current_iteration, 2)
        self.assertEqual(state.current_phase, PomodoroPhase.WORK)
    
    def test_advance_to_next_work_final_iteration(self):
        """Test advancing from final break to done state."""
        state = SessionState(current_iteration=4, total_iterations=4, current_phase=PomodoroPhase.BREAK)
        state.advance_to_next_work()
        self.assertEqual(state.current_iteration, 5)
        self.assertEqual(state.current_phase, PomodoroPhase.DONE)
    
    def test_advance_to_next_work_from_work_invalid(self):
        """Test that advancing to next work from work phase is invalid."""
        state = SessionState(current_iteration=1, total_iterations=4, current_phase=PomodoroPhase.WORK)
        with self.assertRaises(ValueError) as cm:
            state.advance_to_next_work()
        self.assertIn("Can only advance to work from break phase", str(cm.exception))
    
    def test_advance_to_next_work_from_done_invalid(self):
        """Test that advancing to next work from done phase is invalid."""
        state = SessionState(current_iteration=4, total_iterations=4, current_phase=PomodoroPhase.DONE)
        with self.assertRaises(ValueError) as cm:
            state.advance_to_next_work()
        self.assertIn("Can only advance to work from break phase", str(cm.exception))
    
    def test_complete_session(self):
        """Test completing a session sets phase to done."""
        state = SessionState(current_iteration=3, total_iterations=4, current_phase=PomodoroPhase.WORK)
        state.complete_session()
        self.assertEqual(state.current_phase, PomodoroPhase.DONE)


if __name__ == '__main__':
    unittest.main()