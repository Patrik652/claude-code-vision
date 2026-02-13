"""
Wayland Screenshot Capture Implementation.

Uses grim command-line tool to capture screenshots on Wayland compositors.
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


class WaylandScreenshotCapture(IScreenshotCapture):
    """
    Screenshot capture implementation for Wayland using grim.

    Requires grim to be installed on the system.
    For region selection, slurp is also recommended.
    """

    def __init__(self, temp_manager: TempFileManager, image_format: str = "png", quality: int = 90):
        """
        Initialize WaylandScreenshotCapture.

        Args:
            temp_manager: TempFileManager instance for temp file handling
            image_format: Image format ('png', 'jpg', 'jpeg')
            quality: Image quality (1-100, for JPEG)
        """
        self.temp_manager = temp_manager
        self.image_format = image_format.lower()
        self.quality = quality

        # Verify grim is available
        if not self._check_grim_available():
            raise ScreenshotCaptureError(
                "grim is not installed. Install it with: sudo apt install grim"
            )

        # Verify display is available
        if not self._check_display_available():
            raise DisplayNotAvailableError(
                "No Wayland display available. Make sure WAYLAND_DISPLAY environment variable is set."
            )

        logger.debug(f"WaylandScreenshotCapture initialized: format={image_format}, quality={quality}")

    def _check_grim_available(self) -> bool:
        """Check if grim command is available."""
        import shutil
        return shutil.which('grim') is not None

    def _check_display_available(self) -> bool:
        """Check if Wayland display is available."""
        import os
        return os.environ.get('WAYLAND_DISPLAY') is not None

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
            # Build grim command
            cmd = ['grim']

            # Specify output to specific monitor if not the default
            if monitor > 0 or len(monitors) > 1:
                # Get monitor name
                monitor_info = monitors[monitor]
                monitor_name = monitor_info['name']
                cmd.extend(['-o', monitor_name])

            # Add quality for JPEG (grim uses -q parameter)
            if self.image_format in ['jpg', 'jpeg']:
                cmd.extend(['-t', 'jpeg', '-q', str(self.quality)])

            # Output file
            cmd.append(str(temp_path))

            # Execute grim
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10, check=False
            )

            if result.returncode != 0:
                raise ScreenshotCaptureError(f"grim failed: {result.stderr}")

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
                capture_method='grim',
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
            # Build grim command with geometry
            cmd = ['grim']

            # Add quality for JPEG
            if self.image_format in ['jpg', 'jpeg']:
                cmd.extend(['-t', 'jpeg', '-q', str(self.quality)])

            # Add geometry parameter for region capture
            geometry = f"{region.x},{region.y} {region.width}x{region.height}"
            cmd.extend(['-g', geometry])

            # Output file
            cmd.append(str(temp_path))

            # Execute grim
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10, check=False
            )

            if result.returncode != 0:
                raise ScreenshotCaptureError(f"grim region capture failed: {result.stderr}")

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
                capture_method='grim',
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

        try:
            # Use wlr-randr to detect monitors (common on wlroots-based compositors)
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
            logger.debug("wlr-randr not available or timed out")

        # Fallback: try swaymsg (for Sway compositor)
        try:
            result = subprocess.run(
                ['swaymsg', '-t', 'get_outputs', '-r'],
                capture_output=True,
                text=True,
                timeout=5, check=False
            )

            if result.returncode == 0:
                monitors = self._parse_swaymsg_output(result.stdout)
                if monitors:
                    logger.info(f"Detected {len(monitors)} monitor(s) via swaymsg")
                    return monitors

        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.debug("swaymsg not available or timed out")

        # Ultimate fallback: assume single monitor
        logger.warning("Monitor detection failed, using fallback")
        return self._get_fallback_monitor_info()

    def _parse_wlr_randr_output(self, output: str) -> List[dict]:
        """Parse wlr-randr output to extract monitor information."""
        monitors = []
        current_monitor: Dict[str, Any] = {}
        monitor_id = 0

        for output_line in output.split('\n'):
            line = output_line.strip()

            # Monitor name line (starts with name and doesn't have leading space in original)
            if line and not line.startswith(' ') and 'current' in line:
                # Save previous monitor
                if current_monitor:
                    current_monitor['id'] = monitor_id
                    monitors.append(current_monitor)
                    monitor_id += 1

                # Start new monitor
                name = line.split()[0]
                current_monitor = {
                    'name': name,
                    'is_primary': False  # Will be set if we find "Enabled: yes"
                }

            # Parse resolution
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

        # Add last monitor
        if current_monitor and 'width' in current_monitor:
            current_monitor['id'] = monitor_id
            monitors.append(current_monitor)

        return monitors

    def _parse_swaymsg_output(self, output: str) -> List[dict]:
        """Parse swaymsg JSON output to extract monitor information."""
        try:
            import json
            outputs = json.loads(output)

            monitors = []
            for idx, output_info in enumerate(outputs):
                if output_info.get('active'):
                    monitors.append({
                        'id': idx,
                        'name': output_info.get('name', f'output-{idx}'),
                        'width': output_info.get('current_mode', {}).get('width', 1920),
                        'height': output_info.get('current_mode', {}).get('height', 1080),
                        'is_primary': output_info.get('primary', idx == 0)
                    })

            return monitors

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse swaymsg output: {e}")
            return []

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
        """Get image resolution using PIL."""
        try:
            # Try using PIL (Pillow)
            from PIL import Image
            with Image.open(image_path) as img:
                width, height = img.size
                return (int(width), int(height))

        except ImportError:
            # PIL not available, try identify command
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

            except Exception:
                pass

        # Fallback: use monitor size
        logger.warning("Could not determine image resolution, using monitor size")
        monitors = self.detect_monitors()
        return (monitors[0]['width'], monitors[0]['height'])
