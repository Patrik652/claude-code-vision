# Tasks: Claude Code Vision - Visual Feedback System

**Input**: Design documents from `/specs/002-claude-code-vision/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Test-First Development enabled - tests MUST be written before implementation per constitution

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root
- Python 3.8+ project structure
- Test structure: `tests/contract/`, `tests/integration/`, `tests/unit/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure: `src/{models,services,cli,lib}`, `tests/{contract,integration,unit}`
- [x] T002 Initialize Python project with pyproject.toml (Python 3.8+, dependencies: Pillow, PyYAML, requests, click)
- [x] T003 [P] Configure linting (ruff/black) and type checking (mypy) in pyproject.toml
- [x] T004 [P] Create setup.py or pyproject.toml entry points for `claude-vision` CLI command
- [x] T005 [P] Create .gitignore for Python (venv/, __pycache__/, *.pyc, /temp/, *.log)
- [x] T006 [P] Create requirements.txt and requirements-dev.txt with pinned versions
- [x] T007 Create README.md with installation instructions from quickstart.md
- [x] T008 [P] Setup logging configuration module in `src/lib/logging_config.py`

**Checkpoint**: Basic project structure ready for development

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T009 [P] Create all entity dataclasses in `src/models/entities.py` (Screenshot, CaptureRegion, Configuration, PrivacyZone, MonitoringSession, VisionCommand)
- [x] T010 [P] Create all exception classes in `src/lib/exceptions.py` per contracts (VisionError hierarchy)
- [x] T011 [P] Copy all interface definitions from contracts to `src/interfaces/` directory
- [x] T012 Create Configuration management infrastructure in `src/services/config_manager.py` implementing IConfigurationManager
- [x] T013 Create TempFileManager in `src/services/temp_file_manager.py` implementing ITempFileManager
- [x] T014 Create desktop environment detection utility in `src/lib/desktop_detector.py` (X11 vs Wayland detection)
- [x] T015 Create screenshot tool detection utility in `src/lib/tool_detector.py` (scrot, grim, import availability check)
- [x] T016 [P] Create default config template YAML in `src/lib/default_config.yaml`
- [x] T017 [P] Setup pytest configuration in `pyproject.toml` or `pytest.ini`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Manual Screenshot Analysis (Priority: P1) 🎯 MVP

**Goal**: Enable `/vision` command to capture full screen, send to Claude, and display response

**Independent Test**: Run `/vision "test prompt"`, verify screenshot captured, sent to Claude, response displayed

### Tests for User Story 1 (Test-First Development)

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T018 [P] [US1] Contract test for IScreenshotCapture.capture_full_screen() in `tests/contract/test_screenshot_capture.py`
- [x] T019 [P] [US1] Contract test for IImageProcessor.optimize_image() in `tests/contract/test_image_processor.py`
- [x] T020 [P] [US1] Contract test for IClaudeAPIClient.send_multimodal_prompt() in `tests/contract/test_claude_api_client.py`
- [x] T021 [P] [US1] Contract test for IVisionService.execute_vision_command() in `tests/contract/test_vision_service.py`
- [x] T022 [US1] Integration test for `/vision` command end-to-end in `tests/integration/test_vision_command.py`
- [x] T023 [P] [US1] Unit test for desktop environment detection in `tests/unit/test_desktop_detector.py`
- [x] T024 [P] [US1] Unit test for screenshot tool detection in `tests/unit/test_tool_detector.py`

### Implementation for User Story 1

- [x] T025 [P] [US1] Implement X11ScreenshotCapture in `src/services/screenshot_capture/x11_capture.py` implementing IScreenshotCapture
- [x] T026 [P] [US1] Implement WaylandScreenshotCapture in `src/services/screenshot_capture/wayland_capture.py` implementing IScreenshotCapture
- [x] T027 [P] [US1] Implement ImageMagickScreenshotCapture (fallback) in `src/services/screenshot_capture/imagemagick_capture.py` implementing IScreenshotCapture
- [x] T028 [US1] Create ScreenshotCaptureFactory in `src/services/screenshot_capture/factory.py` to auto-select implementation based on desktop environment
- [x] T029 [US1] Implement PillowImageProcessor in `src/services/image_processor.py` implementing IImageProcessor (optimize_image method)
- [x] T030 [US1] Implement AnthropicAPIClient in `src/services/claude_api_client.py` implementing IClaudeAPIClient
- [x] T031 [US1] Implement OAuth token reading from `~/.claude/config.json` in AnthropicAPIClient
- [x] T032 [US1] Implement base64 encoding for screenshot in AnthropicAPIClient
- [x] T033 [US1] Implement multimodal prompt construction in AnthropicAPIClient
- [x] T034 [US1] Implement VisionService.execute_vision_command() in `src/services/vision_service.py` orchestrating all components
- [x] T035 [US1] Implement `/vision` CLI command handler in `src/cli/vision_command.py` using click
- [x] T036 [US1] Add error handling for common scenarios (tool missing, OAuth expired, display unavailable) with FR-017 actionable messages
- [x] T037 [US1] Add logging for all operations in User Story 1
- [x] T038 [US1] Implement temp file cleanup after transmission (FR-011)
- [x] T039 [US1] Verify all tests pass for User Story 1

