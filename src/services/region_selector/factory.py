"""
RegionSelector Factory Implementation.

Factory for creating appropriate region selector based on environment.
Implements hybrid approach with graphical selection and coordinate fallback.
"""

import os
from typing import Optional

from src.interfaces.screenshot_service import IRegionSelector
from src.lib.exceptions import SelectionToolNotFoundError
from src.lib.logging_config import get_logger
from src.services.region_selector.coordinate_selector import CoordinateRegionSelector
from src.services.region_selector.slurp_selector import SlurpRegionSelector
from src.services.region_selector.xrectsel_selector import XrectselRegionSelector

logger = get_logger(__name__)


class RegionSelectorFactory:
    """
    Factory for creating region selector instances.

    Automatically selects the best available region selector based on:
    - Desktop environment (X11 vs Wayland)
    - Available selection tools (slurp, xrectsel, slop)
    - Fallback to coordinate-based selection
    """

    @staticmethod
    def detect_desktop_environment() -> str:
        """
        Detect the current desktop environment.

        Returns:
            'wayland', 'x11', or 'unknown'
        """
        # Check Wayland session
        wayland_display = os.environ.get('WAYLAND_DISPLAY')
        if wayland_display:
            logger.debug(f"Detected Wayland environment: {wayland_display}")
            return 'wayland'

        # Check X11 session
        x_display = os.environ.get('DISPLAY')
        if x_display:
            logger.debug(f"Detected X11 environment: {x_display}")
            return 'x11'

        logger.warning("Could not detect desktop environment")
        return 'unknown'

    @staticmethod
    def create_graphical_selector() -> Optional[IRegionSelector]:
        """
        Create graphical region selector based on environment.

        Returns:
            IRegionSelector instance or None if no graphical selector available
        """
        env = RegionSelectorFactory.detect_desktop_environment()

        # Try Wayland selector
        if env == 'wayland':
            try:
                logger.info("Created SlurpRegionSelector for Wayland")
                return SlurpRegionSelector()
            except SelectionToolNotFoundError as e:
                logger.warning(f"Slurp not available: {e}")

        # Try X11 selector
        if env in ('x11', 'wayland'):
            # Try X11 even on Wayland as fallback (some tools work on both)
            try:
                logger.info("Created XrectselRegionSelector for X11")
                return XrectselRegionSelector()
            except SelectionToolNotFoundError as e:
                logger.warning(f"X11 selection tools not available: {e}")

        return None

    @staticmethod
    def create_coordinate_selector() -> IRegionSelector:
        """
        Create coordinate-based region selector (fallback).

        Returns:
            CoordinateRegionSelector instance
        """
        logger.info("Created CoordinateRegionSelector as fallback")
        return CoordinateRegionSelector()

    @staticmethod
    def create(prefer_graphical: bool = True) -> IRegionSelector:
        """
        Create the best available region selector.

        Args:
            prefer_graphical: Try to create graphical selector first if True

        Returns:
            IRegionSelector instance (graphical or coordinate-based)
        """
        if prefer_graphical:
            graphical_selector = RegionSelectorFactory.create_graphical_selector()
            if graphical_selector:
                return graphical_selector

            logger.info("No graphical selector available, falling back to coordinate selector")

        return RegionSelectorFactory.create_coordinate_selector()

    @staticmethod
    def create_for_environment(environment: str) -> IRegionSelector:
        """
        Create region selector for specific environment.

        Args:
            environment: 'wayland', 'x11', or 'coordinates'

        Returns:
            IRegionSelector instance

        Raises:
            SelectionToolNotFoundError: If requested selector not available
        """
        if environment == 'wayland':
            return SlurpRegionSelector()
        if environment == 'x11':
            return XrectselRegionSelector()
        if environment == 'coordinates':
            return CoordinateRegionSelector()
        raise ValueError(f"Unknown environment: {environment}")
