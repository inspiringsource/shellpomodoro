# Makefile (repo root)

VENV=.venv
PY=$(VENV)/bin/python
PIP=$(VENV)/bin/pip
PYTEST=$(VENV)/bin/pytest
SP=$(VENV)/bin/shellpomodoro

.PHONY: venv install dev test run clean daemon-kill envcheck

venv:
	python3 -m venv $(VENV)

install: venv
	$(PIP) install -U pip
	$(PIP) install -e .

dev: venv
	$(PIP) install -U pip
	$(PIP) install -e .

test:
	$(PYTEST) -q

run:
	$(SP) --work 1 --iterations 1 --display bar

envcheck:
	which -a python; which -a pip; which -a shellpomodoro
	$(PY) -c "import sys;print('PYTHON:',sys.executable)"
	$(SP) --version || true

daemon-kill:
	$(PY) scripts/cleanup_daemon.py

clean: daemon-kill
	rm -rf build/ dist/ *.egg-info/
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
