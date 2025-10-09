# Data Model: Claude Code Vision

**Feature**: Claude Code Vision - Visual Feedback System
**Date**: 2025-10-08
**Status**: Complete

## Overview

This document defines the key entities and their relationships for the Claude Code Vision system. The data model is minimal by design - this is a stateless CLI tool with ephemeral data structures and simple configuration persistence.

---

## Entity: Screenshot

### Description
Represents a captured screen image with associated metadata. Screenshots are ephemeral - captured, processed, transmitted, and immediately deleted.

### Attributes

| Attribute | Type | Required | Validation | Description |
|-----------|------|----------|------------|-------------|
| `id` | string (UUID) | Yes | UUID v4 format | Unique identifier for this screenshot instance |
| `timestamp` | datetime | Yes | ISO 8601 format | When screenshot was captured |
| `file_path` | Path | Yes | Valid temp file path | Location of screenshot file on disk |
| `format` | string | Yes | jpeg \| png \| webp | Image file format |
| `original_size_bytes` | int | Yes | > 0 | Size before optimization |
| `optimized_size_bytes` | int | Yes | > 0, ≤ 2MB | Size after optimization |
| `resolution` | tuple(int, int) | Yes | (width > 0, height > 0) | Image dimensions (width, height) |
| `source_monitor` | int | Yes | ≥ 0 | Monitor index (0 = primary) |
| `capture_method` | string | Yes | scrot \| grim \| import | Tool used for capture |
| `privacy_zones_applied` | bool | Yes | - | Whether privacy redaction was applied |
| `capture_region` | CaptureRegion \| None | No | - | If area selection used, the selected region |

### Relationships
- **Has one** CaptureRegion (optional, if area selection used)
- **Belongs to** MonitoringSession (optional, if part of auto-monitoring)

### Lifecycle
1. **Created**: When screenshot capture initiated
2. **Processed**: Privacy zones applied, optimized
3. **Transmitted**: Sent to Claude API
4. **Destroyed**: File deleted, object dereferenced

### Example (Python dataclass)
```python
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

@dataclass
class Screenshot:
    id: UUID
    timestamp: datetime
    file_path: Path
    format: str  # 'jpeg' | 'png' | 'webp'
    original_size_bytes: int
    optimized_size_bytes: int
    resolution: tuple[int, int]
    source_monitor: int
    capture_method: str  # 'scrot' | 'grim' | 'import'
    privacy_zones_applied: bool
    capture_region: Optional['CaptureRegion'] = None
```

---

## Entity: CaptureRegion

### Description
Defines a rectangular region of the screen for selective capture (used by `/vision.area` command). Can be specified via graphical selection or coordinates.

### Attributes

| Attribute | Type | Required | Validation | Description |
|-----------|------|----------|------------|-------------|
| `x` | int | Yes | ≥ 0 | Top-left X coordinate (pixels from left) |
| `y` | int | Yes | ≥ 0 | Top-left Y coordinate (pixels from top) |
| `width` | int | Yes | > 0 | Region width in pixels |
| `height` | int | Yes | > 0 | Region height in pixels |
| `monitor` | int | Yes | ≥ 0 | Which monitor (0 = primary) |
| `selection_method` | string | Yes | graphical \| coordinates | How region was specified |

### Validation Rules
- `x + width` must not exceed monitor width
- `y + height` must not exceed monitor height
- All values must be non-negative integers

### Example (Python dataclass)
```python
@dataclass
class CaptureRegion:
    x: int
    y: int
    width: int
    height: int
    monitor: int
    selection_method: str  # 'graphical' | 'coordinates'

    def validate(self, monitor_width: int, monitor_height: int) -> None:
        """Validate region is within monitor bounds."""
        if self.x < 0 or self.y < 0:
            raise ValueError("Coordinates must be non-negative")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Dimensions must be positive")
        if self.x + self.width > monitor_width:
            raise ValueError(f"Region exceeds monitor width ({monitor_width})")
        if self.y + self.height > monitor_height:
            raise ValueError(f"Region exceeds monitor height ({monitor_height})")
```

---

