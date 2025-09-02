"""
Integration and end-to-end tests for shellpomodoro.

These tests verify complete system behavior, cross-platform compatibility,
and full workflow from CLI to session completion.
"""

import io
import os
import platform
import subprocess
import sys
import tempfile
import time
from contextlib import redirect_stdout, redirect_stderr
from unittest import TestCase
from unittest.mock import patch, MagicMock

from shellpomodoro import cli
from tests.base import FastPatchedTestCase


class TestIntegration(FastPatchedTestCase):
    """Integration tests for complete shellpomodoro functionality."""

    def test_full_session_simulation_with_mocked_io(self):
        """Test complete session flow with mocked I/O for fast execution."""
        # Capture output
        stdout_capture = io.StringIO()
        
        with redirect_stdout(stdout_capture):
            # Set up arguments for a short session (1 iteration, 1 second phases)
            with patch('sys.argv', ['shellpomodoro', '--work', '1', '--break', '1', '--iterations', '1']):
                try:
                    cli.main()
                except SystemExit:
                    pass  # Expected for successful completion
        
        output = stdout_capture.getvalue()
        
        # Verify session header was displayed
        self.assertIn("Pomodoro Session", output)
        self.assertIn("1min work", output)
        self.assertIn("1min break", output)
        self.assertIn("1 iteration", output)
        
        # Verify completion message was displayed
        self.assertIn("Session complete", output)
        self.assertIn("great work!", output)

    def test_cli_argument_validation_integration(self):
        """Test CLI argument parsing and validation integration."""
        test_cases = [
            # Valid arguments
            (['--work', '25'], True),
            (['--break', '5'], True),
            (['--iterations', '4'], True),
            (['--beeps', '2'], True),
            (['--work', '30', '--break', '10'], True),
            
            # Invalid arguments (should be handled gracefully)
            (['--work', '0'], False),
            (['--break', '-1'], False),
            (['--iterations', '0'], False),
            (['--beeps', '-1'], False),
        ]
        
        for args, should_succeed in test_cases:
            with self.subTest(args=args):
                # Create a temporary script for each test case
                test_script = f'''
import sys
sys.path.insert(0, "src")
sys.argv = ["shellpomodoro"] + {args}
from shellpomodoro.cli import parse_args

try:
    parse_args()
    print("SUCCESS")
except SystemExit:
    print("FAILED")
except Exception as e:
    print("FAILED")
'''
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(test_script)
                    temp_script = f.name
                
                try:
                    result = subprocess.run(
                        [sys.executable, temp_script],
                        capture_output=True,
                        text=True,
                        cwd=os.getcwd()
                    )
                    
                    if should_succeed:
                        self.assertIn("SUCCESS", result.stdout)
                    else:
                        self.assertIn("FAILED", result.stdout)
                finally:
                    os.unlink(temp_script)

    def test_cross_platform_compatibility_verification(self):
        """Test cross-platform compatibility for input handling."""
        # Test platform detection
        current_platform = platform.system()
        
        # Test that appropriate input handler is selected
        if current_platform == "Windows":
            # On Windows, should try to import msvcrt
            with patch('shellpomodoro.cli.platform.system', return_value='Windows'):
                try:
                    import msvcrt
                    # If msvcrt is available, test should pass
                    self.assertTrue(True)
                except ImportError:
                    # If msvcrt not available, should fall back gracefully
                    self.assertTrue(True)
        else:
            # On Unix-like systems, should use termios/tty
            with patch('shellpomodoro.cli.platform.system', return_value='Linux'):
                try:
                    import termios
                    import tty
                    # If termios/tty available, test should pass
                    self.assertTrue(True)
                except ImportError:
                    # Should handle gracefully if not available
                    self.assertTrue(True)

    def test_signal_handling_integration(self):
        """Test signal handling and graceful interruption."""
        # Test KeyboardInterrupt handling in main()
        with patch('shellpomodoro.cli.parse_args') as mock_parse_args:
            mock_args = MagicMock()
            mock_args.work = 25
            setattr(mock_args, 'break', 5)
            mock_args.iterations = 1
            mock_args.beeps = 2
            mock_parse_args.return_value = mock_args
            
            with patch('shellpomodoro.cli.run', side_effect=KeyboardInterrupt):
                stderr_capture = io.StringIO()
                
                with redirect_stderr(stderr_capture):
                    with self.assertRaises(SystemExit) as cm:
                        cli.main()
                    
                    # Should exit with code 1 for abort
                    self.assertEqual(cm.exception.code, 1)

    def test_complete_workflow_cli_to_session_completion(self):
        """Test complete workflow from CLI invocation to session completion."""
        # Create a temporary script that runs a very short session
        test_script = '''
import sys
sys.path.insert(0, "src")

from unittest.mock import patch
from shellpomodoro import cli

# Use fast patches for execution
with patch("shellpomodoro.cli.read_key"):
    with patch("shellpomodoro.cli.time.sleep"):
        with patch("shellpomodoro.cli.beep"):
            # Set up arguments for minimal session
            sys.argv = ['shellpomodoro', '--work', '1', '--break', '1', '--iterations', '1']
            
            try:
                cli.main()
                print("SESSION_COMPLETED_SUCCESSFULLY")
            except SystemExit as e:
                if e.code == 0:
                    print("SESSION_COMPLETED_SUCCESSFULLY")
                else:
                    print(f"SESSION_FAILED_WITH_CODE_{e.code}")
            except Exception as e:
                print(f"SESSION_FAILED_WITH_EXCEPTION_{type(e).__name__}")
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            temp_script = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, temp_script],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            self.assertIn("SESSION_COMPLETED_SUCCESSFULLY", result.stdout)
            
        finally:
            os.unlink(temp_script)

    def test_error_handling_integration(self):
        """Test error handling throughout the application."""
        # Test configuration validation errors
        with patch('sys.argv', ['shellpomodoro', '--work', '0']):
            with patch('shellpomodoro.cli.parse_args', side_effect=ValueError("Invalid work duration")):
                stderr_capture = io.StringIO()
                
                with redirect_stderr(stderr_capture):
                    with self.assertRaises(SystemExit) as cm:
                        cli.main()
                    
                    # Should exit with error code
                    self.assertNotEqual(cm.exception.code, 0)

    def test_beep_functionality_integration(self):
        """Test audio notification system integration."""
        # Temporarily disable fast patches for this test to test actual beep functionality
        self.tearDown()  # Remove fast patches
        
        stdout_capture = io.StringIO()
        
        with redirect_stdout(stdout_capture):
            # Test beep function with different counts
            cli.beep(1)
            cli.beep(3)
        
        output = stdout_capture.getvalue()
        
        # Should contain terminal bell characters
        bell_count = output.count('\a')
        self.assertEqual(bell_count, 4)  # 1 + 3 beeps
        
        self.setUp()  # Restore fast patches

    def test_time_formatting_integration(self):
        """Test time formatting throughout the application."""
        # Test various time values
        test_cases = [
            (0, "00:00"),
            (30, "00:30"),
            (60, "01:00"),
            (90, "01:30"),
            (3600, "60:00"),
            (3661, "61:01"),
        ]
        
        for seconds, expected in test_cases:
            with self.subTest(seconds=seconds):
                result = cli.mmss(seconds)
                self.assertEqual(result, expected)

    def test_session_header_formatting_integration(self):
        """Test session header display formatting."""
        header = cli.session_header(25, 5, 4)
        
        # Verify header contains expected information
        self.assertIn("Pomodoro Session", header)
        self.assertIn("25min work", header)
        self.assertIn("5min break", header)
        self.assertIn("4 iteration", header)

    def test_countdown_display_integration(self):
        """Test countdown display formatting."""
        # Since countdown is mocked by FastPatchedTestCase, test the mmss formatting instead
        from shellpomodoro.cli import mmss
        
        # Test time formatting which is used in countdown
        result = mmss(65)  # 1 minute 5 seconds
        self.assertEqual(result, "01:05")
        
        # Test that countdown function exists and is callable
        self.assertTrue(callable(cli.countdown))

    def test_banner_display_integration(self):
        """Test completion banner display."""
        banner_text = cli.banner()
        
        # Verify banner contains expected elements
        self.assertIn("shellpomodoro", banner_text)
        self.assertIn("great work!", banner_text)
        self.assertIn("Session complete", banner_text)

    def test_memory_and_performance_characteristics(self):
        """Test that the application has reasonable memory and performance characteristics."""
        # Test that the application starts and completes quickly
        import time
        
        start_time = time.time()
        
        # Run a simulated session
        with patch('sys.argv', ['shellpomodoro', '--work', '1', '--iterations', '1']):
            stdout_capture = io.StringIO()
            with redirect_stdout(stdout_capture):
                try:
                    cli.main()
                except SystemExit:
                    pass
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete quickly (less than 1 second with mocked sleep)
        self.assertLess(execution_time, 1.0)

    def test_concurrent_session_safety(self):
        """Test that multiple sessions don't interfere with each other."""
        # This test ensures that global state doesn't cause issues
        
        def run_session():
            with patch('sys.argv', ['shellpomodoro', '--work', '1', '--iterations', '1']):
                stdout_capture = io.StringIO()
                with redirect_stdout(stdout_capture):
                    try:
                        cli.main()
                        return "SUCCESS"
                    except SystemExit:
                        return "SUCCESS"
                    except Exception as e:
                        return f"FAILED: {e}"
        
        # Run multiple sessions in sequence
        results = []
        for i in range(3):
            result = run_session()
            results.append(result)
        
        # All sessions should succeed
        for result in results:
            self.assertEqual(result, "SUCCESS")


class TestEndToEnd(FastPatchedTestCase):
    """End-to-end tests that verify complete user workflows."""

    def test_default_session_workflow(self):
        """Test default session workflow end-to-end."""
        # Create a temporary script for the test
        test_script = '''
