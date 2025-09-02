# tests/__init__.py
import os

# Force non-interactive behavior for ANY test runner (unittest/pytest)
os.environ.setdefault("SHELLPOMODORO_NONINTERACTIVE", "1")