"""Executable contract tests for IVisionService using VisionService with deterministic doubles."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.interfaces.screenshot_service import IVisionService
from src.lib.exceptions import SessionAlreadyActiveError, VisionCommandError
from src.models.entities import CaptureRegion, Configuration, MonitoringSession, Screenshot
from src.services.vision_service import VisionService


@pytest.fixture()
def sample_screenshot(tmp_path: Path) -> Screenshot:
    file_path = tmp_path / "capture.png"
    file_path.write_bytes(b"img")
    size = file_path.stat().st_size
    return Screenshot(
        id=uuid4(),
        timestamp=datetime.now(tz=UTC),
        file_path=file_path,
        format="png",
        original_size_bytes=size,
        optimized_size_bytes=size,
        resolution=(1920, 1080),
        source_monitor=0,
        capture_method="test",
        privacy_zones_applied=False,
    )


@pytest.fixture()
def configured_service(sample_screenshot: Screenshot) -> tuple[VisionService, dict[str, Mock]]:
    config = Configuration()
    config.privacy.prompt_first_use = False
    config.privacy.enabled = False
    config.screenshot.max_size_mb = 2.0

    config_manager = Mock()
    config_manager.load_config.return_value = config

    temp_manager = Mock()
    capture = Mock()
    capture.capture_full_screen.return_value = sample_screenshot
    capture.capture_region.return_value = sample_screenshot

    processor = Mock()
    processor.apply_privacy_zones.return_value = sample_screenshot
    processor.optimize_image.return_value = sample_screenshot

    api_client = Mock()
    api_client.send_multimodal_prompt.return_value = "analysis"

    region_selector = Mock()
    region_selector.select_region_graphical.return_value = CaptureRegion(
        x=10,
        y=20,
        width=300,
        height=200,
        monitor=0,
        selection_method="graphical",
    )

    session_manager = Mock()
    session_manager.start_session.return_value = MonitoringSession(
        id=uuid4(),
        started_at=datetime.now(tz=UTC),
        interval_seconds=30,
    )
    session_manager.get_active_session.return_value = MonitoringSession(
        id=uuid4(),
        started_at=datetime.now(tz=UTC),
        interval_seconds=30,
    )

    service = VisionService(
        config_manager=config_manager,
        temp_manager=temp_manager,
        capture=capture,
        processor=processor,
        api_client=api_client,
        region_selector=region_selector,
        session_manager=session_manager,
    )

    mocks = {
        "config_manager": config_manager,
        "temp_manager": temp_manager,
        "capture": capture,
        "processor": processor,
        "api_client": api_client,
        "region_selector": region_selector,
        "session_manager": session_manager,
    }
    return service, mocks


def test_interface_inheritance(configured_service) -> None:
    service, _ = configured_service
    assert isinstance(service, IVisionService)


def test_execute_vision_command_returns_string(configured_service) -> None:
    service, _ = configured_service
    result = service.execute_vision_command("What do you see?")
    assert isinstance(result, str)
    assert result == "analysis"


def test_execute_vision_command_with_empty_prompt(configured_service) -> None:
    service, mocks = configured_service
    result = service.execute_vision_command("")
    assert result == "analysis"
    mocks["api_client"].send_multimodal_prompt.assert_called_once()


def test_execute_vision_command_with_long_prompt(configured_service) -> None:
    service, _ = configured_service
    result = service.execute_vision_command("Analyze " * 200)
    assert isinstance(result, str)


def test_execute_vision_command_calls_cleanup(configured_service) -> None:
    service, mocks = configured_service
    service.execute_vision_command("cleanup")
    mocks["temp_manager"].cleanup_temp_file.assert_called_once()


def test_execute_vision_area_command_returns_string_with_coordinates(configured_service) -> None:
    service, mocks = configured_service
    region = CaptureRegion(x=0, y=0, width=100, height=100, monitor=0, selection_method="coordinates")

    result = service.execute_vision_area_command("Area", region=region)

    assert result == "analysis"
    mocks["capture"].capture_region.assert_called_once_with(region)


def test_execute_vision_area_command_without_region_uses_selector(configured_service) -> None:
    service, mocks = configured_service

    result = service.execute_vision_area_command("Area")

    assert result == "analysis"
    mocks["region_selector"].select_region_graphical.assert_called_once()


def test_execute_vision_area_command_invalid_region_raises_vision_error(configured_service) -> None:
    service, mocks = configured_service
    bad_region = CaptureRegion(x=-1, y=0, width=10, height=10, monitor=0, selection_method="coordinates")
    mocks["capture"].capture_region.side_effect = ValueError("invalid")

    with pytest.raises(VisionCommandError):
        service.execute_vision_area_command("x", bad_region)


def test_execute_vision_auto_command_returns_session_id(configured_service) -> None:
    service, _ = configured_service
    session_id = service.execute_vision_auto_command(interval_seconds=30)
    assert session_id is not None


def test_execute_vision_auto_command_uses_default_interval(configured_service) -> None:
    service, mocks = configured_service
    service.execute_vision_auto_command(interval_seconds=None)
    mocks["session_manager"].start_session.assert_called_once_with(30)


def test_execute_vision_auto_command_invalid_interval_raises_error(configured_service) -> None:
    service, _ = configured_service
    with pytest.raises(VisionCommandError, match="Interval must be positive"):
        service.execute_vision_auto_command(interval_seconds=0)


def test_execute_vision_auto_command_prevents_multiple_sessions(configured_service) -> None:
    service, mocks = configured_service
    mocks["session_manager"].start_session.side_effect = SessionAlreadyActiveError("abc")

    with pytest.raises(VisionCommandError, match="already active"):
        service.execute_vision_auto_command(interval_seconds=30)


def test_execute_vision_stop_command_stops_active_session(configured_service) -> None:
    service, mocks = configured_service
    service.execute_vision_stop_command()
    mocks["session_manager"].stop_session.assert_called_once()


def test_execute_vision_stop_command_without_active_session_raises_error(configured_service) -> None:
    service, mocks = configured_service
    mocks["session_manager"].get_active_session.return_value = None

    with pytest.raises(VisionCommandError, match="No active monitoring session"):
        service.execute_vision_stop_command()


def test_execute_vision_command_api_error_is_wrapped(configured_service) -> None:
    service, mocks = configured_service
    mocks["api_client"].send_multimodal_prompt.side_effect = RuntimeError("api down")

    with pytest.raises(VisionCommandError, match="Failed to execute vision command"):
        service.execute_vision_command("hello")
