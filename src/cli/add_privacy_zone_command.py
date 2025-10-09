"""
Add Privacy Zone CLI command implementation.

Interactive helper for adding privacy zones to configuration.
"""

import click
from pathlib import Path

from src.services.config_manager import ConfigurationManager
from src.models.entities import PrivacyZone
from src.lib.exceptions import ConfigurationError
from src.lib.logging_config import get_logger

logger = get_logger(__name__)


@click.command(name='add-privacy-zone')
@click.option(
    '--name',
    type=str,
    help='Name of the privacy zone (e.g., "Password Field", "API Keys")'
)
@click.option(
    '--x',
    type=int,
    help='Top-left X coordinate'
)
@click.option(
    '--y',
    type=int,
    help='Top-left Y coordinate'
)
@click.option(
    '--width',
    type=int,
    help='Width of the zone'
)
@click.option(
    '--height',
    type=int,
    help='Height of the zone'
)
@click.option(
    '--monitor',
    type=int,
    default=None,
    help='Monitor index (0 = primary, None = all monitors)'
)
@click.pass_context
def add_privacy_zone(ctx, name, x, y, width, height, monitor):
    """
    Add a privacy zone to protect sensitive screen areas.

    Privacy zones are black rectangles applied to screenshots BEFORE
    transmission to Claude API. Use this to protect passwords, API keys,
    personal information, or any sensitive data.

    Examples:

        \b
        # Interactive mode (recommended)
        /vision.add-privacy-zone

        \b
        # Non-interactive mode with all parameters
        /vision.add-privacy-zone --name "Password" --x 100 --y 200 --width 300 --height 50

        \b
        # Zone that applies to all monitors
        /vision.add-privacy-zone --name "Notifications" --x 1500 --y 900 --width 400 --height 180
    """
    try:
        # Get ConfigurationManager
        config_manager = ConfigurationManager()

        click.echo(click.style("\n=== Add Privacy Zone ===\n", fg='green', bold=True))

        # Interactive mode if parameters not provided
        if name is None:
            click.echo("Privacy zones are black rectangles that protect sensitive screen areas.")
            click.echo("They are applied BEFORE screenshots are sent to Claude API.\n")

            name = click.prompt(
                "Zone name (e.g., 'Password Field', 'API Keys')",
                type=str
            )

        if x is None:
            x = click.prompt(
                "Top-left X coordinate",
                type=int
            )

        if y is None:
            y = click.prompt(
                "Top-left Y coordinate",
                type=int
            )

        if width is None:
            width = click.prompt(
                "Width (pixels)",
                type=int
            )

        if height is None:
            height = click.prompt(
                "Height (pixels)",
                type=int
            )

        if monitor is None:
            monitor_input = click.prompt(
                "Monitor index (0 = primary, leave empty for all monitors)",
                type=str,
                default="",
                show_default=False
            )
            monitor = int(monitor_input) if monitor_input else None

        # Create privacy zone
        zone = PrivacyZone(
            name=name,
            x=x,
            y=y,
            width=width,
            height=height,
            monitor=monitor
        )

        # Validate zone
        try:
            zone.validate()
        except ValueError as e:
            click.echo(click.style(f"\nError: {e}", fg='red'))
            raise click.Abort()

        # Load current config
        config = config_manager.load_config()

        # Check for duplicate names
        if any(z.name == zone.name for z in config.privacy.zones):
            click.echo(click.style(f"\nWarning: Privacy zone '{zone.name}' already exists.", fg='yellow'))
            if not click.confirm("Replace existing zone?", default=False):
                click.echo("Operation cancelled.")
                raise click.Abort()
            # Remove existing zone with same name
            config.privacy.zones = [z for z in config.privacy.zones if z.name != zone.name]

        # Add zone to config
        config.privacy.zones.append(zone)

        # Enable privacy zones if not already enabled
        if not config.privacy.enabled:
            click.echo(click.style("\nPrivacy zones are currently disabled.", fg='yellow'))
            if click.confirm("Enable privacy zones?", default=True):
                config.privacy.enabled = True
                click.echo(click.style("Privacy zones enabled.", fg='green'))

        # Save config
        config_manager.save_config(config)

        # Display summary
        click.echo(click.style("\n✓ Privacy zone added successfully!", fg='green', bold=True))
        click.echo(f"\nZone details:")
        click.echo(f"  Name: {zone.name}")
        click.echo(f"  Position: ({zone.x}, {zone.y})")
        click.echo(f"  Size: {zone.width}x{zone.height}")
        click.echo(f"  Monitor: {zone.monitor if zone.monitor is not None else 'All monitors'}")

        click.echo(f"\nTotal privacy zones configured: {len(config.privacy.zones)}")

        # Helpful tip
        click.echo(click.style("\nTip:", fg='cyan', bold=True))
        click.echo("  To test the privacy zone, run:")
        click.echo(click.style("    /vision \"Test my privacy zones\"", fg='cyan'))

    except ConfigurationError as e:
        click.echo(click.style(f"\nConfiguration error: {e}", fg='red'))
        raise click.Abort()

    except Exception as e:
        logger.error(f"Unexpected error in add-privacy-zone command: {e}", exc_info=True)
        click.echo(click.style(f"\nUnexpected error: {e}", fg='red'))
        raise click.Abort()


