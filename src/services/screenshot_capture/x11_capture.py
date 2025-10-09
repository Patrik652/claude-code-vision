"""
X11 Screenshot Capture Implementation.

Uses scrot command-line tool to capture screenshots on X11 display servers.
Implements IScreenshotCapture interface.
"""

import subprocess
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from typing import List

from src.interfaces.screenshot_service import IScreenshotCapture
from src.models.entities import Screenshot, CaptureRegion
from src.lib.exceptions import (
    ScreenshotCaptureError,
    DisplayNotAvailableError,
    MonitorNotFoundError,
    InvalidRegionError
)
from src.lib.logging_config import get_logger
from src.services.temp_file_manager import TempFileManager

logger = get_logger(__name__)


class X11ScreenshotCapture(IScreenshotCapture):
    """
    Screenshot capture implementation for X11 using scrot.

    Requires scrot to be installed on the system.
    """

    def __init__(self, temp_manager: TempFileManager, image_format: str = "png", quality: int = 90):
        """
        Initialize X11ScreenshotCapture.

        Args:
            temp_manager: TempFileManager instance for temp file handling
            image_format: Image format ('png', 'jpg', 'jpeg')
            quality: Image quality (1-100, for JPEG)
        """
        self.temp_manager = temp_manager
        self.image_format = image_format.lower()
        self.quality = quality

        # Verify scrot is available
        if not self._check_scrot_available():
            raise ScreenshotCaptureError(
                "scrot is not installed. Install it with: sudo apt install scrot"
            )

        # Verify display is available
        if not self._check_display_available():
            raise DisplayNotAvailableError(
                "No X11 display available. Make sure DISPLAY environment variable is set."
            )

        logger.debug(f"X11ScreenshotCapture initialized: format={image_format}, quality={quality}")

    def _check_scrot_available(self) -> bool:
        """Check if scrot command is available."""
        import shutil
        return shutil.which('scrot') is not None

    def _check_display_available(self) -> bool:
        """Check if X11 display is available."""
        import os
        return os.environ.get('DISPLAY') is not None

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
            raise MonitorNotFoundError(f"Monitor {monitor} not found. Available monitors: {len(monitors)}")

        # Create temp file
        extension = 'jpg' if self.image_format in ['jpg', 'jpeg'] else self.image_format
        temp_path = self.temp_manager.create_temp_file(extension)

        try:
            # Build scrot command
            # scrot captures the entire screen by default
            # For multi-monitor, we'll capture all and then crop if needed
            cmd = ['scrot']

            # Add quality parameter for JPEG
            if self.image_format in ['jpg', 'jpeg']:
                cmd.extend(['--quality', str(self.quality)])

            # Output file
            cmd.append(str(temp_path))

            # Execute scrot
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                raise ScreenshotCaptureError(f"scrot failed: {result.stderr}")

            # Get file size
            file_size = temp_path.stat().st_size

            # Get image resolution using identify (ImageMagick) or fallback
            resolution = self._get_image_resolution(temp_path)

            # Create Screenshot object
            screenshot = Screenshot(
                id=uuid4(),
                timestamp=datetime.now(),
                file_path=temp_path,
                format=self.image_format,
                original_size_bytes=file_size,
                optimized_size_bytes=file_size,  # Not optimized yet
                resolution=resolution,
                source_monitor=monitor,
                capture_method='scrot',
                privacy_zones_applied=False,
                capture_region=None
            )

            logger.info(f"Screenshot captured: {screenshot.id}, size={file_size} bytes, resolution={resolution}")
            return screenshot

        except subprocess.TimeoutExpired:
            # Cleanup temp file
            self.temp_manager.cleanup_temp_file(temp_path)
            raise ScreenshotCaptureError("Screenshot capture timed out")

        except Exception as e:
            # Cleanup temp file
            self.temp_manager.cleanup_temp_file(temp_path)
            raise ScreenshotCaptureError(f"Failed to capture screenshot: {e}")

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
            # Build scrot command with geometry
            cmd = ['scrot']

            # Add quality parameter for JPEG
            if self.image_format in ['jpg', 'jpeg']:
                cmd.extend(['--quality', str(self.quality)])

            # Add geometry parameter for region capture
            # Format: WIDTHxHEIGHT+X+Y
            geometry = f"{region.width}x{region.height}+{region.x}+{region.y}"
            cmd.extend(['--autoselect', geometry])

            # Output file
            cmd.append(str(temp_path))

            # Execute scrot
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                raise ScreenshotCaptureError(f"scrot region capture failed: {result.stderr}")

            # Get file size
            file_size = temp_path.stat().st_size

            # Create Screenshot object
            screenshot = Screenshot(
                id=uuid4(),
                timestamp=datetime.now(),
                file_path=temp_path,
                format=self.image_format,
                original_size_bytes=file_size,
                optimized_size_bytes=file_size,
                resolution=(region.width, region.height),
                source_monitor=region.monitor,
                capture_method='scrot',
                privacy_zones_applied=False,
                capture_region=region
            )

            logger.info(f"Region screenshot captured: {screenshot.id}, size={file_size} bytes")
            return screenshot

        except subprocess.TimeoutExpired:
            self.temp_manager.cleanup_temp_file(temp_path)
            raise ScreenshotCaptureError("Region capture timed out")

        except Exception as e:
            self.temp_manager.cleanup_temp_file(temp_path)
            raise ScreenshotCaptureError(f"Failed to capture region: {e}")

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
            # Use xrandr to detect monitors
            result = subprocess.run(
                ['xrandr', '--query'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                # Fallback: assume single primary monitor
                logger.warning("xrandr failed, using fallback single monitor")
                return self._get_fallback_monitor_info()

            # Parse xrandr output
            monitors = self._parse_xrandr_output(result.stdout)

            if not monitors:
                # Fallback
                return self._get_fallback_monitor_info()

            logger.info(f"Detected {len(monitors)} monitor(s)")
            return monitors

        except FileNotFoundError:
            # xrandr not available, use fallback
            logger.warning("xrandr not available, using fallback")
            return self._get_fallback_monitor_info()

        except subprocess.TimeoutExpired:
            logger.warning("xrandr timed out, using fallback")
            return self._get_fallback_monitor_info()

        except Exception as e:
            logger.error(f"Monitor detection failed: {e}, using fallback")
            return self._get_fallback_monitor_info()

    def _parse_xrandr_output(self, output: str) -> List[dict]:
        """Parse xrandr output to extract monitor information."""
        monitors = []
        monitor_id = 0

        for line in output.split('\n'):
            # Look for connected monitors with resolution
            # Example: "HDMI-1 connected primary 1920x1080+0+0"
            if ' connected' in line:
                parts = line.split()
                name = parts[0]
                is_primary = 'primary' in parts

                # Extract resolution
                for part in parts:
                    if 'x' in part and '+' in part:
                        # Format: WIDTHxHEIGHT+X+Y
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

    def _get_fallback_monitor_info(self) -> List[dict]:
        """Get fallback monitor info when detection fails."""
        # Use xdpyinfo to get screen size
        try:
            result = subprocess.run(
                ['xdpyinfo'],
                capture_output=True,
                text=True,
                timeout=3
            )

            if result.returncode == 0:
                # Parse dimensions from xdpyinfo
                for line in result.stdout.split('\n'):
                    if 'dimensions:' in line:
                        # Format: "  dimensions:    1920x1080 pixels (508x285 millimeters)"
                        parts = line.split()
                        if len(parts) >= 2:
                            dims = parts[1].split('x')
                            if len(dims) == 2:
                                return [{
                                    'id': 0,
                                    'name': 'default',
                                    'width': int(dims[0]),
                                    'height': int(dims[1]),
                                    'is_primary': True
                                }]

        except:
            pass

        # Ultimate fallback: assume common resolution
        logger.warning("Using default fallback resolution 1920x1080")
        return [{
            'id': 0,
            'name': 'default',
            'width': 1920,
            'height': 1080,
            'is_primary': True
        }]

    def _get_image_resolution(self, image_path: Path) -> tuple[int, int]:
        """Get image resolution using PIL or identify command."""
        try:
            # Try using PIL (Pillow)
            from PIL import Image
            with Image.open(image_path) as img:
                return img.size

        except ImportError:
            # PIL not available, try identify command
            try:
                result = subprocess.run(
                    ['identify', '-format', '%wx%h', str(image_path)],
                    capture_output=True,
                    text=True,
                    timeout=3
                )

                if result.returncode == 0:
                    width, height = result.stdout.strip().split('x')
                    return (int(width), int(height))

            except:
                pass

        # Fallback: get from file size estimation (very rough)
        logger.warning("Could not determine image resolution, using monitor size")
        monitors = self.detect_monitors()
        return (monitors[0]['width'], monitors[0]['height'])
