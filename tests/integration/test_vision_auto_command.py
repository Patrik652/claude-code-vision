"""Integration tests for /vision.auto and /vision.stop CLI commands."""

from uuid import uuid4

import pytest
from click.testing import CliRunner

from src.lib.exceptions import SessionAlreadyActiveError, VisionCommandError


@pytest.fixture()
def cli_runner() -> CliRunner:
    return CliRunner()


def test_vision_auto_requires_service_when_context_missing(cli_runner: CliRunner) -> None:
    """Command should fail with actionable message when service is unavailable."""
    from src.cli.vision_auto_command import vision_auto

    result = cli_runner.invoke(vision_auto, ["--interval", "5"])

    assert result.exit_code != 0
    assert "Vision service not initialized" in result.output


def test_vision_stop_requires_service_when_context_missing(cli_runner: CliRunner) -> None:
    """Stop command should fail with actionable message when service is unavailable."""
    from src.cli.vision_stop_command import vision_stop

    result = cli_runner.invoke(vision_stop, [])

    assert result.exit_code != 0
    assert "Vision service not initialized" in result.output


def test_vision_auto_starts_monitoring_session(cli_runner: CliRunner, mocker) -> None:
    """Starts session and prints returned session id."""
    from src.cli.vision_auto_command import vision_auto

    session_id = uuid4()
    vision_service = mocker.Mock()
    vision_service.execute_vision_auto_command.return_value = session_id

    result = cli_runner.invoke(
        vision_auto,
        ["--interval", "15", "--monitor", "1"],
        obj={"vision_service": vision_service},
    )

    assert result.exit_code == 0
    assert "Monitoring session started" in result.output
    assert str(session_id) in result.output
    vision_service.execute_vision_auto_command.assert_called_once_with(interval_seconds=15)


def test_vision_auto_rejects_nonpositive_interval(cli_runner: CliRunner, mocker) -> None:
    """Validates interval before invoking service."""
    from src.cli.vision_auto_command import vision_auto

    vision_service = mocker.Mock()
    result = cli_runner.invoke(
        vision_auto,
        ["--interval", "0"],
        obj={"vision_service": vision_service},
    )

    assert result.exit_code != 0
    assert "Interval must be positive" in result.output
    vision_service.execute_vision_auto_command.assert_not_called()


def test_vision_auto_handles_active_session_error(cli_runner: CliRunner, mocker) -> None:
    """Shows friendly guidance when session is already active."""
    from src.cli.vision_auto_command import vision_auto

    vision_service = mocker.Mock()
    vision_service.execute_vision_auto_command.side_effect = SessionAlreadyActiveError("already active")

    result = cli_runner.invoke(
        vision_auto,
        [],
        obj={"vision_service": vision_service},
    )

    assert result.exit_code != 0
    assert "Cannot start monitoring session" in result.output
    assert "/vision.stop" in result.output


def test_vision_stop_stops_active_session(cli_runner: CliRunner, mocker) -> None:
    """Stops active session and prints confirmation."""
    from src.cli.vision_stop_command import vision_stop

    vision_service = mocker.Mock()

    result = cli_runner.invoke(
        vision_stop,
        [],
        obj={"vision_service": vision_service},
    )

    assert result.exit_code == 0
    assert "Monitoring session stopped successfully" in result.output
    vision_service.execute_vision_stop_command.assert_called_once_with()


def test_vision_stop_handles_no_active_session_error(cli_runner: CliRunner, mocker) -> None:
    """Shows actionable guidance when there is no active session."""
    from src.cli.vision_stop_command import vision_stop

    vision_service = mocker.Mock()
    vision_service.execute_vision_stop_command.side_effect = VisionCommandError(
        "No active monitoring session to stop"
    )

    result = cli_runner.invoke(
        vision_stop,
        [],
        obj={"vision_service": vision_service},
    )

    assert result.exit_code != 0
    assert "No monitoring session is currently active" in result.output
    assert "/vision.auto" in result.output
