"""
Vision Service Implementation.

High-level service orchestrating all vision operations.
Composes all other services to implement user-facing commands.
Implements IVisionService interface.
"""

from typing import Optional
from uuid import UUID

from src.interfaces.screenshot_service import (
    IClaudeAPIClient,
    IConfigurationManager,
    IImageProcessor,
    IMonitoringSessionManager,
    IRegionSelector,
    IScreenshotCapture,
    ITempFileManager,
    IVisionService,
)
from src.lib.exceptions import SessionAlreadyActiveError, VisionCommandError
from src.lib.logging_config import get_logger
from src.models.entities import CaptureRegion

logger = get_logger(__name__)


class VisionService(IVisionService):
    """
    High-level vision service orchestrating all operations.

    Coordinates:
    - Screenshot capture
    - Image processing (privacy + optimization)
    - API communication
    - Temp file cleanup
    - Monitoring sessions
    """

    def __init__(
        self,
        config_manager: IConfigurationManager,
        temp_manager: ITempFileManager,
        capture: IScreenshotCapture,
        processor: IImageProcessor,
        api_client: IClaudeAPIClient,
        region_selector: Optional[IRegionSelector] = None,
        session_manager: Optional[IMonitoringSessionManager] = None,
        gemini_client: Optional[IClaudeAPIClient] = None
    ):
        """
        Initialize VisionService.

        Args:
            config_manager: Configuration manager
            temp_manager: Temp file manager
            capture: Screenshot capture implementation
            processor: Image processor
            api_client: Claude API client (can also be Gemini client)
            region_selector: Region selector for area selection (optional)
            session_manager: Monitoring session manager (optional)
            gemini_client: Gemini API client for fallback (optional)
        """
        self.config_manager = config_manager
        self.temp_manager = temp_manager
        self.capture = capture
        self.processor = processor
        self.claude_client = api_client
        self.gemini_client = gemini_client
        self.region_selector = region_selector
        self.session_manager = session_manager

        logger.info("VisionService initialized")

    def _get_api_client(self) -> IClaudeAPIClient:
        """
        Get the appropriate API client based on configuration.

        Returns:
            API client to use (Claude or Gemini)

        Raises:
            VisionCommandError: If no valid API client available
        """
        config = self.config_manager.load_config()
        provider = config.ai_provider.provider.lower()

        # Try primary provider
        if provider == 'gemini' and self.gemini_client:
            logger.info("Using Gemini API as primary provider")
            return self.gemini_client
        if provider == 'claude' and self.claude_client:
            logger.info("Using Claude API as primary provider")
            return self.claude_client

        # Try fallback if enabled
        if config.ai_provider.fallback_to_gemini:
            if provider == 'claude' and self.gemini_client:
                logger.warning("Claude API not available, falling back to Gemini")
                return self.gemini_client
            if provider == 'gemini' and self.claude_client:
                logger.warning("Gemini API not available, falling back to Claude")
                return self.claude_client

        # No valid client available
        raise VisionCommandError(
            f"No API client available for provider '{provider}'. "
            f"Please configure API key in config.yaml"
        )

    def _check_first_use_prompt(self) -> bool:
        """
        Check if first-use privacy prompt should be shown and handle user response.

        Returns:
            True if user accepts, False if user declines

        Raises:
            VisionCommandError: If user declines privacy prompt
        """
        config = self.config_manager.load_config()

        # Check if prompt needed
        if not config.privacy.prompt_first_use:
            return True

        logger.info("First-use privacy prompt required")

        # Display privacy information
        print("\n" + "="*80)
        print("CLAUDE CODE VISION - PRIVACY NOTICE")
        print("="*80)
        print("\nThis tool will:")
        print("  • Capture screenshots of your screen")
        print("  • Transmit screenshots to Claude API for analysis")
        print("  • Immediately delete screenshots after transmission")
        print("  • Never store screenshots permanently")
        print("\nPrivacy protection:")
        print("  • You can configure privacy zones to redact sensitive areas")
        print("  • Privacy zones are black rectangles applied BEFORE transmission")
        print("  • Use --add-privacy-zone command to configure redaction zones")
        print("\n" + "="*80)

        # Get user confirmation
        import click
        if not click.confirm("\nDo you understand and accept these privacy terms?", default=True):
            logger.info("User declined privacy terms")
            raise VisionCommandError("Privacy terms not accepted. Vision command cancelled.")

        # Update config to disable future prompts
        config.privacy.prompt_first_use = False
        self.config_manager.save_config(config)
        logger.info("First-use prompt accepted and disabled")

        return True

    def execute_vision_command(self, prompt: str) -> str:
        """
        Execute /vision command: capture full screen + send to Claude.

        Args:
            prompt: User's text prompt

        Returns:
            Claude's response

        Workflow:
            0. Check first-use privacy prompt (FR-013)
            1. Capture full screen
            2. Apply privacy zones (if configured)
            3. Optimize image
            4. Send to Claude API
            5. Cleanup temp files
            6. Return response

        Raises:
            VisionCommandError: If any step fails
        """
        logger.info(f"Executing /vision command: prompt length={len(prompt)}")

        try:
            # Step 0: First-use privacy prompt
            self._check_first_use_prompt()

            # Load configuration
            config = self.config_manager.load_config()

            # Step 1: Capture full screen
            logger.info("Step 1/5: Capturing full screen")
            screenshot = self.capture.capture_full_screen(monitor=config.monitors.default)
            logger.info(f"Screenshot captured: {screenshot.id}")

            # Step 2: Apply privacy zones (if configured)
            if config.privacy.enabled and config.privacy.zones:
                logger.info(f"Step 2/5: Applying {len(config.privacy.zones)} privacy zone(s)")
                screenshot = self.processor.apply_privacy_zones(screenshot, config.privacy.zones)
            else:
                logger.info("Step 2/5: Privacy zones disabled, skipping")

            # Step 3: Optimize image
            logger.info(f"Step 3/5: Optimizing image (max {config.screenshot.max_size_mb} MB)")
            screenshot = self.processor.optimize_image(screenshot, config.screenshot.max_size_mb)
            logger.info(f"Image optimized: {screenshot.optimized_size_bytes / (1024*1024):.2f} MB")

            # Step 4: Send to AI API (Claude or Gemini)
            api_client = self._get_api_client()
            logger.info("Step 4/5: Sending to AI API")
            response = api_client.send_multimodal_prompt(prompt, screenshot)
            logger.info(f"Response received: {len(response)} chars")

            # Step 5: Cleanup temp files
            logger.info("Step 5/5: Cleaning up temp files")
            self.temp_manager.cleanup_temp_file(screenshot.file_path)

            logger.info("Vision command completed successfully")
            return response

        except Exception as e:
            logger.error(f"Vision command failed: {e}")
            raise VisionCommandError(f"Failed to execute vision command: {e}") from e

    def execute_vision_area_command(self, prompt: str, region: Optional[CaptureRegion] = None) -> str:
        """
        Execute /vision.area command: capture region + send to Claude.

        Args:
            prompt: User's text prompt
            region: Pre-defined region, or None to trigger graphical selection

        Returns:
            Claude's response

        Workflow:
            1. Select region (graphical or coordinates)
            2. Capture selected region
            3. Apply privacy zones (if configured)
            4. Optimize image
            5. Send to Claude API
            6. Cleanup temp files
            7. Return response

        Raises:
            VisionCommandError: If any step fails
        """
        logger.info(f"Executing /vision.area command: prompt length={len(prompt)}")

        try:
            # Load configuration
            config = self.config_manager.load_config()

            # Step 1: Select region (if not provided)
            if region is None:
                if self.region_selector is None:
                    raise VisionCommandError(
                        "Region selector not available. "
                        "Please provide region coordinates using --coords option."
                    )

                logger.info("Step 1/6: Launching graphical region selection")
                region = self.region_selector.select_region_graphical(monitor=config.monitors.default)
                logger.info(f"Region selected: {region.width}x{region.height} at ({region.x},{region.y})")
            else:
                logger.info("Step 1/6: Using provided region coordinates")

            # Step 2: Capture region
            logger.info(f"Step 2/6: Capturing region: {region.width}x{region.height}")
            screenshot = self.capture.capture_region(region)
            logger.info(f"Region screenshot captured: {screenshot.id}")

            # Step 3: Apply privacy zones (if configured)
            if config.privacy.enabled and config.privacy.zones:
                logger.info(f"Step 3/6: Applying {len(config.privacy.zones)} privacy zone(s)")
                screenshot = self.processor.apply_privacy_zones(screenshot, config.privacy.zones)
            else:
                logger.info("Step 3/6: Privacy zones disabled, skipping")

            # Step 4: Optimize image
            logger.info(f"Step 4/6: Optimizing image (max {config.screenshot.max_size_mb} MB)")
            screenshot = self.processor.optimize_image(screenshot, config.screenshot.max_size_mb)

            # Step 5: Send to AI API (Claude or Gemini)
            api_client = self._get_api_client()
            logger.info("Step 5/6: Sending to AI API")
            response = api_client.send_multimodal_prompt(prompt, screenshot)
            logger.info(f"Response received: {len(response)} chars")

            # Step 6: Cleanup temp files
            logger.info("Step 6/6: Cleaning up temp files")
            self.temp_manager.cleanup_temp_file(screenshot.file_path)

            logger.info("Vision area command completed successfully")
            return response

        except Exception as e:
            logger.error(f"Vision area command failed: {e}")
            raise VisionCommandError(f"Failed to execute vision area command: {e}") from e

    def execute_vision_auto_command(self, interval_seconds: Optional[int] = None) -> UUID:
        """
        Execute /vision.auto command: start monitoring session.

        Args:
            interval_seconds: Override default interval, or None to use config

        Returns:
            Session ID of started monitoring session

        Workflow:
            1. Validate no active session
            2. Create monitoring session
            3. Start background capture loop
            4. Return session ID

        Raises:
            VisionCommandError: If session already active or start fails
        """
        logger.info(f"Executing /vision.auto command: interval={interval_seconds}")

        if self.session_manager is None:
            raise VisionCommandError("Monitoring session manager not available")

        try:
            # Load configuration
            config = self.config_manager.load_config()

            # Use config interval if not specified
            if interval_seconds is None:
                interval_seconds = config.monitoring.interval_seconds

            # Validate interval
            if interval_seconds <= 0:
                raise VisionCommandError("Interval must be positive")

            # Start session
            logger.info(f"Starting monitoring session with {interval_seconds}s interval")
            session = self.session_manager.start_session(interval_seconds)

            logger.info(f"Monitoring session started: {session.id}")
            return session.id

        except SessionAlreadyActiveError as e:
            raise VisionCommandError("A monitoring session is already active. Stop it first with /vision.stop") from e
        except Exception as e:
            logger.error(f"Failed to start monitoring session: {e}")
            raise VisionCommandError(f"Failed to start monitoring session: {e}") from e

    def execute_vision_stop_command(self) -> None:
        """
        Execute /vision.stop command: stop monitoring session.

        Workflow:
            1. Get active session
            2. Stop session
            3. Cleanup session resources

        Raises:
            VisionCommandError: If no active session
        """
        logger.info("Executing /vision.stop command")

        if self.session_manager is None:
            raise VisionCommandError("Monitoring session manager not available")

        try:
            # Get active session
            session = self.session_manager.get_active_session()

            if session is None:
                raise VisionCommandError("No active monitoring session to stop")

            # Stop session
            logger.info(f"Stopping monitoring session: {session.id}")
            self.session_manager.stop_session(session.id)

            logger.info("Monitoring session stopped successfully")

        except Exception as e:
            logger.error(f"Failed to stop monitoring session: {e}")
            raise VisionCommandError(f"Failed to stop monitoring session: {e}") from e
