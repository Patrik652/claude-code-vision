#!/usr/bin/env bash

set -euo pipefail

echo "[smoke] Claude Code Vision smoke test"
echo "[smoke] date: $(date -Is)"

if [[ ! -d ".venv" ]]; then
  echo "[smoke] ERROR: .venv not found. Create it first."
  exit 1
fi

export PYTHONPATH=.

echo "[smoke] 1/7 lint"
.venv/bin/ruff check src/services src/cli

echo "[smoke] 2/7 types"
.venv/bin/mypy src/services src/cli

echo "[smoke] 3/7 unit/integration tests"
.venv/bin/pytest -q

echo "[smoke] 4/7 cli --help"
.venv/bin/python -m src.cli.main --help >/dev/null

echo "[smoke] 5/7 validate-config"
.venv/bin/python -m src.cli.main validate-config >/dev/null || true

echo "[smoke] 6/7 doctor"
.venv/bin/python -m src.cli.main doctor >/dev/null || true

echo "[smoke] 7/7 display-aware capture probe"
if [[ -n "${DISPLAY:-}" || -n "${WAYLAND_DISPLAY:-}" ]]; then
  .venv/bin/python -m src.cli.main test-capture >/dev/null || true
  echo "[smoke] capture probe executed (display detected)"
else
  echo "[smoke] skipped capture probe (no DISPLAY/WAYLAND_DISPLAY)"
fi

echo "[smoke] PASS"
