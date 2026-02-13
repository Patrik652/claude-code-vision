"""
ImageMagick Screenshot Capture Implementation.

Uses ImageMagick's import command as a fallback for screenshot capture.
Works on both X11 and Wayland (with XWayland).
Implements IScreenshotCapture interface.
"""

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from src.interfaces.screenshot_service import IScreenshotCapture
from src.lib.exceptions import (
    DisplayNotAvailableError,
    InvalidRegionError,
    MonitorNotFoundError,
    ScreenshotCaptureError,
)
from src.lib.logging_config import get_logger
from src.models.entities import CaptureRegion, Screenshot
from src.services.temp_file_manager import TempFileManager

logger = get_logger(__name__)


class ImageMagickScreenshotCapture(IScreenshotCapture):
    """
    Screenshot capture implementation using ImageMagick's import command.

    This is a fallback implementation that works on both X11 and Wayland (via XWayland).
    Requires ImageMagick to be installed on the system.
    """

    def __init__(self, temp_manager: TempFileManager, image_format: str = "png", quality: int = 90):
        """
        Initialize ImageMagickScreenshotCapture.

        Args:
            temp_manager: TempFileManager instance for temp file handling
            image_format: Image format ('png', 'jpg', 'jpeg')
            quality: Image quality (1-100, for JPEG)
        """
        self.temp_manager = temp_manager
        self.image_format = image_format.lower()
        self.quality = quality

        # Verify import is available
        if not self._check_import_available():
            raise ScreenshotCaptureError(
                "ImageMagick import is not installed. Install it with: sudo apt install imagemagick"
            )

        # Verify display is available
        if not self._check_display_available():
            raise DisplayNotAvailableError(
                "No display available. Make sure DISPLAY or WAYLAND_DISPLAY environment variable is set."
            )

        logger.debug(f"ImageMagickScreenshotCapture initialized: format={image_format}, quality={quality}")

    def _check_import_available(self) -> bool:
        """Check if import command is available."""
        import shutil
        return shutil.which('import') is not None

    def _check_display_available(self) -> bool:
        """Check if display is available (X11 or Wayland)."""
        import os
        return (
            os.environ.get('DISPLAY') is not None or
            os.environ.get('WAYLAND_DISPLAY') is not None
        )

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
        logger.info(f"Capturing full screen from monitor {monitor}")

        # Verify monitor exists
        monitors = self.detect_monitors()
        if monitor >= len(monitors):
            raise MonitorNotFoundError(monitor, len(monitors))

        # Create temp file
        extension = 'jpg' if self.image_format in ['jpg', 'jpeg'] else self.image_format
        temp_path = self.temp_manager.create_temp_file(extension)

        try:
            # Build import command
            cmd = ['import']

            # Capture root window (entire screen)
            cmd.extend(['-window', 'root'])

            # Add quality parameter
            cmd.extend(['-quality', str(self.quality)])

            # Output file
            cmd.append(str(temp_path))

            # Execute import
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10, check=False
            )

            if result.returncode != 0:
                raise ScreenshotCaptureError(f"import failed: {result.stderr}")

            # Get file size
            file_size = temp_path.stat().st_size

            # Get image resolution
            resolution = self._get_image_resolution(temp_path)

            # Create Screenshot object
            screenshot = Screenshot(
                id=uuid4(),
                timestamp=datetime.now(timezone.utc),
                file_path=temp_path,
                format=self.image_format,
                original_size_bytes=file_size,
                optimized_size_bytes=file_size,  # Not optimized yet
                resolution=resolution,
                source_monitor=monitor,
                capture_method='import',
                privacy_zones_applied=False,
                capture_region=None
            )

            logger.info(f"Screenshot captured: {screenshot.id}, size={file_size} bytes, resolution={resolution}")
            return screenshot

        except subprocess.TimeoutExpired:
            # Cleanup temp file
            self.temp_manager.cleanup_temp_file(temp_path)
            raise ScreenshotCaptureError("Screenshot capture timed out") from None

        except Exception as e:
            # Cleanup temp file
            self.temp_manager.cleanup_temp_file(temp_path)
            raise ScreenshotCaptureError(f"Failed to capture screenshot: {e}") from e

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
        logger.info(f"Capturing region: x={region.x}, y={region.y}, w={region.width}, h={region.height}")

        # Validate region
        monitors = self.detect_monitors()
        if region.monitor >= len(monitors):
            raise InvalidRegionError(f"Monitor {region.monitor} not found")

        monitor_info = monitors[region.monitor]

        # Validate coordinates
        if region.x < 0 or region.y < 0:
            raise InvalidRegionError("Region coordinates must be non-negative")

        if region.width <= 0 or region.height <= 0:
            raise InvalidRegionError("Region dimensions must be positive")

        if region.x + region.width > monitor_info['width']:
            raise InvalidRegionError(f"Region exceeds monitor width ({monitor_info['width']})")

        if region.y + region.height > monitor_info['height']:
            raise InvalidRegionError(f"Region exceeds monitor height ({monitor_info['height']})")

        # Create temp file
        extension = 'jpg' if self.image_format in ['jpg', 'jpeg'] else self.image_format
        temp_path = self.temp_manager.create_temp_file(extension)

        try:
            # Build import command with crop
            cmd = ['import']

            # Capture root window
            cmd.extend(['-window', 'root'])

            # Add crop parameter for region
            crop = f"{region.width}x{region.height}+{region.x}+{region.y}"
            cmd.extend(['-crop', crop])

            # Add quality parameter
            cmd.extend(['-quality', str(self.quality)])

            # Output file
            cmd.append(str(temp_path))

            # Execute import
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10, check=False
            )

            if result.returncode != 0:
                raise ScreenshotCaptureError(f"import region capture failed: {result.stderr}")

            # Get file size
            file_size = temp_path.stat().st_size

            # Create Screenshot object
            screenshot = Screenshot(
                id=uuid4(),
                timestamp=datetime.now(timezone.utc),
                file_path=temp_path,
                format=self.image_format,
                original_size_bytes=file_size,
                optimized_size_bytes=file_size,
                resolution=(region.width, region.height),
                source_monitor=region.monitor,
                capture_method='import',
                privacy_zones_applied=False,
                capture_region=region
            )

            logger.info(f"Region screenshot captured: {screenshot.id}, size={file_size} bytes")
            return screenshot

        except subprocess.TimeoutExpired:
            self.temp_manager.cleanup_temp_file(temp_path)
            raise ScreenshotCaptureError("Region capture timed out") from None

        except Exception as e:
            self.temp_manager.cleanup_temp_file(temp_path)
            raise ScreenshotCaptureError(f"Failed to capture region: {e}") from e

    def detect_monitors(self) -> List[dict]:
        """
        Detect available monitors and their properties.

        Returns:
            List of monitor info dicts

        Raises:
            DisplayNotAvailableError: If no display available
        """
        logger.debug("Detecting monitors")

        if not self._check_display_available():
            raise DisplayNotAvailableError("No display available")

        # Try X11 detection first (xrandr)
        import os
        if os.environ.get('DISPLAY'):
            try:
                result = subprocess.run(
                    ['xrandr', '--query'],
                    capture_output=True,
                    text=True,
                    timeout=5, check=False
                )

                if result.returncode == 0:
                    monitors = self._parse_xrandr_output(result.stdout)
                    if monitors:
                        logger.info(f"Detected {len(monitors)} monitor(s) via xrandr")
                        return monitors

            except (FileNotFoundError, subprocess.TimeoutExpired):
                logger.debug("xrandr not available")

        # Try Wayland detection (wlr-randr)
        if os.environ.get('WAYLAND_DISPLAY'):
            try:
                result = subprocess.run(
                    ['wlr-randr'],
                    capture_output=True,
                    text=True,
                    timeout=5, check=False
                )

                if result.returncode == 0:
                    monitors = self._parse_wlr_randr_output(result.stdout)
                    if monitors:
                        logger.info(f"Detected {len(monitors)} monitor(s) via wlr-randr")
                        return monitors

            except (FileNotFoundError, subprocess.TimeoutExpired):
                logger.debug("wlr-randr not available")

        # Fallback
        logger.warning("Monitor detection failed, using fallback")
        return self._get_fallback_monitor_info()

    def _parse_xrandr_output(self, output: str) -> List[dict]:
        """Parse xrandr output to extract monitor information."""
        monitors = []
        monitor_id = 0

        for line in output.split('\n'):
            if ' connected' in line:
                parts = line.split()
                name = parts[0]
                is_primary = 'primary' in parts

                # Extract resolution
                for part in parts:
                    if 'x' in part and '+' in part:
                        res_part = part.split('+')[0]
                        width, height = res_part.split('x')

                        monitors.append({
                            'id': monitor_id,
                            'name': name,
                            'width': int(width),
                            'height': int(height),
                            'is_primary': is_primary
                        })

                        monitor_id += 1
                        break

        return monitors

    def _parse_wlr_randr_output(self, output: str) -> List[dict]:
        """Parse wlr-randr output to extract monitor information."""
        monitors = []
        current_monitor: Dict[str, Any] = {}
        monitor_id = 0

        for output_line in output.split('\n'):
            line = output_line.strip()

            if line and not line.startswith(' ') and 'current' in line:
                if current_monitor:
                    current_monitor['id'] = monitor_id
                    monitors.append(current_monitor)
                    monitor_id += 1

                name = line.split()[0]
                current_monitor = {
                    'name': name,
                    'is_primary': False
                }

            elif 'current' in line and 'x' in line:
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        width = int(parts[0])
                        height = int(parts[2])
                        current_monitor['width'] = width
                        current_monitor['height'] = height
                    except (ValueError, IndexError):
                        pass

            elif 'Enabled: yes' in line:
                current_monitor['is_primary'] = True

        if current_monitor and 'width' in current_monitor:
            current_monitor['id'] = monitor_id
            monitors.append(current_monitor)

        return monitors

    def _get_fallback_monitor_info(self) -> List[dict]:
        """Get fallback monitor info when detection fails."""
        logger.warning("Using default fallback resolution 1920x1080")
        return [{
            'id': 0,
            'name': 'default',
            'width': 1920,
            'height': 1080,
            'is_primary': True
        }]

    def _get_image_resolution(self, image_path: Path) -> Tuple[int, int]:
        """Get image resolution using identify command (part of ImageMagick)."""
        try:
            result = subprocess.run(
                ['identify', '-format', '%wx%h', str(image_path)],
                capture_output=True,
                text=True,
                timeout=3, check=False
            )

            if result.returncode == 0:
                width, height = result.stdout.strip().split('x')
                return (int(width), int(height))

        except Exception as e:
            logger.warning(f"Failed to get image resolution: {e}")

        # Fallback: use monitor size
        logger.warning("Could not determine image resolution, using monitor size")
        monitors = self.detect_monitors()
        return (monitors[0]['width'], monitors[0]['height'])
