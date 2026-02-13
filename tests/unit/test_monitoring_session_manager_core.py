"""Unit tests for MonitoringSessionManager core control-flow branches."""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.lib.exceptions import SessionAlreadyActiveError, SessionNotFoundError
from src.models.entities import Configuration, MonitoringSession, PrivacyZone, Screenshot
from src.services.monitoring_session_manager import MonitoringSessionManager


class _FakeThread:
    def __init__(self, target=None, daemon=None, name=None):
        self.target = target
        self.daemon = daemon
        self.name = name
        self.started = False
        self.join_called = False
        self.alive = False

    def start(self):
        self.started = True

    def is_alive(self):
        return self.alive

    def join(self, timeout=None):
        _ = timeout
        self.join_called = True


@pytest.fixture()
def config() -> Configuration:
    cfg = Configuration()
    cfg.monitoring.interval_seconds = 30
    cfg.monitoring.max_duration_minutes = 30
    cfg.monitoring.idle_pause_minutes = 5
    cfg.monitoring.change_detection = True
    return cfg


@pytest.fixture()
def screenshot(tmp_path: Path) -> Screenshot:
    file_path = tmp_path / "monitor.png"
    file_path.write_bytes(b"img")
    size = file_path.stat().st_size
    return Screenshot(
        id=uuid4(),
        timestamp=datetime.now(tz=UTC),
        file_path=file_path,
        format="png",
        original_size_bytes=size,
        optimized_size_bytes=size,
        resolution=(100, 100),
        source_monitor=0,
        capture_method="test",
        privacy_zones_applied=False,
    )


@pytest.fixture()
def manager(mocker, config: Configuration) -> MonitoringSessionManager:
    config_manager = mocker.Mock()
    config_manager.load_config.return_value = config

    return MonitoringSessionManager(
        config_manager=config_manager,
        temp_manager=mocker.Mock(),
        capture=mocker.Mock(),
        processor=mocker.Mock(),
        api_client=mocker.Mock(),
        idle_seconds_provider=lambda: None,
    )


def test_start_session_uses_default_interval_when_none(monkeypatch: pytest.MonkeyPatch, manager: MonitoringSessionManager) -> None:
    monkeypatch.setattr("src.services.monitoring_session_manager.threading.Thread", _FakeThread)

    session = manager.start_session(interval_seconds=None)

    assert session.interval_seconds == 30
    assert manager.get_active_session() is not None


def test_start_session_raises_when_already_active(
    monkeypatch: pytest.MonkeyPatch,
    manager: MonitoringSessionManager,
) -> None:
    monkeypatch.setattr("src.services.monitoring_session_manager.threading.Thread", _FakeThread)
    session = manager.start_session(interval_seconds=5)
    assert session is not None

    with pytest.raises(SessionAlreadyActiveError):
        manager.start_session(interval_seconds=5)


def test_stop_session_raises_when_not_found(manager: MonitoringSessionManager) -> None:
    with pytest.raises(SessionNotFoundError):
        manager.stop_session(uuid4())


def test_stop_session_joins_thread_when_alive(manager: MonitoringSessionManager) -> None:
    session = MonitoringSession(id=uuid4(), started_at=datetime.now(tz=UTC), interval_seconds=1)
    manager._active_session = session

    fake_thread = _FakeThread()
    fake_thread.alive = True
    manager._capture_thread = fake_thread

    manager.stop_session(session.id)

    assert fake_thread.join_called is True
    assert manager.get_active_session() is None


def test_pause_resume_raise_when_wrong_session(manager: MonitoringSessionManager) -> None:
    with pytest.raises(SessionNotFoundError):
        manager.pause_session(uuid4())
    with pytest.raises(SessionNotFoundError):
        manager.resume_session(uuid4())


def test_pause_session_already_paused_branch(manager: MonitoringSessionManager) -> None:
    session = MonitoringSession(id=uuid4(), started_at=datetime.now(tz=UTC), interval_seconds=1)
    session.paused_at = datetime.now(tz=UTC)
    manager._active_session = session

    manager.pause_session(session.id)

    assert manager._active_session.paused_at is not None


def test_resume_session_not_paused_branch(manager: MonitoringSessionManager) -> None:
    session = MonitoringSession(id=uuid4(), started_at=datetime.now(tz=UTC), interval_seconds=1)
    manager._active_session = session

    manager.resume_session(session.id)

    assert manager._active_session.paused_at is None


def test_capture_loop_exits_when_no_active_session(manager: MonitoringSessionManager, config: Configuration) -> None:
    manager.config_manager.load_config.return_value = config
    manager._active_session = None

    manager._capture_loop()


def test_capture_loop_handles_outer_exception(manager: MonitoringSessionManager, config: Configuration) -> None:
    session = MonitoringSession(id=uuid4(), started_at=datetime.now(tz=UTC), interval_seconds=0)
    manager._active_session = session
    manager.config_manager.load_config.return_value = config

    def _raise(_idle_minutes: int) -> None:
        raise RuntimeError("boom")

    manager._maybe_update_idle_pause = _raise
    manager._capture_loop()


