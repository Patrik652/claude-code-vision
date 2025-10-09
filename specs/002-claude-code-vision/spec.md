# Feature Specification: Claude Code Vision - Visual Feedback System

**Feature Branch**: `002-claude-code-vision`
**Created**: 2025-10-08
**Status**: Draft
**Input**: User description: "Claude Code Vision - Vizuálny feedback systém pre Claude Code s automatickým screen capture a multimodal prompts"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manual Screenshot Analysis (Priority: P1)

A developer encounters a visual bug or UI issue while coding. They want Claude Code to "see" their screen and provide analysis or debugging help based on what's visible.

**Why this priority**: This is the core value proposition - enabling visual context in Claude Code conversations. Delivers immediate value even without automation.

**Independent Test**: Can be fully tested by running `/vision` command, verifying screenshot is captured and sent to Claude, and receiving a response that references visual elements from the screenshot.

**Acceptance Scenarios**:

1. **Given** user is in Claude Code session, **When** user types `/vision` command, **Then** system captures current screen and sends it to Claude with user's prompt
2. **Given** screenshot is captured, **When** Claude receives the image, **Then** Claude responds with analysis referencing visual elements from the screenshot
3. **Given** user is on X11 desktop environment, **When** `/vision` command is executed, **Then** system successfully captures screenshot using appropriate tool (scrot/imagemagick)
4. **Given** user is on Wayland desktop environment, **When** `/vision` command is executed, **Then** system successfully captures screenshot using grim

---

### User Story 2 - Area Selection Capture (Priority: P2)

A developer wants to focus Claude's attention on a specific region of the screen (e.g., a particular window, error dialog, or UI component) rather than the entire screen.

**Why this priority**: Improves signal-to-noise ratio and reduces API payload size. Enhances core functionality but not critical for MVP.

**Independent Test**: Can be tested by running `/vision.area` command, selecting a screen region with mouse, and verifying only that region is captured and analyzed.

**Acceptance Scenarios**:

1. **Given** user types `/vision.area`, **When** system prompts for area selection, **Then** user can drag to select rectangular region
2. **Given** area is selected, **When** selection is confirmed, **Then** only selected region is captured and sent to Claude
3. **Given** selection tool fails, **When** error occurs, **Then** system falls back to full screen capture with user notification

---

### User Story 3 - Continuous Monitoring Mode (Priority: P3)

A developer working on visual debugging or design iteration wants Claude to periodically observe screen changes and provide ongoing feedback without manual triggering.

**Why this priority**: Advanced automation feature. Useful for specific workflows but not essential for basic visual feedback capability.

**Independent Test**: Can be tested by running `/vision.auto`, verifying screenshots are captured at configured intervals, and confirming Claude provides contextual updates when changes are detected.

**Acceptance Scenarios**:

1. **Given** user types `/vision.auto`, **When** auto-monitoring starts, **Then** system captures screenshots at configured interval (default: every 30 seconds)
2. **Given** auto-monitoring is active, **When** user types `/vision.stop`, **Then** monitoring stops immediately
3. **Given** significant screen changes detected, **When** new screenshot differs from previous, **Then** Claude is notified of changes
4. **Given** monitoring is active for extended period (reaches max duration), **When** max duration limit is reached (default: 30 minutes), **Then** system automatically stops monitoring and notifies user

**Future Enhancement**: Idle detection - system may pause monitoring when no user interaction detected for configured period

---

### User Story 4 - Privacy-Safe Capture (Priority: P2)

A developer wants to use vision features but needs to exclude sensitive areas of their screen (passwords, personal information, confidential client data).

**Why this priority**: Critical for real-world adoption in professional environments. Must exist before widespread use.

**Independent Test**: Can be tested by configuring excluded regions, capturing screenshot, and verifying sensitive areas are blacked out or skipped.

**Acceptance Scenarios**:

1. **Given** user configures excluded screen regions in config file, **When** screenshot is captured, **Then** excluded areas are blacked out before sending
2. **Given** user hasn't configured privacy settings, **When** first `/vision` command is run, **Then** system prompts for confirmation and explains data handling
3. **Given** password manager or credential window is detected, **When** screenshot is captured, **Then** system warns user and requires explicit confirmation

---

### Edge Cases

- What happens when multiple display monitors are connected? (Default: capture primary monitor, allow configuration for specific monitor)
- How does system handle screenshot tool not being installed? (Detect at startup, provide clear installation instructions)
- What happens when OAuth session expires during vision command? (Re-authenticate transparently or prompt user)
- How does system handle very large screenshots that exceed API limits? (Auto-resize to maximum supported resolution with quality preservation)
- What happens when screenshot capture fails (permissions, Wayland restrictions)? (Clear error message with troubleshooting steps)
- How does system behave when user tries `/vision` but no display is available (SSH session)? (Detect headless environment, provide helpful error)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST integrate with existing Claude Code installation and reuse its OAuth authentication session
- **FR-002**: System MUST provide `/vision` slash command that captures full screen and sends to Claude
- **FR-003**: System MUST provide `/vision.area` slash command for selective region capture
- **FR-004**: System MUST provide `/vision.auto` slash command for continuous monitoring mode
- **FR-005**: System MUST provide `/vision.stop` slash command to terminate auto-monitoring
- **FR-006**: System MUST auto-detect desktop environment (X11 vs Wayland) and use appropriate screenshot tool
- **FR-007**: System MUST support manual screenshot tool configuration via config file
- **FR-008**: System MUST encode screenshots in base64 for API transmission
- **FR-009**: System MUST construct multimodal prompts combining user text and screenshot image
- **FR-010**: System MUST optimize screenshot size before transmission (resize if exceeds reasonable threshold)
- **FR-011**: System MUST clean up temporary screenshot files after transmission
- **FR-012**: System MUST support privacy exclusion zones configured by user
- **FR-013**: System MUST prompt for user confirmation on first vision command execution
- **FR-014**: System MUST provide configuration file at `~/.config/claude-code-vision/config.yaml`
- **FR-015**: System MUST detect if required screenshot tools are installed and provide installation guidance if missing
- **FR-016**: System MUST handle multi-monitor setups with configurable monitor selection
- **FR-017**: System MUST provide clear error messages for common failure scenarios (permissions, missing tools, authentication)