@click.command(name='list-privacy-zones')
@click.pass_context
def list_privacy_zones(ctx):
    """
    List all configured privacy zones.

    Shows current privacy zone configuration with details.
    """
    try:
        config_manager = ConfigurationManager()
        config = config_manager.load_config()

        click.echo(click.style("\n=== Privacy Zones Configuration ===\n", fg='green', bold=True))

        # Show privacy status
        status = "Enabled" if config.privacy.enabled else "Disabled"
        status_color = 'green' if config.privacy.enabled else 'red'
        click.echo(f"Privacy protection: {click.style(status, fg=status_color, bold=True)}")

        # Show zones
        if not config.privacy.zones:
            click.echo("\nNo privacy zones configured.")
            click.echo(click.style("\nTip: Add a privacy zone with /vision.add-privacy-zone", fg='cyan'))
        else:
            click.echo(f"\nConfigured zones ({len(config.privacy.zones)}):\n")
            for i, zone in enumerate(config.privacy.zones, 1):
                click.echo(f"{i}. {click.style(zone.name, fg='cyan', bold=True)}")
                click.echo(f"   Position: ({zone.x}, {zone.y})")
                click.echo(f"   Size: {zone.width}x{zone.height}")
                monitor_text = str(zone.monitor) if zone.monitor is not None else "All"
                click.echo(f"   Monitor: {monitor_text}")
                click.echo()

    except Exception as e:
        logger.error(f"Error listing privacy zones: {e}", exc_info=True)
        click.echo(click.style(f"\nError: {e}", fg='red'))
        raise click.Abort()


@click.command(name='remove-privacy-zone')
@click.argument('zone_name', type=str)
@click.pass_context
def remove_privacy_zone(ctx, zone_name):
    """
    Remove a privacy zone by name.

    ZONE_NAME: Name of the privacy zone to remove
    """
    try:
        config_manager = ConfigurationManager()
        config = config_manager.load_config()

        # Find zone
        zone = None
        for z in config.privacy.zones:
            if z.name == zone_name:
                zone = z
                break

        if zone is None:
            click.echo(click.style(f"\nError: Privacy zone '{zone_name}' not found.", fg='red'))
            click.echo("\nAvailable zones:")
            for z in config.privacy.zones:
                click.echo(f"  - {z.name}")
            raise click.Abort()

        # Confirm removal
        click.echo(f"\nRemoving privacy zone: {click.style(zone.name, fg='yellow', bold=True)}")
        click.echo(f"  Position: ({zone.x}, {zone.y})")
        click.echo(f"  Size: {zone.width}x{zone.height}")

        if not click.confirm("\nAre you sure?", default=False):
            click.echo("Operation cancelled.")
            raise click.Abort()

        # Remove zone
        config.privacy.zones = [z for z in config.privacy.zones if z.name != zone_name]

        # Save config
        config_manager.save_config(config)

        click.echo(click.style(f"\n✓ Privacy zone '{zone_name}' removed successfully!", fg='green'))
        click.echo(f"Remaining zones: {len(config.privacy.zones)}")

    except Exception as e:
        logger.error(f"Error removing privacy zone: {e}", exc_info=True)
        click.echo(click.style(f"\nError: {e}", fg='red'))
        raise click.Abort()
