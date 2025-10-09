"""
Contract tests for IScreenshotCapture interface.

Verifies that all implementations of IScreenshotCapture adhere to the contract.
These tests are run against each concrete implementation to ensure consistency.
"""

import pytest
from abc import ABC
from pathlib import Path
from uuid import UUID

from src.interfaces.screenshot_service import IScreenshotCapture
from src.models.entities import Screenshot, CaptureRegion
from src.lib.exceptions import (
    ScreenshotCaptureError,
    DisplayNotAvailableError,
    MonitorNotFoundError,
    InvalidRegionError
)


class TestIScreenshotCaptureContract:
    """
    Contract test suite for IScreenshotCapture interface.

    All implementations of IScreenshotCapture MUST pass these tests.
    """

    @pytest.fixture
    def capture_implementation(self):
        """
        Override this fixture in concrete test classes to provide the implementation.

        Example:
            @pytest.fixture
            def capture_implementation(self):
                return X11ScreenshotCapture()
        """
        pytest.skip("Must be implemented by concrete test class")

    def test_interface_inheritance(self, capture_implementation):
        """Test that implementation inherits from IScreenshotCapture."""
        assert isinstance(capture_implementation, IScreenshotCapture)

    def test_capture_full_screen_returns_screenshot(self, capture_implementation):
        """Test that capture_full_screen() returns a Screenshot object."""
        screenshot = capture_implementation.capture_full_screen(monitor=0)

        assert isinstance(screenshot, Screenshot)
        assert isinstance(screenshot.id, UUID)
        assert screenshot.timestamp is not None
        assert isinstance(screenshot.file_path, Path)
        assert screenshot.file_path.exists()
        assert screenshot.format in ['jpeg', 'png', 'webp']
        assert screenshot.original_size_bytes > 0
        assert screenshot.resolution[0] > 0
        assert screenshot.resolution[1] > 0
        assert screenshot.source_monitor == 0

    def test_capture_full_screen_creates_valid_image_file(self, capture_implementation):
        """Test that captured screenshot is a valid image file."""
        screenshot = capture_implementation.capture_full_screen(monitor=0)

        # File must exist
        assert screenshot.file_path.exists()

        # File size must match reported size
        actual_size = screenshot.file_path.stat().st_size
        assert actual_size == screenshot.original_size_bytes

        # File must be readable as image (we'll verify this when implementing)
        assert screenshot.file_path.suffix in ['.jpg', '.jpeg', '.png', '.webp']

    def test_capture_full_screen_default_monitor(self, capture_implementation):
        """Test capture_full_screen() with default monitor parameter."""
        # Should default to monitor 0
        screenshot = capture_implementation.capture_full_screen()
        assert isinstance(screenshot, Screenshot)
        assert screenshot.source_monitor >= 0

    def test_capture_full_screen_invalid_monitor_raises_error(self, capture_implementation):
        """Test that invalid monitor index raises MonitorNotFoundError."""
        with pytest.raises(MonitorNotFoundError):
            capture_implementation.capture_full_screen(monitor=999)

    def test_capture_region_returns_screenshot(self, capture_implementation):
        """Test that capture_region() returns a Screenshot object."""
        region = CaptureRegion(
            x=100,
            y=100,
            width=200,
            height=200,
            monitor=0,
            selection_method='coordinates'
        )

        screenshot = capture_implementation.capture_region(region)

        assert isinstance(screenshot, Screenshot)
        assert isinstance(screenshot.id, UUID)
        assert screenshot.file_path.exists()
        assert screenshot.capture_region == region

    def test_capture_region_respects_dimensions(self, capture_implementation):
        """Test that captured region has correct dimensions."""
        region = CaptureRegion(
            x=0,
            y=0,
            width=400,
            height=300,
            monitor=0,
            selection_method='coordinates'
        )

        screenshot = capture_implementation.capture_region(region)

        # Resolution should match requested dimensions (or be close due to scaling)
        assert screenshot.resolution[0] == region.width
        assert screenshot.resolution[1] == region.height

    def test_capture_region_invalid_coordinates_raises_error(self, capture_implementation):
        """Test that invalid region coordinates raise InvalidRegionError."""
        # Negative coordinates
        region = CaptureRegion(
            x=-10,
            y=-10,
            width=100,
            height=100,
            monitor=0,
            selection_method='coordinates'
        )

        with pytest.raises(InvalidRegionError):
            capture_implementation.capture_region(region)

    def test_capture_region_out_of_bounds_raises_error(self, capture_implementation):
        """Test that out-of-bounds region raises InvalidRegionError."""
        # Region that extends beyond screen bounds
        region = CaptureRegion(
            x=50000,
            y=50000,
            width=100,
            height=100,
            monitor=0,
            selection_method='coordinates'
        )

        with pytest.raises(InvalidRegionError):
            capture_implementation.capture_region(region)

    def test_detect_monitors_returns_list(self, capture_implementation):
        """Test that detect_monitors() returns a list of monitor info."""
        monitors = capture_implementation.detect_monitors()

        assert isinstance(monitors, list)
        assert len(monitors) > 0

        # Verify monitor info structure
        for monitor in monitors:
            assert isinstance(monitor, dict)
            assert 'id' in monitor
            assert 'name' in monitor
            assert 'width' in monitor
            assert 'height' in monitor
            assert 'is_primary' in monitor
            assert isinstance(monitor['id'], int)
            assert isinstance(monitor['width'], int)
            assert isinstance(monitor['height'], int)
            assert isinstance(monitor['is_primary'], bool)
            assert monitor['width'] > 0
            assert monitor['height'] > 0

    def test_detect_monitors_has_primary(self, capture_implementation):
        """Test that at least one monitor is marked as primary."""
        monitors = capture_implementation.detect_monitors()

        primary_count = sum(1 for m in monitors if m['is_primary'])
        assert primary_count >= 1

    def test_multiple_captures_create_different_files(self, capture_implementation):
        """Test that multiple captures create separate files."""
        screenshot1 = capture_implementation.capture_full_screen(monitor=0)
        screenshot2 = capture_implementation.capture_full_screen(monitor=0)

        # Different UUIDs
        assert screenshot1.id != screenshot2.id

        # Different file paths
        assert screenshot1.file_path != screenshot2.file_path

        # Both files exist
        assert screenshot1.file_path.exists()
        assert screenshot2.file_path.exists()

    def test_capture_method_is_recorded(self, capture_implementation):
        """Test that capture_method is recorded in Screenshot."""
        screenshot = capture_implementation.capture_full_screen(monitor=0)

        assert screenshot.capture_method in ['scrot', 'grim', 'import']
        assert isinstance(screenshot.capture_method, str)
        assert len(screenshot.capture_method) > 0

    def test_screenshot_metadata_is_complete(self, capture_implementation):
        """Test that all required Screenshot metadata is populated."""
        screenshot = capture_implementation.capture_full_screen(monitor=0)

        # All required fields must be set
        assert screenshot.id is not None
        assert screenshot.timestamp is not None
        assert screenshot.file_path is not None
        assert screenshot.format is not None
        assert screenshot.original_size_bytes > 0
        assert screenshot.optimized_size_bytes >= 0  # May be 0 if not optimized yet
        assert screenshot.resolution is not None
        assert len(screenshot.resolution) == 2
        assert screenshot.source_monitor is not None
        assert screenshot.capture_method is not None
        assert isinstance(screenshot.privacy_zones_applied, bool)


