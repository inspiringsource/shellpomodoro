# Releasing shellpomodoro

1. Update `pyproject.toml` version (e.g., 0.1.0 -> 0.1.1).
2. Commit: `git commit -am "chore: bump version to 0.1.1" && git push`.
3. Tag: `git tag v0.1.1 && git push --tags`.
4. GitHub Actions builds and publishes to PyPI via Trusted Publisher (OIDC).
5. Verify: `python -m venv .venv-check && source .venv-check/bin/activate && pip install -U pip && pip install shellpomodoro && shellpomodoro --help`.
6. Update README install section (switch to `pip install shellpomodoro`) if this is the first public release.
