"""Tests for single-line viewer updates and server timing."""

import unittest
from unittest.mock import patch, MagicMock
import time
from io import StringIO
import sys

from src.shellpomodoro.server import SessionDaemon


class TestServerTiming(unittest.TestCase):
    """Test that server computes timing correctly using monotonic time."""

    def test_compute_timing_basic(self):
        """Test basic timing computation."""
        daemon = SessionDaemon(25, 5, 1, 2, "timer-back", None)

        # Mock monotonic time
        with patch("time.monotonic") as mock_time:
            # Start at t=0, duration=60s
            daemon.duration_s = 60
            daemon.t0 = 0

            # At t=10: elapsed=10, remaining=50, progress≈0.1667
            mock_time.return_value = 10
            elapsed, remaining, progress = daemon._compute_timing()

            self.assertAlmostEqual(elapsed, 10.0)
            self.assertAlmostEqual(remaining, 50.0)
            self.assertAlmostEqual(progress, 10.0 / 60.0, places=4)

            # At t=60: elapsed=60, remaining=0, progress=1.0
            mock_time.return_value = 60
            elapsed, remaining, progress = daemon._compute_timing()

            self.assertAlmostEqual(elapsed, 60.0)
            self.assertAlmostEqual(remaining, 0.0)
            self.assertAlmostEqual(progress, 1.0)

            # Past end (t=70): remaining stays 0, progress stays 1.0
            mock_time.return_value = 70
            elapsed, remaining, progress = daemon._compute_timing()

            self.assertAlmostEqual(elapsed, 70.0)
            self.assertAlmostEqual(remaining, 0.0)
            self.assertAlmostEqual(progress, 1.0)

    def test_status_payload_fields(self):
        """Test that status payload contains all expected fields."""
        daemon = SessionDaemon(25, 5, 2, 1, "timer-back", None)

        with patch("time.monotonic", return_value=10):
            daemon.duration_s = 60
            daemon.t0 = 0

            status = daemon._status_payload()

            # Check all required fields are present
            required_fields = [
                "phase_id",
                "phase_label",
                "elapsed_s",
                "remaining_s",
                "duration_s",
                "progress",
                "left",
                "total",
                "iter",
                "iters",
                "display",
                "dot_interval",
                "done",
            ]
            for field in required_fields:
                self.assertIn(field, status)

            # Check values
            self.assertEqual(status["phase_id"], "1_Focus")
            self.assertEqual(status["phase_label"], "[1/2] Focus")
            self.assertAlmostEqual(status["elapsed_s"], 10.0)
            self.assertAlmostEqual(status["remaining_s"], 50.0)
            self.assertEqual(status["duration_s"], 60)
            self.assertAlmostEqual(status["progress"], 10.0 / 60.0, places=4)
            self.assertEqual(status["left"], 50)  # Backward compatibility
            self.assertEqual(status["total"], 60)  # Backward compatibility
            self.assertFalse(status["done"])


class TestViewerANSI(unittest.TestCase):
    """Test ANSI cursor movement in viewer."""

    @patch("src.shellpomodoro.cli._supports_ansi")
    @patch("sys.stdout", new_callable=StringIO)
    def test_ansi_sequences_in_output(self, mock_stdout, mock_ansi_support):
        """Test that ANSI escape sequences are used when supported."""
        mock_ansi_support.return_value = True

        # This is a simplified test - in reality we'd mock the full status stream
        from src.shellpomodoro.cli import _csi_up, _csi_down, _csi_clear_line

        # Test ANSI helper functions
        self.assertEqual(_csi_up(1), "\x1b[1A")
        self.assertEqual(_csi_down(1), "\x1b[1B")
        self.assertEqual(_csi_clear_line(), "\x1b[2K")

        # Test that helpers work
        sys.stdout.write(_csi_up(1) + "\r" + _csi_clear_line() + "test" + _csi_down(1))
        output = mock_stdout.getvalue()

        self.assertIn("\x1b[1A", output)  # cursor up
        self.assertIn("\x1b[2K", output)  # clear line
        self.assertIn("\x1b[1B", output)  # cursor down

    @patch("src.shellpomodoro.cli._supports_ansi")
    def test_ansi_fallback_mode(self, mock_ansi_support):
        """Test fallback when ANSI is not supported."""
        mock_ansi_support.return_value = False

        # When ANSI is not supported, we should not generate escape sequences
        # This would be tested more fully with a mocked attach_ui call


class TestRuntimeCleanup(unittest.TestCase):
    """Test stale runtime detection and cleanup."""

    @patch("src.shellpomodoro.runtime.is_process_running")
    @patch("src.shellpomodoro.runtime.read_runtime")
    @patch("src.shellpomodoro.runtime.remove_runtime_safely")
    def test_cleanup_stale_runtime(self, mock_remove, mock_read, mock_is_running):
        """Test cleanup of stale runtime when process is dead."""
        from src.shellpomodoro.runtime import cleanup_stale_runtime

        # Case 1: No runtime file
        mock_read.return_value = None
        result = cleanup_stale_runtime()
        self.assertFalse(result)
        mock_remove.assert_not_called()

        # Case 2: Runtime file exists but no PID
        mock_read.return_value = {"port": 12345, "secret": "abc"}
        result = cleanup_stale_runtime()
        self.assertTrue(result)
        mock_remove.assert_called_once()

        # Case 3: Runtime file exists, PID exists, but process is dead
        mock_remove.reset_mock()
        mock_read.return_value = {"port": 12345, "secret": "abc", "pid": 999}
        mock_is_running.return_value = False
        result = cleanup_stale_runtime()
        self.assertTrue(result)
        mock_remove.assert_called_once()

        # Case 4: Runtime file exists, PID exists, process is alive
        mock_remove.reset_mock()
        mock_is_running.return_value = True
        result = cleanup_stale_runtime()
        self.assertFalse(result)
        mock_remove.assert_not_called()


if __name__ == "__main__":
    unittest.main()
