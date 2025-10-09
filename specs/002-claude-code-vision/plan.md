# Implementation Plan: Claude Code Vision - Visual Feedback System

**Branch**: `002-claude-code-vision` | **Date**: 2025-10-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-claude-code-vision/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Claude Code Vision extends Claude Code with visual feedback capabilities, enabling developers to share screenshots during coding sessions. The system integrates with existing Claude Code OAuth, auto-detects Linux desktop environments (X11/Wayland), and provides slash commands (/vision, /vision.area, /vision.auto) for manual, selective, and continuous screen capture. Privacy controls allow exclusion zones for sensitive information. Implementation uses a plugin/wrapper architecture to avoid modifying Claude Code core.

## Technical Context

**Language/Version**: Python 3.8+ (Decision 1 in research.md - chosen for superior image manipulation libraries and system integration)
**Primary Dependencies**: Python: Pillow, PyYAML, requests, click; External tools: scrot (X11), grim (Wayland), slurp (Wayland area selection), slop/xrectsel (X11 area selection), imagemagick (fallback) - see Decision 2 in research.md
**Storage**: Local filesystem (temporary screenshots, config file at ~/.config/claude-code-vision/config.yaml)
**Testing**: pytest with contract/integration/unit test structure; integration tests for screenshot capture and Claude Code OAuth interaction
**Target Platform**: Linux (X11 and Wayland desktop environments)
**Project Type**: Single project (CLI tool/wrapper integrating with Claude Code)
**Performance Goals**: <5 seconds from /vision command to Claude response; <2MB screenshot payload after optimization
**Constraints**: Must not modify Claude Code core; must use existing OAuth session; must clean up temp files immediately; must respect API rate limits
**Scale/Scope**: Single-user CLI tool; 4 slash commands; 4 prioritized user stories; integration with 1 external system (Claude Code)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ I. Specification-Driven Development
**Status**: PASS
**Evidence**: Feature specification completed at `specs/002-claude-code-vision/spec.md` with user scenarios, requirements, success criteria, and design decisions documented.

### ✅ II. Independent User Stories
**Status**: PASS
**Evidence**: Specification defines 4 independent user stories with priorities (P1: Manual Screenshot, P2: Area Selection & Privacy, P3: Auto-monitoring). Each story is independently testable and deliverable.

### ✅ III. Test-First Development
**Status**: PASS (to be verified during implementation)
**Evidence**: Plan will generate test structure in Phase 1. Tasks will enforce test-first cycle: write tests → verify fail → implement → verify pass → refactor.

### ✅ IV. Clarity Over Cleverness
**Status**: PASS
**Evidence**: Design decisions favor simplicity: single session (not multi-session), query-only monitoring (not proactive), hybrid area selection (user-friendly with fallback). Plugin/wrapper approach avoids complex core modifications.

### ✅ V. Incremental Delivery
**Status**: PASS
**Evidence**: User stories prioritized P1→P2→P3. P1 (Manual Screenshot) delivers core value independently. P2 (Area Selection + Privacy) enhances P1. P3 (Auto-monitoring) builds on previous stories.

### Summary (Initial Check)
**Overall Status**: ✅ PASS - No constitutional violations. Proceeded to Phase 0 research.

---

### Re-Evaluation After Phase 1 Design

**Date**: 2025-10-08
**Artifacts Reviewed**: research.md, data-model.md, contracts/, quickstart.md

### ✅ I. Specification-Driven Development
**Status**: PASS
**Evidence**: Complete specification maintained. Research decisions documented in research.md. All design choices traced back to spec requirements.

### ✅ II. Independent User Stories
**Status**: PASS
**Evidence**: Data model and contracts support independent story implementation. P1 (Screenshot capture + API client) can be built without P2/P3 dependencies. Contract interfaces enable parallel development.

### ✅ III. Test-First Development
**Status**: PASS
**Evidence**: Contract tests defined in contracts/README.md with examples. Test structure documented: contract tests → integration tests → unit tests. Each interface specifies testable behavior and expected exceptions.