## Entity: Configuration

### Description
User preferences for screenshot capture, privacy settings, and system behavior. Persisted in `~/.config/claude-code-vision/config.yaml`.

### Attributes (High-Level Groups)

#### Screenshot Settings
| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `screenshot.tool` | string | "auto" | Screenshot tool (auto \| scrot \| grim \| import) |
| `screenshot.format` | string | "jpeg" | Output format (jpeg \| png \| webp) |
| `screenshot.quality` | int | 85 | JPEG/WebP quality (0-100) |
| `screenshot.max_size_mb` | float | 2.0 | Max payload size in MB |

#### Monitor Settings
| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `monitors.default` | int | 0 | Default monitor to capture (0 = primary) |

#### Area Selection Settings
| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `area_selection.tool` | string | "auto" | Selection tool (auto \| slurp \| xrectsel \| coordinates) |
| `area_selection.show_coordinates` | bool | true | Display selected region coordinates |

#### Privacy Settings
| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `privacy.enabled` | bool | true | Enable privacy zone redaction |
| `privacy.prompt_first_use` | bool | true | Ask for confirmation on first /vision |
| `privacy.zones` | list[PrivacyZone] | [] | List of privacy exclusion zones |

#### Monitoring Settings
| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `monitoring.interval_seconds` | int | 30 | Capture interval for /vision.auto |
| `monitoring.max_duration_minutes` | int | 30 | Auto-stop after duration |
| `monitoring.idle_pause_minutes` | int | 5 | Pause if no user interaction |
| `monitoring.change_detection` | bool | true | Track screen changes |

#### Claude Code Integration
| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `claude_code.oauth_token_path` | string | "~/.claude/config.json" | OAuth token location |
| `claude_code.api_endpoint` | string | "https://api.anthropic.com/v1/messages" | Claude API endpoint |

#### Temporary Files
| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `temp.directory` | string | "/tmp/claude-vision" | Temp file location |
| `temp.cleanup` | bool | true | Delete after transmission |
| `temp.keep_on_error` | bool | false | Keep temp files on error |

#### Logging
| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `logging.level` | string | "INFO" | Log level (DEBUG \| INFO \| WARNING \| ERROR) |
| `logging.file` | string | "~/.config/claude-code-vision/vision.log" | Log file path |
| `logging.max_size_mb` | int | 10 | Max log file size before rotation |
| `logging.backup_count` | int | 3 | Number of rotated logs to keep |

### Example (Python dataclass)
```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class ScreenshotConfig:
    tool: str = "auto"
    format: str = "jpeg"
    quality: int = 85
    max_size_mb: float = 2.0

@dataclass
class MonitorConfig:
    default: int = 0

@dataclass
class AreaSelectionConfig:
    tool: str = "auto"
    show_coordinates: bool = True

@dataclass
class PrivacyConfig:
    enabled: bool = True
    prompt_first_use: bool = True
    zones: List['PrivacyZone'] = field(default_factory=list)

@dataclass
class MonitoringConfig:
    interval_seconds: int = 30
    max_duration_minutes: int = 30
    idle_pause_minutes: int = 5
    change_detection: bool = True

@dataclass
class ClaudeCodeConfig:
    oauth_token_path: str = "~/.claude/config.json"
    api_endpoint: str = "https://api.anthropic.com/v1/messages"

@dataclass
class TempConfig:
    directory: str = "/tmp/claude-vision"
    cleanup: bool = True
    keep_on_error: bool = False

@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: str = "~/.config/claude-code-vision/vision.log"
    max_size_mb: int = 10
    backup_count: int = 3

@dataclass
class Configuration:
    version: str = "1.0"
    screenshot: ScreenshotConfig = field(default_factory=ScreenshotConfig)
    monitors: MonitorConfig = field(default_factory=MonitorConfig)
    area_selection: AreaSelectionConfig = field(default_factory=AreaSelectionConfig)
    privacy: PrivacyConfig = field(default_factory=PrivacyConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    claude_code: ClaudeCodeConfig = field(default_factory=ClaudeCodeConfig)
    temp: TempConfig = field(default_factory=TempConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
```

