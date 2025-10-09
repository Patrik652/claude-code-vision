"""
Exception definitions for Claude Code Vision.

Provides a complete hierarchy of exceptions used throughout the application.
All exceptions inherit from VisionError base class with comprehensive error messages
and troubleshooting guidance.
"""


class VisionError(Exception):
    """
    Base exception for all vision-related errors.

    All custom exceptions include:
    - Descriptive error message
    - Troubleshooting steps
    - Suggested fixes
    """

    def __init__(self, message: str, troubleshooting: str = None):
        """
        Initialize VisionError.

        Args:
            message: Primary error message
            troubleshooting: Optional troubleshooting guidance
        """
        self.message = message
        self.troubleshooting = troubleshooting or self._default_troubleshooting()
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format complete error message with troubleshooting."""
        if self.troubleshooting:
            return f"{self.message}\n\nTroubleshooting:\n{self.troubleshooting}"
        return self.message

    def _default_troubleshooting(self) -> str:
        """Default troubleshooting steps."""
        return (
            "• Run diagnostics: claude-vision --doctor\n"
            "• Check configuration: claude-vision --validate-config\n"
            "• Review logs for more details"
        )


# Screenshot Capture Errors
class ScreenshotCaptureError(VisionError):
    """Screenshot capture failed."""

    def __init__(self, message: str, troubleshooting: str = None):
        if troubleshooting is None:
            troubleshooting = (
                "• Verify screenshot tool is installed:\n"
                "  - X11: sudo apt install scrot\n"
                "  - Wayland: sudo apt install grim\n"
                "  - Universal: sudo apt install imagemagick\n"
                "• Test capture: claude-vision --test-capture\n"
                "• Check display is available: echo $DISPLAY\n"
                "• Run diagnostics: claude-vision --doctor"
            )
        super().__init__(message, troubleshooting)


class DisplayNotAvailableError(VisionError):
    """No display available (headless environment)."""

    def __init__(self, message: str = "No display available", troubleshooting: str = None):
        if troubleshooting is None:
            troubleshooting = (
                "• Verify you're running in a graphical environment (not SSH without X forwarding)\n"
                "• Check DISPLAY environment variable: echo $DISPLAY\n"
                "• For X11: export DISPLAY=:0\n"
                "• For Wayland: Check WAYLAND_DISPLAY variable\n"
                "• If using SSH, enable X forwarding: ssh -X user@host\n"
                "• Claude Code Vision requires a graphical display to capture screenshots"
            )
        super().__init__(message, troubleshooting)


class MonitorNotFoundError(VisionError):
    """Specified monitor not found."""

    def __init__(self, monitor_id: int, available_count: int):
        message = f"Monitor {monitor_id} not found. Available monitors: {available_count}"
        troubleshooting = (
            f"• List available monitors: claude-vision --list-monitors\n"
            f"• Valid monitor indices: 0 to {available_count - 1}\n"
            f"• Use --monitor 0 for primary monitor (default)\n"
            f"• Check monitor connections with: xrandr (X11) or wlr-randr (Wayland)"
        )
        super().__init__(message, troubleshooting)


class InvalidRegionError(VisionError):
    """Capture region out of bounds or invalid."""

    def __init__(self, message: str, troubleshooting: str = None):
        if troubleshooting is None:
            troubleshooting = (
                "• Verify region coordinates are within screen bounds\n"
                "• Use graphical selection instead: /vision.area (without --coords)\n"
                "• Check screen resolution: xrandr (X11) or wlr-randr (Wayland)\n"
                "• Format for --coords: 'x,y,width,height' (e.g., '100,100,800,600')\n"
                "• All values must be positive integers"
            )
        super().__init__(message, troubleshooting)


# Image Processing Errors
class ImageProcessingError(VisionError):
    """Image processing operation failed."""

    def __init__(self, message: str, troubleshooting: str = None):
        if troubleshooting is None:
            troubleshooting = (
                "• Verify PIL/Pillow is installed: pip install Pillow\n"
                "• Check screenshot file is valid and readable\n"
                "• Ensure sufficient disk space in temp directory\n"
                "• Try reducing screenshot quality in config\n"
                "• Verify image format is supported (png, jpg, jpeg)"
            )
        super().__init__(message, troubleshooting)


# Region Selection Errors
class RegionSelectionCancelledError(VisionError):
    """User cancelled region selection."""

    def __init__(self):
        message = "Region selection cancelled by user"
        troubleshooting = (
            "• Region selection was cancelled\n"
            "• To retry: Run the command again\n"
            "• Alternative: Use --coords to specify region manually\n"
            "  Example: /vision.area --coords '100,100,800,600' \"Analyze this\""
        )
        super().__init__(message, troubleshooting)


class SelectionToolNotFoundError(VisionError):
    """Graphical selection tool not installed."""

    def __init__(self, message: str = "Graphical selection tool not found", troubleshooting: str = None):
        if troubleshooting is None:
            troubleshooting = (
                "• Install region selection tool:\n"
                "  - Wayland: sudo apt install slurp\n"
                "  - X11: sudo apt install slop  # or xrectsel\n"
                "• Alternative: Use --coords flag to specify region manually\n"
                "  Example: /vision.area --coords '100,100,800,600' \"Analyze this\"\n"
                "• Run diagnostics: claude-vision --doctor"
            )
        super().__init__(message, troubleshooting)


# Authentication & API Errors
class AuthenticationError(VisionError):
    """OAuth authentication failed."""

    def __init__(self, message: str, troubleshooting: str = None):
        if troubleshooting is None:
            troubleshooting = (
                "• Verify Claude Code OAuth token is valid\n"
                "• Check OAuth config file exists: ~/.config/claude/config.json\n"
                "• Try re-authenticating with Claude Code\n"
                "• Verify API credentials are not expired\n"
                "• Check network connectivity to Claude API"
            )
        super().__init__(message, troubleshooting)


class APIError(VisionError):
    """Claude API call failed."""

    def __init__(self, message: str, status_code: int = None, troubleshooting: str = None):
        self.status_code = status_code
        if troubleshooting is None:
            troubleshooting = (
                f"• HTTP status code: {status_code or 'Unknown'}\n"
                "• Check network connectivity: ping api.anthropic.com\n"
                "• Verify API credentials are valid\n"
                "• Check Claude API status: https://status.anthropic.com\n"
                "• Review API rate limits and quotas\n"
                "• Try again after a short delay"
            )
        super().__init__(message, troubleshooting)


class PayloadTooLargeError(VisionError):
    """Screenshot payload exceeds API limits."""

    def __init__(self, size_mb: float, limit_mb: float = 5.0):
        message = f"Screenshot too large: {size_mb:.2f} MB (limit: {limit_mb} MB)"
        troubleshooting = (
            f"• Reduce screenshot quality in config (current may be too high)\n"
            f"• Reduce max_size_mb in config to trigger more aggressive compression\n"
            f"• Use /vision.area to capture smaller region instead of full screen\n"
            f"• Lower screen resolution if possible\n"
            f"• Edit config: claude-vision --validate-config"
        )
        super().__init__(message, troubleshooting)


class OAuthConfigNotFoundError(VisionError):
    """Claude Code OAuth config not found."""

    def __init__(self, message: str = None, troubleshooting: str = None):
        if message is None:
            message = "Claude Code OAuth configuration not found"
        if troubleshooting is None:
            troubleshooting = (
                "• Verify Claude Code is installed and configured\n"
                "• Check config file exists: ~/.claude/.credentials.json\n"
                "• Authenticate with Claude Code first\n"
                "• Ensure you're running this from within Claude Code environment\n"
                "• This feature requires Claude Code integration"
            )
        super().__init__(message, troubleshooting)


# Configuration Errors
class ConfigurationError(VisionError):
    """Configuration invalid or load/save failed."""

    def __init__(self, message: str, troubleshooting: str = None):
        if troubleshooting is None:
            troubleshooting = (
                "• Validate config: claude-vision --validate-config\n"
                "• Reset to defaults: claude-vision --init --force\n"
                "• Check config file syntax (YAML format)\n"
                "• Config location: ~/.config/claude-code-vision/config.yaml\n"
                "• Review error details above for specific issues"
            )
        super().__init__(message, troubleshooting)


# Monitoring Session Errors
class SessionAlreadyActiveError(VisionError):
    """Monitoring session already active."""

    def __init__(self, session_id: str = None):
        message = f"Monitoring session already active{f': {session_id}' if session_id else ''}"
        troubleshooting = (
            "• Stop current session: /vision.stop\n"
            "• Only one monitoring session can be active at a time\n"
            "• Check active session status\n"
            "• If stuck, restart Claude Code"
        )
        super().__init__(message, troubleshooting)


class SessionNotFoundError(VisionError):
    """Monitoring session not found."""

    def __init__(self, session_id: str = None):
        message = f"Monitoring session not found{f': {session_id}' if session_id else ''}"
        troubleshooting = (
            "• No active monitoring session to stop\n"
            "• Start a new session: /vision.auto\n"
            "• Sessions automatically stop after max duration (default: 30 min)\n"
            "• Check if session already completed or timed out"
        )
        super().__init__(message, troubleshooting)


# File Management Errors
class TempFileError(VisionError):
    """Temporary file operation failed."""

    def __init__(self, message: str, troubleshooting: str = None):
        if troubleshooting is None:
            troubleshooting = (
                "• Check disk space: df -h\n"
                "• Verify temp directory is writable\n"
                "• Temp directory location in config: ~/.config/claude-code-vision/config.yaml\n"
                "• Check permissions: ls -la ~/.cache/claude-code-vision/\n"
                "• Clean up temp files manually if needed"
            )
        super().__init__(message, troubleshooting)


# Command Execution Errors
class VisionCommandError(VisionError):
    """High-level command execution failed."""

    def __init__(self, message: str, troubleshooting: str = None):
        if troubleshooting is None:
            troubleshooting = (
                "• Run diagnostics: claude-vision --doctor\n"
                "• Test screenshot capture: claude-vision --test-capture\n"
                "• Validate configuration: claude-vision --validate-config\n"
                "• Check logs for detailed error information\n"
                "• Review the error message above for specific guidance"
            )
        super().__init__(message, troubleshooting)
