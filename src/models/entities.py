"""
Data model entities for Claude Code Vision.

This module defines all core data structures used throughout the application.
All entities are implemented as dataclasses for simplicity and immutability.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import UUID


@dataclass
class CaptureRegion:
    """
    Defines a rectangular region of the screen for selective capture.

    Used by /vision.area command. Can be specified via graphical selection
    or explicit coordinates.
    """
    x: int
    y: int
    width: int
    height: int
    monitor: int
    selection_method: str  # 'graphical' | 'coordinates'

    def validate(self, monitor_width: int, monitor_height: int) -> None:
        """
        Validate region is within monitor bounds.

        Args:
            monitor_width: Width of the monitor in pixels
            monitor_height: Height of the monitor in pixels

        Raises:
            ValueError: If coordinates are invalid or out of bounds
        """
        if self.x < 0 or self.y < 0:
            raise ValueError("Coordinates must be non-negative")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Dimensions must be positive")
        if self.x + self.width > monitor_width:
            raise ValueError(f"Region exceeds monitor width ({monitor_width})")
        if self.y + self.height > monitor_height:
            raise ValueError(f"Region exceeds monitor height ({monitor_height})")


@dataclass
class Screenshot:
    """
    Represents a captured screen image with metadata.

    Screenshots are ephemeral - captured, processed, transmitted, and immediately deleted.
    Lifecycle: Created → Processed (privacy + optimization) → Transmitted → Destroyed
    """
    id: UUID
    timestamp: datetime
    file_path: Path
    format: str  # 'jpeg' | 'png' | 'webp'
    original_size_bytes: int
    optimized_size_bytes: int
    resolution: Tuple[int, int]  # (width, height)
    source_monitor: int
    capture_method: str  # 'scrot' | 'grim' | 'import'
    privacy_zones_applied: bool
    capture_region: Optional[CaptureRegion] = None


@dataclass
class PrivacyZone:
    """
    A rectangular region to redact from screenshots before transmission.

    Configured by user to protect sensitive information (passwords, personal data, etc.)
    """
    name: str
    x: int
    y: int
    width: int
    height: int
    monitor: Optional[int] = None  # None = apply to all monitors

    def validate(self, monitor_width: Optional[int] = None, monitor_height: Optional[int] = None) -> None:
        """
        Validate privacy zone coordinates and dimensions.

        Args:
            monitor_width: Width of the monitor in pixels (optional)
            monitor_height: Height of the monitor in pixels (optional)

        Raises:
            ValueError: If coordinates are invalid or out of bounds
        """
        if self.x < 0 or self.y < 0:
            raise ValueError("Privacy zone coordinates must be non-negative")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Privacy zone dimensions must be positive")

        # Validate against monitor bounds if provided
        if monitor_width is not None and self.x + self.width > monitor_width:
            raise ValueError(f"Privacy zone exceeds monitor width ({monitor_width})")
        if monitor_height is not None and self.y + self.height > monitor_height:
            raise ValueError(f"Privacy zone exceeds monitor height ({monitor_height})")

        # Validate monitor index
        if self.monitor is not None and self.monitor < 0:
            raise ValueError("Monitor index must be non-negative")

        # Validate name is not empty
        if not self.name or not self.name.strip():
            raise ValueError("Privacy zone name cannot be empty")


@dataclass
class ScreenshotConfig:
    """Screenshot capture settings."""
    tool: str = "auto"
    format: str = "jpeg"
    quality: int = 85
    max_size_mb: float = 2.0


@dataclass
class MonitorConfig:
    """Multi-monitor settings."""
    default: int = 0


@dataclass
class AreaSelectionConfig:
    """Area selection tool settings."""
    tool: str = "auto"
    show_coordinates: bool = True


@dataclass
class PrivacyConfig:
    """Privacy and security settings."""
    enabled: bool = True
    prompt_first_use: bool = True
    zones: List[PrivacyZone] = field(default_factory=list)


@dataclass
class MonitoringConfig:
    """Auto-monitoring mode settings."""
    interval_seconds: int = 30
    max_duration_minutes: int = 30
    idle_pause_minutes: int = 5
    change_detection: bool = True


@dataclass
class AIProviderConfig:
    """AI provider selection settings."""
    provider: str = "gemini"  # 'claude' or 'gemini'
    fallback_to_gemini: bool = True


@dataclass
class ClaudeCodeConfig:
    """Claude Code integration settings."""
    oauth_token_path: str = "~/.claude/config.json"
    api_endpoint: str = "https://api.anthropic.com/v1/messages"


@dataclass
class GeminiConfig:
    """Google Gemini API settings."""
    api_key: str = ""
    model: str = "gemini-2.0-flash-exp"


@dataclass
class TempConfig:
    """Temporary file management settings."""
    directory: str = "/tmp/claude-vision"
    cleanup: bool = True
    keep_on_error: bool = False


@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    level: str = "INFO"
    file: str = "~/.config/claude-code-vision/vision.log"
    max_size_mb: int = 10
    backup_count: int = 3


@dataclass
class Configuration:
    """
    Complete user configuration for Claude Code Vision.

    Persisted in ~/.config/claude-code-vision/config.yaml
    """
    version: str = "1.0"
    screenshot: ScreenshotConfig = field(default_factory=ScreenshotConfig)
    monitors: MonitorConfig = field(default_factory=MonitorConfig)
    area_selection: AreaSelectionConfig = field(default_factory=AreaSelectionConfig)
    privacy: PrivacyConfig = field(default_factory=PrivacyConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    ai_provider: AIProviderConfig = field(default_factory=AIProviderConfig)
    claude_code: ClaudeCodeConfig = field(default_factory=ClaudeCodeConfig)
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    temp: TempConfig = field(default_factory=TempConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


@dataclass
class MonitoringSession:
    """
    Represents an active auto-monitoring session.

    Created by /vision.auto command. Tracks state and captures history.
    State transitions: Created → Capturing → Paused → Resumed → Stopped
    """
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


@dataclass
class VisionCommand:
    """
    Represents a user-triggered vision command.

    Used for logging and error tracking. Primarily for operational visibility.
    """
    command_type: str  # 'vision' | 'vision.area' | 'vision.auto' | 'vision.stop'
    executed_at: datetime
    status: str  # 'success' | 'failed' | 'in_progress'
    user_prompt: Optional[str] = None
    capture_region: Optional[CaptureRegion] = None
    error_message: Optional[str] = None
    screenshot_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