### Key Entities

- **Screenshot**: Captured image data with metadata (timestamp, resolution, source monitor, capture method)
- **Vision Command**: User-triggered action requesting visual analysis (includes command type, target area, prompt text)
- **Configuration**: User preferences for screenshot tool, monitoring interval, excluded regions, default monitor
- **Monitoring Session**: Active auto-monitoring state tracking interval, last capture time, change detection status

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developer can capture and analyze screenshot within 5 seconds of typing `/vision` command
- **SC-002**: System successfully captures screenshots on both X11 and Wayland environments without manual configuration
- **SC-003**: Screenshot transmission payload size is under 2MB after optimization for 95% of typical developer screens
- **SC-004**: Privacy exclusion zones prevent sensitive information from being transmitted in 100% of configured cases
- **SC-005**: Auto-monitoring mode operates for at least 30 minutes without memory leaks or performance degradation
- **SC-006**: Setup process (including dependency installation) completes in under 10 minutes on standard Linux distributions
- **SC-007**: 90% of developers successfully complete their first vision command without consulting documentation
- **SC-008**: System provides actionable error messages for all common failure scenarios (screenshot tool missing, OAuth expired, permissions denied)

## Assumptions *(mandatory)*

- Claude Code is already installed and user has completed OAuth login
- User is running Linux with X11 or Wayland (no Windows/macOS initially)
- User has permissions to install system packages (for screenshot tool dependencies)
- Claude API supports multimodal input (image + text prompts)
- Network connectivity is available for API calls
- User's screen resolution is within common ranges (1920x1080 to 3840x2160)
- Standard Linux screenshot tools (scrot, grim, imagemagick) are available in distro repositories
- User has at least 100MB free disk space for temporary files and caching

## Constraints *(mandatory)*

- MUST NOT store screenshots persistently after transmission (privacy requirement)
- MUST NOT modify Claude Code core codebase (plugin/wrapper approach only)
- MUST NOT require separate API key (must use Claude Code OAuth)
- MUST NOT transmit screenshots without user awareness (explicit command or confirmed auto-mode)
- MUST NOT exceed Claude API image size limits (resize/compress as needed)
- MUST operate within Claude API rate limits (throttle auto-monitoring if needed)
- MUST NOT bypass system security (respect Wayland restrictions, no screen capture of lockscreens)

## Scope Boundaries

### In Scope
- Screenshot capture on Linux (X11 and Wayland)
- Integration with Claude Code via plugin/wrapper architecture
- Privacy controls for sensitive screen regions
- Basic area selection for focused captures
- Continuous monitoring mode with configurable intervals
- Configuration file for user preferences
- Installation script and dependency management

### Out of Scope
- Windows and macOS support (future consideration)
- Video recording or screen recording capabilities
- OCR or text extraction from screenshots (Claude handles this)
- Image editing or annotation tools
- Screenshot history or gallery
- Sharing screenshots with other users
- Integration with other AI models besides Claude
- Mobile device screenshot capture
- Remote desktop screenshot capture
- Browser extension for web page capture

## Dependencies

### External Dependencies
- Claude Code (must be installed and OAuth configured)
- Screenshot tools: scrot (X11), grim (Wayland), or imagemagick
- Python 3.8+ OR Node.js 16+ (for wrapper/plugin implementation)
- Linux display server (X11 or Wayland)
- Optional: dmenu or rofi for area selection UI

### Internal Dependencies
- Claude Code command parser/handler
- Claude Code OAuth token management
- Claude API multimodal endpoint

## Design Decisions

### Area Selection Implementation
**Decision**: Hybrid approach - graphical selection by default with coordinate-based fallback.
- Primary method: Use graphical tools (slurp for Wayland, xrectsel for X11) for intuitive drag-to-select interface
- Fallback: Support coordinate input via command parameters (--coords x,y,width,height) for scripting and environments where graphical tools unavailable
- Provides best user experience while maintaining flexibility for automation and edge cases

### Auto-Monitoring Behavior
**Decision**: Query-only mode - screenshots captured silently, Claude responds only when explicitly queried.
- Auto-monitoring captures screenshots at configured intervals and stores context
- Claude does not proactively comment on changes unless user asks
- Reduces noise and API usage while maintaining visual context history
- User maintains full control over conversation flow

### Multiple Monitoring Sessions
**Decision**: Single session in v1, architecture designed for future multi-session support.
- MVP supports one active monitoring session at a time
- System architecture uses session management pattern that can be extended
- Future versions can support multiple simultaneous sessions (different regions/monitors)
- Pragmatic approach: simpler implementation, lower resource usage, expandable design
