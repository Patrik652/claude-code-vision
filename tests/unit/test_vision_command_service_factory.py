"""Unit tests for get_vision_service dependency wiring."""

from unittest.mock import Mock

import pytest

from src.lib.exceptions import VisionCommandError
from src.models.entities import Configuration


@pytest.fixture()
def vision_command_module():
    from src.cli import vision_command

    return vision_command


def _build_config(provider: str) -> Configuration:
    config = Configuration()
    config.ai_provider.provider = provider
    config.gemini.api_key = "gemini-key"
    return config


def _patch_core_dependencies(mocker, vision_command_module, config: Configuration):
    config_manager = Mock()
    config_manager.load_config.return_value = config
    mocker.patch.object(vision_command_module, "ConfigurationManager", return_value=config_manager)
    mocker.patch.object(vision_command_module, "setup_logging")
    temp_manager = object()
    capture = object()
    processor = object()
    mocker.patch.object(vision_command_module, "TempFileManager", return_value=temp_manager)
    mocker.patch.object(vision_command_module.ScreenshotCaptureFactory, "create", return_value=capture)
    mocker.patch.object(vision_command_module, "PillowImageProcessor", return_value=processor)
    return config_manager, temp_manager, capture, processor


def test_get_vision_service_prefers_gemini_when_configured(mocker, vision_command_module) -> None:
    config = _build_config(provider="gemini")
    config_manager, temp_manager, capture, processor = _patch_core_dependencies(
        mocker, vision_command_module, config
    )
    claude_client = object()
    gemini_client = object()
    mocker.patch.object(vision_command_module, "AnthropicAPIClient", return_value=claude_client)
    mocker.patch.object(vision_command_module, "GeminiAPIClient", return_value=gemini_client)
    service_instance = object()
    vision_service = mocker.patch.object(vision_command_module, "VisionService", return_value=service_instance)

    result = vision_command_module.get_vision_service()

    assert result is service_instance
    assert vision_service.call_args.kwargs["config_manager"] is config_manager
    assert vision_service.call_args.kwargs["temp_manager"] is temp_manager
    assert vision_service.call_args.kwargs["capture"] is capture
    assert vision_service.call_args.kwargs["processor"] is processor
    assert vision_service.call_args.kwargs["api_client"] is gemini_client
    assert vision_service.call_args.kwargs["gemini_client"] is gemini_client


def test_get_vision_service_prefers_claude_when_configured(mocker, vision_command_module) -> None:
    config = _build_config(provider="claude")
    _patch_core_dependencies(mocker, vision_command_module, config)
    claude_client = object()
    gemini_client = object()
    mocker.patch.object(vision_command_module, "AnthropicAPIClient", return_value=claude_client)
    mocker.patch.object(vision_command_module, "GeminiAPIClient", return_value=gemini_client)
    vision_service = mocker.patch.object(vision_command_module, "VisionService", return_value=object())

    vision_command_module.get_vision_service()

    assert vision_service.call_args.kwargs["api_client"] is claude_client
    assert vision_service.call_args.kwargs["gemini_client"] is gemini_client


def test_get_vision_service_falls_back_to_available_client(mocker, vision_command_module) -> None:
    config = _build_config(provider="claude")
    _patch_core_dependencies(mocker, vision_command_module, config)
    claude_error = RuntimeError("claude unavailable")
    gemini_client = object()
    mocker.patch.object(vision_command_module, "AnthropicAPIClient", side_effect=claude_error)
    mocker.patch.object(vision_command_module, "GeminiAPIClient", return_value=gemini_client)
    vision_service = mocker.patch.object(vision_command_module, "VisionService", return_value=object())

    vision_command_module.get_vision_service()

    assert vision_service.call_args.kwargs["api_client"] is gemini_client


def test_get_vision_service_raises_when_no_client_available(mocker, vision_command_module) -> None:
    config = _build_config(provider="gemini")
    _patch_core_dependencies(mocker, vision_command_module, config)
    mocker.patch.object(vision_command_module, "AnthropicAPIClient", side_effect=RuntimeError("claude unavailable"))
    mocker.patch.object(vision_command_module, "GeminiAPIClient", side_effect=RuntimeError("gemini unavailable"))

    with pytest.raises(VisionCommandError, match="No API client configured"):
        vision_command_module.get_vision_service()


def test_get_vision_service_wraps_unexpected_creation_errors(mocker, vision_command_module) -> None:
    failing_manager = Mock()
    failing_manager.load_config.side_effect = ValueError("bad config data")
    mocker.patch.object(vision_command_module, "ConfigurationManager", return_value=failing_manager)

    with pytest.raises(VisionCommandError, match="Failed to initialize vision service: bad config data"):
        vision_command_module.get_vision_service()
