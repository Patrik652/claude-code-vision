"""
--doctor CLI command implementation.

Diagnostic tool to verify Claude Code Vision setup and dependencies.
"""

import click
import shutil
import sys
from pathlib import Path

from src.services.config_manager import ConfigurationManager
from src.lib.desktop_detector import detect_desktop_type
from src.lib.tool_detector import get_preferred_tool
from src.lib.logging_config import get_logger

logger = get_logger(__name__)


@click.command(name='doctor')
@click.pass_context
def doctor(ctx):
    """
    Run diagnostics on Claude Code Vision setup.

    Verifies:
    - Configuration file exists and is valid
    - Screenshot tools are available
    - Desktop environment is supported
    - Python version is compatible
    - Required dependencies are installed

    Examples:

        \b
        # Run full diagnostic check
        claude-vision --doctor
    """
    click.echo(click.style("\n🔍 Claude Code Vision Diagnostics", fg='cyan', bold=True))
    click.echo("="*80 + "\n")

    all_checks_passed = True

    # Check 1: Python version
    click.echo(click.style("1. Python Version", fg='cyan', bold=True))
    python_version = sys.version_info
    if python_version >= (3, 8):
        click.echo(click.style(f"   ✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}", fg='green'))
    else:
        click.echo(click.style(f"   ✗ Python {python_version.major}.{python_version.minor}.{python_version.micro} (requires 3.8+)", fg='red'))
        all_checks_passed = False
    click.echo()

    # Check 2: Configuration
    click.echo(click.style("2. Configuration File", fg='cyan', bold=True))
    config_path = ConfigurationManager.DEFAULT_CONFIG_PATH
    if config_path.exists():
        click.echo(click.style(f"   ✓ Config exists: {config_path}", fg='green'))
        try:
            config_manager = ConfigurationManager()
            config = config_manager.load_config()
            config_manager.validate_config(config)
            click.echo(click.style(f"   ✓ Config is valid", fg='green'))
        except Exception as e:
            click.echo(click.style(f"   ✗ Config validation failed: {e}", fg='red'))
            all_checks_passed = False
    else:
        click.echo(click.style(f"   ⚠️  Config not found: {config_path}", fg='yellow'))
        click.echo(click.style(f"   → Run: claude-vision --init", fg='yellow'))
        all_checks_passed = False
    click.echo()

    # Check 3: Desktop Environment
    click.echo(click.style("3. Desktop Environment", fg='cyan', bold=True))
    try:
        desktop_type = detect_desktop_type()
        desktop_env = desktop_type.value
        if desktop_env in ['x11', 'wayland']:
            click.echo(click.style(f"   ✓ Detected: {desktop_env.upper()}", fg='green'))
        else:
            click.echo(click.style(f"   ⚠️  Unknown desktop environment: {desktop_env}", fg='yellow'))
            all_checks_passed = False
    except Exception as e:
        click.echo(click.style(f"   ✗ Detection failed: {e}", fg='red'))
        all_checks_passed = False
    click.echo()

    # Check 4: Screenshot Tools
    click.echo(click.style("4. Screenshot Tools", fg='cyan', bold=True))
    try:
        tool = get_preferred_tool()
        if tool:
            click.echo(click.style(f"   ✓ Available: {tool.value}", fg='green'))
        else:
            click.echo(click.style(f"   ✗ No screenshot tool found", fg='red'))
            click.echo(click.style(f"   → Install: scrot (X11) or grim (Wayland)", fg='yellow'))
            all_checks_passed = False
    except Exception as e:
        click.echo(click.style(f"   ✗ Detection failed: {e}", fg='red'))
        all_checks_passed = False
    click.echo()

    # Check 5: Region Selection Tools
    click.echo(click.style("5. Region Selection Tools", fg='cyan', bold=True))
    has_selector = False
    if shutil.which('slurp'):
        click.echo(click.style(f"   ✓ slurp (Wayland)", fg='green'))
        has_selector = True
    if shutil.which('xrectsel'):
        click.echo(click.style(f"   ✓ xrectsel (X11)", fg='green'))
        has_selector = True
    if shutil.which('slop'):
        click.echo(click.style(f"   ✓ slop (X11)", fg='green'))
        has_selector = True

    if not has_selector:
        click.echo(click.style(f"   ⚠️  No region selector found (optional)", fg='yellow'))
        click.echo(click.style(f"   → Install: slop (X11) or slurp (Wayland)", fg='yellow'))
        click.echo(click.style(f"   → You can still use --coords for area selection", fg='yellow'))
    click.echo()

    # Check 6: Dependencies
    click.echo(click.style("6. Python Dependencies", fg='cyan', bold=True))
    required_packages = ['click', 'yaml', 'PIL']
    for package in required_packages:
        try:
            __import__(package)
            click.echo(click.style(f"   ✓ {package}", fg='green'))
        except ImportError:
            click.echo(click.style(f"   ✗ {package} not installed", fg='red'))
            all_checks_passed = False
    click.echo()

    # Check 7: Temp Directory
    click.echo(click.style("7. Temporary Directory", fg='cyan', bold=True))
    try:
        config_manager = ConfigurationManager()
        config = config_manager.load_config()
        temp_dir = Path(config.temp.directory).expanduser()
        temp_dir.mkdir(parents=True, exist_ok=True)
        click.echo(click.style(f"   ✓ Writable: {temp_dir}", fg='green'))
    except Exception as e:
        click.echo(click.style(f"   ✗ Cannot create temp directory: {e}", fg='red'))
        all_checks_passed = False
    click.echo()

    # Check 8: Log Directory
    click.echo(click.style("8. Log Directory", fg='cyan', bold=True))
    try:
        config_manager = ConfigurationManager()
        config = config_manager.load_config()
        log_file = Path(config.logging.file).expanduser()
        log_file.parent.mkdir(parents=True, exist_ok=True)
        click.echo(click.style(f"   ✓ Writable: {log_file.parent}", fg='green'))
    except Exception as e:
        click.echo(click.style(f"   ✗ Cannot create log directory: {e}", fg='red'))
        all_checks_passed = False
    click.echo()

    # Final Summary
    click.echo("="*80)
    if all_checks_passed:
        click.echo(click.style("\n✓ All checks passed! Claude Code Vision is ready to use.", fg='green', bold=True))
        click.echo("\n" + click.style("Try your first command:", fg='cyan'))
        click.echo(click.style('  /vision "What do you see?"', fg='cyan'))
    else:
        click.echo(click.style("\n⚠️  Some checks failed. Please address the issues above.", fg='yellow', bold=True))
        click.echo("\n" + click.style("Common fixes:", fg='cyan'))
        click.echo(click.style("  • Run: claude-vision --init (create config)", fg='cyan'))
        click.echo(click.style("  • Install screenshot tools for your desktop environment", fg='cyan'))
        click.echo(click.style("  • Check Python version (requires 3.8+)", fg='cyan'))
    click.echo("\n" + "="*80 + "\n")
