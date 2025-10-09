"""
Contract tests for IMonitoringSessionManager interface.

Verifies that all implementations of IMonitoringSessionManager adhere to the contract.
These tests are run against each concrete implementation to ensure consistency.
"""

import pytest
from uuid import UUID
from datetime import datetime
import time

from src.interfaces.screenshot_service import IMonitoringSessionManager
from src.models.entities import MonitoringSession
from src.lib.exceptions import SessionAlreadyActiveError, SessionNotFoundError


class TestIMonitoringSessionManagerContract:
    """
    Contract test suite for IMonitoringSessionManager interface.

    All implementations of IMonitoringSessionManager MUST pass these tests.
    """

    @pytest.fixture
    def manager_implementation(self):
        """
        Override this fixture in concrete test classes to provide the implementation.

        Example:
            @pytest.fixture
            def manager_implementation(self):
                return MonitoringSessionManager(...)
        """
        pytest.skip("Must be implemented by concrete test class")

    def test_interface_inheritance(self, manager_implementation):
        """Test that implementation inherits from IMonitoringSessionManager."""
        assert isinstance(manager_implementation, IMonitoringSessionManager)

    def test_start_session_returns_monitoring_session(self, manager_implementation):
        """Test that start_session() returns a MonitoringSession object."""
        session = manager_implementation.start_session(interval_seconds=30)

        assert isinstance(session, MonitoringSession)
        assert isinstance(session.id, UUID)
        assert isinstance(session.started_at, datetime)
        assert session.interval_seconds == 30
        assert session.is_active is True
        assert session.capture_count == 0

        # Cleanup
        manager_implementation.stop_session(session.id)

    def test_start_session_with_custom_interval(self, manager_implementation):
        """Test starting session with custom interval."""
        session = manager_implementation.start_session(interval_seconds=60)

        assert session.interval_seconds == 60
        assert session.is_active is True

        # Cleanup
        manager_implementation.stop_session(session.id)

    def test_start_session_default_interval(self, manager_implementation):
        """Test starting session with default interval."""
        # Should use default from configuration (30 seconds)
        session = manager_implementation.start_session()

        assert session.interval_seconds > 0
        assert session.is_active is True

        # Cleanup
        manager_implementation.stop_session(session.id)

    def test_start_session_only_one_active_at_time(self, manager_implementation):
        """Test that only one session can be active at a time."""
        # Start first session
        session1 = manager_implementation.start_session(interval_seconds=30)
        assert session1.is_active is True

        # Try to start second session - should raise error
        with pytest.raises(SessionAlreadyActiveError):
            manager_implementation.start_session(interval_seconds=30)

        # Cleanup
        manager_implementation.stop_session(session1.id)

    def test_get_active_session_returns_session(self, manager_implementation):
        """Test that get_active_session() returns the active session."""
        # Start session
        session = manager_implementation.start_session(interval_seconds=30)

        # Get active session
        active = manager_implementation.get_active_session()

        assert active is not None
        assert active.id == session.id
        assert active.is_active is True

        # Cleanup
        manager_implementation.stop_session(session.id)

    def test_get_active_session_returns_none_when_no_session(self, manager_implementation):
        """Test that get_active_session() returns None when no active session."""
        active = manager_implementation.get_active_session()
        assert active is None

    def test_stop_session_stops_monitoring(self, manager_implementation):
        """Test that stop_session() stops the monitoring session."""
        # Start session
        session = manager_implementation.start_session(interval_seconds=30)
        session_id = session.id

        # Stop session
        manager_implementation.stop_session(session_id)

        # Verify no active session
        active = manager_implementation.get_active_session()
        assert active is None

    def test_stop_session_nonexistent_raises_error(self, manager_implementation):
        """Test that stopping non-existent session raises error."""
        from uuid import uuid4
        fake_id = uuid4()

        with pytest.raises(SessionNotFoundError):
            manager_implementation.stop_session(fake_id)

    def test_pause_session_pauses_monitoring(self, manager_implementation):
        """Test that pause_session() pauses the session."""
        # Start session
        session = manager_implementation.start_session(interval_seconds=30)

        # Pause session
        manager_implementation.pause_session(session.id)

        # Get session to check state
        active = manager_implementation.get_active_session()
        assert active is not None
        assert active.paused_at is not None

        # Cleanup
        manager_implementation.stop_session(session.id)

    def test_pause_session_nonexistent_raises_error(self, manager_implementation):
        """Test that pausing non-existent session raises error."""
        from uuid import uuid4
        fake_id = uuid4()

        with pytest.raises(SessionNotFoundError):
            manager_implementation.pause_session(fake_id)

    def test_resume_session_resumes_monitoring(self, manager_implementation):
        """Test that resume_session() resumes paused session."""
        # Start session
        session = manager_implementation.start_session(interval_seconds=30)

        # Pause session
        manager_implementation.pause_session(session.id)

        # Resume session
        manager_implementation.resume_session(session.id)

        # Verify resumed
        active = manager_implementation.get_active_session()
        assert active is not None
        assert active.paused_at is None

        # Cleanup
        manager_implementation.stop_session(session.id)

    def test_resume_session_nonexistent_raises_error(self, manager_implementation):
        """Test that resuming non-existent session raises error."""
        from uuid import uuid4
        fake_id = uuid4()

        with pytest.raises(SessionNotFoundError):
            manager_implementation.resume_session(fake_id)


