"""
Screenshot Service Interfaces

Defines the interface contracts for screenshot capture, processing, and transmission.
These interfaces ensure consistent behavior across all implementations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from uuid import UUID

# Import entities from our models
from src.models.entities import Screenshot, CaptureRegion, PrivacyZone, Configuration, MonitoringSession


class IScreenshotCapture(ABC):
    """Interface for capturing screenshots from the display."""

    @abstractmethod
    def capture_full_screen(self, monitor: int = 0) -> Screenshot:
        """
        Capture full screen from specified monitor.

        Args:
            monitor: Monitor index (0 = primary)

        Returns:
            Screenshot object with captured image

        Raises:
            ScreenshotCaptureError: If capture fails
            DisplayNotAvailableError: If running headless
            MonitorNotFoundError: If monitor index invalid
        """
        pass

    @abstractmethod
    def capture_region(self, region: CaptureRegion) -> Screenshot:
        """
        Capture specific region of the screen.

        Args:
            region: CaptureRegion defining area to capture

        Returns:
            Screenshot object with captured region

        Raises:
            ScreenshotCaptureError: If capture fails
            InvalidRegionError: If region out of bounds
        """
        pass

    @abstractmethod
    def detect_monitors(self) -> List[dict]:
        """
        Detect available monitors and their properties.

        Returns:
            List of monitor info dicts:
            [
                {"id": 0, "name": "eDP-1", "width": 1920, "height": 1080, "is_primary": True},
                {"id": 1, "name": "HDMI-1", "width": 2560, "height": 1440, "is_primary": False}
            ]

        Raises:
            DisplayNotAvailableError: If no display available
        """
        pass


class IImageProcessor(ABC):
    """Interface for image processing operations."""

    @abstractmethod
    def apply_privacy_zones(self, screenshot: Screenshot, zones: List[PrivacyZone]) -> Screenshot:
        """
        Apply privacy zone redaction to screenshot.

        Args:
            screenshot: Screenshot to process
            zones: List of privacy zones to redact

        Returns:
            Screenshot with privacy zones blacked out

        Raises:
            ImageProcessingError: If processing fails
        """
        pass

    @abstractmethod
    def optimize_image(self, screenshot: Screenshot, max_size_mb: float = 2.0) -> Screenshot:
        """
        Optimize screenshot to meet size constraints.

        Args:
            screenshot: Screenshot to optimize
            max_size_mb: Maximum size in megabytes

        Returns:
            Optimized screenshot (may be resized/recompressed)

        Raises:
            ImageProcessingError: If optimization fails
        """
        pass

    @abstractmethod
    def calculate_image_hash(self, screenshot: Screenshot) -> str:
        """
        Calculate hash of screenshot for change detection.

        Args:
            screenshot: Screenshot to hash

        Returns:
            SHA256 hash of image data

        Raises:
            ImageProcessingError: If hashing fails
        """
        pass


class IRegionSelector(ABC):
    """Interface for interactive region selection."""

    @abstractmethod
    def select_region_graphical(self, monitor: int = 0) -> CaptureRegion:
        """
        Launch graphical region selection tool.

        Args:
            monitor: Monitor to select from (0 = primary)

        Returns:
            CaptureRegion defined by user selection

        Raises:
            RegionSelectionCancelledError: If user cancels
            SelectionToolNotFoundError: If graphical tool unavailable
        """
        pass

    @abstractmethod
    def select_region_coordinates(self, x: int, y: int, width: int, height: int, monitor: int = 0) -> CaptureRegion:
        """
        Create region from explicit coordinates.

        Args:
            x: Top-left X coordinate
            y: Top-left Y coordinate
            width: Region width
            height: Region height
            monitor: Monitor index

        Returns:
            Validated CaptureRegion

        Raises:
            InvalidRegionError: If coordinates out of bounds
        """
        pass


class IClaudeAPIClient(ABC):
    """Interface for Claude API communication."""

    @abstractmethod
    def send_multimodal_prompt(self, text: str, screenshot: Screenshot) -> str:
        """
        Send text + image prompt to Claude API.

        Args:
            text: User's text prompt
            screenshot: Screenshot to include

        Returns:
            Claude's response text

        Raises:
            AuthenticationError: If OAuth token invalid/expired
            APIError: If API call fails
            PayloadTooLargeError: If screenshot exceeds API limits
        """
        pass

    @abstractmethod
    def validate_oauth_token(self) -> bool:
        """
        Check if OAuth token is valid.

        Returns:
            True if token valid, False otherwise

        Raises:
            OAuthConfigNotFoundError: If config file missing
        """
        pass

    @abstractmethod
    def refresh_oauth_token(self) -> None:
        """
        Refresh expired OAuth token.

        Raises:
            AuthenticationError: If refresh fails
        """
        pass


class IConfigurationManager(ABC):
    """Interface for configuration management."""

    @abstractmethod
    def load_config(self) -> Configuration:
        """
        Load configuration from file or create defaults.

        Returns:
            Configuration object

        Raises:
            ConfigurationError: If config invalid
        """
        pass

    @abstractmethod
    def save_config(self, config: Configuration) -> None:
        """
        Save configuration to file.

        Args:
            config: Configuration to persist

        Raises:
            ConfigurationError: If save fails
        """
        pass

    @abstractmethod
    def validate_config(self, config: Configuration) -> bool:
        """
        Validate configuration against schema.

        Args:
            config: Configuration to validate

        Returns:
            True if valid

        Raises:
            ConfigurationError: If validation fails with specific errors
        """
        pass


class IMonitoringSessionManager(ABC):
    """Interface for auto-monitoring session management."""

    @abstractmethod
    def start_session(self, interval_seconds: int) -> MonitoringSession:
        """
        Start new monitoring session.

        Args:
            interval_seconds: Capture interval

        Returns:
            Active MonitoringSession

        Raises:
            SessionAlreadyActiveError: If session already running
        """
        pass

    @abstractmethod
    def stop_session(self, session_id: UUID) -> None:
        """
        Stop active monitoring session.

        Args:
            session_id: Session to stop

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        pass

    @abstractmethod
    def pause_session(self, session_id: UUID) -> None:
        """
        Pause monitoring session (idle detected).

        Args:
            session_id: Session to pause

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        pass

    @abstractmethod
    def resume_session(self, session_id: UUID) -> None:
        """
        Resume paused monitoring session.

        Args:
            session_id: Session to resume

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        pass

    @abstractmethod
    def get_active_session(self) -> Optional[MonitoringSession]:
        """
        Get currently active monitoring session.

        Returns:
            Active MonitoringSession or None
        """
        pass


