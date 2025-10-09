"""
Unit tests for MonitoringSession state transitions.

Tests the state management logic in MonitoringSession entity.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from src.models.entities import MonitoringSession


class TestMonitoringSessionCreation:
    """Unit tests for MonitoringSession dataclass creation."""

    def test_monitoring_session_creation_all_fields(self):
        """Test MonitoringSession can be created with all fields."""
        session_id = uuid4()
        started_at = datetime.now()

        session = MonitoringSession(
            id=session_id,
            started_at=started_at,
            interval_seconds=30,
            is_active=True,
            capture_count=5,
            last_capture_at=datetime.now(),
            paused_at=None,
            last_change_detected_at=None,
            previous_screenshot_hash=None,
            screenshots=[]
        )

        assert session.id == session_id
        assert session.started_at == started_at
        assert session.interval_seconds == 30
        assert session.is_active is True
        assert session.capture_count == 5

    def test_monitoring_session_creation_minimal(self):
        """Test MonitoringSession with minimal required fields."""
        session_id = uuid4()
        started_at = datetime.now()

        session = MonitoringSession(
            id=session_id,
            started_at=started_at,
            interval_seconds=30
        )

        assert session.id == session_id
        assert session.started_at == started_at
        assert session.interval_seconds == 30
        assert session.is_active is True  # Default value
        assert session.capture_count == 0  # Default value


class TestMonitoringSessionStateTransitions:
    """Unit tests for MonitoringSession state transitions."""

    def test_new_session_is_active(self):
        """Test that new session starts in active state."""
        session = MonitoringSession(
            id=uuid4(),
            started_at=datetime.now(),
            interval_seconds=30
        )

        assert session.is_active is True
        assert session.paused_at is None

    def test_session_can_be_paused(self):
        """Test that session can be paused."""
        session = MonitoringSession(
            id=uuid4(),
            started_at=datetime.now(),
            interval_seconds=30,
            is_active=True
        )

        # Simulate pause
        session.paused_at = datetime.now()

        assert session.is_active is True  # Still active, just paused
        assert session.paused_at is not None

    def test_session_can_be_resumed(self):
        """Test that paused session can be resumed."""
        session = MonitoringSession(
            id=uuid4(),
            started_at=datetime.now(),
            interval_seconds=30,
            is_active=True,
            paused_at=datetime.now()
        )

        # Simulate resume
        session.paused_at = None

        assert session.is_active is True
        assert session.paused_at is None

    def test_session_can_be_stopped(self):
        """Test that session can be stopped."""
        session = MonitoringSession(
            id=uuid4(),
            started_at=datetime.now(),
            interval_seconds=30,
            is_active=True
        )

        # Simulate stop
        session.is_active = False

        assert session.is_active is False


class TestMonitoringSessionCaptureTracking:
    """Unit tests for capture tracking in MonitoringSession."""

    def test_capture_count_starts_at_zero(self):
        """Test that new session has zero captures."""
        session = MonitoringSession(
            id=uuid4(),
            started_at=datetime.now(),
            interval_seconds=30
        )

        assert session.capture_count == 0
        assert session.last_capture_at is None

    def test_capture_count_increments(self):
        """Test that capture count can be incremented."""
        session = MonitoringSession(
            id=uuid4(),
            started_at=datetime.now(),
            interval_seconds=30,
            capture_count=0
        )

        # Simulate captures
        session.capture_count += 1
        session.last_capture_at = datetime.now()

        assert session.capture_count == 1
        assert session.last_capture_at is not None

        session.capture_count += 1
        assert session.capture_count == 2

    def test_last_capture_at_updated(self):
        """Test that last_capture_at timestamp is updated."""
        now = datetime.now()
        session = MonitoringSession(
            id=uuid4(),
            started_at=now,
            interval_seconds=30
        )

        # First capture
        capture_time_1 = now + timedelta(seconds=30)
        session.last_capture_at = capture_time_1
        session.capture_count += 1

        assert session.last_capture_at == capture_time_1

        # Second capture
        capture_time_2 = now + timedelta(seconds=60)
        session.last_capture_at = capture_time_2
        session.capture_count += 1

        assert session.last_capture_at == capture_time_2


class TestMonitoringSessionChangeDetection:
    """Unit tests for change detection tracking in MonitoringSession."""

    def test_previous_screenshot_hash_starts_none(self):
        """Test that new session has no previous hash."""
        session = MonitoringSession(
            id=uuid4(),
            started_at=datetime.now(),
            interval_seconds=30
        )

        assert session.previous_screenshot_hash is None
        assert session.last_change_detected_at is None

    def test_previous_screenshot_hash_can_be_set(self):
        """Test that screenshot hash can be stored."""
        session = MonitoringSession(
            id=uuid4(),
            started_at=datetime.now(),
            interval_seconds=30
        )

        # Simulate storing hash after first capture
        test_hash = "abc123def456"
        session.previous_screenshot_hash = test_hash

        assert session.previous_screenshot_hash == test_hash

    def test_last_change_detected_at_updated(self):
        """Test that last_change_detected_at is updated when change detected."""
        session = MonitoringSession(
            id=uuid4(),
            started_at=datetime.now(),
            interval_seconds=30
        )

        # Simulate change detection
        change_time = datetime.now()
        session.last_change_detected_at = change_time

        assert session.last_change_detected_at == change_time

    def test_hash_comparison_logic(self):
        """Test logic for comparing screenshot hashes."""
        session = MonitoringSession(
            id=uuid4(),
            started_at=datetime.now(),
            interval_seconds=30,
            previous_screenshot_hash="hash1"
        )

        # Simulate comparison
        new_hash = "hash2"
        has_changed = (session.previous_screenshot_hash != new_hash)

        assert has_changed is True

        # Same hash
        same_hash = "hash1"
        has_changed = (session.previous_screenshot_hash != same_hash)

        assert has_changed is False


class TestMonitoringSessionTimestamps:
    """Unit tests for timestamp management in MonitoringSession."""

    def test_started_at_recorded(self):
        """Test that session start time is recorded."""
        start_time = datetime.now()
        session = MonitoringSession(
            id=uuid4(),
            started_at=start_time,
            interval_seconds=30
        )

        assert session.started_at == start_time

    def test_session_duration_calculation(self):
        """Test calculating session duration."""
        start_time = datetime.now() - timedelta(minutes=10)
        session = MonitoringSession(
            id=uuid4(),
            started_at=start_time,
            interval_seconds=30
        )

        # Calculate duration
        duration = datetime.now() - session.started_at

        assert duration.total_seconds() >= 600  # At least 10 minutes

    def test_time_since_last_capture(self):
        """Test calculating time since last capture."""
        now = datetime.now()
        last_capture = now - timedelta(seconds=45)

        session = MonitoringSession(
            id=uuid4(),
            started_at=now - timedelta(minutes=5),
            interval_seconds=30,
            last_capture_at=last_capture
        )

        # Calculate time since last capture
        time_since = datetime.now() - session.last_capture_at

        assert time_since.total_seconds() >= 45


class TestMonitoringSessionEquality:
    """Unit tests for MonitoringSession equality comparison."""

    def test_monitoring_session_equality(self):
        """Test MonitoringSession equality comparison."""
        session_id = uuid4()
        started_at = datetime.now()

        session1 = MonitoringSession(
            id=session_id,
            started_at=started_at,
            interval_seconds=30
        )
        session2 = MonitoringSession(
            id=session_id,
            started_at=started_at,
            interval_seconds=30
        )

        assert session1 == session2

    def test_monitoring_session_inequality(self):
        """Test MonitoringSession inequality comparison."""
        session1 = MonitoringSession(
            id=uuid4(),
            started_at=datetime.now(),
            interval_seconds=30
        )
        session2 = MonitoringSession(
            id=uuid4(),
            started_at=datetime.now(),
            interval_seconds=30
        )

        assert session1 != session2  # Different IDs


class TestMonitoringSessionEdgeCases:
    """Edge case tests for MonitoringSession."""

    def test_session_with_very_short_interval(self):
        """Test session with 1 second interval."""
        session = MonitoringSession(
            id=uuid4(),
            started_at=datetime.now(),
            interval_seconds=1
        )

        assert session.interval_seconds == 1

    def test_session_with_very_long_interval(self):
        """Test session with 1 hour interval."""
        session = MonitoringSession(
            id=uuid4(),
            started_at=datetime.now(),
            interval_seconds=3600
        )

        assert session.interval_seconds == 3600

    def test_session_with_many_captures(self):
        """Test session with large capture count."""
        session = MonitoringSession(
            id=uuid4(),
            started_at=datetime.now(),
            interval_seconds=30,
            capture_count=1000
        )

        assert session.capture_count == 1000

    def test_paused_at_in_past(self):
        """Test session paused in the past."""
        past_time = datetime.now() - timedelta(hours=2)
        session = MonitoringSession(
            id=uuid4(),
            started_at=datetime.now() - timedelta(hours=3),
            interval_seconds=30,
            paused_at=past_time
        )

        assert session.paused_at == past_time

        # Calculate pause duration
        pause_duration = datetime.now() - session.paused_at
        assert pause_duration.total_seconds() >= 7200  # At least 2 hours


class TestMonitoringSessionRepresentation:
    """Test MonitoringSession string representation."""

    def test_monitoring_session_repr(self):
        """Test MonitoringSession has useful string representation."""
        session = MonitoringSession(
            id=uuid4(),
            started_at=datetime.now(),
            interval_seconds=30
        )

        repr_str = repr(session)

        # Should contain key information
        assert "MonitoringSession" in repr_str or "id=" in repr_str

    def test_monitoring_session_str(self):
        """Test MonitoringSession string conversion."""
        session = MonitoringSession(
            id=uuid4(),
            started_at=datetime.now(),
            interval_seconds=30
        )

        str_repr = str(session)

        # Should be a valid string
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0
