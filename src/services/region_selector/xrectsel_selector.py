"""
Xrectsel Region Selector Implementation.

Uses xrectsel tool for graphical region selection on X11.
Implements IRegionSelector interface.
"""

import subprocess

from src.interfaces.screenshot_service import IRegionSelector
from src.lib.exceptions import InvalidRegionError, RegionSelectionCancelledError, SelectionToolNotFoundError
from src.lib.logging_config import get_logger
from src.models.entities import CaptureRegion

logger = get_logger(__name__)


class XrectselRegionSelector(IRegionSelector):
    """
    Region selector implementation for X11 using xrectsel.

    Requires xrectsel to be installed on the system.
    Fallback to slop if xrectsel not available.
    """

    def __init__(self) -> None:
        """Initialize XrectselRegionSelector."""
        # Check for xrectsel or slop
        self.tool = self._detect_selection_tool()

        if not self.tool:
            raise SelectionToolNotFoundError(
                "No X11 selection tool found. Install xrectsel or slop:\n"
                "  Ubuntu/Debian: sudo apt install slop\n"
                "  Or build xrectsel from source"
            )

        logger.debug(f"XrectselRegionSelector initialized with tool: {self.tool}")

    def _detect_selection_tool(self) -> str:
        """
        Detect available selection tool.

        Returns:
            Tool name ('xrectsel' or 'slop') or empty string if none found
        """
        import shutil

        if shutil.which('xrectsel'):
            return 'xrectsel'
        if shutil.which('slop'):
            return 'slop'

        return ''

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
        logger.info(f"Launching {self.tool} for graphical region selection on monitor {monitor}")

        try:
            if self.tool == 'xrectsel':
                return self._select_with_xrectsel(monitor)
            if self.tool == 'slop':
                return self._select_with_slop(monitor)
            raise SelectionToolNotFoundError("No selection tool available")

        except subprocess.TimeoutExpired:
            logger.warning("Region selection timed out")
            raise RegionSelectionCancelledError() from None

        except FileNotFoundError:
            raise SelectionToolNotFoundError(f"{self.tool} command not found") from None

        except Exception as e:
            logger.error(f"Region selection failed: {e}")
            raise

    def _select_with_xrectsel(self, monitor: int) -> CaptureRegion:
        """
        Select region using xrectsel.

        Args:
            monitor: Monitor index

        Returns:
            CaptureRegion

        Raises:
            RegionSelectionCancelledError: If cancelled
        """
        # Build xrectsel command
        cmd = ['xrectsel', '%x %y %w %h']

        # Execute xrectsel
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60, check=False
        )

        # Check if user cancelled (exit code != 0)
        if result.returncode != 0:
            if result.returncode == 1:
                logger.info("User cancelled region selection")
                raise RegionSelectionCancelledError()
            logger.error(f"xrectsel failed with exit code {result.returncode}: {result.stderr}")
            raise SelectionToolNotFoundError(f"xrectsel failed: {result.stderr}")

        # Parse output
        output = result.stdout.strip()
        logger.debug(f"xrectsel output: {output}")

        # Parse format: "X Y W H"
        region = self._parse_xrectsel_output(output, monitor)

        logger.info(f"Region selected: {region.width}x{region.height} at ({region.x},{region.y})")
        return region

    def _select_with_slop(self, monitor: int) -> CaptureRegion:
        """
        Select region using slop.

        Args:
            monitor: Monitor index

        Returns:
            CaptureRegion

        Raises:
            RegionSelectionCancelledError: If cancelled
        """
        # Build slop command
        cmd = ['slop', '-f', '%x %y %w %h']

        # Execute slop
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60, check=False
        )

        # Check if user cancelled (exit code 1)
        if result.returncode == 1:
            logger.info("User cancelled region selection")
            raise RegionSelectionCancelledError()

        # Check for other errors
        if result.returncode != 0:
            logger.error(f"slop failed with exit code {result.returncode}: {result.stderr}")
            raise SelectionToolNotFoundError(f"slop failed: {result.stderr}")

        # Parse output (slop uses same format as xrectsel with our format string)
        output = result.stdout.strip()
        logger.debug(f"slop output: {output}")

        region = self._parse_xrectsel_output(output, monitor)

        logger.info(f"Region selected: {region.width}x{region.height} at ({region.x},{region.y})")
        return region

    def _parse_xrectsel_output(self, output: str, monitor: int) -> CaptureRegion:
        """
        Parse xrectsel/slop output to CaptureRegion.

        Args:
            output: Output from tool (format: "X Y W H")
            monitor: Monitor index

        Returns:
            CaptureRegion object

        Raises:
            InvalidRegionError: If output format is invalid
        """
        try:
            # Expected format: "X Y W H"
            parts = output.split()

            if len(parts) != 4:
                raise InvalidRegionError(f"Invalid output format: {output}")

            x = int(parts[0])
            y = int(parts[1])
            width = int(parts[2])
            height = int(parts[3])

            # Create CaptureRegion
            return CaptureRegion(
                x=x,
                y=y,
                width=width,
                height=height,
                monitor=monitor,
                selection_method='graphical'
            )


        except (ValueError, IndexError) as e:
            raise InvalidRegionError(f"Failed to parse output '{output}': {e}") from e

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