**Checkpoint**: At this point, `/vision` command should be fully functional and testable independently. MVP COMPLETE!

---

## Phase 4: User Story 2 - Area Selection Capture (Priority: P2)

**Goal**: Enable `/vision.area` command for selective region capture with graphical or coordinate-based selection

**Independent Test**: Run `/vision.area "test prompt"`, select region graphically or via coordinates, verify only selected region captured and analyzed

### Tests for User Story 2 (Test-First Development)

- [x] T040 [P] [US2] Contract test for IScreenshotCapture.capture_region() in `tests/contract/test_screenshot_capture.py` (extend existing)
- [x] T041 [P] [US2] Contract test for IRegionSelector.select_region_graphical() in `tests/contract/test_region_selector.py`
- [x] T042 [P] [US2] Contract test for IRegionSelector.select_region_coordinates() in `tests/contract/test_region_selector.py`
- [x] T043 [P] [US2] Contract test for IVisionService.execute_vision_area_command() in `tests/contract/test_vision_service.py` (extend existing)
- [x] T044 [US2] Integration test for `/vision.area` graphical selection in `tests/integration/test_vision_area_command.py`
- [x] T045 [US2] Integration test for `/vision.area --coords` coordinate input in `tests/integration/test_vision_area_command.py`
- [x] T046 [P] [US2] Unit test for CaptureRegion validation in `tests/unit/test_capture_region.py`

### Implementation for User Story 2

- [x] T047 [P] [US2] Implement capture_region() method in X11ScreenshotCapture (extend T025)
- [x] T048 [P] [US2] Implement capture_region() method in WaylandScreenshotCapture (extend T026)
- [x] T049 [P] [US2] Implement SlurpRegionSelector (Wayland) in `src/services/region_selector/slurp_selector.py` implementing IRegionSelector
- [x] T050 [P] [US2] Implement XrectselRegionSelector (X11) in `src/services/region_selector/xrectsel_selector.py` implementing IRegionSelector
- [x] T051 [P] [US2] Implement CoordinateRegionSelector in `src/services/region_selector/coordinate_selector.py` implementing IRegionSelector
- [x] T052 [US2] Create RegionSelectorFactory in `src/services/region_selector/factory.py` implementing hybrid approach (graphical with coordinate fallback)
- [x] T053 [US2] Implement CaptureRegion.validate() method in `src/models/entities.py` (extend T009)
- [x] T054 [US2] Implement VisionService.execute_vision_area_command() in `src/services/vision_service.py` (extend T034)
- [x] T055 [US2] Implement `/vision.area` CLI command handler in `src/cli/vision_area_command.py` with --coords option
- [x] T056 [US2] Add error handling for region selection cancellation and tool not found (FR-017)
- [x] T057 [US2] Add fallback logic: graphical selection fails → coordinate input
- [x] T058 [US2] Verify all tests pass for User Story 2

**Checkpoint**: At this point, both `/vision` and `/vision.area` commands should work independently

---

## Phase 5: User Story 4 - Privacy-Safe Capture (Priority: P2)

**Goal**: Enable privacy zone configuration to redact sensitive screen areas before transmission

**Independent Test**: Configure privacy zones, run `/vision`, verify sensitive areas are blacked out in transmitted screenshot

### Tests for User Story 4 (Test-First Development)

- [x] T059 [P] [US4] Contract test for IImageProcessor.apply_privacy_zones() in `tests/contract/test_image_processor.py` (extend T019)
- [x] T060 [US4] Integration test for privacy zone redaction in `tests/integration/test_privacy_zones.py`
- [x] T061 [P] [US4] Unit test for PrivacyZone validation in `tests/unit/test_privacy_zone.py`
- [x] T062 [US4] Integration test for first-use confirmation prompt (FR-013) in `tests/integration/test_first_use_prompt.py`

