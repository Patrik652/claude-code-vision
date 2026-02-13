"""Integration tests for first-use privacy confirmation workflow (FR-013)."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
import yaml

from src.lib.exceptions import VisionCommandError
from src.models.entities import Configuration, PrivacyConfig, Screenshot
from src.services.config_manager import ConfigurationManager
from src.services.vision_service import VisionService


def _build_service(mocker, config: Configuration):
    config.ai_provider.provider = "claude"
    config.ai_provider.fallback_to_gemini = False

    config_manager = mocker.Mock()
    config_manager.load_config.return_value = config

    temp_manager = mocker.Mock()
    capture = mocker.Mock()
    processor = mocker.Mock()
    api_client = mocker.Mock()

    screenshot = Screenshot(
        id=uuid4(),
        timestamp=datetime.now(tz=UTC),
        file_path=Path("/tmp/test.png"),
        format="png",
        original_size_bytes=1024,
        optimized_size_bytes=512,
        resolution=(100, 100),
        source_monitor=0,
        capture_method="scrot",
        privacy_zones_applied=False,
    )

    capture.capture_full_screen.return_value = screenshot
    processor.optimize_image.return_value = screenshot
    processor.apply_privacy_zones.return_value = screenshot
    api_client.send_multimodal_prompt.return_value = "analysis"

    service = VisionService(
        config_manager=config_manager,
        temp_manager=temp_manager,
        capture=capture,
        processor=processor,
        api_client=api_client,
        region_selector=mocker.Mock(),
        session_manager=mocker.Mock(),
        gemini_client=None,
    )

    return service, config_manager, api_client, temp_manager


class TestFirstUseConfiguration:
    @pytest.fixture()
    def config_manager(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        return ConfigurationManager(config_file)

    def test_default_config_has_prompt_enabled(self):
        config = Configuration()
        assert config.privacy.prompt_first_use is True

    def test_config_persists_prompt_state(self, config_manager):
        config = Configuration(
            privacy=PrivacyConfig(
                enabled=True,
                prompt_first_use=False,
                zones=[],
            )
        )
        config_manager.save_config(config)

        with config_manager.config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert data["privacy"]["prompt_first_use"] is False

    def test_config_loads_prompt_state(self, config_manager):
        config_data = {
            "version": "1.0",
            "privacy": {
                "enabled": True,
                "prompt_first_use": False,
                "zones": [],
            },
        }
        with config_manager.config_path.open("w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        loaded = config_manager.load_config()
        assert loaded.privacy.prompt_first_use is False


class TestFirstUseWorkflow:
    def test_prompt_acceptance_disables_future_prompt(self, mocker):
        config = Configuration()
        config.privacy.prompt_first_use = True
        service, config_manager, _api_client, _temp_manager = _build_service(mocker, config)

        confirm = mocker.patch("click.confirm", return_value=True)

        assert service._check_first_use_prompt() is True
        assert config.privacy.prompt_first_use is False
        config_manager.save_config.assert_called_once_with(config)
        confirm.assert_called_once()

    def test_prompt_rejection_raises_actionable_error(self, mocker):
        config = Configuration()
        config.privacy.prompt_first_use = True
        service, config_manager, _api_client, _temp_manager = _build_service(mocker, config)

        mocker.patch("click.confirm", return_value=False)

        with pytest.raises(VisionCommandError, match="Privacy terms not accepted"):
            service._check_first_use_prompt()

        config_manager.save_config.assert_not_called()

    def test_prompt_not_shown_when_disabled(self, mocker):
        config = Configuration()
        config.privacy.prompt_first_use = False
        service, config_manager, _api_client, _temp_manager = _build_service(mocker, config)

        confirm = mocker.patch("click.confirm")

        assert service._check_first_use_prompt() is True
        confirm.assert_not_called()
        config_manager.save_config.assert_not_called()

    def test_execute_vision_command_shows_prompt_only_once(self, mocker):
        config = Configuration()
        config.privacy.prompt_first_use = True
        config.privacy.enabled = False
        service, _config_manager, api_client, temp_manager = _build_service(mocker, config)

        confirm = mocker.patch("click.confirm", return_value=True)

        first = service.execute_vision_command("First call")
        second = service.execute_vision_command("Second call")

        assert first == "analysis"
        assert second == "analysis"
        assert confirm.call_count == 1
        assert api_client.send_multimodal_prompt.call_count == 2
        assert temp_manager.cleanup_temp_file.call_count == 2

    def test_prompt_prints_privacy_notice_header(self, mocker):
        config = Configuration()
        config.privacy.prompt_first_use = True
        service, _config_manager, _api_client, _temp_manager = _build_service(mocker, config)

        mocker.patch("click.confirm", return_value=True)
        print_mock = mocker.patch("builtins.print")

        service._check_first_use_prompt()

        printed = " ".join(" ".join(map(str, c.args)) for c in print_mock.call_args_list)
        assert "PRIVACY NOTICE" in printed
        assert "Capture screenshots of your screen" in printed
        assert "Immediately delete screenshots after transmission" in printed
