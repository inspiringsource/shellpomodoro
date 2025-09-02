"""
Installation verification tests for shellpomodoro package.

These tests verify that the package can be properly installed and that
the CLI entry point is correctly configured.
"""

import subprocess
import sys
import tempfile
import venv
from pathlib import Path
from unittest import TestCase


class TestInstallation(TestCase):
    """Test package installation and distribution functionality."""

    def test_development_installation_works(self):
        """Test that pip install -e . works correctly."""
        # This test assumes the package is already installed in development mode
        # We verify by checking if the command is available
        result = subprocess.run(
            [sys.executable, "-c", "import shellpomodoro.cli; print('OK')"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("OK", result.stdout)

    def test_cli_entry_point_available(self):
        """Test that shellpomodoro command is available globally."""
        result = subprocess.run(
            ["shellpomodoro", "--help"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("shellpomodoro", result.stdout)
        self.assertIn("Pomodoro timer", result.stdout)

    def test_cli_entry_point_shows_help(self):
        """Test that --help flag works and shows expected content."""
        result = subprocess.run(
            ["shellpomodoro", "--help"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        
        # Check for expected help content
        expected_content = [
            "usage: shellpomodoro",
            "--work MINUTES",
            "--break MINUTES", 
            "--iterations COUNT",
            "--beeps COUNT",
            "Examples:"
        ]
        
        for content in expected_content:
            self.assertIn(content, result.stdout)

    def test_package_metadata_accessible(self):
        """Test that package metadata is properly accessible."""
        result = subprocess.run(
            [sys.executable, "-c", 
             "import shellpomodoro; "
             "from importlib.metadata import version; "
             "print(version('shellpomodoro'))"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("1.0.0", result.stdout)

    def test_package_structure_correct(self):
        """Test that package structure follows src-layout correctly."""
        import shellpomodoro
        import shellpomodoro.cli
        import shellpomodoro.models
        
        # Verify modules can be imported
        self.assertTrue(hasattr(shellpomodoro.cli, 'main'))
        self.assertTrue(hasattr(shellpomodoro.models, 'SessionConfig'))

    def test_wheel_installation_in_clean_environment(self):
        """Test that the built wheel can be installed in a clean virtual environment."""
        with tempfile.TemporaryDirectory() as temp_dir:
            venv_path = Path(temp_dir) / "test_venv"
            
            # Create virtual environment
            venv.create(venv_path, with_pip=True)
            
            # Get paths for the virtual environment
            if sys.platform == "win32":
                python_exe = venv_path / "Scripts" / "python.exe"
                pip_exe = venv_path / "Scripts" / "pip.exe"
            else:
                python_exe = venv_path / "bin" / "python"
                pip_exe = venv_path / "bin" / "pip"
            
            # Find the wheel file
            wheel_path = Path("dist") / "shellpomodoro-1.0.0-py3-none-any.whl"
            if not wheel_path.exists():
                self.skipTest("Wheel file not found. Run 'python -m build' first.")
            
            # Install the wheel in the virtual environment
            install_result = subprocess.run(
                [str(pip_exe), "install", str(wheel_path)],
                capture_output=True,
                text=True
            )
            self.assertEqual(install_result.returncode, 0, 
                           f"Installation failed: {install_result.stderr}")
            
            # Test that the command works in the virtual environment
            test_result = subprocess.run(
                [str(python_exe), "-c", 
                 "import sys; sys.argv = ['shellpomodoro', '--help']; "
                 "import shellpomodoro.cli; shellpomodoro.cli.main()"],
                capture_output=True,
                text=True
            )
            if test_result.returncode != 0:
                print(f"Test command failed with stderr: {test_result.stderr}")
                print(f"Test command stdout: {test_result.stdout}")
            self.assertEqual(test_result.returncode, 0)

    def test_sdist_contains_required_files(self):
        """Test that the source distribution contains all required files."""
        import tarfile
        
        sdist_path = Path("dist") / "shellpomodoro-1.0.0.tar.gz"
        if not sdist_path.exists():
            self.skipTest("Source distribution not found. Run 'python -m build' first.")
        
        with tarfile.open(sdist_path, 'r:gz') as tar:
            files = tar.getnames()
            
            # Check for required files
            required_files = [
                "shellpomodoro-1.0.0/pyproject.toml",
                "shellpomodoro-1.0.0/README.md",
                "shellpomodoro-1.0.0/LICENSE",
                "shellpomodoro-1.0.0/src/shellpomodoro/__init__.py",
                "shellpomodoro-1.0.0/src/shellpomodoro/cli.py",
                "shellpomodoro-1.0.0/src/shellpomodoro/models.py",
            ]
            
            for required_file in required_files:
                self.assertIn(required_file, files, 
                            f"Required file {required_file} not found in sdist")

    def test_console_script_entry_point(self):
        """Test that the console script entry point is properly configured."""
        result = subprocess.run(
            [sys.executable, "-c", 
             "from importlib.metadata import entry_points; "
             "eps = entry_points(); "
             "console_scripts = eps.select(group='console_scripts'); "
             "shellpomodoro_ep = [ep for ep in console_scripts if ep.name == 'shellpomodoro']; "
             "print(len(shellpomodoro_ep) > 0 and shellpomodoro_ep[0].value == 'shellpomodoro.cli:main')"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("True", result.stdout)