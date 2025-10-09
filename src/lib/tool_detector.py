"""
Screenshot Tool Detection Utility.

Detects available screenshot capture tools on the system.
Supports scrot (X11), grim (Wayland), and ImageMagick import (fallback).
"""

import shutil
import subprocess
from enum import Enum
from typing import Optional, List

from src.lib.logging_config import get_logger

logger = get_logger(__name__)


class ScreenshotTool(Enum):
    """Enumeration of supported screenshot tools."""
    SCROT = "scrot"  # X11 screenshot tool
    GRIM = "grim"  # Wayland screenshot tool
    IMPORT = "import"  # ImageMagick (fallback, works on both)
    UNKNOWN = "unknown"


class ToolDetector:
    """
    Detects available screenshot capture tools on the system.

    Checks for scrot, grim, and ImageMagick's import command.
    """

    # Tool command names
    TOOLS = {
        ScreenshotTool.SCROT: "scrot",
        ScreenshotTool.GRIM: "grim",
        ScreenshotTool.IMPORT: "import",
    }

    @staticmethod
    def detect_tool(tool: ScreenshotTool) -> bool:
        """
        Check if a specific screenshot tool is available.

        Args:
            tool: ScreenshotTool enum value to check

        Returns:
            True if tool is available in PATH
        """
        if tool == ScreenshotTool.UNKNOWN:
            return False

        command = ToolDetector.TOOLS.get(tool)
        if not command:
            return False

        # Use shutil.which to check if command exists in PATH
        tool_path = shutil.which(command)
        available = tool_path is not None

        if available:
            logger.debug(f"Screenshot tool '{command}' found at: {tool_path}")
        else:
            logger.debug(f"Screenshot tool '{command}' not found in PATH")

        return available

    @staticmethod
    def detect_all_tools() -> List[ScreenshotTool]:
        """
        Detect all available screenshot tools.

        Returns:
            List of available ScreenshotTool enum values
        """
        available = []

        for tool in [ScreenshotTool.SCROT, ScreenshotTool.GRIM, ScreenshotTool.IMPORT]:
            if ToolDetector.detect_tool(tool):
                available.append(tool)

        logger.info(f"Available screenshot tools: {[t.value for t in available]}")
        return available

    @staticmethod
    def get_preferred_tool(desktop_type: str = "auto") -> Optional[ScreenshotTool]:
        """
        Get the preferred screenshot tool for the current environment.

        Args:
            desktop_type: Desktop type hint ("x11", "wayland", or "auto")

        Returns:
            Preferred ScreenshotTool or None if no tools available
        """
        available_tools = ToolDetector.detect_all_tools()

        if not available_tools:
            logger.warning("No screenshot tools available")
            return None

        # If desktop type specified, prefer matching tool
        desktop_type_lower = desktop_type.lower()

        if desktop_type_lower == "wayland":
            # Prefer grim for Wayland
            if ScreenshotTool.GRIM in available_tools:
                logger.info("Selected grim for Wayland")
                return ScreenshotTool.GRIM
        elif desktop_type_lower == "x11":
            # Prefer scrot for X11
            if ScreenshotTool.SCROT in available_tools:
                logger.info("Selected scrot for X11")
                return ScreenshotTool.SCROT

        # Auto-detection or fallback
        # Priority order: scrot > grim > import
        if ScreenshotTool.SCROT in available_tools:
            logger.info("Selected scrot (auto-detection)")
            return ScreenshotTool.SCROT
        elif ScreenshotTool.GRIM in available_tools:
            logger.info("Selected grim (auto-detection)")
            return ScreenshotTool.GRIM
        elif ScreenshotTool.IMPORT in available_tools:
            logger.info("Selected ImageMagick import (fallback)")
            return ScreenshotTool.IMPORT

        return None

    @staticmethod
    def verify_tool_works(tool: ScreenshotTool) -> bool:
        """
        Verify that a tool is not only installed but actually works.

        Args:
            tool: ScreenshotTool to verify

        Returns:
            True if tool executes successfully (with --help or --version)
        """
        if not ToolDetector.detect_tool(tool):
            return False

        command = ToolDetector.TOOLS.get(tool)
        if not command:
            return False

        # Try to run tool with --version or --help to verify it works
        test_args = {
            ScreenshotTool.SCROT: ["--version"],
            ScreenshotTool.GRIM: ["--help"],
            ScreenshotTool.IMPORT: ["--version"],
        }

        args = test_args.get(tool, ["--help"])

        try:
            result = subprocess.run(
                [command] + args,
                capture_output=True,
                timeout=2
            )

            # Most tools return 0 for --version/--help, but some may return 1
            # We just check it doesn't crash
            works = result.returncode in [0, 1]

            if works:
                logger.debug(f"Tool '{command}' verified working")
            else:
                logger.warning(f"Tool '{command}' failed verification (exit code: {result.returncode})")

            return works

        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
            logger.warning(f"Tool '{command}' verification failed: {e}")
            return False

    @staticmethod
    def get_tool_info(tool: ScreenshotTool) -> dict:
        """
        Get detailed information about a screenshot tool.

        Args:
            tool: ScreenshotTool to get info for

        Returns:
            Dictionary with tool information
        """
        command = ToolDetector.TOOLS.get(tool, "unknown")
        available = ToolDetector.detect_tool(tool)
        works = ToolDetector.verify_tool_works(tool) if available else False
        path = shutil.which(command) if available else None

        info = {
            'tool': tool.value,
            'command': command,
            'available': available,
            'works': works,
            'path': path,
        }

        # Try to get version info
        if works:
            info['version'] = ToolDetector._get_tool_version(tool)

        return info

    @staticmethod
    def _get_tool_version(tool: ScreenshotTool) -> Optional[str]:
        """
        Get version string for a tool.

        Args:
            tool: ScreenshotTool to get version for

        Returns:
            Version string or None
        """
        command = ToolDetector.TOOLS.get(tool)
        if not command:
            return None

        try:
            result = subprocess.run(
                [command, "--version"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                # Return first line of output
                version = result.stdout.strip().split('\n')[0]
                return version
            elif result.stderr:
                # Some tools output version to stderr
                version = result.stderr.strip().split('\n')[0]
                return version

        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass

        return None

    @staticmethod
    def get_installation_hints(tool: ScreenshotTool) -> str:
        """
        Get installation hints for a missing tool.

        Args:
            tool: ScreenshotTool to get hints for

        Returns:
            Installation hint string
        """
        hints = {
            ScreenshotTool.SCROT: (
                "Install scrot:\n"
                "  Ubuntu/Debian: sudo apt install scrot\n"
                "  Fedora: sudo dnf install scrot\n"
                "  Arch: sudo pacman -S scrot"
            ),
            ScreenshotTool.GRIM: (
                "Install grim (Wayland):\n"
                "  Ubuntu/Debian: sudo apt install grim\n"
                "  Fedora: sudo dnf install grim\n"
                "  Arch: sudo pacman -S grim"
            ),
            ScreenshotTool.IMPORT: (
                "Install ImageMagick:\n"
                "  Ubuntu/Debian: sudo apt install imagemagick\n"
                "  Fedora: sudo dnf install ImageMagick\n"
                "  Arch: sudo pacman -S imagemagick"
            ),
        }

        return hints.get(tool, "No installation hints available")


# Convenience functions for quick detection
def detect_tool(tool: ScreenshotTool) -> bool:
    """
    Convenience function to detect a specific tool.

    Args:
        tool: ScreenshotTool to detect

    Returns:
        True if tool is available
    """
    return ToolDetector.detect_tool(tool)


def detect_all_tools() -> List[ScreenshotTool]:
    """
    Convenience function to detect all available tools.

    Returns:
        List of available ScreenshotTool enum values
    """
    return ToolDetector.detect_all_tools()


def get_preferred_tool(desktop_type: str = "auto") -> Optional[ScreenshotTool]:
    """
    Convenience function to get preferred tool.

    Args:
        desktop_type: Desktop type hint ("x11", "wayland", or "auto")

    Returns:
        Preferred ScreenshotTool or None
    """
    return ToolDetector.get_preferred_tool(desktop_type)