### Implementation for User Story 4

- [x] T063 [US4] Implement apply_privacy_zones() in PillowImageProcessor (extend T029)
- [x] T064 [US4] Implement black rectangle overlay logic using PIL ImageDraw
- [x] T065 [US4] Implement PrivacyZone validation in `src/models/entities.py` (extend T009)
- [x] T066 [US4] Add privacy zone loading from Configuration in ConfigurationManager
- [x] T067 [US4] Implement first-use confirmation prompt in VisionService (FR-013)
- [x] T068 [US4] Add privacy zone application to VisionService.execute_vision_command() workflow
- [x] T069 [US4] Add privacy zone application to VisionService.execute_vision_area_command() workflow
- [x] T070 [US4] Create `claude-vision --add-privacy-zone` interactive helper CLI command
- [x] T071 [US4] Verify SC-004: Privacy zones prevent 100% of configured sensitive data transmission
- [x] T072 [US4] Verify all tests pass for User Story 4

**Checkpoint**: Privacy features integrated with US1 and US2, all working independently

---

## Phase 6: User Story 3 - Continuous Monitoring Mode (Priority: P3)

**Goal**: Enable `/vision.auto` and `/vision.stop` commands for continuous screenshot capture at intervals

**Independent Test**: Run `/vision.auto`, verify screenshots captured every 30 seconds, run `/vision.stop`, verify monitoring stops

### Tests for User Story 3 (Test-First Development)

- [x] T073 [P] [US3] Contract test for IMonitoringSessionManager.start_session() in `tests/contract/test_monitoring_session_manager.py`
- [x] T074 [P] [US3] Contract test for IMonitoringSessionManager.stop_session() in `tests/contract/test_monitoring_session_manager.py`
- [x] T075 [P] [US3] Contract test for IMonitoringSessionManager.pause_session() in `tests/contract/test_monitoring_session_manager.py`
- [x] T076 [P] [US3] Contract test for IImageProcessor.calculate_image_hash() in `tests/contract/test_image_processor.py` (extend T019)
- [x] T077 [P] [US3] Contract test for IVisionService.execute_vision_auto_command() in `tests/contract/test_vision_service.py` (extend T021)
- [x] T078 [P] [US3] Contract test for IVisionService.execute_vision_stop_command() in `tests/contract/test_vision_service.py` (extend T021)
- [x] T079 [US3] Integration test for `/vision.auto` monitoring lifecycle in `tests/integration/test_vision_auto_command.py`
- [x] T080 [US3] Integration test for session pause on idle in `tests/integration/test_monitoring_idle_pause.py`
- [x] T081 [US3] Integration test for max duration auto-stop in `tests/integration/test_monitoring_max_duration.py`
- [x] T082 [P] [US3] Unit test for MonitoringSession state transitions in `tests/unit/test_monitoring_session.py`

### Implementation for User Story 3

- [x] T083 [US3] Implement MonitoringSessionManager in `src/services/monitoring_session_manager.py` implementing IMonitoringSessionManager
- [x] T084 [US3] Implement start_session() with background capture loop using threading or asyncio
- [x] T085 [US3] Implement stop_session() with cleanup
- [x] T086 [US3] Implement pause_session() for idle detection
- [x] T087 [US3] Implement resume_session() for idle recovery
- [x] T088 [US3] Implement get_active_session() for session state queries
- [x] T089 [US3] Implement calculate_image_hash() in PillowImageProcessor for change detection (extend T029)
- [x] T090 [US3] Implement change detection logic in MonitoringSessionManager
- [x] T091 [US3] Implement idle pause logic (5 minutes no interaction)
- [x] T092 [US3] Implement max duration auto-stop (30 minutes default)
- [x] T093 [US3] Implement single session enforcement (only one active at a time)
- [x] T094 [US3] Implement VisionService.execute_vision_auto_command() in `src/services/vision_service.py` (extend T034)
- [x] T095 [US3] Implement VisionService.execute_vision_stop_command() in `src/services/vision_service.py` (extend T034)
- [x] T096 [US3] Implement `/vision.auto` CLI command handler in `src/cli/vision_auto_command.py`
- [x] T097 [US3] Implement `/vision.stop` CLI command handler in `src/cli/vision_stop_command.py`
- [x] T098 [US3] Add error handling for SessionAlreadyActiveError and SessionNotFoundError
- [x] T099 [US3] Verify SC-005: Auto-monitoring operates 30+ minutes without memory leaks
- [x] T100 [US3] Verify all tests pass for User Story 3

