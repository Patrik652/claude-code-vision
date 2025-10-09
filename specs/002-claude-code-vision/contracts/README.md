# API Contracts: Claude Code Vision

## Overview

This directory contains interface contracts for the Claude Code Vision system. Contracts define the expected behavior of each service component without specifying implementation details.

## Contract Files

### screenshot-service.py

Defines interfaces for all screenshot-related operations:

- **IScreenshotCapture**: Screenshot capture from display (X11/Wayland)
- **IImageProcessor**: Image optimization, privacy zones, hashing
- **IRegionSelector**: Interactive and coordinate-based region selection
- **IClaudeAPIClient**: Claude API communication with multimodal prompts
- **IConfigurationManager**: Config file loading, saving, validation
- **IMonitoringSessionManager**: Auto-monitoring session lifecycle
- **ITempFileManager**: Temporary file creation and cleanup
- **IVisionService**: High-level orchestration of all operations

## Contract Principles

### 1. Interface Segregation
Each interface has a single responsibility. Implementations can compose multiple interfaces.

**Example**: A `VisionService` implementation composes `IScreenshotCapture`, `IImageProcessor`, `IClaudeAPIClient`, etc.

### 2. Explicit Error Handling
All methods declare expected exceptions. Callers must handle these exceptions.

**Example**:
```python
try:
    screenshot = capture.capture_full_screen(monitor=0)
except MonitorNotFoundError:
    logger.error("Monitor 0 not found, falling back to primary")
    screenshot = capture.capture_full_screen(monitor=0)
except DisplayNotAvailableError:
    raise VisionCommandError("No display available. Are you in SSH session?")
```

### 3. Type Safety
All parameters and return types are explicitly typed using Python type hints.

### 4. Immutability
Data model entities (Screenshot, CaptureRegion, etc.) should be treated as immutable. Methods return new instances rather than mutating in place.

## Implementation Guidance

### Step 1: Implement Core Interfaces

Start with foundational interfaces in this order:

1. **ITempFileManager** - Simple, no external dependencies
2. **IConfigurationManager** - Depends on ITempFileManager for config path
3. **IScreenshotCapture** - Depends on ITempFileManager
4. **IImageProcessor** - Depends on Screenshot entities
5. **IRegionSelector** - Depends on IScreenshotCapture for monitor detection
6. **IClaudeAPIClient** - Depends on IConfigurationManager for OAuth config
7. **IMonitoringSessionManager** - Depends on IScreenshotCapture
8. **IVisionService** - Composes all interfaces

### Step 2: Write Contract Tests

For each interface, write tests that verify the contract is honored:

```python
# tests/contract/test_screenshot_capture.py
import pytest
from contracts.screenshot_service import IScreenshotCapture, ScreenshotCaptureError

def test_capture_full_screen_returns_screenshot(screenshot_capture: IScreenshotCapture):
    """Verify capture_full_screen returns valid Screenshot."""
    screenshot = screenshot_capture.capture_full_screen(monitor=0)

    assert screenshot.id is not None
    assert screenshot.timestamp is not None
    assert screenshot.file_path.exists()
    assert screenshot.resolution[0] > 0
    assert screenshot.resolution[1] > 0

def test_capture_full_screen_invalid_monitor_raises(screenshot_capture: IScreenshotCapture):
    """Verify capture_full_screen raises MonitorNotFoundError for invalid monitor."""
    with pytest.raises(MonitorNotFoundError):
        screenshot_capture.capture_full_screen(monitor=999)

def test_detect_monitors_returns_list(screenshot_capture: IScreenshotCapture):
    """Verify detect_monitors returns non-empty list."""
    monitors = screenshot_capture.detect_monitors()

    assert len(monitors) > 0
    assert monitors[0]['id'] == 0
    assert 'width' in monitors[0]
    assert 'height' in monitors[0]
```

### Step 3: Implement Services

Create concrete implementations:

