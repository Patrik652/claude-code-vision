"""Executable contract tests for IRegionSelector using a deterministic fake implementation."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.interfaces.screenshot_service import IRegionSelector
from src.lib.exceptions import InvalidRegionError, RegionSelectionCancelledError, SelectionToolNotFoundError
from src.models.entities import CaptureRegion


@dataclass
class _Monitor:
    width: int
    height: int


class FakeRegionSelector(IRegionSelector):
    """Deterministic selector implementation to validate contract behavior."""

    def __init__(self) -> None:
        self._monitors = {0: _Monitor(1920, 1080), 1: _Monitor(2560, 1440)}
        self._graphical_mode = "ok"  # ok | cancel | tool_missing

    def set_graphical_mode(self, mode: str) -> None:
        self._graphical_mode = mode

    def select_region_graphical(self, monitor: int = 0) -> CaptureRegion:
        self._ensure_monitor(monitor)
        if self._graphical_mode == "cancel":
            raise RegionSelectionCancelledError()
        if self._graphical_mode == "tool_missing":
            raise SelectionToolNotFoundError()

        return CaptureRegion(
            x=20,
            y=30,
            width=640,
            height=360,
            monitor=monitor,
            selection_method="graphical",
        )

    def select_region_coordinates(
        self, x: int, y: int, width: int, height: int, monitor: int = 0
    ) -> CaptureRegion:
        monitor_info = self._ensure_monitor(monitor)

        region = CaptureRegion(
            x=x,
            y=y,
            width=width,
            height=height,
            monitor=monitor,
            selection_method="coordinates",
        )

        try:
            region.validate(monitor_width=monitor_info.width, monitor_height=monitor_info.height)
        except ValueError as exc:
            raise InvalidRegionError(str(exc)) from exc

        return region

    def _ensure_monitor(self, monitor: int) -> _Monitor:
        if monitor not in self._monitors:
            raise InvalidRegionError(f"Monitor {monitor} is not available")
        return self._monitors[monitor]


@pytest.fixture()
def selector_implementation() -> FakeRegionSelector:
    return FakeRegionSelector()


def test_interface_inheritance(selector_implementation: FakeRegionSelector) -> None:
    assert isinstance(selector_implementation, IRegionSelector)


def test_select_region_graphical_returns_capture_region(
    selector_implementation: FakeRegionSelector,
) -> None:
    region = selector_implementation.select_region_graphical()

    assert isinstance(region, CaptureRegion)
    assert region.selection_method == "graphical"
    assert region.monitor == 0
    assert region.width > 0
    assert region.height > 0


def test_select_region_graphical_specific_monitor(selector_implementation: FakeRegionSelector) -> None:
    region = selector_implementation.select_region_graphical(monitor=1)
    assert region.monitor == 1


def test_select_region_graphical_user_cancels(selector_implementation: FakeRegionSelector) -> None:
    selector_implementation.set_graphical_mode("cancel")
    with pytest.raises(RegionSelectionCancelledError):
        selector_implementation.select_region_graphical()


def test_select_region_graphical_tool_not_found(selector_implementation: FakeRegionSelector) -> None:
    selector_implementation.set_graphical_mode("tool_missing")
    with pytest.raises(SelectionToolNotFoundError):
        selector_implementation.select_region_graphical()


def test_select_region_coordinates_returns_capture_region(
    selector_implementation: FakeRegionSelector,
) -> None:
    region = selector_implementation.select_region_coordinates(
        x=100,
        y=100,
        width=400,
        height=300,
        monitor=0,
    )

    assert isinstance(region, CaptureRegion)
    assert region.x == 100
    assert region.y == 100
    assert region.width == 400
    assert region.height == 300
    assert region.monitor == 0
    assert region.selection_method == "coordinates"


@pytest.mark.parametrize(
    ("x", "y", "width", "height"),
    [(-10, 0, 100, 100), (0, -10, 100, 100), (0, 0, 0, 100), (0, 0, 100, 0), (0, 0, -1, 10), (0, 0, 10, -1)],
)
def test_select_region_coordinates_invalid_values_raise_error(
    selector_implementation: FakeRegionSelector,
    x: int,
    y: int,
    width: int,
    height: int,
) -> None:
    with pytest.raises(InvalidRegionError):
        selector_implementation.select_region_coordinates(
            x=x,
            y=y,
            width=width,
            height=height,
            monitor=0,
        )


def test_select_region_coordinates_large_values_within_monitor_allowed(
    selector_implementation: FakeRegionSelector,
) -> None:
    region = selector_implementation.select_region_coordinates(
        x=0,
        y=0,
        width=1920,
        height=1080,
        monitor=0,
    )

    assert region.width == 1920
    assert region.height == 1080


def test_select_region_coordinates_out_of_bounds_detected(
    selector_implementation: FakeRegionSelector,
) -> None:
    with pytest.raises(InvalidRegionError):
        selector_implementation.select_region_coordinates(
            x=1900,
            y=1000,
            width=100,
            height=100,
            monitor=0,
        )


def test_select_region_coordinates_multiple_monitors(selector_implementation: FakeRegionSelector) -> None:
    region_primary = selector_implementation.select_region_coordinates(0, 0, 100, 100, monitor=0)
    region_secondary = selector_implementation.select_region_coordinates(0, 0, 100, 100, monitor=1)

    assert region_primary.monitor == 0
    assert region_secondary.monitor == 1


def test_invalid_monitor_index_handled(selector_implementation: FakeRegionSelector) -> None:
    with pytest.raises(InvalidRegionError):
        selector_implementation.select_region_coordinates(0, 0, 10, 10, monitor=99)


def test_graphical_selection_invalid_monitor_index_handled(
    selector_implementation: FakeRegionSelector,
) -> None:
    with pytest.raises(InvalidRegionError):
        selector_implementation.select_region_graphical(monitor=99)
