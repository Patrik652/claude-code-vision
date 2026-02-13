# Test Hardening and Release Checklist Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reduce skipped tests, raise coverage for weak API client modules, and add a production release checklist.

**Architecture:** Replace abstract placeholder contract tests with executable tests against concrete implementations and mocked dependencies. Add focused unit tests for `AnthropicAPIClient` and `GeminiAPIClient` error/success paths without network calls. Capture release readiness process in a repository checklist document.

**Tech Stack:** Python 3.12, pytest, monkeypatch, unittest.mock style patching, ruff, mypy.

### Task 1: Convert Screenshot Capture Contract Suite to Executable Tests

**Files:**
- Modify: `tests/contract/test_screenshot_capture.py`
- Test: `tests/contract/test_screenshot_capture.py`

**Step 1: Write failing executable contract fixture and tests**

Create a concrete `FakeScreenshotCapture` implementing `IScreenshotCapture` that:
- returns monitor metadata from `detect_monitors()`
- generates image files in `tmp_path`
- raises `MonitorNotFoundError`, `InvalidRegionError`, and `DisplayNotAvailableError` in relevant paths

**Step 2: Run test to verify behavior**

Run: `PYTHONPATH=. .venv/bin/pytest -q tests/contract/test_screenshot_capture.py`

Expected: tests execute (no placeholder fixture skip paths).

**Step 3: Keep contract assertions and remove placeholder skips**

Ensure contract checks still assert interface behavior and metadata consistency.

**Step 4: Re-run test to verify pass**

Run: `PYTHONPATH=. .venv/bin/pytest -q tests/contract/test_screenshot_capture.py`

Expected: PASS.

### Task 2: Raise Coverage for API Clients with Unit Tests

**Files:**
- Create: `tests/unit/test_claude_api_client.py`
- Create: `tests/unit/test_gemini_api_client.py`
- Test: `tests/unit/test_claude_api_client.py`
- Test: `tests/unit/test_gemini_api_client.py`

**Step 1: Write failing tests for key paths**

For `AnthropicAPIClient`:
- `_construct_multimodal_messages` content shape and mime mapping
- `_get_api_key` loading from JSON structures and missing config error
- `send_multimodal_prompt` handles 401, 413, timeout, non-200 API error

For `GeminiAPIClient`:
- `_get_api_key` from env and missing key error
- `send_multimodal_prompt` handles missing screenshot, payload too large, blocked/empty response, successful response extraction

**Step 2: Run targeted tests**

Run:
- `PYTHONPATH=. .venv/bin/pytest -q tests/unit/test_claude_api_client.py`
- `PYTHONPATH=. .venv/bin/pytest -q tests/unit/test_gemini_api_client.py`

Expected: PASS without network access.

**Step 3: Keep tests deterministic**

Use monkeypatch/mocks for `requests.post`, `genai.configure`, and model responses.

**Step 4: Re-run targeted tests**

Run both commands again and confirm pass.

### Task 3: Add Production Release Checklist

**Files:**
- Create: `docs/release-checklist.md`

**Step 1: Draft actionable checklist**

Include:
- preflight environment validation
- lint/type/test gates
- security and secret checks
- packaging/build checks
- manual smoke test commands
- versioning/tagging/changelog
- rollback and post-release verification

**Step 2: Validate formatting and references**

Run: `PYTHONPATH=. .venv/bin/ruff check tests/unit/test_claude_api_client.py tests/unit/test_gemini_api_client.py tests/contract/test_screenshot_capture.py`

Expected: no lint errors.

### Task 4: End-to-End Verification and Commit

**Files:**
- Modify/Create all files above

**Step 1: Run full verification**

Run:
- `PYTHONPATH=. .venv/bin/ruff check src/services src/cli tests/contract/test_screenshot_capture.py tests/unit/test_claude_api_client.py tests/unit/test_gemini_api_client.py`
- `PYTHONPATH=. .venv/bin/mypy src/services src/cli`
- `PYTHONPATH=. .venv/bin/pytest -q`

**Step 2: Commit**

Run:
```bash
git add tests/contract/test_screenshot_capture.py tests/unit/test_claude_api_client.py tests/unit/test_gemini_api_client.py docs/release-checklist.md docs/plans/2026-02-13-test-hardening-and-release-checklist.md
git commit -m "test: reduce skipped suites and add api client coverage"
git push
```
