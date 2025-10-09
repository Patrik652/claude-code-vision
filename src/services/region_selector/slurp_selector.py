"""
Slurp Region Selector Implementation.

Uses slurp tool for graphical region selection on Wayland.
Implements IRegionSelector interface.
"""

import subprocess
from typing import List

from src.interfaces.screenshot_service import IRegionSelector
from src.models.entities import CaptureRegion
from src.lib.exceptions import (
    RegionSelectionCancelledError,
    SelectionToolNotFoundError,
    InvalidRegionError
)
from src.lib.logging_config import get_logger

logger = get_logger(__name__)


class SlurpRegionSelector(IRegionSelector):
    """
    Region selector implementation for Wayland using slurp.

    Requires slurp to be installed on the system.
    """

    def __init__(self):
        """Initialize SlurpRegionSelector."""
        # Verify slurp is available
        if not self._check_slurp_available():
            raise SelectionToolNotFoundError(
                "slurp is not installed. Install it with: sudo apt install slurp"
            )

        logger.debug("SlurpRegionSelector initialized")

    def _check_slurp_available(self) -> bool:
        """Check if slurp command is available."""
        import shutil
        return shutil.which('slurp') is not None

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
        logger.info(f"Launching slurp for graphical region selection on monitor {monitor}")

        try:
            # Build slurp command
            cmd = ['slurp']

            # Add format to get coordinates
            # slurp outputs: "X,Y WIDTHxHEIGHT"
            cmd.extend(['-f', '%x,%y %wx%h'])

            # Execute slurp
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # Wait up to 60 seconds for user selection
            )

            # Check if user cancelled (exit code 1)
            if result.returncode == 1:
                logger.info("User cancelled region selection")
                raise RegionSelectionCancelledError("Region selection was cancelled by user")

            # Check for other errors
            if result.returncode != 0:
                logger.error(f"slurp failed with exit code {result.returncode}: {result.stderr}")
                raise SelectionToolNotFoundError(f"slurp failed: {result.stderr}")

            # Parse output
            output = result.stdout.strip()
            logger.debug(f"slurp output: {output}")

            # Parse format: "X,Y WxH"
            region = self._parse_slurp_output(output, monitor)

            logger.info(f"Region selected: {region.width}x{region.height} at ({region.x},{region.y})")
            return region

        except subprocess.TimeoutExpired:
            logger.warning("Region selection timed out")
            raise RegionSelectionCancelledError("Region selection timed out")

        except FileNotFoundError:
            raise SelectionToolNotFoundError("slurp command not found")

        except Exception as e:
            logger.error(f"Region selection failed: {e}")
            raise

    def _parse_slurp_output(self, output: str, monitor: int) -> CaptureRegion:
        """
        Parse slurp output to CaptureRegion.

        Args:
            output: Output from slurp command (format: "X,Y WxH")
            monitor: Monitor index

        Returns:
            CaptureRegion object

        Raises:
            InvalidRegionError: If output format is invalid
        """
        try:
            # Expected format: "X,Y WxH"
            # Example: "100,200 400x300"
            parts = output.split()

            if len(parts) != 2:
                raise InvalidRegionError(f"Invalid slurp output format: {output}")

            # Parse coordinates
            coords = parts[0].split(',')
            if len(coords) != 2:
                raise InvalidRegionError(f"Invalid coordinates format: {parts[0]}")

            x = int(coords[0])
            y = int(coords[1])

            # Parse dimensions
            dims = parts[1].split('x')
            if len(dims) != 2:
                raise InvalidRegionError(f"Invalid dimensions format: {parts[1]}")

            width = int(dims[0])
            height = int(dims[1])

            # Create CaptureRegion
            region = CaptureRegion(
                x=x,
                y=y,
                width=width,
                height=height,
                monitor=monitor,
                selection_method='graphical'
            )

            return region

        except (ValueError, IndexError) as e:
            raise InvalidRegionError(f"Failed to parse slurp output '{output}': {e}")

    def select_region_coordinates(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        monitor: int = 0
    ) -> CaptureRegion:
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
        logger.debug(f"Creating region from coordinates: ({x},{y}) {width}x{height}")

        # Validate coordinates
        if x < 0 or y < 0:
            raise InvalidRegionError("Coordinates must be non-negative")

        if width <= 0 or height <= 0:
            raise InvalidRegionError("Dimensions must be positive")

        # Create region
        region = CaptureRegion(
            x=x,
            y=y,
            width=width,
            height=height,
            monitor=monitor,
            selection_method='coordinates'
        )

        logger.info(f"Region created from coordinates: {width}x{height} at ({x},{y})")
        return region
