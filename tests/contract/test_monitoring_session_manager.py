"""Executable contract tests for IMonitoringSessionManager implementations."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from src.interfaces.screenshot_service import IMonitoringSessionManager
from src.lib.exceptions import SessionAlreadyActiveError, SessionNotFoundError
from src.models.entities import MonitoringSession


class ContractMonitoringSessionManager(IMonitoringSessionManager):
    """Small deterministic implementation used to enforce interface contract."""

    def __init__(self):
        self._active_session: MonitoringSession | None = None

    def start_session(self, interval_seconds: int | None = None) -> MonitoringSession:
        if self._active_session is not None:
            raise SessionAlreadyActiveError("session already active")

        interval = interval_seconds if interval_seconds is not None else 30
        if interval <= 0:
            raise ValueError("Interval must be positive")

        session = MonitoringSession(
            id=uuid4(),
            started_at=datetime.now(tz=UTC),
            interval_seconds=interval,
            is_active=True,
            capture_count=0,
        )
        self._active_session = session
        return session

    def stop_session(self, session_id: UUID) -> None:
        if self._active_session is None or self._active_session.id != session_id:
            raise SessionNotFoundError(f"Session {session_id} not found")
        self._active_session.is_active = False
        self._active_session = None

    def pause_session(self, session_id: UUID) -> None:
        if self._active_session is None or self._active_session.id != session_id:
            raise SessionNotFoundError(f"Session {session_id} not found")
        if self._active_session.paused_at is None:
            self._active_session.paused_at = datetime.now(tz=UTC)

    def resume_session(self, session_id: UUID) -> None:
        if self._active_session is None or self._active_session.id != session_id:
            raise SessionNotFoundError(f"Session {session_id} not found")
        self._active_session.paused_at = None

    def get_active_session(self) -> MonitoringSession | None:
        return self._active_session


@pytest.fixture()
def manager_implementation():
    return ContractMonitoringSessionManager()


def test_interface_inheritance(manager_implementation) -> None:
    assert isinstance(manager_implementation, IMonitoringSessionManager)


def test_start_session_returns_monitoring_session(manager_implementation) -> None:
    session = manager_implementation.start_session(interval_seconds=30)

    assert isinstance(session, MonitoringSession)
    assert isinstance(session.id, UUID)
    assert isinstance(session.started_at, datetime)
    assert session.interval_seconds == 30
    assert session.is_active is True
    assert session.capture_count == 0


def test_start_session_default_interval(manager_implementation) -> None:
    session = manager_implementation.start_session()
    assert session.interval_seconds == 30


def test_start_session_only_one_active_at_time(manager_implementation) -> None:
    session = manager_implementation.start_session(interval_seconds=30)
    with pytest.raises(SessionAlreadyActiveError):
        manager_implementation.start_session(interval_seconds=30)
    manager_implementation.stop_session(session.id)


def test_get_active_session_returns_none_when_no_session(manager_implementation) -> None:
    assert manager_implementation.get_active_session() is None


def test_stop_session_stops_monitoring(manager_implementation) -> None:
    session = manager_implementation.start_session(interval_seconds=30)
    manager_implementation.stop_session(session.id)
    assert manager_implementation.get_active_session() is None


def test_stop_session_nonexistent_raises_error(manager_implementation) -> None:
    with pytest.raises(SessionNotFoundError):
        manager_implementation.stop_session(uuid4())


def test_pause_and_resume_flow(manager_implementation) -> None:
    session = manager_implementation.start_session(interval_seconds=30)

    manager_implementation.pause_session(session.id)
    paused = manager_implementation.get_active_session()
    assert paused is not None
    assert paused.paused_at is not None

    manager_implementation.resume_session(session.id)
    resumed = manager_implementation.get_active_session()
    assert resumed is not None
    assert resumed.paused_at is None

    manager_implementation.stop_session(session.id)


def test_pause_resume_nonexistent_raise_error(manager_implementation) -> None:
    fake_id = uuid4()
    with pytest.raises(SessionNotFoundError):
        manager_implementation.pause_session(fake_id)
    with pytest.raises(SessionNotFoundError):
        manager_implementation.resume_session(fake_id)


def test_invalid_interval_raises_error(manager_implementation) -> None:
    with pytest.raises(ValueError, match="Interval must be positive"):
        manager_implementation.start_session(interval_seconds=0)
    with pytest.raises(ValueError, match="Interval must be positive"):
        manager_implementation.start_session(interval_seconds=-1)


def test_double_stop_raises_error(manager_implementation) -> None:
    session = manager_implementation.start_session(interval_seconds=30)
    manager_implementation.stop_session(session.id)
    with pytest.raises(SessionNotFoundError):
        manager_implementation.stop_session(session.id)