class TestIMonitoringSessionManagerLifecycle:
    """
    Contract tests for session lifecycle management.
    """

    @pytest.fixture
    def manager_implementation(self):
        """Override in concrete test classes."""
        pytest.skip("Must be implemented by concrete test class")

    def test_session_lifecycle_start_stop(self, manager_implementation):
        """Test complete session lifecycle: start → stop."""
        # Start
        session = manager_implementation.start_session(interval_seconds=30)
        assert session.is_active is True
        assert manager_implementation.get_active_session() is not None

        # Stop
        manager_implementation.stop_session(session.id)
        assert manager_implementation.get_active_session() is None

    def test_session_lifecycle_start_pause_resume_stop(self, manager_implementation):
        """Test complete session lifecycle: start → pause → resume → stop."""
        # Start
        session = manager_implementation.start_session(interval_seconds=30)
        assert session.is_active is True

        # Pause
        manager_implementation.pause_session(session.id)
        paused = manager_implementation.get_active_session()
        assert paused.paused_at is not None

        # Resume
        manager_implementation.resume_session(session.id)
        resumed = manager_implementation.get_active_session()
        assert resumed.paused_at is None

        # Stop
        manager_implementation.stop_session(session.id)
        assert manager_implementation.get_active_session() is None

    def test_multiple_sequential_sessions(self, manager_implementation):
        """Test starting multiple sessions sequentially."""
        # Session 1
        session1 = manager_implementation.start_session(interval_seconds=30)
        manager_implementation.stop_session(session1.id)

        # Session 2
        session2 = manager_implementation.start_session(interval_seconds=60)
        assert session2.id != session1.id
        manager_implementation.stop_session(session2.id)


class TestIMonitoringSessionManagerErrorHandling:
    """
    Contract tests for error handling in IMonitoringSessionManager implementations.
    """

    @pytest.fixture
    def manager_implementation(self):
        """Override in concrete test classes."""
        pytest.skip("Must be implemented by concrete test class")

    def test_invalid_interval_raises_error(self, manager_implementation):
        """Test that invalid interval raises error."""
        with pytest.raises((ValueError, SessionAlreadyActiveError)):
            # Try zero interval
            manager_implementation.start_session(interval_seconds=0)

        with pytest.raises((ValueError, SessionAlreadyActiveError)):
            # Try negative interval
            manager_implementation.start_session(interval_seconds=-10)

    def test_double_stop_raises_error(self, manager_implementation):
        """Test that stopping already stopped session raises error."""
        session = manager_implementation.start_session(interval_seconds=30)
        manager_implementation.stop_session(session.id)

        # Try to stop again
        with pytest.raises(SessionNotFoundError):
            manager_implementation.stop_session(session.id)

    def test_double_pause_handled_gracefully(self, manager_implementation):
        """Test that pausing already paused session is handled."""
        session = manager_implementation.start_session(interval_seconds=30)
        manager_implementation.pause_session(session.id)

        # Try to pause again - should not raise error
        manager_implementation.pause_session(session.id)

        # Cleanup
        manager_implementation.stop_session(session.id)

    def test_resume_unpaused_session_handled_gracefully(self, manager_implementation):
        """Test that resuming unpaused session is handled."""
        session = manager_implementation.start_session(interval_seconds=30)

        # Try to resume without pause - should not raise error
        manager_implementation.resume_session(session.id)

        # Cleanup
        manager_implementation.stop_session(session.id)


# NOTE: Concrete test classes will inherit from these and provide actual implementations
# Example:
# class TestMonitoringSessionManager(TestIMonitoringSessionManagerContract):
#     @pytest.fixture
#     def manager_implementation(self):
#         return MonitoringSessionManager(...)