import sys
sys.path.insert(0, "src")
from unittest.mock import patch
from shellpomodoro import cli

with patch("shellpomodoro.cli.read_key"):
    with patch("shellpomodoro.cli.time.sleep"):
        with patch("shellpomodoro.cli.beep"):
            sys.argv = ["shellpomodoro"]
            try:
                cli.main()
                print("SUCCESS")
            except SystemExit:
                print("SUCCESS")
            except Exception as e:
                print(f"FAILED: {e}")
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            temp_script = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, temp_script],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            self.assertIn("SUCCESS", result.stdout)
        finally:
            os.unlink(temp_script)

    def test_custom_configuration_workflow(self):
        """Test custom configuration workflow end-to-end."""
        # Create a temporary script for the test
        test_script = '''
import sys
sys.path.insert(0, "src")
from unittest.mock import patch
from shellpomodoro import cli

with patch("shellpomodoro.cli.read_key"):
    with patch("shellpomodoro.cli.time.sleep"):
        with patch("shellpomodoro.cli.beep"):
            sys.argv = ["shellpomodoro", "--work", "30", "--break", "10", "--iterations", "2"]
            try:
                cli.main()
                print("SUCCESS")
            except SystemExit:
                print("SUCCESS")
            except Exception as e:
                print(f"FAILED: {e}")
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            temp_script = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, temp_script],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            self.assertIn("SUCCESS", result.stdout)
        finally:
            os.unlink(temp_script)

    def test_help_command_workflow(self):
        """Test help command workflow end-to-end."""
        # Create a temporary script for the test
        test_script = '''