def test_capture_loop_stops_when_max_duration_reached(manager: MonitoringSessionManager, config: Configuration) -> None:
    config.monitoring.max_duration_minutes = 0.000001
    session = MonitoringSession(id=uuid4(), started_at=datetime.now(tz=UTC), interval_seconds=1)
    manager._active_session = session
    manager.config_manager.load_config.return_value = config

    manager._capture_loop()

    assert manager._stop_event.is_set() is True
    assert manager._active_session.is_active is False


def test_capture_loop_skips_capture_when_paused(
    manager: MonitoringSessionManager,
    config: Configuration,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MonitoringSession(id=uuid4(), started_at=datetime.now(tz=UTC), interval_seconds=1)
    session.paused_at = datetime.now(tz=UTC)
    manager._active_session = session
    manager.config_manager.load_config.return_value = config

    def _sleep(_seconds: float) -> None:
        manager._stop_event.set()

    monkeypatch.setattr("src.services.monitoring_session_manager.time.sleep", _sleep)

    manager._capture_loop()

    manager.capture.capture_full_screen.assert_not_called()


def test_perform_capture_returns_when_no_active_session(manager: MonitoringSessionManager, config: Configuration) -> None:
    manager.config_manager.load_config.return_value = config
    manager._active_session = None

    manager._perform_capture(change_detection_enabled=True)


def test_perform_capture_skips_when_hash_unchanged(
    manager: MonitoringSessionManager,
    config: Configuration,
    screenshot: Screenshot,
) -> None:
    session = MonitoringSession(id=uuid4(), started_at=datetime.now(tz=UTC), interval_seconds=1)
    session.previous_screenshot_hash = "same"
    manager._active_session = session
    manager.config_manager.load_config.return_value = config
    manager.capture.capture_full_screen.return_value = screenshot
    manager.processor.calculate_image_hash.return_value = "same"

    manager._perform_capture(change_detection_enabled=True)

    manager.temp_manager.cleanup_temp_file.assert_called_once_with(screenshot.file_path)
    manager.api_client.send_multimodal_prompt.assert_not_called()


def test_perform_capture_updates_change_stats_and_applies_privacy(
    manager: MonitoringSessionManager,
    config: Configuration,
    screenshot: Screenshot,
) -> None:
    config.privacy.enabled = True
    config.privacy.zones = [PrivacyZone(name="p", x=0, y=0, width=10, height=10, monitor=0)]

    session = MonitoringSession(id=uuid4(), started_at=datetime.now(tz=UTC), interval_seconds=1)
    session.previous_screenshot_hash = "old"
    manager._active_session = session
    manager.config_manager.load_config.return_value = config
    manager.capture.capture_full_screen.return_value = screenshot
    manager.processor.calculate_image_hash.return_value = "new"
    manager.processor.apply_privacy_zones.return_value = screenshot
    manager.processor.optimize_image.return_value = screenshot
    manager.api_client.send_multimodal_prompt.return_value = "ok"

    manager._perform_capture(change_detection_enabled=True)

    assert session.previous_screenshot_hash == "new"
    assert session.last_change_detected_at is not None
    assert session.capture_count == 1
    assert session.last_capture_at is not None
    manager.processor.apply_privacy_zones.assert_called_once()


def test_perform_capture_first_change_detection_sets_hash(
    manager: MonitoringSessionManager,
    config: Configuration,
    screenshot: Screenshot,
) -> None:
    session = MonitoringSession(id=uuid4(), started_at=datetime.now(tz=UTC), interval_seconds=1)
    manager._active_session = session
    manager.config_manager.load_config.return_value = config
    manager.capture.capture_full_screen.return_value = screenshot
    manager.processor.calculate_image_hash.return_value = "first"
    manager.processor.optimize_image.return_value = screenshot
    manager.api_client.send_multimodal_prompt.return_value = "ok"

    manager._perform_capture(change_detection_enabled=True)

    assert session.previous_screenshot_hash == "first"


def test_get_system_idle_seconds_returns_none_when_tool_missing(
    manager: MonitoringSessionManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("src.services.monitoring_session_manager.shutil.which", lambda _tool: None)

    assert manager._get_system_idle_seconds() is None


def test_get_system_idle_seconds_returns_parsed_value(
    manager: MonitoringSessionManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("src.services.monitoring_session_manager.shutil.which", lambda _tool: "/usr/bin/xprintidle")
    monkeypatch.setattr(
        "src.services.monitoring_session_manager.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(stdout="2500\n"),
    )

    assert manager._get_system_idle_seconds() == 2.5


def test_get_system_idle_seconds_handles_parse_and_subprocess_errors(
    manager: MonitoringSessionManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("src.services.monitoring_session_manager.shutil.which", lambda _tool: "/usr/bin/xprintidle")
    monkeypatch.setattr(
        "src.services.monitoring_session_manager.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(stdout="nan-value"),
    )
    assert manager._get_system_idle_seconds() is None

    def _raise(*_args, **_kwargs):
        raise subprocess.SubprocessError("boom")

    monkeypatch.setattr("src.services.monitoring_session_manager.subprocess.run", _raise)
    assert manager._get_system_idle_seconds() is None
