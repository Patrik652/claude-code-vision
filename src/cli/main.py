"""
Main CLI entry point for Claude Code Vision.

Aggregates all commands and provides the primary interface.
"""

import sys

import click

from src.cli.add_privacy_zone_command import add_privacy_zone, list_privacy_zones, remove_privacy_zone
from src.cli.doctor_command import doctor
from src.cli.init_command import init_config
from src.cli.list_monitors_command import list_monitors
from src.cli.test_capture_command import test_capture
from src.cli.validate_config_command import validate_config
from src.cli.vision_area_command import vision_area
from src.cli.vision_auto_command import vision_auto
from src.cli.vision_command import vision
from src.cli.vision_stop_command import vision_stop
from src.lib.logging_config import get_logger

logger = get_logger(__name__)


@click.group(invoke_without_command=True)
@click.version_option(version='0.1.0', prog_name='claude-vision')
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    Claude Code Vision - Screenshot analysis integration for Claude Code.

    Enables Claude to see and analyze your screen through custom slash commands.

    Examples:

        \b
        # First-time setup
        claude-vision --init
        claude-vision --doctor

        \b
        # Basic usage (from within Claude Code)
        /vision "What do you see?"
        /vision.area "Analyze this region"
        /vision.auto

        \b
        # Utility commands
        claude-vision --list-monitors
        claude-vision --validate-config
        claude-vision --test-capture
    """
    # If no command is provided, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Add all commands to the CLI group
cli.add_command(vision)
cli.add_command(vision_area)
cli.add_command(vision_auto)
cli.add_command(vision_stop)
cli.add_command(add_privacy_zone)
cli.add_command(list_privacy_zones)
cli.add_command(remove_privacy_zone)
cli.add_command(init_config)
cli.add_command(doctor)
cli.add_command(list_monitors)
cli.add_command(validate_config)
cli.add_command(test_capture)


def main() -> None:
    """Main entry point for the CLI."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        click.echo("\n\nInterrupted by user.", err=True)
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unhandled exception in CLI: {e}", exc_info=True)
        click.echo(f"\n❌ Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
