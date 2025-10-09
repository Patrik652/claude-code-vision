# Research & Technology Decisions: Claude Code Vision

**Feature**: Claude Code Vision - Visual Feedback System
**Date**: 2025-10-08
**Status**: Complete

## Overview

This document resolves all technical uncertainties identified in the Technical Context section of the implementation plan. Each decision includes rationale, alternatives considered, and implementation guidance.

---

## Decision 1: Implementation Language

### Decision
**Python 3.8+** will be used for the Claude Code Vision implementation.

### Rationale
1. **Claude Code Integration**: Claude Code is built with Node.js/TypeScript, but the plugin/wrapper architecture doesn't require language matching
2. **Screenshot Libraries**: Python has superior image manipulation libraries (Pillow) with better documentation and stability
3. **System Integration**: Python has excellent subprocess management for invoking screenshot tools (scrot, grim, imagemagick)
4. **YAML Configuration**: PyYAML is mature and widely used
5. **Development Speed**: Python's simplicity aligns with "Clarity Over Cleverness" constitutional principle
6. **Existing Ecosystem**: User's environment shows Python-based tools (sage-mcp, cldmemory uses Python extensively)

### Alternatives Considered
- **Node.js 16+**:
  - Pro: Matches Claude Code's runtime, potentially easier IPC
  - Con: Image manipulation libraries (sharp) require native bindings, less stable on Linux
  - Con: Subprocess management more complex than Python
  - Rejected: Python's image handling superiority outweighs runtime matching benefit

- **Bash Script**:
  - Pro: Minimal dependencies, direct system tool access
  - Con: No image manipulation capabilities, would require external tools for resize/optimize
  - Con: Complex state management for monitoring mode
  - Rejected: Too limited for requirements like privacy zones and image optimization

### Implementation Guidance
- Use Python 3.8 as minimum version (available in Ubuntu 20.04 LTS and later)
- Structure as installable package with entry points for slash commands
- Use `subprocess.run()` for screenshot tool invocation
- Use `pathlib` for cross-platform path handling

---

## Decision 2: Primary Dependencies

### Decision
**Core Python Libraries**:
- **Pillow (PIL Fork)**: Image manipulation, optimization, privacy zone redaction
- **PyYAML**: Configuration file parsing
- **requests**: HTTP client for Claude API multimodal endpoints (if direct API access needed)
- **click**: CLI argument parsing for coordinate-based area selection

**Screenshot Tools (external binaries)**:
- **scrot**: X11 screenshot capture
- **grim**: Wayland screenshot capture
- **slurp**: Wayland area selection (graphical)
- **xrectsel**: X11 area selection (graphical)
- **ImageMagick (import command)**: Fallback screenshot tool

### Rationale

#### Pillow
- Industry standard for Python image processing
- Supports all required operations: resize, crop, format conversion, region overlay (for privacy)
- Excellent documentation and active maintenance
- Performance adequate for screenshot optimization (<2MB requirement)

#### PyYAML
- De facto standard for YAML in Python
- Safe loading prevents code injection
- Simple API matches project simplicity goals

#### requests
- Most widely used Python HTTP library
- Simpler than alternatives (httpx, urllib3 directly)
- Adequate for API communication needs
- May not be needed if we pipe through Claude Code's existing session

#### click
- Modern, well-documented CLI framework
- Better than argparse for complex command structures
- Supports command groups (aligns with /vision.area, /vision.auto subcommands)

#### Screenshot Tools
- **scrot**: Lightweight, reliable, standard X11 tool
- **grim**: Official Wayland compositor screenshot tool
- **slurp**: De facto standard for Wayland region selection (used by sway/wlroots compositors)
- **xrectsel**: Minimal X11 region selector
- **ImageMagick**: Universal fallback, available on virtually all Linux distros

### Alternatives Considered

**For Image Manipulation**:
- **opencv-python**:
  - Pro: Powerful computer vision features
  - Con: Massive dependency (100MB+), overkill for basic resize/crop
  - Rejected: Violates simplicity and installation speed goals

**For HTTP**:
- **httpx**:
  - Pro: Modern async support
  - Con: Not needed (no async requirements)
  - Rejected: requests sufficient for sync operations

**For CLI**:
- **argparse** (stdlib):
  - Pro: No external dependency
  - Con: Verbose for subcommand patterns
  - Rejected: click's clarity worth the small dependency

**For Screenshots**:
- **pyscreenshot** (Python library):
  - Pro: Pure Python, cross-platform
  - Con: Unreliable on Wayland, poor multi-monitor support
  - Rejected: External tools more reliable and flexible

