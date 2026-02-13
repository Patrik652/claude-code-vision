"""
Configuration Manager for Claude Code Vision.

Handles loading, saving, and validating configuration from YAML file.
Implements IConfigurationManager interface.
"""

from pathlib import Path
from typing import Optional

import yaml

from src.interfaces.screenshot_service import IConfigurationManager
from src.lib.exceptions import ConfigurationError
from src.lib.logging_config import get_logger
from src.models.entities import Configuration

logger = get_logger(__name__)


class ConfigurationManager(IConfigurationManager):
    """
    Manages configuration loading, saving, and validation.

    Default config location: ~/.config/claude-code-vision/config.yaml
    """

    DEFAULT_CONFIG_PATH = Path.home() / ".config" / "claude-code-vision" / "config.yaml"

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize ConfigurationManager.

        Args:
            config_path: Path to config file. If None, uses default location.
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        logger.debug(f"ConfigurationManager initialized with path: {self.config_path}")

    def load_config(self) -> Configuration:
        """
        Load configuration from file or create defaults.

        Returns:
            Configuration object

        Raises:
            ConfigurationError: If config invalid
        """
        # If config file doesn't exist, return defaults
        if not self.config_path.exists():
            logger.info(f"Config file not found at {self.config_path}, using defaults")
            return Configuration()

        try:
            with open(self.config_path, encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data:
                logger.warning(f"Empty config file at {self.config_path}, using defaults")
                return Configuration()

            # Merge loaded data with defaults
            config = self._merge_with_defaults(data)

            # Validate
            self.validate_config(config)

            logger.info(f"Configuration loaded successfully from {self.config_path}")
            return config

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in config file: {e}") from e
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}") from e

    def save_config(self, config: Configuration) -> None:
        """
        Save configuration to file.

        Args:
            config: Configuration to persist

        Raises:
            ConfigurationError: If save fails
        """
        try:
            # Validate before saving
            self.validate_config(config)

            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert config to dict
            config_dict = self._config_to_dict(config)

            # Write YAML
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

            logger.info(f"Configuration saved successfully to {self.config_path}")

        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {e}") from e

    def validate_config(self, config: Configuration) -> bool:
        """
        Validate configuration against schema.

        Args:
            config: Configuration to validate

        Returns:
            True if valid

        Raises:
            ConfigurationError: If validation fails with specific errors
        """
        errors = []

        # Validate screenshot settings
        if config.screenshot.quality < 0 or config.screenshot.quality > 100:
            errors.append("screenshot.quality must be between 0 and 100")

        if config.screenshot.max_size_mb <= 0:
            errors.append("screenshot.max_size_mb must be positive")

        if config.screenshot.format not in ['jpeg', 'png', 'webp']:
            errors.append("screenshot.format must be 'jpeg', 'png', or 'webp'")

        # Validate monitoring settings
        if config.monitoring.interval_seconds <= 0:
            errors.append("monitoring.interval_seconds must be positive")

        if config.monitoring.max_duration_minutes <= 0:
            errors.append("monitoring.max_duration_minutes must be positive")

        # Validate logging settings
        if config.logging.level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            errors.append("logging.level must be DEBUG, INFO, WARNING, or ERROR")

        # Validate privacy zones
        for zone in config.privacy.zones:
            if zone.x < 0 or zone.y < 0:
                errors.append(f"Privacy zone '{zone.name}' has negative coordinates")
            if zone.width <= 0 or zone.height <= 0:
                errors.append(f"Privacy zone '{zone.name}' has invalid dimensions")

        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ConfigurationError(error_msg)

        return True

    def _merge_with_defaults(self, data: dict) -> Configuration:  # noqa: PLR0912, PLR0915
        """
        Merge loaded configuration with defaults.

        Args:
            data: Loaded YAML data

        Returns:
            Configuration with defaults applied for missing fields
        """
        # Start with default configuration
        config = Configuration()

        # Override with loaded data
        if 'version' in data:
            config.version = data['version']

        if 'screenshot' in data:
            s = data['screenshot']
            if 'tool' in s:
                config.screenshot.tool = s['tool']
            if 'format' in s:
                config.screenshot.format = s['format']
            if 'quality' in s:
                config.screenshot.quality = s['quality']
            if 'max_size_mb' in s:
                config.screenshot.max_size_mb = s['max_size_mb']

        if 'monitors' in data:
            m = data['monitors']
            if 'default' in m:
                config.monitors.default = m['default']

        if 'area_selection' in data:
            a = data['area_selection']
            if 'tool' in a:
                config.area_selection.tool = a['tool']
            if 'show_coordinates' in a:
                config.area_selection.show_coordinates = a['show_coordinates']

        if 'privacy' in data:
            p = data['privacy']
            if 'enabled' in p:
                config.privacy.enabled = p['enabled']
            if 'prompt_first_use' in p:
                config.privacy.prompt_first_use = p['prompt_first_use']
            if 'zones' in p:
                from src.models.entities import PrivacyZone
                config.privacy.zones = [
                    PrivacyZone(
                        name=z['name'],
                        x=z['x'],
                        y=z['y'],
                        width=z['width'],
                        height=z['height'],
                        monitor=z.get('monitor')
                    )
                    for z in p['zones']
                ]

        if 'monitoring' in data:
            m = data['monitoring']
            if 'interval_seconds' in m:
                config.monitoring.interval_seconds = m['interval_seconds']
            if 'max_duration_minutes' in m:
                config.monitoring.max_duration_minutes = m['max_duration_minutes']
            if 'idle_pause_minutes' in m:
                config.monitoring.idle_pause_minutes = m['idle_pause_minutes']
            if 'change_detection' in m:
                config.monitoring.change_detection = m['change_detection']

        if 'claude_code' in data:
            c = data['claude_code']
            if 'oauth_token_path' in c:
                config.claude_code.oauth_token_path = c['oauth_token_path']
            if 'api_endpoint' in c:
                config.claude_code.api_endpoint = c['api_endpoint']

        if 'temp' in data:
            t = data['temp']
            if 'directory' in t:
                config.temp.directory = t['directory']
            if 'cleanup' in t:
                config.temp.cleanup = t['cleanup']
            if 'keep_on_error' in t:
                config.temp.keep_on_error = t['keep_on_error']

        if 'logging' in data:
            logging_cfg = data['logging']
            if 'level' in logging_cfg:
                config.logging.level = logging_cfg['level']
            if 'file' in logging_cfg:
                config.logging.file = logging_cfg['file']
            if 'max_size_mb' in logging_cfg:
                config.logging.max_size_mb = logging_cfg['max_size_mb']
            if 'backup_count' in logging_cfg:
                config.logging.backup_count = logging_cfg['backup_count']

        if 'ai_provider' in data:
            ap = data['ai_provider']
            if 'provider' in ap:
                config.ai_provider.provider = ap['provider']
            if 'fallback_to_gemini' in ap:
                config.ai_provider.fallback_to_gemini = ap['fallback_to_gemini']

        if 'gemini' in data:
            g = data['gemini']
            if 'api_key' in g:
                config.gemini.api_key = g['api_key']
            if 'model' in g:
                config.gemini.model = g['model']

        return config

    def _config_to_dict(self, config: Configuration) -> dict:
        """
        Convert Configuration object to dictionary for YAML serialization.

        Args:
            config: Configuration object

        Returns:
            Dictionary representation
        """
        return {
            'version': config.version,
            'screenshot': {
                'tool': config.screenshot.tool,
                'format': config.screenshot.format,
                'quality': config.screenshot.quality,
                'max_size_mb': config.screenshot.max_size_mb,
            },
            'monitors': {
                'default': config.monitors.default,
            },
            'area_selection': {
                'tool': config.area_selection.tool,
                'show_coordinates': config.area_selection.show_coordinates,
            },
            'privacy': {
                'enabled': config.privacy.enabled,
                'prompt_first_use': config.privacy.prompt_first_use,
                'zones': [
                    {
                        'name': zone.name,
                        'x': zone.x,
                        'y': zone.y,
                        'width': zone.width,
                        'height': zone.height,
                        'monitor': zone.monitor,
                    }
                    for zone in config.privacy.zones
                ],
            },
            'monitoring': {
                'interval_seconds': config.monitoring.interval_seconds,
                'max_duration_minutes': config.monitoring.max_duration_minutes,
                'idle_pause_minutes': config.monitoring.idle_pause_minutes,
                'change_detection': config.monitoring.change_detection,
            },
            'claude_code': {
                'oauth_token_path': config.claude_code.oauth_token_path,
                'api_endpoint': config.claude_code.api_endpoint,
            },
            'temp': {
                'directory': config.temp.directory,
                'cleanup': config.temp.cleanup,
                'keep_on_error': config.temp.keep_on_error,
            },
            'logging': {
                'level': config.logging.level,
                'file': config.logging.file,
                'max_size_mb': config.logging.max_size_mb,
                'backup_count': config.logging.backup_count,
            },
            'ai_provider': {
                'provider': config.ai_provider.provider,
                'fallback_to_gemini': config.ai_provider.fallback_to_gemini,
            },
            'gemini': {
                'api_key': config.gemini.api_key,
                'model': config.gemini.model,
            },
        }
