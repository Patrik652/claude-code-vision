"""Integration tests for /vision CLI command with mocked service boundaries."""

import pytest
from click.testing import CliRunner

from src.lib.exceptions import (
    AuthenticationError,
    ConfigurationError,
    DisplayNotAvailableError,
    OAuthConfigNotFoundError,
    ScreenshotCaptureError,
    VisionCommandError,
)
from src.models.entities import Configuration


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def mocked_service(mocker):
    service = mocker.Mock()
    service.execute_vision_command.return_value = "Mocked response"
    service.config_manager.load_config.return_value = Configuration()
    return service


def test_vision_command_success(cli_runner: CliRunner, mocked_service, mocker) -> None:
    from src.cli.vision_command import vision

    mocker.patch("src.cli.vision_command.get_vision_service", return_value=mocked_service)
    result = cli_runner.invoke(vision, ["What do you see?"])

    assert result.exit_code == 0
    assert "Capturing screenshot" in result.output
    assert "Claude's Response:" in result.output
    assert "Mocked response" in result.output
    mocked_service.execute_vision_command.assert_called_once_with("What do you see?")


def test_vision_command_supports_long_prompt(cli_runner: CliRunner, mocked_service, mocker) -> None:
    from src.cli.vision_command import vision

    mocker.patch("src.cli.vision_command.get_vision_service", return_value=mocked_service)
    long_prompt = "analyze " * 120
    result = cli_runner.invoke(vision, [long_prompt])

    assert result.exit_code == 0
    mocked_service.execute_vision_command.assert_called_once_with(long_prompt)


def test_vision_command_supports_empty_prompt(cli_runner: CliRunner, mocked_service, mocker) -> None:
    from src.cli.vision_command import vision

    mocker.patch("src.cli.vision_command.get_vision_service", return_value=mocked_service)
    result = cli_runner.invoke(vision, [""])

    assert result.exit_code == 0
    mocked_service.execute_vision_command.assert_called_once_with("")


def test_vision_command_overrides_monitor_from_flag(
    cli_runner: CliRunner, mocked_service, mocker
) -> None:
    from src.cli.vision_command import vision

    cfg = Configuration()
    cfg.monitors.default = 0
    mocked_service.config_manager.load_config.return_value = cfg

    mocker.patch("src.cli.vision_command.get_vision_service", return_value=mocked_service)
    result = cli_runner.invoke(vision, ["Prompt", "--monitor", "2"])

    assert result.exit_code == 0
    assert cfg.monitors.default == 2


@pytest.mark.parametrize(
    ("error", "expected_text"),
    [
        (DisplayNotAvailableError("No display"), "No display available"),
        (ScreenshotCaptureError("Capture failed"), "Screenshot capture failed"),
        (OAuthConfigNotFoundError("Missing oauth"), "authentication not configured"),
        (AuthenticationError("invalid key"), "Authentication failed"),
        (ConfigurationError("bad config"), "Configuration invalid"),
        (VisionCommandError("bad workflow"), "Vision command failed"),
    ],
)
def test_vision_command_actionable_errors(
    cli_runner: CliRunner, mocked_service, mocker, error: Exception, expected_text: str
) -> None:
    from src.cli.vision_command import vision

    mocked_service.execute_vision_command.side_effect = error
    mocker.patch("src.cli.vision_command.get_vision_service", return_value=mocked_service)
    result = cli_runner.invoke(vision, ["Prompt"])

    assert result.exit_code == 1
    assert expected_text in result.output


def test_vision_command_handles_unexpected_errors(cli_runner: CliRunner, mocked_service, mocker) -> None:
    from src.cli.vision_command import vision

    mocked_service.execute_vision_command.side_effect = RuntimeError("boom")
    mocker.patch("src.cli.vision_command.get_vision_service", return_value=mocked_service)
    result = cli_runner.invoke(vision, ["Prompt"])

    assert result.exit_code == 1
    assert "Unexpected error" in result.output


def test_vision_command_handles_keyboard_interrupt(cli_runner: CliRunner, mocked_service, mocker) -> None:
    from src.cli.vision_command import vision

    mocked_service.execute_vision_command.side_effect = KeyboardInterrupt()
    mocker.patch("src.cli.vision_command.get_vision_service", return_value=mocked_service)
    result = cli_runner.invoke(vision, ["Prompt"])

    assert result.exit_code == 130
    assert "Interrupted by user" in result.output
