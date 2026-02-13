"""Unit tests for core VisionService orchestration behavior."""

from uuid import uuid4

import pytest

from src.lib.exceptions import VisionCommandError
from src.models.entities import Configuration, MonitoringSession
from src.services.vision_service import VisionService


def _build_service(mocker, config: Configuration | None = None) -> VisionService:
    config_manager = mocker.Mock()
    config_manager.load_config.return_value = config or Configuration()

    return VisionService(
        config_manager=config_manager,
        temp_manager=mocker.Mock(),
        capture=mocker.Mock(),
        processor=mocker.Mock(),
        api_client=mocker.Mock(name="claude_client"),
        region_selector=mocker.Mock(),
        session_manager=mocker.Mock(),
        gemini_client=mocker.Mock(name="gemini_client"),
    )


def test_get_api_client_uses_primary_provider(mocker) -> None:
    config = Configuration()
    config.ai_provider.provider = "gemini"
    service = _build_service(mocker, config=config)

    client = service._get_api_client()

    assert client is service.gemini_client


def test_get_api_client_uses_fallback_when_enabled(mocker) -> None:
    config = Configuration()
    config.ai_provider.provider = "claude"
    config.ai_provider.fallback_to_gemini = True

    service = _build_service(mocker, config=config)
    service.claude_client = None

    client = service._get_api_client()

    assert client is service.gemini_client


def test_get_api_client_raises_when_no_client_available(mocker) -> None:
    config = Configuration()
    config.ai_provider.provider = "gemini"
    config.ai_provider.fallback_to_gemini = False

    service = _build_service(mocker, config=config)
    service.claude_client = None
    service.gemini_client = None

    with pytest.raises(VisionCommandError, match="No API client available for provider 'gemini'"):
        service._get_api_client()


def test_execute_vision_auto_uses_config_interval(mocker) -> None:
    config = Configuration()
    config.monitoring.interval_seconds = 42
    service = _build_service(mocker, config=config)

    session = MonitoringSession(id=uuid4(), started_at=mocker.Mock(), interval_seconds=42)
    service.session_manager.start_session.return_value = session

    result = service.execute_vision_auto_command(interval_seconds=None)

    assert result == session.id
    service.session_manager.start_session.assert_called_once_with(42)


def test_execute_vision_auto_invalid_interval_is_actionable(mocker) -> None:
    service = _build_service(mocker)

    with pytest.raises(VisionCommandError, match="Interval must be positive"):
        service.execute_vision_auto_command(interval_seconds=0)

    service.session_manager.start_session.assert_not_called()


def test_execute_vision_stop_without_active_session_is_actionable(mocker) -> None:
    service = _build_service(mocker)
    service.session_manager.get_active_session.return_value = None

    with pytest.raises(VisionCommandError, match="No active monitoring session to stop"):
        service.execute_vision_stop_command()

    service.session_manager.stop_session.assert_not_called()