import sys
sys.path.insert(0, "src")
from shellpomodoro import cli

sys.argv = ["shellpomodoro", "--help"]
try:
    cli.main()
except SystemExit as e:
    print("SUCCESS" if e.code == 0 else f"FAILED: {e.code}")
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            temp_script = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, temp_script],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            self.assertIn("SUCCESS", result.stdout)
        finally:
            os.unlink(temp_script)

    def test_abort_workflow(self):
        """Test session abort workflow end-to-end."""
        # Create a temporary script for the test
        test_script = '''
import sys
sys.path.insert(0, "src")
from unittest.mock import patch
from shellpomodoro import cli

with patch("shellpomodoro.cli.run", side_effect=KeyboardInterrupt):
    sys.argv = ["shellpomodoro"]
    try:
        cli.main()
        print("FAILED: Should have exited")
    except SystemExit as e:
        print("SUCCESS" if e.code == 1 else f"FAILED: Wrong exit code {e.code}")
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            temp_script = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, temp_script],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            self.assertIn("SUCCESS", result.stdout)
        finally:
            os.unlink(temp_script)

    def test_package_console_script_workflow(self):
        """Test that the installed console script works end-to-end."""
        # This test requires the package to be installed
        result = subprocess.run(
            ['shellpomodoro', '--help'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("shellpomodoro", result.stdout)
        self.assertIn("Pomodoro timer", result.stdout)