**Checkpoint**: All user stories (US1, US2, US3, US4) should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and production readiness

- [x] T101 [P] Create `claude-vision --init` command to generate default config in `src/cli/init_command.py`
- [x] T102 [P] Create `claude-vision --doctor` diagnostic command in `src/cli/doctor_command.py` (verify tools, OAuth, config)
- [x] T103 [P] Create `claude-vision --list-monitors` command in `src/cli/list_monitors_command.py`
- [x] T104 [P] Create `claude-vision --validate-config` command in `src/cli/validate_config_command.py`
- [x] T105 [P] Create `claude-vision --test-capture` command for screenshot tool testing in `src/cli/test_capture_command.py`
- [x] T106 Create main CLI entry point in `src/cli/main.py` aggregating all commands using click groups
- [ ] T107 Implement multi-monitor support: detect monitors, support --monitor flag (FR-016)
- [ ] T108 Add comprehensive error messages with troubleshooting steps for all exception types (FR-017)
- [ ] T109 Optimize screenshot capture performance to meet <5 second SC-001 requirement
- [ ] T110 Verify SC-002: Auto-detection works on both X11 and Wayland without manual config
- [ ] T111 Verify SC-003: Screenshot payload <2MB for 95% of typical screens
- [ ] T112 Verify SC-006: Setup completes in <10 minutes on standard Linux distros
- [ ] T113 Verify SC-007: 90% of developers complete first /vision without docs
- [ ] T114 Verify SC-008: Actionable error messages for all common failures
- [ ] T115 [P] Add docstrings to all public methods and classes
- [ ] T116 [P] Run mypy type checking across entire codebase and fix issues
- [ ] T117 [P] Run black/ruff linting and format all code
- [x] T118 Create installation script `install.sh` for dependency management
- [x] T119 Create CONTRIBUTING.md with development setup instructions
- [x] T120 [P] Add GitHub Actions CI workflow (if using GitHub) for automated testing
- [ ] T121 Validate all quickstart.md scenarios work end-to-end
- [ ] T122 Final integration testing: all commands work together without conflicts
- [ ] T123 Performance profiling and optimization if needed
- [ ] T124 Security review: no credentials logged, temp files cleaned, OAuth handling secure

**Checkpoint**: Production-ready release candidate

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 - P1 (Phase 3)**: Depends on Foundational - Can start immediately after Phase 2
- **User Story 2 - P2 (Phase 4)**: Depends on Foundational - Can run parallel with US1 OR sequentially after US1
- **User Story 4 - P2 (Phase 5)**: Depends on Foundational + US1 (applies privacy to US1 workflow) - Can run parallel with US2
- **User Story 3 - P3 (Phase 6)**: Depends on Foundational + US1 (uses US1 capture logic) - Can run parallel with US2/US4
- **Polish (Phase 7)**: Depends on completion of desired user stories

### User Story Dependencies