### ✅ IV. Clarity Over Cleverness
**Status**: PASS
**Evidence**:
- Python chosen for clarity over performance (research decision #1)
- Simple black rectangle overlay for privacy vs complex blur/encryption (research decision #6)
- Explicit error handling with actionable messages (contract design)
- Auto-detection with manual override (simplicity + flexibility)

### ✅ V. Incremental Delivery
**Status**: PASS
**Evidence**:
- Implementation order defined: Core interfaces → P1 (Manual Screenshot) → P2 (Area + Privacy) → P3 (Auto-monitoring)
- Each interface independently testable (IScreenshotCapture, IImageProcessor, etc.)
- Quickstart validates P1 can deliver value standalone

### Post-Design Summary
**Overall Status**: ✅ PASS - All constitutional principles maintained through design phase. Ready for Phase 2 (task generation via /speckit.tasks).

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
src/
├── models/
│   └── entities.py              # Screenshot, CaptureRegion, Configuration, PrivacyZone, MonitoringSession
├── services/
│   ├── screenshot_capture/
│   │   ├── x11_capture.py       # X11 screenshot implementation (scrot)
│   │   ├── wayland_capture.py   # Wayland screenshot implementation (grim)
│   │   ├── imagemagick_capture.py  # Fallback implementation
│   │   └── factory.py           # Auto-selection based on desktop environment
│   ├── region_selector/
│   │   ├── slurp_selector.py    # Wayland region selection
│   │   ├── xrectsel_selector.py # X11 region selection
│   │   ├── coordinate_selector.py  # Fallback coordinate-based selection
│   │   └── factory.py           # Region selector factory
│   ├── vision_service.py        # High-level orchestration service
│   ├── image_processor.py       # Privacy zones, optimization (Pillow)
│   ├── claude_api_client.py     # Multimodal API integration
│   ├── config_manager.py        # YAML configuration management
│   ├── temp_file_manager.py     # Temporary file lifecycle
│   └── monitoring_session_manager.py  # Auto-monitoring sessions
├── cli/
│   ├── main.py                  # CLI entry point (click groups)
│   ├── vision_command.py        # /vision command handler
│   ├── vision_area_command.py   # /vision.area command handler
│   ├── vision_auto_command.py   # /vision.auto command handler
│   ├── vision_stop_command.py   # /vision.stop command handler
│   ├── add_privacy_zone_command.py  # Privacy zone management
│   ├── init_command.py          # --init configuration generator
│   ├── doctor_command.py        # --doctor diagnostics
│   ├── list_monitors_command.py # --list-monitors utility
│   ├── validate_config_command.py  # --validate-config utility
│   └── test_capture_command.py  # --test-capture utility
├── interfaces/
│   └── screenshot_service.py    # ABC interfaces (IScreenshotCapture, IImageProcessor, etc.)
└── lib/
    ├── exceptions.py            # VisionError hierarchy with troubleshooting
    ├── desktop_detector.py      # X11 vs Wayland detection
    ├── tool_detector.py         # Screenshot tool availability detection
    ├── logging_config.py        # Logging configuration
    └── default_config.yaml      # Default configuration template

tests/
├── contract/                    # Interface compliance tests
│   ├── test_screenshot_capture.py
│   ├── test_image_processor.py
│   ├── test_claude_api_client.py
│   ├── test_vision_service.py
│   └── test_region_selector.py
├── integration/                 # Multi-component tests
│   ├── test_vision_command.py
│   ├── test_vision_area_command.py
│   ├── test_vision_auto_command.py
│   ├── test_privacy_zones.py
│   └── test_first_use_prompt.py
└── unit/                        # Isolated component tests
    ├── test_desktop_detector.py
    ├── test_tool_detector.py
    ├── test_capture_region.py
    └── test_privacy_zone.py
```

**Structure Decision**: Single project layout using Python package structure. CLI entry points registered via setup.py/pyproject.toml for `claude-vision` command. Test structure follows test-first development principle with three layers: contract tests (interface compliance), integration tests (multi-component workflows), and unit tests (isolated logic).

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
