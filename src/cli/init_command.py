"""
--init CLI command implementation.

Generates default configuration file for Claude Code Vision.
"""

from pathlib import Path
from typing import Optional

import click

from src.lib.exceptions import ConfigurationError
from src.lib.logging_config import get_logger
from src.models.entities import Configuration
from src.services.config_manager import ConfigurationManager

logger = get_logger(__name__)


@click.command(name='init')
@click.option(
    '--force',
    is_flag=True,
    help='Overwrite existing configuration file'
)
@click.option(
    '--path',
    type=click.Path(),
    default=None,
    help='Custom config file path (default: ~/.config/claude-code-vision/config.yaml)'
)
@click.pass_context
def init_config(_ctx: click.Context, force: bool, path: Optional[str]) -> None:  # noqa: PLR0915
    """
    Initialize Claude Code Vision configuration.

    Creates a default configuration file with recommended settings.
    Use this command to get started quickly with sensible defaults.

    Examples:

        \b
        # Create config in default location
        claude-vision --init

        \b
        # Overwrite existing config
        claude-vision --init --force

        \b
        # Create config in custom location
        claude-vision --init --path /path/to/config.yaml
    """
    try:
        # Determine config path
        config_path = Path(path).expanduser().absolute() if path else ConfigurationManager.DEFAULT_CONFIG_PATH

        # Check if config already exists
        if config_path.exists() and not force:
            click.echo(click.style("\n⚠️  Configuration already exists:", fg='yellow', bold=True))
            click.echo(f"  {config_path}")
            click.echo("\nUse --force to overwrite, or edit the existing file.")
            raise click.Abort()

        # Create default configuration
        click.echo(click.style("\n📝 Creating configuration file...", fg='green', bold=True))

        config = Configuration()
        config_manager = ConfigurationManager(config_path)
        config_manager.save_config(config)

        click.echo(click.style("\n✓ Configuration created successfully!", fg='green', bold=True))
        click.echo(f"\nLocation: {click.style(str(config_path), fg='cyan')}")

        # Display configuration summary
        click.echo("\n" + "="*80)
        click.echo(click.style("Configuration Summary:", fg='green', bold=True))
        click.echo("="*80)
        click.echo("\n📸 Screenshot Settings:")
        click.echo(f"  Format: {config.screenshot.format}")
        click.echo(f"  Quality: {config.screenshot.quality}")
        click.echo(f"  Max size: {config.screenshot.max_size_mb} MB")
        click.echo(f"  Tool: {config.screenshot.tool}")

        click.echo("\n🖥️  Monitor Settings:")
        click.echo(f"  Default monitor: {config.monitors.default}")

        click.echo("\n🔒 Privacy Settings:")
        click.echo(f"  Enabled: {config.privacy.enabled}")
        click.echo(f"  First-use prompt: {config.privacy.prompt_first_use}")
        click.echo(f"  Privacy zones: {len(config.privacy.zones)}")

        click.echo("\n🔄 Auto-monitoring Settings:")
        click.echo(f"  Interval: {config.monitoring.interval_seconds} seconds")
        click.echo(f"  Max duration: {config.monitoring.max_duration_minutes} minutes")
        click.echo(f"  Change detection: {config.monitoring.change_detection}")

        click.echo("\n📝 Logging:")
        click.echo(f"  Level: {config.logging.level}")
        click.echo(f"  File: {config.logging.file}")

        # Display next steps
        click.echo("\n" + "="*80)
        click.echo(click.style("Next Steps:", fg='cyan', bold=True))
        click.echo("="*80)
        click.echo("\n1. Try your first screenshot analysis:")
        click.echo(click.style('   /vision "What do you see?"', fg='cyan'))

        click.echo("\n2. Configure privacy zones (optional):")
        click.echo(click.style('   /vision.add-privacy-zone', fg='cyan'))

        click.echo("\n3. Edit configuration file:")
        click.echo(click.style(f'   {config_path}', fg='cyan'))

        click.echo("\n4. Run diagnostics:")
        click.echo(click.style('   claude-vision --doctor', fg='cyan'))

        click.echo("\n" + "="*80 + "\n")

    except ConfigurationError as e:
        click.echo(click.style(f"\n❌ Configuration error: {e}", fg='red'))
        raise click.Abort() from e

    except Exception as e:
        logger.error(f"Unexpected error in --init command: {e}", exc_info=True)
        click.echo(click.style(f"\n❌ Unexpected error: {e}", fg='red'))
        raise click.Abort() from e
