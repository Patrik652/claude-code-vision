"""
Coordinate Region Selector Implementation.

Provides coordinate-based region selection (non-graphical).
Implements IRegionSelector interface.
"""

from src.interfaces.screenshot_service import IRegionSelector
from src.models.entities import CaptureRegion
from src.lib.exceptions import InvalidRegionError
from src.lib.logging_config import get_logger

logger = get_logger(__name__)


class CoordinateRegionSelector(IRegionSelector):
    """
    Region selector implementation using explicit coordinates.

    This is a non-graphical selector that creates regions from provided coordinates.
    Used as a fallback when graphical selection is not available.
    """

    def __init__(self):
        """Initialize CoordinateRegionSelector."""
        logger.debug("CoordinateRegionSelector initialized")

    def select_region_graphical(self, monitor: int = 0) -> CaptureRegion:
        """
        Launch graphical region selection tool.

        This implementation does not support graphical selection.

        Args:
            monitor: Monitor to select from (0 = primary)

        Returns:
            CaptureRegion defined by user selection

        Raises:
            NotImplementedError: Graphical selection not supported
        """
        raise NotImplementedError(
            "CoordinateRegionSelector does not support graphical selection. "
            "Use select_region_coordinates() instead."
        )

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
            InvalidRegionError: If coordinates are invalid
        """
        logger.debug(f"Creating region from coordinates: ({x},{y}) {width}x{height} on monitor {monitor}")

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

        logger.info(f"Region created from coordinates: {width}x{height} at ({x},{y}) on monitor {monitor}")
        return region
