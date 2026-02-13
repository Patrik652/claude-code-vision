"""Integration tests for /vision.area command with mocked service boundary."""

import pytest
from click.testing import CliRunner

from src.lib.exceptions import (
    InvalidRegionError,
    RegionSelectionCancelledError,
    SelectionToolNotFoundError,
    VisionCommandError,
)
from src.models.entities import CaptureRegion


@pytest.fixture()
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def mocked_service(mocker):
    service = mocker.Mock()
    service.execute_vision_area_command.return_value = "Area response"
    return service


def test_vision_area_requires_service_when_context_missing(cli_runner: CliRunner) -> None:
    from src.cli.vision_area_command import vision_area

    result = cli_runner.invoke(vision_area, ["Prompt"])

    assert result.exit_code != 0
    assert "Vision service not initialized" in result.output


def test_vision_area_with_coords_calls_service(cli_runner: CliRunner, mocked_service, mocker) -> None:
    from src.cli.vision_area_command import vision_area

    mocker.patch("src.cli.vision_area_command.click.echo")
    result = cli_runner.invoke(
        vision_area,
        ["--coords", "100,120,400,300", "--monitor", "1", "What is here?"],
        obj={"vision_service": mocked_service},
    )

    assert result.exit_code == 0
    call = mocked_service.execute_vision_area_command.call_args
    assert call.kwargs["prompt"] == "What is here?"
    region = call.kwargs["region"]
    assert isinstance(region, CaptureRegion)
    assert (region.x, region.y, region.width, region.height, region.monitor) == (100, 120, 400, 300, 1)
    assert region.selection_method == "coordinates"


@pytest.mark.parametrize("bad_coords", ["100,100", "x,y,w,h", "100,100,0", "100"])
def test_vision_area_invalid_coords_are_rejected(
    cli_runner: CliRunner, mocked_service, bad_coords: str
) -> None:
    from src.cli.vision_area_command import vision_area

    result = cli_runner.invoke(
        vision_area,
        ["--coords", bad_coords, "Prompt"],
        obj={"vision_service": mocked_service},
    )

    assert result.exit_code != 0
    assert "Invalid coordinates format" in result.output
    mocked_service.execute_vision_area_command.assert_not_called()


def test_vision_area_without_coords_passes_none_region(
    cli_runner: CliRunner, mocked_service
) -> None:
    from src.cli.vision_area_command import vision_area

    result = cli_runner.invoke(
        vision_area,
        ["Prompt"],
        obj={"vision_service": mocked_service},
    )

    assert result.exit_code == 0
    mocked_service.execute_vision_area_command.assert_called_once_with(prompt="Prompt", region=None)


def test_vision_area_fallback_to_manual_coords_when_selection_fails(
    cli_runner: CliRunner, mocked_service, mocker
) -> None:
    from src.cli.vision_area_command import vision_area

    mocked_service.execute_vision_area_command.side_effect = [
        SelectionToolNotFoundError("slurp not found"),
        "Recovered by fallback",
    ]
    mocker.patch("src.cli.vision_area_command.click.confirm", return_value=True)
    mocker.patch("src.cli.vision_area_command.click.prompt", return_value="10,20,300,200")

    result = cli_runner.invoke(
        vision_area,
        ["Prompt"],
        obj={"vision_service": mocked_service},
    )

    assert result.exit_code == 0
    assert mocked_service.execute_vision_area_command.call_count == 2
    retry_region = mocked_service.execute_vision_area_command.call_args_list[1].kwargs["region"]
    assert isinstance(retry_region, CaptureRegion)
    assert (retry_region.x, retry_region.y, retry_region.width, retry_region.height) == (10, 20, 300, 200)


def test_vision_area_fallback_cancel_aborts(cli_runner: CliRunner, mocked_service, mocker) -> None:
    from src.cli.vision_area_command import vision_area

    mocked_service.execute_vision_area_command.side_effect = RegionSelectionCancelledError()
    mocker.patch("src.cli.vision_area_command.click.confirm", return_value=False)

    result = cli_runner.invoke(
        vision_area,
        ["Prompt"],
        obj={"vision_service": mocked_service},
    )

    assert result.exit_code != 0
    assert "Operation cancelled" in result.output


def test_vision_area_vision_command_error_is_actionable(
    cli_runner: CliRunner, mocked_service
) -> None:
    from src.cli.vision_area_command import vision_area

    mocked_service.execute_vision_area_command.side_effect = VisionCommandError("bad workflow")
    result = cli_runner.invoke(
        vision_area,
        ["Prompt"],
        obj={"vision_service": mocked_service},
    )

    assert result.exit_code != 0
    assert "Error: bad workflow" in result.output


def test_vision_area_invalid_region_error_is_actionable(
    cli_runner: CliRunner, mocked_service
) -> None:
    from src.cli.vision_area_command import vision_area

    mocked_service.execute_vision_area_command.side_effect = InvalidRegionError("out of bounds")
    result = cli_runner.invoke(
        vision_area,
        ["Prompt"],
        obj={"vision_service": mocked_service},
    )

    assert result.exit_code != 0
    assert "Invalid region" in result.output
