"""
/vision.area CLI command implementation.

Handles area-based screenshot capture with optional coordinate specification.
"""

from typing import Optional, Tuple

import click

from src.lib.exceptions import (
    InvalidRegionError,
    RegionSelectionCancelledError,
    SelectionToolNotFoundError,
    VisionCommandError,
)
from src.lib.logging_config import get_logger
from src.models.entities import CaptureRegion
from src.services.vision_service import VisionService

logger = get_logger(__name__)


def parse_coordinates(coords_str: str) -> Tuple[int, int, int, int]:
    """
    Parse coordinate string to tuple.

    Args:
        coords_str: Coordinate string in format "x,y,width,height"

    Returns:
        Tuple of (x, y, width, height)

    Raises:
        ValueError: If format is invalid
    """
    try:
        parts = coords_str.split(',')
        if len(parts) != 4:
            raise ValueError("Coordinates must be in format: x,y,width,height")

        x, y, width, height = map(int, parts)
        return (x, y, width, height)

    except ValueError as e:
        raise ValueError(f"Invalid coordinates format: {e}") from e


@click.command(name='area')
@click.argument('prompt', type=str)
@click.option(
    '--coords',
    type=str,
    help='Region coordinates in format "x,y,width,height" (e.g., "100,100,800,600")'
)
@click.option(
    '--monitor',
    type=int,
    default=0,
    help='Monitor index to capture from (default: 0 = primary)'
)
@click.pass_context
def vision_area(  # noqa: PLR0912, PLR0915
    ctx: click.Context,
    prompt: str,
    coords: Optional[str],
    monitor: int
) -> None:
    """
    Capture a specific screen region and analyze with Claude.

    Without --coords: Launches graphical selection tool (slurp/xrectsel/slop)
    With --coords: Uses provided coordinates directly

    Examples:

        \b
        # Graphical selection (interactive)
        /vision.area "What's in this region?"

        \b
        # Coordinate-based selection
        /vision.area --coords "100,100,800,600" "What's in this region?"

        \b
        # Select from secondary monitor
        /vision.area --monitor 1 "What's on my second screen?"
    """
    try:
        # Get VisionService from context
        vision_service: VisionService = ctx.obj.get('vision_service')

        if vision_service is None:
            click.echo(click.style("Error: Vision service not initialized", fg='red'))
            raise click.Abort()

        # Parse coordinates if provided
        region = None
        if coords:
            try:
                x, y, width, height = parse_coordinates(coords)
                region = CaptureRegion(
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    monitor=monitor,
                    selection_method='coordinates'
                )
                logger.info(f"Using coordinates: {width}x{height} at ({x},{y}) on monitor {monitor}")

            except ValueError as e:
                click.echo(click.style(f"Error: {e}", fg='red'))
                raise click.Abort() from e

        # Execute vision area command
        click.echo("Analyzing screen region...")

        try:
            response = vision_service.execute_vision_area_command(
                prompt=prompt,
                region=region
            )

            # Display response
            click.echo("\n" + "="*80)
            click.echo(click.style("Claude's Analysis:", fg='green', bold=True))
            click.echo("="*80)
            click.echo(response)
            click.echo("="*80 + "\n")

        except (SelectionToolNotFoundError, RegionSelectionCancelledError) as e:
            # Fallback: prompt for coordinate input
            if region is None:  # Only fallback if user didn't provide coords
                click.echo(click.style(f"\n{e}", fg='yellow'))
                click.echo(click.style("\nFalling back to coordinate input...", fg='yellow'))

                if click.confirm("Would you like to enter coordinates manually?", default=True):
                    coords_input = click.prompt(
                        "Enter coordinates (format: x,y,width,height)",
                        type=str
                    )

                    try:
                        x, y, width, height = parse_coordinates(coords_input)
                        region = CaptureRegion(
                            x=x,
                            y=y,
                            width=width,
                            height=height,
                            monitor=monitor,
                            selection_method='coordinates'
                        )

                        # Retry with coordinates
                        click.echo("Analyzing screen region...")
                        response = vision_service.execute_vision_area_command(
                            prompt=prompt,
                            region=region
                        )

                        # Display response
                        click.echo("\n" + "="*80)
                        click.echo(click.style("Claude's Analysis:", fg='green', bold=True))
                        click.echo("="*80)
                        click.echo(response)
                        click.echo("="*80 + "\n")

                    except ValueError as parse_error:
                        click.echo(click.style(f"\nError: {parse_error}", fg='red'))
                        raise click.Abort() from e
                else:
                    click.echo(click.style("Operation cancelled", fg='yellow'))
                    raise click.Abort() from e
            else:
                # User provided coords but still failed - re-raise
                raise

    except RegionSelectionCancelledError:
        # This is now handled above in the fallback logic
        pass

    except SelectionToolNotFoundError:
        # This is now handled above in the fallback logic
        pass

    except InvalidRegionError as e:
        click.echo(click.style(f"\nError: Invalid region - {e}", fg='red'))
        raise click.Abort() from e

    except VisionCommandError as e:
        click.echo(click.style(f"\nError: {e}", fg='red'))
        raise click.Abort() from e

    except Exception as e:
        logger.error(f"Unexpected error in /vision.area command: {e}", exc_info=True)
        click.echo(click.style(f"\nUnexpected error: {e}", fg='red'))
        raise click.Abort() from e
