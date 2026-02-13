"""Executable contract tests for IScreenshotCapture using a deterministic fake implementation."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from PIL import Image

from src.interfaces.screenshot_service import IScreenshotCapture
from src.lib.exceptions import DisplayNotAvailableError, InvalidRegionError, MonitorNotFoundError
from src.models.entities import CaptureRegion, Screenshot


class FakeScreenshotCapture(IScreenshotCapture):
    """Minimal deterministic implementation used to enforce interface contract behavior."""

    def __init__(self, out_dir: Path) -> None:
        self._out_dir = out_dir
        self._out_dir.mkdir(parents=True, exist_ok=True)
        self._counter = 0
        self._monitors = [
            {"id": 0, "name": "Primary", "width": 1920, "height": 1080, "is_primary": True},
            {"id": 1, "name": "External", "width": 2560, "height": 1440, "is_primary": False},
        ]

    def capture_full_screen(self, monitor: int = 0) -> Screenshot:
        self._ensure_display_available()
        monitor_info = self._monitor(monitor)
        return self._create_screenshot(
            width=monitor_info["width"],
            height=monitor_info["height"],
            monitor=monitor,
            capture_region=None,
        )

    def capture_region(self, region: CaptureRegion) -> Screenshot:
        self._ensure_display_available()
        if region.x < 0 or region.y < 0:
            raise InvalidRegionError("Coordinates must be non-negative")

        monitor = self._monitor(region.monitor)
        try:
            region.validate(monitor_width=monitor["width"], monitor_height=monitor["height"])
        except ValueError as exc:
            raise InvalidRegionError(str(exc)) from exc

        return self._create_screenshot(
            width=region.width,
            height=region.height,
            monitor=region.monitor,
            capture_region=region,
        )

    def detect_monitors(self) -> list[dict]:
        self._ensure_display_available()
        return list(self._monitors)

    def _monitor(self, monitor: int) -> dict:
        if monitor < 0 or monitor >= len(self._monitors):
            raise MonitorNotFoundError(monitor_id=monitor, available_count=len(self._monitors))
        return self._monitors[monitor]

    def _ensure_display_available(self) -> None:
        if os.getenv("FAKE_CAPTURE_HEADLESS") == "1":
            raise DisplayNotAvailableError()

    def _create_screenshot(
        self,
        *,
        width: int,
        height: int,
        monitor: int,
        capture_region: CaptureRegion | None,
    ) -> Screenshot:
        self._counter += 1
        file_path = self._out_dir / f"capture-{self._counter}.png"
        img = Image.new("RGB", (width, height), color=(20, 30, 40))
        img.save(file_path, format="PNG")

        size = file_path.stat().st_size
        return Screenshot(
            id=uuid4(),
            timestamp=datetime.now(tz=UTC),
            file_path=file_path,
            format="png",
            original_size_bytes=size,
            optimized_size_bytes=size,
            resolution=(width, height),
            source_monitor=monitor,
            capture_method="scrot",
            privacy_zones_applied=False,
            capture_region=capture_region,
        )


@pytest.fixture()
def capture_implementation(tmp_path: Path) -> FakeScreenshotCapture:
    return FakeScreenshotCapture(out_dir=tmp_path / "captures")


def test_interface_inheritance(capture_implementation: FakeScreenshotCapture) -> None:
    assert isinstance(capture_implementation, IScreenshotCapture)


def test_capture_full_screen_returns_screenshot(capture_implementation: FakeScreenshotCapture) -> None:
    screenshot = capture_implementation.capture_full_screen(monitor=0)

    assert isinstance(screenshot, Screenshot)
    assert screenshot.file_path.exists()
    assert screenshot.source_monitor == 0
    assert screenshot.resolution == (1920, 1080)
    assert screenshot.format == "png"


def test_capture_full_screen_default_monitor(capture_implementation: FakeScreenshotCapture) -> None:
    screenshot = capture_implementation.capture_full_screen()
    assert screenshot.source_monitor == 0


def test_capture_full_screen_invalid_monitor_raises_error(
    capture_implementation: FakeScreenshotCapture,
) -> None:
    with pytest.raises(MonitorNotFoundError):
        capture_implementation.capture_full_screen(monitor=999)


def test_capture_region_returns_screenshot(capture_implementation: FakeScreenshotCapture) -> None:
    region = CaptureRegion(x=100, y=120, width=300, height=220, monitor=0, selection_method="coordinates")

    screenshot = capture_implementation.capture_region(region)

    assert isinstance(screenshot, Screenshot)
    assert screenshot.file_path.exists()
    assert screenshot.capture_region == region
    assert screenshot.resolution == (300, 220)


def test_capture_region_invalid_coordinates_raises_error(
    capture_implementation: FakeScreenshotCapture,
) -> None:
    region = CaptureRegion(x=-1, y=0, width=20, height=20, monitor=0, selection_method="coordinates")

    with pytest.raises(InvalidRegionError):
        capture_implementation.capture_region(region)


def test_capture_region_out_of_bounds_raises_error(capture_implementation: FakeScreenshotCapture) -> None:
    region = CaptureRegion(x=1800, y=1000, width=300, height=200, monitor=0, selection_method="coordinates")

    with pytest.raises(InvalidRegionError):
        capture_implementation.capture_region(region)


def test_detect_monitors_returns_list(capture_implementation: FakeScreenshotCapture) -> None:
    monitors = capture_implementation.detect_monitors()

    assert isinstance(monitors, list)
    assert len(monitors) == 2
    for monitor in monitors:
        assert {"id", "name", "width", "height", "is_primary"}.issubset(monitor.keys())
        assert monitor["width"] > 0
        assert monitor["height"] > 0


def test_detect_monitors_has_primary(capture_implementation: FakeScreenshotCapture) -> None:
    monitors = capture_implementation.detect_monitors()
    assert any(monitor["is_primary"] for monitor in monitors)


def test_multiple_captures_create_different_files(capture_implementation: FakeScreenshotCapture) -> None:
    screenshot1 = capture_implementation.capture_full_screen(monitor=0)
    screenshot2 = capture_implementation.capture_full_screen(monitor=0)

    assert screenshot1.id != screenshot2.id
    assert screenshot1.file_path != screenshot2.file_path
    assert screenshot1.file_path.exists()
    assert screenshot2.file_path.exists()


def test_capture_method_is_recorded(capture_implementation: FakeScreenshotCapture) -> None:
    screenshot = capture_implementation.capture_full_screen(monitor=0)
    assert screenshot.capture_method == "scrot"


def test_screenshot_metadata_is_complete(capture_implementation: FakeScreenshotCapture) -> None:
    screenshot = capture_implementation.capture_full_screen(monitor=0)

    assert screenshot.id is not None
    assert screenshot.timestamp is not None
    assert screenshot.file_path is not None
    assert screenshot.original_size_bytes > 0
    assert screenshot.optimized_size_bytes > 0
    assert screenshot.resolution == (1920, 1080)
    assert isinstance(screenshot.privacy_zones_applied, bool)


def test_capture_raises_display_not_available_when_headless(
    capture_implementation: FakeScreenshotCapture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FAKE_CAPTURE_HEADLESS", "1")

    with pytest.raises(DisplayNotAvailableError):
        capture_implementation.capture_full_screen(monitor=0)


def test_capture_region_invalid_monitor_raises_monitor_not_found(
    capture_implementation: FakeScreenshotCapture,
) -> None:
    region = CaptureRegion(x=1, y=1, width=10, height=10, monitor=99, selection_method="coordinates")

    with pytest.raises(MonitorNotFoundError):
        capture_implementation.capture_region(region)