- **User Story 1 (P1)**: INDEPENDENT - No dependencies on other stories
- **User Story 2 (P2)**: INDEPENDENT - No dependencies on other stories (extends capture, doesn't modify US1)
- **User Story 4 (P2)**: Integrates with US1 and US2 (adds privacy layer) but independently testable
- **User Story 3 (P3)**: Uses US1 capture logic but independently testable (different command)

### Within Each User Story

- Tests MUST be written and FAIL before implementation (Test-First Development)
- Interfaces before implementations
- Models before services
- Services before CLI commands
- Core implementation before error handling
- Story complete before moving to next priority

### Parallel Opportunities

**Setup Phase (Phase 1):**
- T003, T004, T005, T006, T008 can run in parallel

**Foundational Phase (Phase 2):**
- T009, T010, T011, T016, T017 can run in parallel

**User Story 1 Tests:**
- T018, T019, T020, T021, T023, T024 can run in parallel

**User Story 1 Implementation:**
- T025, T026, T027 (different screenshot implementations) can run in parallel
- After T028 completes: T029, T030 can run in parallel

**User Story 2 Tests:**
- T040, T041, T042, T043, T046 can run in parallel

**User Story 2 Implementation:**
- T047, T048, T049, T050, T051 can run in parallel

**User Story 4 Tests:**
- T059, T061 can run in parallel

**User Story 3 Tests:**
- T073, T074, T075, T076, T077, T078, T082 can run in parallel

**Polish Phase:**
- T101, T102, T103, T104, T105, T115, T116, T117, T120 can run in parallel

**Different User Stories:**
- Once Foundational (Phase 2) completes, US1, US2, US4, US3 can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all User Story 1 contract tests together:
Task T018: "Contract test for IScreenshotCapture.capture_full_screen() in tests/contract/test_screenshot_capture.py"
Task T019: "Contract test for IImageProcessor.optimize_image() in tests/contract/test_image_processor.py"
Task T020: "Contract test for IClaudeAPIClient.send_multimodal_prompt() in tests/contract/test_claude_api_client.py"
Task T021: "Contract test for IVisionService.execute_vision_command() in tests/contract/test_vision_service.py"
Task T023: "Unit test for desktop environment detection in tests/unit/test_desktop_detector.py"
Task T024: "Unit test for screenshot tool detection in tests/unit/test_tool_detector.py"

# Verify all tests FAIL

# Launch all screenshot capture implementations together:
Task T025: "Implement X11ScreenshotCapture in src/services/screenshot_capture/x11_capture.py"
Task T026: "Implement WaylandScreenshotCapture in src/services/screenshot_capture/wayland_capture.py"
Task T027: "Implement ImageMagickScreenshotCapture in src/services/screenshot_capture/imagemagick_capture.py"

# Verify tests PASS after implementation
```

---

## Implementation Strategy

### MVP First (User Story 1 Only) - Recommended

1. Complete Phase 1: Setup (T001-T008)
2. Complete Phase 2: Foundational (T009-T017) - CRITICAL blocking phase
3. Complete Phase 3: User Story 1 (T018-T039)
4. **STOP and VALIDATE**: Test `/vision` command independently
5. Deploy/demo MVP if ready
6. Gather feedback before building US2, US4, US3

**Estimated effort**: 15-20 tasks (Setup + Foundational + US1) = ~2-3 days for experienced developer

### Incremental Delivery (Full Feature Set)

1. Complete Setup (Phase 1) + Foundational (Phase 2) → Foundation ready (T001-T017)
2. Add User Story 1 (Phase 3) → Test `/vision` independently → Deploy/Demo MVP! (T018-T039)
3. Add User Story 2 (Phase 4) → Test `/vision.area` independently → Deploy (T040-T058)
4. Add User Story 4 (Phase 5) → Test privacy zones independently → Deploy (T059-T072)
5. Add User Story 3 (Phase 6) → Test `/vision.auto` independently → Deploy (T073-T100)
6. Polish (Phase 7) → Production-ready (T101-T124)

Each story adds value without breaking previous stories.

**Total estimated effort**: 124 tasks = ~1-2 weeks for experienced developer (full feature set)

### Parallel Team Strategy

With 3 developers after Foundational phase completes:

- **Developer A**: User Story 1 (T018-T039) - MVP priority
- **Developer B**: User Story 2 (T040-T058) - Can start in parallel
- **Developer C**: User Story 4 (T059-T072) - Can start in parallel

User Story 3 (T073-T100) waits until US1 completes (reuses capture logic).

---

## Task Count Summary

- **Phase 1 - Setup**: 8 tasks
- **Phase 2 - Foundational**: 9 tasks (BLOCKS all user stories)
- **Phase 3 - User Story 1 (P1) MVP**: 22 tasks (7 tests + 15 implementation)
- **Phase 4 - User Story 2 (P2)**: 19 tasks (7 tests + 12 implementation)
- **Phase 5 - User Story 4 (P2)**: 14 tasks (4 tests + 10 implementation)
- **Phase 6 - User Story 3 (P3)**: 28 tasks (10 tests + 18 implementation)
- **Phase 7 - Polish**: 24 tasks

**Total**: 124 tasks

**MVP Scope** (Setup + Foundational + US1): 39 tasks
**Parallel opportunities**: 35+ tasks can run in parallel across the project

---

## Notes

- **[P]** tasks = different files, no dependencies, can run in parallel
- **[Story]** label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **Test-First Development**: Verify tests fail before implementing, pass after implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Constitution compliance: All 5 principles maintained throughout task structure
- Success criteria SC-001 through SC-008 verified in Polish phase
