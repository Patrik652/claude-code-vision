"""
/vision.stop CLI command implementation.

Handles stopping active auto-monitoring sessions.
"""

import click

from src.lib.exceptions import VisionCommandError
from src.lib.logging_config import get_logger
from src.services.vision_service import VisionService

logger = get_logger(__name__)


@click.command(name='stop')
@click.pass_context
def vision_stop(ctx: click.Context) -> None:
    """
    Stop the active auto-monitoring session.

    Stops the background monitoring session started with /vision.auto,
    cleanly terminating the capture loop and freeing resources.

    Examples:

        \b
        # Stop active monitoring session
        /vision.stop
    """
    try:
        # Get VisionService from context
        vision_service: VisionService = ctx.obj.get('vision_service')

        if vision_service is None:
            click.echo(click.style("Error: Vision service not initialized", fg='red'))
            raise click.Abort()

        # Display stopping message
        click.echo(click.style("\n⏹️  Stopping auto-monitoring session...", fg='yellow', bold=True))

        # Stop monitoring session
        vision_service.execute_vision_stop_command()

        # Display success message
        click.echo(click.style("\n✓ Monitoring session stopped successfully!", fg='green', bold=True))
        click.echo("\nThe background capture loop has been terminated.")
        click.echo("All resources have been cleaned up.")
        click.echo("\n" + "="*80)
        click.echo(click.style("To start a new session:", fg='cyan', bold=True))
        click.echo(click.style("  /vision.auto", fg='cyan'))
        click.echo("="*80 + "\n")

    except VisionCommandError as e:
        click.echo(click.style(f"\n❌ Error: {e}", fg='red'))

        # Check if it's a "no active session" error
        if "no active" in str(e).lower() or "not found" in str(e).lower():
            click.echo("\n" + click.style("No monitoring session is currently active.", fg='yellow'))
            click.echo("\n" + click.style("Start a new session with:", fg='cyan'))
            click.echo(click.style("  /vision.auto", fg='cyan'))

        raise click.Abort() from e

    except Exception as e:
        logger.error(f"Unexpected error in /vision.stop command: {e}", exc_info=True)
        click.echo(click.style(f"\n❌ Unexpected error: {e}", fg='red'))
        raise click.Abort() from e