class ITempFileManager(ABC):
    """Interface for temporary file management."""

    @abstractmethod
    def create_temp_file(self, extension: str) -> Path:
        """
        Create temporary file for screenshot.

        Args:
            extension: File extension (e.g., 'jpg', 'png')

        Returns:
            Path to temp file

        Raises:
            TempFileError: If creation fails
        """
        pass

    @abstractmethod
    def cleanup_temp_file(self, path: Path) -> None:
        """
        Delete temporary file.

        Args:
            path: Path to temp file

        Raises:
            TempFileError: If deletion fails (non-fatal)
        """
        pass

    @abstractmethod
    def cleanup_all_temp_files(self) -> None:
        """
        Delete all temporary files in temp directory.

        Raises:
            TempFileError: If cleanup fails (non-fatal)
        """
        pass


class IVisionService(ABC):
    """
    High-level service orchestrating all vision operations.
    Composes all other interfaces to implement user-facing commands.
    """

    @abstractmethod
    def execute_vision_command(self, prompt: str) -> str:
        """
        Execute /vision command: capture full screen + send to Claude.

        Args:
            prompt: User's text prompt

        Returns:
            Claude's response

        Workflow:
            1. Capture full screen
            2. Apply privacy zones (if configured)
            3. Optimize image
            4. Send to Claude API
            5. Cleanup temp files
            6. Return response

        Raises:
            VisionCommandError: If any step fails
        """
        pass

    @abstractmethod
    def execute_vision_area_command(self, prompt: str, region: Optional[CaptureRegion] = None) -> str:
        """
        Execute /vision.area command: capture region + send to Claude.

        Args:
            prompt: User's text prompt
            region: Pre-defined region, or None to trigger selection

        Returns:
            Claude's response

        Workflow:
            1. Select region (graphical or coordinates)
            2. Capture selected region
            3. Apply privacy zones (if configured)
            4. Optimize image
            5. Send to Claude API
            6. Cleanup temp files
            7. Return response

        Raises:
            VisionCommandError: If any step fails
        """
        pass

    @abstractmethod
    def execute_vision_auto_command(self, interval_seconds: Optional[int] = None) -> UUID:
        """
        Execute /vision.auto command: start monitoring session.

        Args:
            interval_seconds: Override default interval, or None to use config

        Returns:
            Session ID of started monitoring session

        Workflow:
            1. Validate no active session
            2. Create monitoring session
            3. Start background capture loop
            4. Return session ID

        Raises:
            VisionCommandError: If session already active or start fails
        """
        pass

    @abstractmethod
    def execute_vision_stop_command(self) -> None:
        """
        Execute /vision.stop command: stop monitoring session.

        Workflow:
            1. Get active session
            2. Stop session
            3. Cleanup session resources

        Raises:
            VisionCommandError: If no active session
        """
        pass