### Implementation Guidance
- Use virtual environment for isolation
- Pin dependency versions in requirements.txt
- Detect screenshot tool availability at startup with clear error messages
- Auto-detect desktop environment (check $XDG_SESSION_TYPE or $WAYLAND_DISPLAY)

---

## Decision 3: Testing Framework

### Decision
**pytest** with the following structure:
- **Contract Tests**: Verify screenshot capture, image optimization, config parsing
- **Integration Tests**: Test slash command execution, Claude Code interaction, multi-monitor detection
- **Unit Tests**: Test individual functions (desktop detection, image resize logic, privacy zone application)

### Rationale
1. **pytest** is Python's de facto standard testing framework
2. Excellent fixture system for setup/teardown (temp files, mock configs)
3. Clear assertion messages aid debugging
4. Plugin ecosystem (pytest-cov for coverage, pytest-mock for mocking)
5. Aligns with Test-First Development constitutional principle

### Test Structure
```
tests/
├── contract/
│   ├── test_screenshot_capture.py    # Verify screenshot tools work
│   ├── test_image_optimization.py    # Verify <2MB payload
│   └── test_config_parsing.py        # Verify YAML config valid
├── integration/
│   ├── test_vision_command.py        # End-to-end /vision flow
│   ├── test_area_selection.py        # /vision.area workflow
│   └── test_auto_monitoring.py       # /vision.auto lifecycle
└── unit/
    ├── test_desktop_detection.py     # X11 vs Wayland logic
    ├── test_image_processing.py      # Resize, crop, privacy zones
    └── test_session_management.py    # Monitoring session state
```

### Alternatives Considered
- **unittest** (stdlib):
  - Pro: No dependency
  - Con: More verbose, weaker fixture system
  - Rejected: pytest's clarity and ecosystem worth dependency

- **nose2**:
  - Pro: Compatible with unittest
  - Con: Less active maintenance than pytest
  - Rejected: pytest more widely adopted

### Implementation Guidance
- Write tests BEFORE implementation (verify they fail)
- Use `pytest-mock` for mocking subprocess calls to screenshot tools
- Use `tmp_path` fixture for temporary config/screenshot files
- Aim for >80% code coverage, 100% for critical paths (privacy zones, OAuth handling)

---

## Decision 4: Claude Code Integration Approach

### Decision
**Wrapper Script + IPC (Inter-Process Communication)**

Architecture:
1. Create `claude-vision` wrapper command that intercepts `/vision*` commands
2. Wrapper handles screenshot capture, optimization, privacy zones
3. Wrapper communicates with Claude Code via:
   - **Option A (Preferred)**: Inject into Claude Code session using stdio piping
   - **Option B (Fallback)**: Direct API call to Claude using OAuth token extracted from Claude Code config

### Rationale
1. **No Core Modification**: Satisfies "MUST NOT modify Claude Code core codebase" constraint
2. **OAuth Reuse**: Can read Claude Code's OAuth token from `~/.claude/` config directory
3. **User Experience**: Seamless - user types `/vision` in Claude Code, wrapper handles behind scenes
4. **Maintainability**: Decoupled from Claude Code version changes

### Architecture Detail

**Wrapper Flow**:
```
User types: /vision "analyze this error"
    ↓
Claude Code detects unknown command → checks for custom command handler
    ↓
claude-vision wrapper activated
    ↓
1. Capture screenshot (auto-detect X11/Wayland tool)
2. Apply privacy zones (if configured)
3. Optimize image (<2MB)
4. Encode base64
5. Construct multimodal prompt: {"text": "analyze this error", "image": "base64..."}
6. Inject into Claude Code session OR call API directly
    ↓
Response flows back to user in Claude Code interface
```

**Implementation Strategy**:
- Register custom slash commands in `~/.claude/commands/` directory (if Claude Code supports)
- OR: Create bash wrapper that proxies Claude Code and intercepts vision commands
- Store OAuth token path in vision config, read when needed
- Cache token to avoid repeated disk reads

### Alternatives Considered

**Direct API Plugin**:
- Pro: Clean separation, independent deployment
- Con: Requires separate Claude API key (violates "must use Claude Code OAuth" constraint)
- Rejected: Cannot meet OAuth reuse requirement

**Fork Claude Code**:
- Pro: Native integration, best UX
- Con: Violates "MUST NOT modify Claude Code core" constraint
- Con: Maintenance burden for upstream changes
- Rejected: Constitutional violation

