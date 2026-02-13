"""Integration tests for idle pause behavior in MonitoringSessionManager."""

from datetime import UTC, datetime
from uuid import uuid4

from src.models.entities import Configuration, MonitoringSession
from src.services.monitoring_session_manager import MonitoringSessionManager


def _build_manager(mocker, idle_seconds_provider, idle_pause_minutes: int = 5):
    config = Configuration()
    config.monitoring.idle_pause_minutes = idle_pause_minutes
    config.monitoring.max_duration_minutes = 0
    config.monitoring.change_detection = False
    config.monitoring.interval_seconds = 1

    config_manager = mocker.Mock()
    config_manager.load_config.return_value = config

    return MonitoringSessionManager(
        config_manager=config_manager,
        temp_manager=mocker.Mock(),
        capture=mocker.Mock(),
        processor=mocker.Mock(),
        api_client=mocker.Mock(),
        idle_seconds_provider=idle_seconds_provider,
    )


def _active_session() -> MonitoringSession:
    return MonitoringSession(
        id=uuid4(),
        started_at=datetime.now(tz=UTC),
        interval_seconds=1,
        is_active=True,
    )


class TestIdlePauseDetection:
    def test_session_pauses_after_idle_timeout(self, mocker) -> None:
        manager = _build_manager(mocker, idle_seconds_provider=lambda: 300.0, idle_pause_minutes=5)
        manager._active_session = _active_session()

        manager._maybe_update_idle_pause(idle_pause_minutes=5)

        assert manager._active_session.paused_at is not None
        assert manager._active_session.is_active is True

    def test_session_resumes_after_activity(self, mocker) -> None:
        manager = _build_manager(mocker, idle_seconds_provider=lambda: 1.0, idle_pause_minutes=5)
        manager._active_session = _active_session()
        manager._active_session.paused_at = datetime.now(tz=UTC)

        manager._maybe_update_idle_pause(idle_pause_minutes=5)

        assert manager._active_session.paused_at is None
        assert manager._active_session.is_active is True

    def test_idle_pause_can_be_disabled(self, mocker) -> None:
        manager = _build_manager(mocker, idle_seconds_provider=lambda: 9999.0, idle_pause_minutes=0)
        manager._active_session = _active_session()

        manager._maybe_update_idle_pause(idle_pause_minutes=0)

        assert manager._active_session.paused_at is None

    def test_idle_detection_unavailable_does_not_change_state(self, mocker) -> None:
        manager = _build_manager(mocker, idle_seconds_provider=lambda: None, idle_pause_minutes=5)
        manager._active_session = _active_session()

        manager._maybe_update_idle_pause(idle_pause_minutes=5)

        assert manager._active_session.paused_at is None


class TestIdlePauseState:
    def test_paused_at_timestamp_set_when_paused(self, mocker) -> None:
        manager = _build_manager(mocker, idle_seconds_provider=lambda: 600.0, idle_pause_minutes=5)
        manager._active_session = _active_session()

        manager._maybe_update_idle_pause(idle_pause_minutes=5)

        assert isinstance(manager._active_session.paused_at, datetime)

    def test_paused_at_timestamp_cleared_on_resume(self, mocker) -> None:
        manager = _build_manager(mocker, idle_seconds_provider=lambda: 0.0, idle_pause_minutes=5)
        manager._active_session = _active_session()
        manager._active_session.paused_at = datetime.now(tz=UTC)

        manager._maybe_update_idle_pause(idle_pause_minutes=5)

        assert manager._active_session.paused_at is None

    def test_stop_while_paused(self, mocker) -> None:
        manager = _build_manager(mocker, idle_seconds_provider=lambda: 600.0, idle_pause_minutes=5)
        session = _active_session()
        manager._active_session = session
        manager._active_session.paused_at = datetime.now(tz=UTC)

        manager.stop_session(session.id)

        assert manager.get_active_session() is None


class TestIdlePauseLoopBehavior:
    def test_capture_loop_skips_capture_when_session_paused(self, mocker) -> None:
        manager = _build_manager(mocker, idle_seconds_provider=lambda: 600.0, idle_pause_minutes=5)
        manager._active_session = _active_session()
        manager._active_session.paused_at = datetime.now(tz=UTC)

        perform_capture = mocker.patch.object(manager, "_perform_capture")

        def _sleep_and_stop(_seconds: float) -> None:
            manager._stop_event.set()

        mocker.patch("src.services.monitoring_session_manager.time.sleep", side_effect=_sleep_and_stop)

        manager._capture_loop()

        perform_capture.assert_not_called()
        assert manager._stop_event.is_set()

    def test_capture_loop_resumes_capture_after_activity(self, mocker) -> None:
        idle_values = iter([600.0, 0.0])
        manager = _build_manager(mocker, idle_seconds_provider=lambda: next(idle_values), idle_pause_minutes=5)
        manager._active_session = _active_session()

        call_count = {"perform": 0}

        def _perform_capture(_change_detection_enabled: bool) -> None:
            call_count["perform"] += 1
            manager._stop_event.set()

        manager._perform_capture = _perform_capture
        mocker.patch("src.services.monitoring_session_manager.time.sleep", side_effect=lambda _s: None)

        manager._capture_loop()

        assert call_count["perform"] == 1
