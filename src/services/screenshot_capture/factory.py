"""
Screenshot Capture Factory.

Auto-selects the appropriate screenshot capture implementation based on:
1. Desktop environment (X11 vs Wayland)
2. Available screenshot tools (scrot, grim, import)
"""

from typing import Any, Callable, List, Optional

from src.interfaces.screenshot_service import IScreenshotCapture
from src.lib.desktop_detector import DesktopDetector, DesktopType
from src.lib.exceptions import ScreenshotCaptureError
from src.lib.logging_config import get_logger
from src.lib.tool_detector import ScreenshotTool, ToolDetector
from src.services.temp_file_manager import TempFileManager

logger = get_logger(__name__)


class ScreenshotCaptureFactory:
    """
    Factory for creating appropriate screenshot capture implementation.

    Automatically detects desktop environment and available tools,
    then instantiates the best implementation.
    """

    @staticmethod
    def create(
        temp_manager: Optional[TempFileManager] = None,
        image_format: str = "png",
        quality: int = 90,
        preferred_tool: Optional[str] = None
    ) -> IScreenshotCapture:
        """
        Create screenshot capture implementation based on environment.

        Args:
            temp_manager: TempFileManager instance (creates default if None)
            image_format: Image format ('png', 'jpg', 'jpeg')
            quality: Image quality (1-100, for JPEG)
            preferred_tool: Override auto-detection ('scrot', 'grim', 'import', 'auto')

        Returns:
            IScreenshotCapture implementation

        Raises:
            ScreenshotCaptureError: If no suitable implementation available
        """
        logger.info("Creating screenshot capture implementation")

        # Create temp manager if not provided
        if temp_manager is None:
            temp_manager = TempFileManager()

        # Detect desktop environment
        desktop_type = DesktopDetector.detect()
        logger.info(f"Detected desktop type: {desktop_type.value}")

        # Determine which tool to use
        if preferred_tool and preferred_tool.lower() != 'auto':
            # User specified a preferred tool
            tool = ScreenshotCaptureFactory._get_tool_from_name(preferred_tool)
            if tool and ToolDetector.detect_tool(tool):
                logger.info(f"Using user-specified tool: {tool.value}")
            else:
                logger.warning(f"Preferred tool '{preferred_tool}' not available, auto-detecting")
                tool = ToolDetector.get_preferred_tool(desktop_type.value)
        else:
            # Auto-detect best tool
            tool = ToolDetector.get_preferred_tool(desktop_type.value)

        if tool is None:
            raise ScreenshotCaptureError(
                "No screenshot tools available. Please install one of: scrot, grim, or imagemagick"
            )

        logger.info(f"Selected screenshot tool: {tool.value}")

        # Create appropriate implementation
        return ScreenshotCaptureFactory._create_implementation(
            tool=tool,
            desktop_type=desktop_type,
            temp_manager=temp_manager,
            image_format=image_format,
            quality=quality
        )

    @staticmethod
    def _get_tool_from_name(tool_name: str) -> Optional[ScreenshotTool]:
        """Convert tool name string to ScreenshotTool enum."""
        tool_map = {
            'scrot': ScreenshotTool.SCROT,
            'grim': ScreenshotTool.GRIM,
            'import': ScreenshotTool.IMPORT,
        }
        return tool_map.get(tool_name.lower())

    @staticmethod
    def _create_implementation(
        tool: ScreenshotTool,
        desktop_type: DesktopType,
        temp_manager: TempFileManager,
        image_format: str,
        quality: int
    ) -> IScreenshotCapture:
        """
        Create the actual implementation instance.

        Args:
            tool: Screenshot tool to use
            desktop_type: Desktop environment type
            temp_manager: TempFileManager instance
            image_format: Image format
            quality: Image quality

        Returns:
            IScreenshotCapture implementation

        Raises:
            ScreenshotCaptureError: If implementation cannot be created
        """
        _ = desktop_type
        try:
            if tool == ScreenshotTool.SCROT:
                from src.services.screenshot_capture.x11_capture import X11ScreenshotCapture
                logger.info("Creating X11ScreenshotCapture (scrot)")
                return X11ScreenshotCapture(
                    temp_manager=temp_manager,
                    image_format=image_format,
                    quality=quality
                )

            if tool == ScreenshotTool.GRIM:
                from src.services.screenshot_capture.wayland_capture import WaylandScreenshotCapture
                logger.info("Creating WaylandScreenshotCapture (grim)")
                return WaylandScreenshotCapture(
                    temp_manager=temp_manager,
                    image_format=image_format,
                    quality=quality
                )

            if tool == ScreenshotTool.IMPORT:
                from src.services.screenshot_capture.imagemagick_capture import ImageMagickScreenshotCapture
                logger.info("Creating ImageMagickScreenshotCapture (import)")
                return ImageMagickScreenshotCapture(
                    temp_manager=temp_manager,
                    image_format=image_format,
                    quality=quality
                )

            raise ScreenshotCaptureError(f"Unsupported screenshot tool: {tool}")

        except ImportError as e:
            raise ScreenshotCaptureError(
                f"Failed to import screenshot capture implementation: {e}"
            ) from e

    @staticmethod
    def get_available_tools() -> List[ScreenshotTool]:
        """
        Get list of available screenshot tools.

        Returns:
            List of available ScreenshotTool enums
        """
        return ToolDetector.detect_all_tools()

    @staticmethod
    def get_recommended_tool() -> Optional[ScreenshotTool]:
        """
        Get recommended tool for current environment.

        Returns:
            Recommended ScreenshotTool or None
        """
        desktop_type = DesktopDetector.detect()
        return ToolDetector.get_preferred_tool(desktop_type.value)

    @staticmethod
    def create_for_testing(
        implementation_class: Callable[..., IScreenshotCapture],
        temp_manager: Optional[TempFileManager] = None,
        **kwargs: Any
    ) -> IScreenshotCapture:
        """
        Create a specific implementation for testing purposes.

        Args:
            implementation_class: The class to instantiate
            temp_manager: TempFileManager instance
            **kwargs: Additional arguments for the implementation

        Returns:
            IScreenshotCapture implementation
        """
        if temp_manager is None:
            temp_manager = TempFileManager()

        return implementation_class(temp_manager=temp_manager, **kwargs)


# Convenience function
def create_screenshot_capture(
    image_format: str = "png",
    quality: int = 90,
    preferred_tool: Optional[str] = None
) -> IScreenshotCapture:
    """
    Convenience function to create screenshot capture implementation.

    Args:
        image_format: Image format ('png', 'jpg', 'jpeg')
        quality: Image quality (1-100, for JPEG)
        preferred_tool: Override auto-detection ('scrot', 'grim', 'import', 'auto')

    Returns:
        IScreenshotCapture implementation
    """
    return ScreenshotCaptureFactory.create(
        image_format=image_format,
        quality=quality,
        preferred_tool=preferred_tool
    )
