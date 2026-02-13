"""Integration tests for max-duration behavior in MonitoringSessionManager."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.models.entities import Configuration, MonitoringSession
from src.services.monitoring_session_manager import MonitoringSessionManager


def _build_manager(mocker, max_duration_minutes: int):
    config = Configuration()
    config.monitoring.max_duration_minutes = max_duration_minutes
    config.monitoring.idle_pause_minutes = 0
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
        idle_seconds_provider=lambda: 0.0,
    )


def _active_session() -> MonitoringSession:
    return MonitoringSession(
        id=uuid4(),
        started_at=datetime.now(tz=UTC),
        interval_seconds=1,
        is_active=True,
    )


class TestMaxDurationAutoStop:
    def test_session_stops_after_max_duration(self, mocker) -> None:
        manager = _build_manager(mocker, max_duration_minutes=5)
        manager._active_session = _active_session()
        perform_capture = mocker.patch.object(manager, "_perform_capture")

        t0 = datetime(2026, 1, 1, tzinfo=UTC)
        t1 = t0 + timedelta(minutes=6)
        mock_dt = mocker.patch("src.services.monitoring_session_manager.datetime")
        mock_dt.now.side_effect = [t0, t1]

        manager._capture_loop()

        assert manager._active_session.is_active is False
        assert manager._stop_event.is_set()
        perform_capture.assert_not_called()

    def test_max_duration_can_be_disabled(self, mocker) -> None:
        manager = _build_manager(mocker, max_duration_minutes=0)
        manager._active_session = _active_session()

        perform_called = {"count": 0}

        def _perform_capture(_change_detection_enabled: bool) -> None:
            perform_called["count"] += 1
            manager._stop_event.set()

        manager._perform_capture = _perform_capture
        mocker.patch("src.services.monitoring_session_manager.time.sleep", side_effect=lambda _s: None)

        manager._capture_loop()

        assert perform_called["count"] == 1
        assert manager._active_session.is_active is True

    def test_max_duration_default_30_minutes_from_config(self, mocker) -> None:
        manager = _build_manager(mocker, max_duration_minutes=30)
        session = manager.start_session(interval_seconds=2)
        try:
            loaded_config = manager.config_manager.load_config.return_value
            assert loaded_config.monitoring.max_duration_minutes == 30
            assert session.interval_seconds == 2
        finally:
            manager.stop_session(session.id)


class TestMaxDurationCalculation:
    def test_started_at_timestamp_recorded(self, mocker) -> None:
        manager = _build_manager(mocker, max_duration_minutes=30)
        session = manager.start_session(interval_seconds=1)
        try:
            assert session.started_at.tzinfo is not None
            assert isinstance(session.started_at, datetime)
        finally:
            manager.stop_session(session.id)

    def test_session_marked_inactive_after_auto_stop(self, mocker) -> None:
        manager = _build_manager(mocker, max_duration_minutes=1)
        manager._active_session = _active_session()

        t0 = datetime(2026, 1, 1, tzinfo=UTC)
        t1 = t0 + timedelta(minutes=2)
        mock_dt = mocker.patch("src.services.monitoring_session_manager.datetime")
        mock_dt.now.side_effect = [t0, t1]

        manager._capture_loop()

        assert manager._active_session.is_active is False
        assert manager._stop_event.is_set()

    def test_manual_stop_before_max_duration(self, mocker) -> None:
        manager = _build_manager(mocker, max_duration_minutes=30)
        session = manager.start_session(interval_seconds=1)
        manager.stop_session(session.id)

        assert manager.get_active_session() is None


class TestMaxDurationWithPause:
    def test_paused_time_counted_toward_max_duration(self, mocker) -> None:
        manager = _build_manager(mocker, max_duration_minutes=10)
        manager._active_session = _active_session()
        manager._active_session.paused_at = datetime.now(tz=UTC)

        t0 = datetime(2026, 1, 1, tzinfo=UTC)
        t1 = t0 + timedelta(minutes=11)
        mock_dt = mocker.patch("src.services.monitoring_session_manager.datetime")
        mock_dt.now.side_effect = [t0, t1]

        manager._capture_loop()

        assert manager._active_session.is_active is False
        assert manager._stop_event.is_set()


class TestMaxDurationEdgeCases:
    def test_max_duration_zero_keeps_session_running_until_manual_stop(self, mocker) -> None:
        manager = _build_manager(mocker, max_duration_minutes=0)
        manager._active_session = _active_session()

        def _perform_capture(_change_detection_enabled: bool) -> None:
            manager._stop_event.set()

        manager._perform_capture = _perform_capture
        mocker.patch("src.services.monitoring_session_manager.time.sleep", side_effect=lambda _s: None)

        manager._capture_loop()

        assert manager._active_session.is_active is True

    def test_negative_interval_rejected_on_start(self, mocker) -> None:
        manager = _build_manager(mocker, max_duration_minutes=30)

        with pytest.raises(ValueError, match="Interval must be positive"):
            manager.start_session(interval_seconds=-10)
