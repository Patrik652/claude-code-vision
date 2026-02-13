"""
CLI Command Handler for --list-monitors command.

Implements the --list-monitors command to display available monitors.
"""

import sys

import click

from src.lib.exceptions import VisionCommandError
from src.lib.logging_config import get_logger, setup_logging
from src.services.config_manager import ConfigurationManager
from src.services.screenshot_capture.factory import ScreenshotCaptureFactory
from src.services.temp_file_manager import TempFileManager

logger = get_logger(__name__)


@click.command()
def list_monitors() -> None:
    """
    List all available monitors with their details.

    Shows monitor index, resolution, and position for each detected monitor.
    Helps users identify which monitor to use with --monitor flag.
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

        # Create temp manager and screenshot capture
        temp_manager = TempFileManager(
            temp_dir=config.temp.directory,
            cleanup_enabled=config.temp.cleanup,
            keep_on_error=config.temp.keep_on_error
        )

        capture = ScreenshotCaptureFactory.create(
            temp_manager=temp_manager,
            image_format=config.screenshot.format,
            quality=config.screenshot.quality,
            preferred_tool=config.screenshot.tool
        )

        # Get monitor information
        click.echo("\n" + "="*60)
        click.echo("Available Monitors")
        click.echo("="*60 + "\n")

        # Try to get monitor info from the capture implementation
        if hasattr(capture, '_detect_monitors'):
            monitors = capture._detect_monitors()

            if not monitors:
                click.echo("⚠️  No monitors detected")
                click.echo("\nThis might indicate:")
                click.echo("  • No display server running (DISPLAY/WAYLAND_DISPLAY not set)")
                click.echo("  • Monitor detection tools not available")
                sys.exit(1)

            for idx, monitor in enumerate(monitors):
                is_default = "⭐ DEFAULT" if idx == config.monitors.default else ""
                click.echo(f"Monitor {idx}: {is_default}")
                click.echo(f"  Resolution: {monitor['width']}x{monitor['height']}")
                click.echo(f"  Position:   ({monitor['x']}, {monitor['y']})")
                click.echo()

            click.echo(f"Total monitors: {len(monitors)}")
            click.echo(f"Default monitor: {config.monitors.default}")
            click.echo("\nTo capture from a specific monitor, use:")
            click.echo("  claude-vision vision --monitor <number> \"your prompt\"")
        else:
            click.echo("⚠️  Monitor detection not supported by current capture method")
            click.echo("\nUsing fallback capture method. Multi-monitor support requires:")
            click.echo("  • scrot (X11) or grim (Wayland)")
            sys.exit(1)

        sys.exit(0)

    except VisionCommandError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)

    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Interrupted by user", err=True)
        sys.exit(130)

    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        logger.exception("Unexpected error in list-monitors command")
        sys.exit(1)


if __name__ == '__main__':
    list_monitors()