---

## Entity: PrivacyZone

### Description
A rectangular region to redact from screenshots before transmission. Configured by user to protect sensitive information.

### Attributes

| Attribute | Type | Required | Validation | Description |
|-----------|------|----------|------------|-------------|
| `name` | string | Yes | Non-empty | Descriptive name (e.g., "password_manager") |
| `x` | int | Yes | ≥ 0 | Top-left X coordinate |
| `y` | int | Yes | ≥ 0 | Top-left Y coordinate |
| `width` | int | Yes | > 0 | Zone width in pixels |
| `height` | int | Yes | > 0 | Zone height in pixels |
| `monitor` | int | No | ≥ 0 | Specific monitor (default: all monitors) |

### Validation Rules
- Same as CaptureRegion (must be within screen bounds)
- Zones can overlap (both applied)
- Empty zones list is valid (no privacy redaction)

### Example (Python dataclass)
```python
@dataclass
class PrivacyZone:
    name: str
    x: int
    y: int
    width: int
    height: int
    monitor: Optional[int] = None  # None = apply to all monitors
```

---

## Entity: MonitoringSession

### Description
Represents an active auto-monitoring session created by `/vision.auto` command. Tracks state and history.

### Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string (UUID) | Yes | Unique session identifier |
| `started_at` | datetime | Yes | When monitoring started |
| `last_capture_at` | datetime | No | When last screenshot was taken |
| `capture_count` | int | Yes | Number of screenshots captured |
| `interval_seconds` | int | Yes | Capture interval (from config) |
| `is_active` | bool | Yes | Whether session is currently running |
| `paused_at` | datetime | No | When paused due to idle |
| `last_change_detected_at` | datetime | No | When screen change last detected |
| `previous_screenshot_hash` | string | No | Hash of previous screenshot for change detection |

### State Transitions
1. **Created** (is_active=True): `/vision.auto` executed
2. **Capturing** (is_active=True): Taking periodic screenshots
3. **Paused** (is_active=False, paused_at set): No user interaction for idle_pause_minutes
4. **Resumed** (is_active=True, paused_at=None): User interaction detected
5. **Stopped** (destroyed): `/vision.stop` executed or max_duration reached

### Relationships
- **Has many** Screenshots (captured during session)

### Example (Python dataclass)
```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from uuid import UUID

@dataclass
class MonitoringSession:
    id: UUID
    started_at: datetime
    interval_seconds: int
    is_active: bool = True
    capture_count: int = 0
    last_capture_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    last_change_detected_at: Optional[datetime] = None
    previous_screenshot_hash: Optional[str] = None
    screenshots: List[Screenshot] = field(default_factory=list)
```

---

## Entity: VisionCommand

### Description
Represents a user-triggered vision command (/vision, /vision.area, /vision.auto, /vision.stop). Primarily used for logging and error tracking.

### Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `command_type` | string | Yes | vision \| vision.area \| vision.auto \| vision.stop |
| `executed_at` | datetime | Yes | When command was executed |
| `user_prompt` | string | No | User's text prompt (e.g., "analyze this error") |
| `capture_region` | CaptureRegion | No | For vision.area commands |
| `status` | string | Yes | success \| failed \| in_progress |
| `error_message` | string | No | Error details if status=failed |
| `screenshot_id` | UUID | No | Associated screenshot (if captured) |
| `session_id` | UUID | No | Associated monitoring session (if vision.auto) |

### Example (Python dataclass)
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

@dataclass
class VisionCommand:
    command_type: str  # 'vision' | 'vision.area' | 'vision.auto' | 'vision.stop'
    executed_at: datetime
    status: str  # 'success' | 'failed' | 'in_progress'
    user_prompt: Optional[str] = None
    capture_region: Optional[CaptureRegion] = None
    error_message: Optional[str] = None
    screenshot_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
```

---

## Relationships Diagram

```
┌─────────────────────┐
│  VisionCommand      │
│  - command_type     │
│  - executed_at      │
│  - user_prompt      │
└──────┬──────────────┘
       │
       │ references (optional)
       │
       ├──────────────────────┐
       │                      │
       ▼                      ▼
