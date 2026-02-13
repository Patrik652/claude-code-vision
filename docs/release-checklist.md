# Claude Code Vision Release Checklist

Use this checklist before every production release.

## 1. Preflight

- [ ] Confirm branch is up to date with `origin/002-claude-code-vision` (or release branch).
- [ ] Confirm local workspace is clean: `git status --short`.
- [ ] Confirm Python and venv are ready: `python --version` and `test -d .venv`.
- [ ] Confirm required env vars are set for the target environment.

## 2. Quality Gates

- [ ] Run lint: `PYTHONPATH=. .venv/bin/ruff check src/services src/cli tests`.
- [ ] Run type checks: `PYTHONPATH=. .venv/bin/mypy src/services src/cli`.
- [ ] Run test suite: `PYTHONPATH=. .venv/bin/pytest -q`.
- [ ] Verify no unexpected skips were introduced.

## 3. Security and Secrets

- [ ] Verify no secrets are committed (`rg -n "api[_-]?key|token|secret" src tests docs`).
- [ ] Confirm runtime secrets are sourced from environment/config and not hardcoded.
- [ ] Confirm OAuth/API key paths are environment-specific and documented.

## 4. Packaging and Runtime Checks

- [ ] Validate install/run flow in a clean shell.
- [ ] Run CLI help and sanity checks:
  - [ ] `PYTHONPATH=. .venv/bin/python -m src.main --help`
  - [ ] `PYTHONPATH=. .venv/bin/python -m src.main --doctor`
- [ ] Validate screenshot capture dependencies available for target desktop environment.

## 5. Manual Smoke Tests

- [ ] `/vision "Describe this screen"` executes and returns response.
- [ ] `/vision.area` with a small region returns response.
- [ ] `/vision.auto` starts and `/vision.stop` ends cleanly.
- [ ] Privacy zones are applied before API submission.

## 6. Release Metadata

- [ ] Update changelog/release notes with user-facing changes and known limitations.
- [ ] Bump version if release policy requires versioned tags.
- [ ] Create annotated tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`.
- [ ] Push commit and tags: `git push && git push --tags`.

## 7. Rollback Plan

- [ ] Identify previous known-good tag.
- [ ] Confirm rollback command and owner are documented.
- [ ] Keep release notes with exact commit SHA for quick reversion.

## 8. Post-release Verification

- [ ] Re-run smoke tests in production environment.
- [ ] Check logs for API/auth/capture errors for at least one monitoring window.
- [ ] Confirm no spike in user-facing errors.
- [ ] Record release outcome in release notes.
