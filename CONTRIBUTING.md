# Contributing

## Dev setup

```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -e .[dev]
pytest -q
```

## Standards

- Python ≥ 3.9, stdlib-only at runtime
- Tests run fast (mock sleeps/keypress)
- Update README/--help when adding flags

## Commit & PR

- Conventional commits (feat:, fix:, docs:…)
- Include/adjust tests and CHANGELOG.md as needed

## Releases

- Bump pyproject.toml version
- Tag vX.Y.Z → GitHub Actions (Trusted Publisher) releases to PyPI

## Security

Please do not file public issues for vulnerabilities. Use:
<https://github.com/inspiringsource/shellpomodoro/security/advisories/new>
