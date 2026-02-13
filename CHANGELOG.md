# Changelog

All notable changes to this project are documented in this file.

## [Unreleased] - 2026-02-13

### Added
- Idle-based pause/resume behavior in monitoring session manager.
- Unit tests for idle pause logic in `tests/unit/test_monitoring_session_manager_idle.py`.
- Structured PR draft in `PR_DRAFT.md` for this feature branch.

### Changed
- Improved CLI and service exception handling with explicit exception chaining.
- Cleaned up lint/type issues across CLI and services for stable CI.
- Updated contributor and task documentation to match current implementation state.

### Fixed
- Integration test setup issues in privacy zones and vision command test modules.
- Multiple static-analysis findings (Ruff and mypy) without changing command behavior.
