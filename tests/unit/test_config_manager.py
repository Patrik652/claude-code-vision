"""Unit tests for ConfigurationManager loading, validation, and persistence behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.lib.exceptions import ConfigurationError
from src.models.entities import Configuration, PrivacyZone
from src.services.config_manager import ConfigurationManager


@pytest.fixture()
def config_path(tmp_path: Path) -> Path:
    return tmp_path / "cfg" / "config.yaml"


@pytest.fixture()
def manager(config_path: Path) -> ConfigurationManager:
    return ConfigurationManager(config_path=config_path)


def test_load_config_returns_defaults_when_file_missing(manager: ConfigurationManager) -> None:
    config = manager.load_config()

    assert isinstance(config, Configuration)
    assert config.screenshot.format == "jpeg"
    assert config.monitoring.interval_seconds == 30


def test_load_config_returns_defaults_for_empty_file(manager: ConfigurationManager, config_path: Path) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("", encoding="utf-8")

    config = manager.load_config()

    assert isinstance(config, Configuration)
    assert config.privacy.prompt_first_use is True


def test_load_config_raises_on_invalid_yaml(manager: ConfigurationManager, config_path: Path) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("version: [", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="Invalid YAML"):
        manager.load_config()


def test_load_config_merges_partial_data(manager: ConfigurationManager, config_path: Path) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        """
version: "2.0"
screenshot:
  format: png
  quality: 70
privacy:
  enabled: true
  prompt_first_use: false
  zones:
    - name: terminal
      x: 10
      y: 20
      width: 200
      height: 100
monitoring:
  interval_seconds: 45
ai_provider:
  provider: gemini
gemini:
  api_key: demo-key
  model: gemini-2.5
""",
        encoding="utf-8",
    )

    config = manager.load_config()

    assert config.version == "2.0"
    assert config.screenshot.format == "png"
    assert config.screenshot.quality == 70
    assert config.privacy.prompt_first_use is False
    assert len(config.privacy.zones) == 1
    assert config.privacy.zones[0].name == "terminal"
    assert config.monitoring.interval_seconds == 45
    assert config.ai_provider.provider == "gemini"
    assert config.gemini.api_key == "demo-key"
    assert config.gemini.model == "gemini-2.5"


def test_save_config_persists_yaml_and_parent_directory(manager: ConfigurationManager, config_path: Path) -> None:
    config = Configuration()
    config.screenshot.format = "png"
    config.screenshot.quality = 80
    config.privacy.zones = [PrivacyZone(name="editor", x=0, y=0, width=100, height=40, monitor=0)]

    manager.save_config(config)

    assert config_path.exists()
    text = config_path.read_text(encoding="utf-8")
    assert "screenshot:" in text
    assert "format: png" in text
    assert "name: editor" in text


def test_save_then_load_round_trip_preserves_values(manager: ConfigurationManager) -> None:
    config = Configuration()
    config.logging.level = "DEBUG"
    config.temp.keep_on_error = True
    config.ai_provider.provider = "gemini"

    manager.save_config(config)
    loaded = manager.load_config()

    assert loaded.logging.level == "DEBUG"
    assert loaded.temp.keep_on_error is True
    assert loaded.ai_provider.provider == "gemini"


def test_validate_config_accepts_valid_configuration(manager: ConfigurationManager) -> None:
    config = Configuration()

    assert manager.validate_config(config) is True


def test_validate_config_raises_with_multiple_errors(manager: ConfigurationManager) -> None:
    config = Configuration()
    config.screenshot.quality = 101
    config.screenshot.max_size_mb = 0
    config.screenshot.format = "bmp"
    config.monitoring.interval_seconds = 0
    config.monitoring.max_duration_minutes = 0
    config.logging.level = "TRACE"

    with pytest.raises(ConfigurationError) as exc:
        manager.validate_config(config)

    message = str(exc.value)
    assert "screenshot.quality must be between 0 and 100" in message
    assert "screenshot.max_size_mb must be positive" in message
    assert "screenshot.format must be 'jpeg', 'png', or 'webp'" in message
    assert "monitoring.interval_seconds must be positive" in message
    assert "monitoring.max_duration_minutes must be positive" in message
    assert "logging.level must be DEBUG, INFO, WARNING, or ERROR" in message


def test_validate_config_raises_for_invalid_privacy_zone(manager: ConfigurationManager) -> None:
    config = Configuration()
    config.privacy.zones = [PrivacyZone(name="bad", x=-1, y=0, width=0, height=1, monitor=0)]

    with pytest.raises(ConfigurationError) as exc:
        manager.validate_config(config)

    assert "negative coordinates" in str(exc.value)
    assert "invalid dimensions" in str(exc.value)


def test_load_config_wraps_validation_error_as_configuration_error(
    manager: ConfigurationManager,
    config_path: Path,
) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        """
screenshot:
  quality: 120
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="Failed to load configuration"):
        manager.load_config()


def test_config_to_dict_contains_expected_sections(manager: ConfigurationManager) -> None:
    config = Configuration()
    as_dict = manager._config_to_dict(config)

    assert "screenshot" in as_dict
    assert "privacy" in as_dict
    assert "monitoring" in as_dict
    assert "logging" in as_dict
    assert "ai_provider" in as_dict
    assert "gemini" in as_dict