┌─────────────────┐   ┌──────────────────────┐
│  Screenshot     │   │  MonitoringSession   │
│  - id           │   │  - id                │
│  - timestamp    │◄──┤  - started_at        │
│  - file_path    │   │  - is_active         │
│  - resolution   │   │  - screenshots[]     │
└─────┬───────────┘   └──────────────────────┘
      │
      │ has one (optional)
      │
      ▼
┌─────────────────┐
│  CaptureRegion  │
│  - x, y         │
│  - width,height │
└─────────────────┘

┌─────────────────┐
│  Configuration  │────┐
│  - screenshot   │    │
│  - privacy      │    │
│  - monitoring   │    │
└─────────────────┘    │
                       │ contains many
                       │
                       ▼
                ┌─────────────────┐
                │  PrivacyZone    │
                │  - name         │
                │  - x, y         │
                │  - width,height │
                └─────────────────┘
```

---

## Validation Rules Summary

### Cross-Entity Rules

1. **Screenshot Lifecycle**:
   - MUST be deleted from filesystem after transmission (temp.cleanup=true)
   - MUST NOT persist beyond single command execution
   - Exception: keep if temp.keep_on_error=true AND error occurred

2. **Privacy Zones**:
   - MUST be applied before optimization (to redact original resolution)
   - MUST validate against monitor bounds before application
   - Empty zones list is valid (no redaction)

3. **Monitoring Session**:
   - Only ONE active session allowed at a time (per design decision)
   - MUST auto-stop after max_duration_minutes
   - MUST pause after idle_pause_minutes with no user interaction

4. **Configuration**:
   - MUST validate on load (reject invalid YAML)
   - MUST merge with defaults (partial configs allowed)
   - MUST migrate if version mismatch

5. **Capture Region**:
   - MUST validate against actual monitor dimensions
   - MUST handle multi-monitor offsets (monitor 1 may start at x=1920)

---

## Persistence Strategy

### Persistent (on disk)
- **Configuration**: `~/.config/claude-code-vision/config.yaml`
- **Logs**: `~/.config/claude-code-vision/vision.log` (rotated)

### Ephemeral (in-memory only)
- **Screenshots**: Temporary files, deleted after transmission
- **MonitoringSession**: In-memory during /vision.auto, discarded on stop
- **VisionCommand**: Logged but not persisted structurally

### No Persistence
- No database required
- No screenshot history/gallery
- No user accounts or profiles

---

## Implementation Notes

### Language-Specific Considerations (Python)

1. **Use dataclasses** for entities (shown in examples)
2. **Use Pydantic** alternative for runtime validation:
   ```python
   from pydantic import BaseModel, Field, validator

   class PrivacyZone(BaseModel):
       name: str = Field(min_length=1)
       x: int = Field(ge=0)
       y: int = Field(ge=0)
       width: int = Field(gt=0)
       height: int = Field(gt=0)
       monitor: Optional[int] = Field(default=None, ge=0)

       @validator('x', 'y', 'width', 'height')
       def validate_bounds(cls, v):
           if v < 0 or v > 10000:  # Reasonable screen size limit
               raise ValueError('Screen coordinate out of bounds')
           return v
   ```

3. **Configuration loading**:
   ```python
   import yaml
   from pathlib import Path

   def load_config() -> Configuration:
       config_path = Path.home() / '.config/claude-code-vision/config.yaml'
       if config_path.exists():
           with open(config_path) as f:
               data = yaml.safe_load(f)
               return Configuration(**data)
       return Configuration()  # Use defaults
   ```

4. **Temporary file handling**:
   ```python
   import tempfile
   from pathlib import Path

   def create_temp_screenshot() -> Path:
       temp_dir = Path(config.temp.directory)
       temp_dir.mkdir(parents=True, exist_ok=True)
       return temp_dir / f"screenshot-{uuid.uuid4()}.{config.screenshot.format}"
   ```

---

**Data Model Complete**: Entities defined with attributes, relationships, validation rules, and implementation examples. Ready for contract generation.