```python
# src/services/screenshot_capture.py
from contracts.screenshot_service import IScreenshotCapture
from entities import Screenshot
import subprocess
from pathlib import Path

class X11ScreenshotCapture(IScreenshotCapture):
    """Screenshot capture implementation using scrot (X11)."""

    def capture_full_screen(self, monitor: int = 0) -> Screenshot:
        # Validate monitor exists
        monitors = self.detect_monitors()
        if monitor >= len(monitors):
            raise MonitorNotFoundError(f"Monitor {monitor} not found")

        # Create temp file
        temp_file = self.temp_file_manager.create_temp_file('png')

        # Execute scrot
        try:
            subprocess.run(
                ['scrot', '-m', str(temp_file)],
                check=True,
                timeout=5,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise ScreenshotCaptureError(f"scrot failed: {e.stderr.decode()}")
        except subprocess.TimeoutExpired:
            raise ScreenshotCaptureError("scrot timed out after 5 seconds")

        # Create Screenshot entity
        from PIL import Image
        image = Image.open(temp_file)

        return Screenshot(
            id=uuid.uuid4(),
            timestamp=datetime.now(),
            file_path=temp_file,
            format='png',
            original_size_bytes=temp_file.stat().st_size,
            optimized_size_bytes=temp_file.stat().st_size,
            resolution=(image.width, image.height),
            source_monitor=monitor,
            capture_method='scrot',
            privacy_zones_applied=False
        )

    def detect_monitors(self) -> List[dict]:
        # Use xrandr to detect monitors
        # Implementation details...
```

### Step 4: Dependency Injection

Use dependency injection to compose services:

```python
# src/main.py
from services.screenshot_capture import X11ScreenshotCapture
from services.image_processor import PillowImageProcessor
from services.claude_api_client import AnthropicAPIClient
from services.vision_service import VisionService

def create_vision_service(config: Configuration) -> IVisionService:
    """Factory function to create VisionService with dependencies."""

    temp_file_manager = TempFileManager(config.temp.directory)
    screenshot_capture = X11ScreenshotCapture(temp_file_manager)
    image_processor = PillowImageProcessor()
    claude_client = AnthropicAPIClient(config.claude_code.oauth_token_path)

    return VisionService(
        screenshot_capture=screenshot_capture,
        image_processor=image_processor,
        claude_client=claude_client,
        temp_file_manager=temp_file_manager,
        config=config
    )
```

## Testing Strategy

### Contract Tests
Verify implementations honor interface contracts.

**Location**: `tests/contract/`

**Purpose**: Ensure each implementation correctly implements interface methods with expected behavior and error handling.

### Integration Tests
Verify services work together correctly.

**Location**: `tests/integration/`

**Purpose**: Test complete workflows (e.g., `/vision` command end-to-end).

### Unit Tests
Test individual implementation logic.

**Location**: `tests/unit/`

**Purpose**: Test specific algorithms (image resize, hash calculation, config parsing).

## Exception Hierarchy

All exceptions inherit from `VisionError`:

```
VisionError (base)
├── ScreenshotCaptureError
│   ├── DisplayNotAvailableError
│   └── MonitorNotFoundError
├── ImageProcessingError
├── RegionSelectionCancelledError
├── SelectionToolNotFoundError
├── AuthenticationError
├── APIError
│   └── PayloadTooLargeError
├── OAuthConfigNotFoundError
├── ConfigurationError
├── SessionAlreadyActiveError
├── SessionNotFoundError
├── TempFileError
└── VisionCommandError (high-level)
```

### Error Handling Pattern

```python
try:
    response = vision_service.execute_vision_command("analyze this error")
    print(response)
except DisplayNotAvailableError:
    print("ERROR: No display available. Are you in SSH session?")
    print("  Try running from graphical terminal.")
except AuthenticationError:
    print("ERROR: Claude Code OAuth token expired.")
    print("  Run: claude login")
except ScreenshotCaptureError as e:
    print(f"ERROR: Screenshot capture failed: {e}")
    print("  Check screenshot tool is installed: sudo apt install scrot")
except VisionCommandError as e:
    print(f"ERROR: Command failed: {e}")
```

## Contract Validation Checklist

Before marking an implementation complete, verify:

- [ ] All interface methods implemented
- [ ] All declared exceptions handled/raised correctly
- [ ] All type hints match contract signatures
- [ ] Contract tests pass for this implementation
- [ ] Documentation strings updated with implementation details
- [ ] Error messages are actionable (tell user what to do)

## Future Extensions

### Adding New Commands

To add new vision commands (e.g., `/vision.history`):

1. Add method to `IVisionService` interface
2. Define expected exceptions
3. Write contract tests
4. Implement in concrete `VisionService` class
5. Update CLI command parser

### Supporting New Platforms

To add Windows/macOS support:

1. Create platform-specific `IScreenshotCapture` implementations
   - `WindowsScreenshotCapture` (using `win32gui`)
   - `MacOSScreenshotCapture` (using `screencapture`)
2. Create platform detection utility
3. Factory function selects implementation based on platform
4. All other interfaces remain unchanged (abstraction)

---

**Contract Version**: 1.0
**Last Updated**: 2025-10-08