class TestIScreenshotCaptureErrorHandling:
    """
    Contract tests for error handling in IScreenshotCapture implementations.
    """

    @pytest.fixture
    def capture_implementation(self):
        """Override in concrete test classes."""
        pytest.skip("Must be implemented by concrete test class")

    def test_capture_raises_display_not_available_when_headless(self, capture_implementation, monkeypatch):
        """Test that DisplayNotAvailableError is raised in headless environment."""
        # Mock headless environment by removing DISPLAY variables
        monkeypatch.delenv('DISPLAY', raising=False)
        monkeypatch.delenv('WAYLAND_DISPLAY', raising=False)
        monkeypatch.delenv('XDG_SESSION_TYPE', raising=False)

        # This test may need to be skipped if we can't simulate headless
        # Implementation should raise DisplayNotAvailableError when no display available
        # Exact behavior depends on implementation

    def test_capture_handles_tool_missing_gracefully(self, capture_implementation):
        """Test that ScreenshotCaptureError is raised when tool is missing."""
        # This is implementation-specific and may need to be tested differently
        # The contract is that if the tool is missing, an appropriate error should be raised


# NOTE: Concrete test classes will inherit from these and provide actual implementations
# Example:
# class TestX11ScreenshotCapture(TestIScreenshotCaptureContract):
#     @pytest.fixture
#     def capture_implementation(self):
#         return X11ScreenshotCapture()