**Browser Extension**:
- Pro: Could capture browser-specific content
- Con: Out of scope (spec explicitly excludes browser extension)
- Con: Doesn't work for non-browser development
- Rejected: Wrong scope

### Implementation Guidance
- Study Claude Code's custom command mechanism (check `~/.claude/` for extension points)
- Implement OAuth token reading with fallback error handling
- Test token expiration scenario (FR-017 requirement)
- Provide clear error if Claude Code not installed or OAuth not configured

---

## Decision 5: Screenshot Tool Selection Logic

### Decision
**Auto-Detection with Manual Override**

Detection Algorithm:
```python
def detect_screenshot_tool():
    # 1. Check manual config override
    if config.screenshot_tool:
        return validate_tool(config.screenshot_tool)

    # 2. Detect desktop environment
    session_type = os.environ.get('XDG_SESSION_TYPE', 'x11')

    if session_type == 'wayland':
        # Wayland preference order
        if command_exists('grim'):
            return 'grim'
        elif command_exists('import'):  # ImageMagick
            return 'import'
        else:
            raise ToolNotFoundError("Install grim: sudo apt install grim")
    else:  # X11 or unknown (assume X11)
        # X11 preference order
        if command_exists('scrot'):
            return 'scrot'
        elif command_exists('import'):  # ImageMagick
            return 'import'
        else:
            raise ToolNotFoundError("Install scrot: sudo apt install scrot")
```

### Rationale
1. **Flexibility**: Manual override for edge cases or user preference
2. **Smart Defaults**: Auto-detection works for 95% of users
3. **Graceful Degradation**: ImageMagick as universal fallback
4. **Clear Errors**: Actionable installation instructions (FR-015)

### Area Selection Tool Detection
```python
def detect_area_selection_tool():
    session_type = os.environ.get('XDG_SESSION_TYPE', 'x11')

    if session_type == 'wayland':
        if command_exists('slurp'):
            return 'slurp'
        else:
            return 'coordinate_fallback'  # Use --coords parameter
    else:  # X11
        if command_exists('xrectsel'):
            return 'xrectsel'
        elif command_exists('slop'):  # Alternative X11 selector
            return 'slop'
        else:
            return 'coordinate_fallback'
```

### Alternatives Considered
- **Python Screenshot Libraries** (pyscreenshot, mss):
  - Pro: No external dependencies
  - Con: Unreliable on Wayland, poor multi-monitor support
  - Rejected: External tools more mature

- **Single Tool Only** (e.g., ImageMagick everywhere):
  - Pro: Simpler logic
  - Con: ImageMagick heavier than scrot/grim
  - Rejected: Optimizing for most common case better

### Implementation Guidance
- Cache detected tool for session duration (avoid repeated checks)
- Validate tool works on first use (capture test screenshot to /tmp)
- Provide `claude-vision --doctor` diagnostic command showing detected tools
- Document tool installation per distro (apt, dnf, pacman) in README

---

## Decision 6: Privacy Zone Implementation

### Decision
**Image Overlay with Black Rectangles**

Implementation:
```python
def apply_privacy_zones(image: Image, zones: List[Zone]) -> Image:
    """Apply privacy redaction by overlaying black rectangles.

    Args:
        image: PIL Image object
        zones: List of Zone(x, y, width, height) from config

    Returns:
        Image with privacy zones redacted
    """
    draw = ImageDraw.Draw(image)
    for zone in zones:
        # Draw filled black rectangle
        draw.rectangle(
            [(zone.x, zone.y), (zone.x + zone.width, zone.y + zone.height)],
            fill='black'
        )
    return image
```

Configuration Format:
```yaml
privacy:
  enabled: true
  zones:
    - name: "password_manager"
      x: 100
      y: 50
      width: 400
      height: 300
      monitor: 0  # Optional: which monitor (0=primary)
    - name: "notifications_area"
      x: 1500
      y: 0
      width: 420
      height: 100
```

### Rationale
1. **Simple & Reliable**: Black overlay guaranteed to hide content
2. **Visual Feedback**: User can see zones in final screenshot (debugging)
3. **No Data Leakage**: Pixel data completely replaced, not just blurred
4. **Performance**: Fast operation, no encryption overhead

### Alternatives Considered

**Crop Out Zones** (remove regions entirely):
- Pro: Smaller payload
- Con: Confusing layout, hard to understand context
- Rejected: Black overlay better preserves spatial context

**Blur Instead of Black**:
- Pro: More aesthetically pleasing
- Con: Sophisticated attacks can reverse blur (not secure)
- Rejected: Security over aesthetics for sensitive data

