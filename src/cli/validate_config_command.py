"""
--validate-config CLI command implementation.

Validates configuration file and reports any issues.
"""

from pathlib import Path
from typing import Optional

import click

from src.lib.exceptions import ConfigurationError
from src.lib.logging_config import get_logger
from src.services.config_manager import ConfigurationManager

logger = get_logger(__name__)


@click.command(name='validate-config')
@click.option(
    '--path',
    type=click.Path(exists=True),
    default=None,
    help='Path to config file (default: ~/.config/claude-code-vision/config.yaml)'
)
@click.pass_context
def validate_config(_ctx: click.Context, path: Optional[str]) -> None:  # noqa: PLR0912, PLR0915
    """
    Validate configuration file.

    Checks configuration for errors, invalid values, and potential issues.
    Reports detailed validation results.

    Examples:

        \b
        # Validate default config
        claude-vision --validate-config

        \b
        # Validate custom config
        claude-vision --validate-config --path /path/to/config.yaml
    """
    click.echo(click.style("\n✓ Configuration Validation", fg='cyan', bold=True))
    click.echo("="*80 + "\n")

    try:
        # Determine config path
        config_path = Path(path).expanduser().absolute() if path else ConfigurationManager.DEFAULT_CONFIG_PATH

        click.echo(f"Validating: {click.style(str(config_path), fg='cyan')}\n")

        # Check if file exists
        if not config_path.exists():
            click.echo(click.style("✗ Configuration file not found", fg='red', bold=True))
            click.echo(f"\nExpected location: {config_path}")
            click.echo(click.style("\nCreate config with: claude-vision --init", fg='yellow'))
            raise click.Abort()

        # Load and validate configuration
        config_manager = ConfigurationManager(config_path)
        config = config_manager.load_config()

        click.echo(click.style("Loading configuration...", fg='green'))

        # Perform validation
        try:
            config_manager.validate_config(config)
            click.echo(click.style("✓ Configuration is valid!", fg='green', bold=True))
        except ConfigurationError as e:
            click.echo(click.style("✗ Validation failed:", fg='red', bold=True))
            click.echo(click.style(str(e), fg='red'))
            raise click.Abort() from e

        # Display configuration details
        click.echo("\n" + "="*80)
        click.echo(click.style("Configuration Details:", fg='cyan', bold=True))
        click.echo("="*80)

        click.echo("\n📸 Screenshot:")
        click.echo(f"  Format: {config.screenshot.format}")
        click.echo(f"  Quality: {config.screenshot.quality}")
        click.echo(f"  Max size: {config.screenshot.max_size_mb} MB")
        click.echo(f"  Tool: {config.screenshot.tool}")

        click.echo("\n🖥️  Monitors:")
        click.echo(f"  Default: {config.monitors.default}")

        click.echo("\n📐 Area Selection:")
        click.echo(f"  Tool: {config.area_selection.tool}")
        click.echo(f"  Show coordinates: {config.area_selection.show_coordinates}")

        click.echo("\n🔒 Privacy:")
        click.echo(f"  Enabled: {config.privacy.enabled}")
        click.echo(f"  First-use prompt: {config.privacy.prompt_first_use}")
        click.echo(f"  Privacy zones: {len(config.privacy.zones)}")
        if config.privacy.zones:
            for i, zone in enumerate(config.privacy.zones, 1):
                click.echo(f"    {i}. {zone.name}: ({zone.x},{zone.y}) {zone.width}x{zone.height}")

        click.echo("\n🔄 Monitoring:")
        click.echo(f"  Interval: {config.monitoring.interval_seconds} seconds")
        click.echo(f"  Max duration: {config.monitoring.max_duration_minutes} minutes")
        click.echo(f"  Idle pause: {config.monitoring.idle_pause_minutes} minutes")
        click.echo(f"  Change detection: {config.monitoring.change_detection}")

        click.echo("\n📁 Temp Files:")
        click.echo(f"  Directory: {config.temp.directory}")
        click.echo(f"  Cleanup: {config.temp.cleanup}")
        click.echo(f"  Keep on error: {config.temp.keep_on_error}")

        click.echo("\n📝 Logging:")
        click.echo(f"  Level: {config.logging.level}")
        click.echo(f"  File: {config.logging.file}")
        click.echo(f"  Max size: {config.logging.max_size_mb} MB")
        click.echo(f"  Backups: {config.logging.backup_count}")

        # Warnings and recommendations
        click.echo("\n" + "="*80)
        click.echo(click.style("Recommendations:", fg='cyan', bold=True))
        click.echo("="*80 + "\n")

        warnings = []

        # Check screenshot quality
        if config.screenshot.quality < 70:
            warnings.append("Screenshot quality is low (<70). May affect Claude's analysis.")

        # Check max size
        if config.screenshot.max_size_mb > 5:
            warnings.append("Max screenshot size is large (>5 MB). May slow down transmission.")

        # Check privacy zones
        if config.privacy.enabled and len(config.privacy.zones) == 0:
            warnings.append("Privacy enabled but no zones configured. Add zones with /vision.add-privacy-zone")

        # Check monitoring interval
        if config.monitoring.interval_seconds < 10:
            warnings.append("Monitoring interval is very short (<10s). May consume excessive resources.")

        # Check max duration
        if config.monitoring.max_duration_minutes > 60:
            warnings.append("Max monitoring duration is long (>60 min). Consider shorter sessions.")

        if warnings:
            for warning in warnings:
                click.echo(click.style(f"⚠️  {warning}", fg='yellow'))
        else:
            click.echo(click.style("✓ No issues found. Configuration looks good!", fg='green'))

        click.echo("\n" + "="*80 + "\n")

    except ConfigurationError as e:
        click.echo(click.style(f"\n❌ Configuration error: {e}", fg='red'))
        raise click.Abort() from e

    except Exception as e:
        logger.error(f"Unexpected error validating config: {e}", exc_info=True)
        click.echo(click.style(f"\n❌ Unexpected error: {e}", fg='red'))
        raise click.Abort() from e
