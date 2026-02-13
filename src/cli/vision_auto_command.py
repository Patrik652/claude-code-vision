"""
/vision.auto CLI command implementation.

Handles auto-monitoring session start with configurable intervals.
"""

from typing import Optional

import click

from src.lib.exceptions import SessionAlreadyActiveError, VisionCommandError
from src.lib.logging_config import get_logger
from src.services.vision_service import VisionService

logger = get_logger(__name__)


@click.command(name='auto')
@click.option(
    '--interval',
    type=int,
    default=None,
    help='Capture interval in seconds (default: 30 from config)'
)
@click.option(
    '--monitor',
    type=int,
    default=0,
    help='Monitor index to capture from (default: 0 = primary)'
)
@click.pass_context
def vision_auto(ctx: click.Context, interval: Optional[int], monitor: int) -> None:
    """
    Start auto-monitoring session with periodic screenshot capture.

    Captures screenshots at regular intervals and sends them to Claude for
    continuous analysis. Session runs in the background until stopped with
    /vision.stop command.

    Features:
    - Configurable capture interval
    - Change detection (skip if screen unchanged)
    - Privacy zone redaction
    - Auto-stop after max duration (30 min default)
    - Pause on user idle

    Examples:

        \b
        # Start with default 30 second interval
        /vision.auto

        \b
        # Start with custom 60 second interval
        /vision.auto --interval 60

        \b
        # Monitor secondary display
        /vision.auto --monitor 1

    Stop the session:
        /vision.stop
    """
    try:
        # Get VisionService from context
        ctx_obj = ctx.obj or {}
        vision_service: Optional[VisionService] = ctx_obj.get('vision_service')

        if vision_service is None:
            click.echo(click.style("Error: Vision service not initialized", fg='red'))
            raise click.Abort()

        # Validate interval
        if interval is not None and interval <= 0:
            click.echo(click.style("Error: Interval must be positive", fg='red'))
            raise click.Abort()

        # Display start message
        interval_text = f"{interval}s" if interval else "default"
        click.echo(click.style("\n🚀 Starting auto-monitoring session...", fg='green', bold=True))
        click.echo(f"Interval: {interval_text}")
        click.echo(f"Monitor: {monitor}")

        # Start monitoring session
        session_id = vision_service.execute_vision_auto_command(interval_seconds=interval)

        # Display success message
        click.echo(click.style("\n✓ Monitoring session started!", fg='green', bold=True))
        click.echo(f"Session ID: {session_id}")
        click.echo("\nThe session is now running in the background.")
        click.echo("Screenshots will be captured and analyzed automatically.")
        click.echo("\n" + "="*80)
        click.echo(click.style("To stop the session:", fg='cyan', bold=True))
        click.echo(click.style("  /vision.stop", fg='cyan'))
        click.echo("="*80 + "\n")

    except SessionAlreadyActiveError as e:
        click.echo(click.style("\n❌ Cannot start monitoring session", fg='red', bold=True))
        click.echo(click.style(str(e), fg='yellow'))
        click.echo("\n" + click.style("Stop the active session first:", fg='cyan'))
        click.echo(click.style("  /vision.stop", fg='cyan'))
        raise click.Abort() from e

    except VisionCommandError as e:
        click.echo(click.style(f"\n❌ Error: {e}", fg='red'))
        raise click.Abort() from e

    except Exception as e:
        logger.error(f"Unexpected error in /vision.auto command: {e}", exc_info=True)
        click.echo(click.style(f"\n❌ Unexpected error: {e}", fg='red'))
        raise click.Abort() from e