**Encrypt Zones**:
- Pro: Recoverable if needed
- Con: Complex key management, violates "no persistent storage" constraint
- Rejected: Overcomplicated

**Window-Based Detection** (auto-detect password managers):
- Pro: User doesn't configure manually
- Con: Unreliable (window titles vary), security risk if detection fails
- Rejected: User explicit control better for privacy

### Implementation Guidance
- Validate zones at config load time (x/y/width/height within screen bounds)
- Support monitor-relative coordinates (zone.monitor = 1 for second monitor)
- Provide helper command: `claude-vision --add-privacy-zone` (interactive setup)
- Log privacy zone application (for debugging, not in production)

---

## Decision 7: Image Optimization Strategy

### Decision
**Resize + Quality Compression**

Target: <2MB payload (SC-003 success criterion)

Algorithm:
```python
def optimize_screenshot(image: Image, max_size_mb: float = 2.0) -> bytes:
    """Optimize screenshot to meet size target.

    Strategy:
    1. Resize if resolution exceeds threshold
    2. Compress JPEG quality progressively
    3. Convert to WebP if still too large

    Returns:
        Optimized image bytes
    """
    MAX_BYTES = int(max_size_mb * 1024 * 1024)

    # Step 1: Resize large images
    width, height = image.size
    if width > 1920 or height > 1080:
        # Scale down to 1920x1080 max (preserve aspect ratio)
        image.thumbnail((1920, 1080), Image.LANCZOS)

    # Step 2: Try JPEG with quality=85
    buffer = io.BytesIO()
    image.convert('RGB').save(buffer, format='JPEG', quality=85, optimize=True)

    if buffer.tell() <= MAX_BYTES:
        return buffer.getvalue()

    # Step 3: Reduce quality to 70
    buffer = io.BytesIO()
    image.convert('RGB').save(buffer, format='JPEG', quality=70, optimize=True)

    if buffer.tell() <= MAX_BYTES:
        return buffer.getvalue()

    # Step 4: Try WebP (better compression)
    buffer = io.BytesIO()
    image.save(buffer, format='WEBP', quality=80)

    if buffer.tell() <= MAX_BYTES:
        return buffer.getvalue()

    # Step 5: Aggressive WebP
    buffer = io.BytesIO()
    image.save(buffer, format='WEBP', quality=60)

    return buffer.getvalue()  # Best effort
```

### Rationale
1. **Common Resolutions**: 1920x1080 adequate for debugging UI (most monitors)
2. **JPEG Quality**: 85 is imperceptible quality loss, 70 still very good
3. **WebP Fallback**: 25-35% better compression than JPEG
4. **Predictable**: Deterministic steps, easy to debug

### Benchmarks (estimated)
- 4K screenshot (3840x2160): ~8MB uncompressed → ~500KB optimized
- 1080p screenshot (1920x1080): ~2MB uncompressed → ~200KB optimized
- Typical developer screen: 1.5-2MB → <500KB

### Alternatives Considered

**PNG Compression**:
- Pro: Lossless
- Con: Much larger than JPEG for screenshots (text/UI compresses poorly)
- Rejected: Size constraint more important than perfect fidelity

**Adaptive Quality** (analyze image complexity):
- Pro: Optimal quality per image
- Con: Unpredictable results, slower
- Rejected: Fixed strategy simpler and adequate

**Client-Side Resize** (browser-based):
- Pro: No Python image library needed
- Con: Out of scope (not browser extension)
- Rejected: Wrong architecture

### Implementation Guidance
- Make max_size_mb configurable (default 2.0)
- Log optimization steps for debugging (original size, final size, format)
- Warn user if final size still exceeds target
- Measure optimization time (should be <500ms per SC-001 requirement)

---

## Decision 8: Configuration File Schema

### Decision
**YAML at `~/.config/claude-code-vision/config.yaml`**

