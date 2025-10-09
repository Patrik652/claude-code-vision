"""
--test-capture CLI command implementation.

Tests screenshot capture functionality and displays the result.
"""

import click
from pathlib import Path
import tempfile
import shutil

from src.services.screenshot_capture.factory import ScreenshotCaptureFactory
from src.services.config_manager import ConfigurationManager
from src.lib.tool_detector import get_preferred_tool
from src.lib.desktop_detector import detect_desktop_type
from src.lib.exceptions import ScreenshotCaptureError
from src.lib.logging_config import get_logger

logger = get_logger(__name__)


@click.command(name='test-capture')
@click.option(
    '--monitor',
    type=int,
    default=0,
    help='Monitor index to test (default: 0)'
)
@click.option(
    '--open',
    'open_file',
    is_flag=True,
    help='Open the captured screenshot after saving'
)
@click.pass_context
def test_capture(ctx, monitor: int, open_file: bool):
    """
    Test screenshot capture functionality.

    Captures a test screenshot and saves it to a temporary location.
    Useful for verifying that screenshot tools are working correctly
    and troubleshooting capture issues.

    Examples:

        \b
        # Test default monitor capture
        claude-vision --test-capture

        \b
        # Test specific monitor
        claude-vision --test-capture --monitor 1

        \b
        # Test and open the result
        claude-vision --test-capture --open
    """
    click.echo(click.style("\n📸 Testing Screenshot Capture", fg='cyan', bold=True))
    click.echo("="*80 + "\n")

    try:
        # Display system information
        click.echo(click.style("System Information:", fg='cyan', bold=True))

        desktop_type = detect_desktop_type()
        click.echo(f"  Desktop Environment: {desktop_type.value.upper()}")

        screenshot_tool = get_preferred_tool()
        if screenshot_tool:
            click.echo(click.style(f"  Screenshot Tool: {screenshot_tool.value}", fg='green'))
        else:
            click.echo(click.style(f"  Screenshot Tool: None detected", fg='red'))
            click.echo(click.style("\n⚠️  No screenshot tool found. Install scrot (X11) or grim (Wayland).", fg='yellow'))
            raise click.Abort()

        click.echo(f"  Monitor: {monitor}\n")

        # Load configuration
        config_manager = ConfigurationManager()
        config = config_manager.load_config()

        click.echo(click.style("Configuration:", fg='cyan', bold=True))
        click.echo(f"  Format: {config.screenshot.format}")
        click.echo(f"  Quality: {config.screenshot.quality}")
        click.echo(f"  Max Size: {config.screenshot.max_size_mb} MB")
        click.echo(f"  Tool Override: {config.screenshot.tool}\n")

        # Attempt capture
        click.echo(click.style("Capturing screenshot...", fg='green'))

        screenshot_capture = ScreenshotCaptureFactory.create(
            image_format=config.screenshot.format,
            quality=config.screenshot.quality
        )
        screenshot = screenshot_capture.capture_full_screen(monitor=monitor)
        screenshot_path = screenshot.file_path

        click.echo(click.style("✓ Capture successful!", fg='green', bold=True))

        # Display file information
        file_size_mb = screenshot_path.stat().st_size / (1024 * 1024)
        click.echo(f"\nScreenshot saved to: {click.style(str(screenshot_path), fg='cyan')}")
        click.echo(f"File size: {file_size_mb:.2f} MB")

        # Verify image can be opened
        try:
            from PIL import Image
            img = Image.open(screenshot_path)
            click.echo(f"Dimensions: {img.width}x{img.height}")
            click.echo(f"Mode: {img.mode}")
            click.echo(f"Format: {img.format}")
        except Exception as e:
            click.echo(click.style(f"⚠️  Could not read image metadata: {e}", fg='yellow'))

        # Check file size against limit
        if file_size_mb > config.screenshot.max_size_mb:
            click.echo(click.style(f"\n⚠️  Warning: Screenshot exceeds max size limit ({config.screenshot.max_size_mb} MB)", fg='yellow'))
            click.echo(click.style(f"   Consider reducing quality or max_size_mb in config", fg='yellow'))

        # Open file if requested
        if open_file:
            click.echo(f"\nOpening screenshot...")
            try:
                import subprocess
                if shutil.which('xdg-open'):
                    subprocess.run(['xdg-open', str(screenshot_path)], check=False)
                elif shutil.which('open'):  # macOS
                    subprocess.run(['open', str(screenshot_path)], check=False)
                else:
                    click.echo(click.style("⚠️  Could not find image viewer (xdg-open)", fg='yellow'))
            except Exception as e:
                click.echo(click.style(f"⚠️  Could not open image: {e}", fg='yellow'))

        # Success summary
        click.echo("\n" + "="*80)
        click.echo(click.style("✓ Screenshot capture is working correctly!", fg='green', bold=True))
        click.echo("\nYou can now use:")
        click.echo(click.style('  /vision "What do you see?"', fg='cyan'))
        click.echo(click.style('  /vision.area "Analyze this region"', fg='cyan'))
        click.echo(click.style('  /vision.auto', fg='cyan'))
        click.echo("="*80 + "\n")

    except ScreenshotCaptureError as e:
        click.echo(click.style(f"\n❌ Screenshot capture failed: {e}", fg='red'))
        click.echo("\n" + click.style("Troubleshooting:", fg='cyan', bold=True))
        click.echo("  1. Run diagnostics: claude-vision --doctor")
        click.echo("  2. Check if screenshot tool is installed:")
        click.echo("     • X11: sudo apt install scrot")
        click.echo("     • Wayland: sudo apt install grim")
        click.echo("  3. Verify monitor index with: claude-vision --list-monitors")
        raise click.Abort()

    except Exception as e:
        logger.error(f"Unexpected error in test-capture: {e}", exc_info=True)
        click.echo(click.style(f"\n❌ Unexpected error: {e}", fg='red'))
        raise click.Abort()
