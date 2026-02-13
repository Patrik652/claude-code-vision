"""
Unit tests for idle pause/resume behavior in MonitoringSessionManager.
"""

from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

from src.models.entities import MonitoringSession
from src.services.monitoring_session_manager import MonitoringSessionManager


def _create_manager(idle_seconds_provider):
    """Create manager with mocked dependencies for idle behavior tests."""
    return MonitoringSessionManager(
        config_manager=Mock(),
        temp_manager=Mock(),
        capture=Mock(),
        processor=Mock(),
        api_client=Mock(),
        idle_seconds_provider=idle_seconds_provider,
    )


def _create_active_session():
    """Create a minimal active session for tests."""
    return MonitoringSession(
        id=uuid4(),
        started_at=datetime.now(),
        interval_seconds=30,
        is_active=True,
    )


class TestMonitoringSessionManagerIdleBehavior:
    """Unit tests for idle pause and auto-resume behavior."""

    def test_pauses_session_when_idle_timeout_reached(self):
        """Session is paused when system idle time reaches threshold."""
        manager = _create_manager(idle_seconds_provider=lambda: 300.0)
        manager._active_session = _create_active_session()

        manager._maybe_update_idle_pause(idle_pause_minutes=5)

        assert manager._active_session.paused_at is not None

    def test_resumes_session_when_activity_returns(self):
        """Paused session resumes when idle time drops below threshold."""
        manager = _create_manager(idle_seconds_provider=lambda: 1.0)
        manager._active_session = _create_active_session()
        manager._active_session.paused_at = datetime.now()

        manager._maybe_update_idle_pause(idle_pause_minutes=5)

        assert manager._active_session.paused_at is None

    def test_does_not_pause_when_idle_detection_unavailable(self):
        """Session state does not change when idle detection cannot be read."""
        manager = _create_manager(idle_seconds_provider=lambda: None)
        manager._active_session = _create_active_session()

        manager._maybe_update_idle_pause(idle_pause_minutes=5)

        assert manager._active_session.paused_at is None

    def test_idle_pause_disabled_does_not_change_state(self):
        """Disabled idle pause leaves session state unchanged."""
        manager = _create_manager(idle_seconds_provider=lambda: 999.0)
        manager._active_session = _create_active_session()

        manager._maybe_update_idle_pause(idle_pause_minutes=0)

        assert manager._active_session.paused_at is None