Schema:
```yaml
# Claude Code Vision Configuration
version: "1.0"

# Screenshot settings
screenshot:
  tool: auto  # auto | scrot | grim | import
  format: jpeg  # jpeg | png | webp
  quality: 85  # 0-100 for JPEG/WebP
  max_size_mb: 2.0

# Multi-monitor support
monitors:
  default: 0  # 0=primary, 1=secondary, etc.
  # Per-monitor settings (optional)
  # - id: 0
  #   name: "eDP-1"
  # - id: 1
  #   name: "HDMI-1"

# Area selection
area_selection:
  tool: auto  # auto | slurp | xrectsel | slop | coordinates
  show_coordinates: true  # Display selected region coordinates

# Privacy zones (exclude from screenshots)
privacy:
  enabled: true
  prompt_first_use: true  # Ask for confirmation on first /vision command
  zones:
    # Example: password manager window
    # - name: "1password"
    #   x: 100
    #   y: 50
    #   width: 400
    #   height: 300
    #   monitor: 0

# Auto-monitoring mode
monitoring:
  interval_seconds: 30  # How often to capture in /vision.auto mode
  max_duration_minutes: 30  # Auto-stop after this duration
  idle_pause_minutes: 5  # Pause if no user interaction
  change_detection: true  # Track if screen changed since last capture

# Claude Code integration
claude_code:
  oauth_token_path: "~/.claude/config.json"  # Where to find OAuth token
  api_endpoint: "https://api.anthropic.com/v1/messages"  # Claude API

# Temporary files
temp:
  directory: "/tmp/claude-vision"  # Where to store temp screenshots
  cleanup: true  # Delete after transmission
  keep_on_error: false  # Keep temp files if error occurs (for debugging)

# Logging
logging:
  level: INFO  # DEBUG | INFO | WARNING | ERROR
  file: "~/.config/claude-code-vision/vision.log"
  max_size_mb: 10
  backup_count: 3
```

### Rationale
1. **YAML**: Human-readable, comments supported, hierarchical
2. **Sensible Defaults**: Works out-of-box for 90% of users
3. **Extensibility**: Easy to add settings without breaking existing configs
4. **Validation**: Schema version allows migration if format changes

### Alternatives Considered

**JSON**:
- Pro: Universally parsable
- Con: No comments, less human-friendly
- Rejected: YAML better for user-edited config

**TOML**:
- Pro: Gaining popularity (pyproject.toml standard)
- Con: Less familiar to average user
- Rejected: YAML more widely known

**Python Module** (.py config):
- Pro: Programmable, dynamic defaults
- Con: Security risk (arbitrary code execution)
- Rejected: Declarative safer

**INI**:
- Pro: Simple
- Con: No nested structures (can't represent privacy zones list)
- Rejected: Too limited

### Implementation Guidance
- Validate config on load with clear error messages
- Provide `claude-vision --init` to generate default config
- Support `~` expansion for paths
- Merge user config with defaults (don't require full config)
- Version config schema (reject incompatible versions with migration guide)

---

## Summary of Resolved Unknowns

| Technical Context Item | Decision | Confidence |
|------------------------|----------|------------|
| Language/Version | Python 3.8+ | ✅ High |
| Primary Dependencies | Pillow, PyYAML, requests, click + screenshot tools | ✅ High |
| Testing Framework | pytest with contract/integration/unit tests | ✅ High |
| Claude Code Integration | Wrapper script + OAuth token reuse | ⚠️ Medium (needs validation) |
| Screenshot Tool Selection | Auto-detect with fallback | ✅ High |
| Privacy Implementation | Black rectangle overlay | ✅ High |
| Image Optimization | Resize + JPEG quality + WebP fallback | ✅ High |
| Configuration Format | YAML with versioned schema | ✅ High |

### Remaining Validation Needed
1. **Claude Code Integration**: Verify custom command mechanism exists in Claude Code
2. **OAuth Token Location**: Confirm `~/.claude/config.json` structure
3. **Multi-monitor on Wayland**: Test grim multi-monitor support

These will be validated during Phase 1 implementation.

---

## Best Practices Identified

### Python Project Structure
- Use `pyproject.toml` for modern Python packaging (PEP 621)
- Entry points: `claude-vision` command, `/vision*` slash command handlers
- Virtual environment recommended for development and installation

### Linux Desktop Environment Handling
- Always check `$XDG_SESSION_TYPE` for Wayland vs X11
- Provide clear errors if tools missing (distro-specific install commands)
- Test on multiple compositors (GNOME/Wayland, KDE/Plasma, Sway, Xorg)

### Screenshot Capture Patterns
- Use subprocess timeouts (5s) to prevent hanging
- Capture stderr for error messages
- Validate screenshot file exists and non-zero size before processing

### Privacy & Security
- Never log screenshot content or paths (only metadata)
- Clear temp files immediately after transmission (not just on exit)
- Prompt for confirmation before first screenshot transmission
- Document data handling clearly in README

### Error Handling
- Provide actionable error messages with next steps
- Detect common failures: tools missing, permissions denied, display not available
- Graceful degradation: coordinate fallback if graphical selection unavailable

---

**Research Complete**: All NEEDS CLARIFICATION items resolved. Ready for Phase 1 design artifacts.
