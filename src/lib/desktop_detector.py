"""
Desktop Environment Detection Utility.

Detects the display server type (X11 vs Wayland) on Linux systems.
Used to determine which screenshot capture implementation to use.
"""

import os
import subprocess
from enum import Enum
from typing import Optional

from src.lib.logging_config import get_logger

logger = get_logger(__name__)


class DesktopType(Enum):
    """Enumeration of supported desktop environment types."""
    X11 = "x11"
    WAYLAND = "wayland"
    UNKNOWN = "unknown"


class DesktopDetector:
    """
    Detects the desktop environment type (X11 or Wayland).

    Uses multiple detection methods to reliably identify the display server:
    1. XDG_SESSION_TYPE environment variable
    2. WAYLAND_DISPLAY environment variable
    3. DISPLAY environment variable
    4. loginctl session information
    """

    @staticmethod
    def detect() -> DesktopType:
        """
        Detect the current desktop environment type.

        Returns:
            DesktopType enum value (X11, WAYLAND, or UNKNOWN)
        """
        # Method 1: Check XDG_SESSION_TYPE (most reliable)
        session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
        if session_type:
            logger.debug(f"XDG_SESSION_TYPE detected: {session_type}")
            if 'wayland' in session_type:
                return DesktopType.WAYLAND
            elif 'x11' in session_type:
                return DesktopType.X11

        # Method 2: Check WAYLAND_DISPLAY
        wayland_display = os.environ.get('WAYLAND_DISPLAY')
        if wayland_display:
            logger.debug(f"WAYLAND_DISPLAY detected: {wayland_display}")
            return DesktopType.WAYLAND

        # Method 3: Check DISPLAY (X11)
        x_display = os.environ.get('DISPLAY')
        if x_display and not wayland_display:
            logger.debug(f"DISPLAY detected (no WAYLAND_DISPLAY): {x_display}")
            return DesktopType.X11

        # Method 4: Try loginctl (systemd-based systems)
        desktop_type = DesktopDetector._detect_via_loginctl()
        if desktop_type != DesktopType.UNKNOWN:
            return desktop_type

        # All methods failed
        logger.warning("Could not detect desktop environment type")
        return DesktopType.UNKNOWN

    @staticmethod
    def _detect_via_loginctl() -> DesktopType:
        """
        Detect desktop type using loginctl command.

        Returns:
            DesktopType enum value
        """
        try:
            # Get current session info
            result = subprocess.run(
                ['loginctl', 'show-session', 'self', '-p', 'Type'],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                output = result.stdout.strip().lower()
                logger.debug(f"loginctl output: {output}")

                if 'wayland' in output:
                    return DesktopType.WAYLAND
                elif 'x11' in output:
                    return DesktopType.X11

        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
            logger.debug(f"loginctl detection failed: {e}")

        return DesktopType.UNKNOWN

    @staticmethod
    def is_x11() -> bool:
        """
        Check if running on X11.

        Returns:
            True if X11 is detected
        """
        return DesktopDetector.detect() == DesktopType.X11

    @staticmethod
    def is_wayland() -> bool:
        """
        Check if running on Wayland.

        Returns:
            True if Wayland is detected
        """
        return DesktopDetector.detect() == DesktopType.WAYLAND

    @staticmethod
    def get_display_info() -> dict:
        """
        Get detailed display environment information.

        Returns:
            Dictionary with display-related environment variables
        """
        info = {
            'desktop_type': DesktopDetector.detect().value,
            'xdg_session_type': os.environ.get('XDG_SESSION_TYPE'),
            'wayland_display': os.environ.get('WAYLAND_DISPLAY'),
            'display': os.environ.get('DISPLAY'),
            'xdg_session_desktop': os.environ.get('XDG_SESSION_DESKTOP'),
            'xdg_current_desktop': os.environ.get('XDG_CURRENT_DESKTOP'),
        }

        logger.debug(f"Display info: {info}")
        return info

    @staticmethod
    def is_display_available() -> bool:
        """
        Check if any display is available (not headless).

        Returns:
            True if a display is available
        """
        desktop_type = DesktopDetector.detect()

        if desktop_type == DesktopType.X11:
            return os.environ.get('DISPLAY') is not None
        elif desktop_type == DesktopType.WAYLAND:
            return os.environ.get('WAYLAND_DISPLAY') is not None

        # Unknown type - try both
        return (
            os.environ.get('DISPLAY') is not None or
            os.environ.get('WAYLAND_DISPLAY') is not None
        )


# Convenience functions for quick detection
def detect_desktop_type() -> DesktopType:
    """
    Convenience function to detect desktop type.

    Returns:
        DesktopType enum value
    """
    return DesktopDetector.detect()


def is_x11() -> bool:
    """
    Convenience function to check for X11.

    Returns:
        True if X11 is detected
    """
    return DesktopDetector.is_x11()


def is_wayland() -> bool:
    """
    Convenience function to check for Wayland.

    Returns:
        True if Wayland is detected
    """
    return DesktopDetector.is_wayland()


def is_display_available() -> bool:
    """
    Convenience function to check if display is available.

    Returns:
        True if a display is available
    """
    return DesktopDetector.is_display_available()
