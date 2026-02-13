"""
CLI Command Handler for /vision command.

Implements the /vision command using Click framework.
Handles user input, error reporting, and output formatting.
"""

import sys
from typing import Optional

import click

from src.interfaces.screenshot_service import IClaudeAPIClient
from src.lib.exceptions import (
    AuthenticationError,
    ConfigurationError,
    DisplayNotAvailableError,
    OAuthConfigNotFoundError,
    ScreenshotCaptureError,
    VisionCommandError,
)
from src.lib.logging_config import get_logger, setup_logging
from src.services.claude_api_client import AnthropicAPIClient
from src.services.config_manager import ConfigurationManager
from src.services.gemini_api_client import GeminiAPIClient
from src.services.image_processor import PillowImageProcessor
from src.services.screenshot_capture.factory import ScreenshotCaptureFactory
from src.services.temp_file_manager import TempFileManager
from src.services.vision_service import VisionService

logger = get_logger(__name__)


def get_vision_service() -> VisionService:
    """
    Create and configure VisionService with all dependencies.

    Returns:
        Configured VisionService instance

    Raises:
        VisionCommandError: If service creation fails
    """
    try:
        # Load configuration
        config_manager = ConfigurationManager()
        config = config_manager.load_config()

        # Setup logging
        setup_logging(
            level=config.logging.level,
            log_file=config.logging.file,
            max_size_mb=config.logging.max_size_mb,
            backup_count=config.logging.backup_count
        )

        # Create temp file manager
        temp_manager = TempFileManager(
            temp_dir=config.temp.directory,
            cleanup_enabled=config.temp.cleanup,
            keep_on_error=config.temp.keep_on_error
        )

        # Create screenshot capture implementation
        capture = ScreenshotCaptureFactory.create(
            temp_manager=temp_manager,
            image_format=config.screenshot.format,
            quality=config.screenshot.quality,
            preferred_tool=config.screenshot.tool
        )

        # Create image processor
        processor = PillowImageProcessor(temp_manager=temp_manager)

        # Create API clients (try both, use whichever is configured)
        claude_client = None
        gemini_client = None

        # Try to create Claude client
        try:
            claude_client = AnthropicAPIClient(
                oauth_token_path=config.claude_code.oauth_token_path,
                api_endpoint=config.claude_code.api_endpoint
            )
            logger.debug("Claude API client initialized")
        except Exception as e:
            logger.debug(f"Claude API client not available: {e}")

        # Try to create Gemini client
        try:
            gemini_api_key = config.gemini.api_key if config.gemini.api_key else None
            logger.debug(f"Gemini API key from config: {gemini_api_key[:10] if gemini_api_key else 'None'}...{gemini_api_key[-5:] if gemini_api_key else ''} (length: {len(gemini_api_key) if gemini_api_key else 0})")
            gemini_client = GeminiAPIClient(
                api_key=gemini_api_key,
                model_name=config.gemini.model
            )
            logger.debug("Gemini API client initialized")
        except Exception as e:
            logger.debug(f"Gemini API client not available: {e}")

        # Use primary provider as api_client
        api_client: Optional[IClaudeAPIClient] = None
        if config.ai_provider.provider.lower() == 'gemini' and gemini_client:
            api_client = gemini_client
        elif config.ai_provider.provider.lower() == 'claude' and claude_client:
            api_client = claude_client
        elif gemini_client:
            api_client = gemini_client
        elif claude_client:
            api_client = claude_client
        else:
            raise VisionCommandError(
                "No API client configured. Please set either Gemini API key or Claude API key in config.yaml"
            )

        # Create vision service
        return VisionService(
            config_manager=config_manager,
            temp_manager=temp_manager,
            capture=capture,
            processor=processor,
            api_client=api_client,
            session_manager=None,  # Not yet implemented
            gemini_client=gemini_client
        )


    except Exception as e:
        logger.error(f"Failed to create vision service: {e}")
        raise VisionCommandError(f"Failed to initialize vision service: {e}") from e


@click.command()
@click.argument('prompt', required=True)
@click.option('--monitor', type=int, default=None, help='Monitor index to capture (default: from config)')
def vision(prompt: str, monitor: Optional[int] = None) -> None:  # noqa: PLR0915
    """
    Capture screenshot and analyze with Claude.

    PROMPT: The question or instruction for Claude about the screenshot.

    Examples:
        vision "What do you see in this screenshot?"
        vision "Describe the application shown"
        vision "What errors are visible on screen?"
        vision --monitor 1 "What's on my second screen?"
    """
    try:
        # Create vision service
        service = get_vision_service()

        # Override monitor if specified
        if monitor is not None:
            # Temporarily override the config
            config = service.config_manager.load_config()
            config.monitors.default = monitor

        # Execute vision command
        click.echo("📸 Capturing screenshot...", err=True)
        response = service.execute_vision_command(prompt)

        # Output response
        click.echo("\n" + "="*60)
        click.echo("Claude's Response:")
        click.echo("="*60 + "\n")
        click.echo(response)

        sys.exit(0)

    except DisplayNotAvailableError as e:
        click.echo("❌ Error: No display available", err=True)
        click.echo(f"\n{e}", err=True)
        click.echo("\nMake sure you're running in a graphical environment with DISPLAY or WAYLAND_DISPLAY set.", err=True)
        sys.exit(1)

    except ScreenshotCaptureError as e:
        click.echo("❌ Error: Screenshot capture failed", err=True)
        click.echo(f"\n{e}", err=True)
        click.echo("\nPossible solutions:", err=True)
        click.echo("  - Install a screenshot tool: scrot (X11), grim (Wayland), or imagemagick", err=True)
        click.echo("  - On Ubuntu/Debian: sudo apt install scrot", err=True)
        sys.exit(1)

    except OAuthConfigNotFoundError as e:
        click.echo("❌ Error: Claude Code authentication not configured", err=True)
        click.echo(f"\n{e}", err=True)
        click.echo("\nPlease configure Claude Code with your API key:", err=True)
        click.echo("  1. Get your API key from https://console.anthropic.com/", err=True)
        click.echo("  2. Save it in ~/.claude/config.json:", err=True)
        click.echo('     {"api_key": "your-api-key-here"}', err=True)
        sys.exit(1)

    except AuthenticationError as e:
        click.echo("❌ Error: Authentication failed", err=True)
        click.echo(f"\n{e}", err=True)
        click.echo("\nYour API key may be invalid or expired.", err=True)
        click.echo("Please check your ~/.claude/config.json file.", err=True)
        sys.exit(1)

    except ConfigurationError as e:
        click.echo("❌ Error: Configuration invalid", err=True)
        click.echo(f"\n{e}", err=True)
        click.echo("\nPlease check your configuration file:", err=True)
        click.echo("  ~/.config/claude-code-vision/config.yaml", err=True)
        sys.exit(1)

    except VisionCommandError as e:
        click.echo("❌ Error: Vision command failed", err=True)
        click.echo(f"\n{e}", err=True)
        sys.exit(1)

    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Interrupted by user", err=True)
        sys.exit(130)

    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        logger.exception("Unexpected error in vision command")
        sys.exit(1)


if __name__ == '__main__':
    vision()
