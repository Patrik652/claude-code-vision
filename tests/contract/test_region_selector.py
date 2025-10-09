"""
Contract tests for IRegionSelector interface.

Verifies that all implementations of IRegionSelector adhere to the contract.
These tests are run against each concrete implementation to ensure consistency.
"""

import pytest
from src.interfaces.screenshot_service import IRegionSelector
from src.models.entities import CaptureRegion
from src.lib.exceptions import (
    RegionSelectionCancelledError,
    SelectionToolNotFoundError,
    InvalidRegionError
)


class TestIRegionSelectorContract:
    """
    Contract test suite for IRegionSelector interface.

    All implementations of IRegionSelector MUST pass these tests.
    """

    @pytest.fixture
    def selector_implementation(self):
        """
        Override this fixture in concrete test classes to provide the implementation.

        Example:
            @pytest.fixture
            def selector_implementation(self):
                return SlurpRegionSelector()
        """
        pytest.skip("Must be implemented by concrete test class")

    def test_interface_inheritance(self, selector_implementation):
        """Test that implementation inherits from IRegionSelector."""
        assert isinstance(selector_implementation, IRegionSelector)

    def test_select_region_graphical_returns_capture_region(self, selector_implementation):
        """Test that select_region_graphical() returns a CaptureRegion object."""
        # This test requires user interaction or mocking
        # Skip in automated tests
        pytest.skip("Requires user interaction or mocking")

    def test_select_region_graphical_default_monitor(self, selector_implementation):
        """Test select_region_graphical() with default monitor parameter."""
        pytest.skip("Requires user interaction or mocking")

    def test_select_region_graphical_specific_monitor(self, selector_implementation):
        """Test select_region_graphical() with specific monitor."""
        pytest.skip("Requires user interaction or mocking")

    def test_select_region_graphical_user_cancels(self, selector_implementation):
        """Test that user cancellation raises RegionSelectionCancelledError."""
        pytest.skip("Requires user interaction or mocking")

    def test_select_region_graphical_tool_not_found(self, selector_implementation):
        """Test that missing tool raises SelectionToolNotFoundError."""
        pytest.skip("Requires mocking tool detection")

    def test_select_region_coordinates_returns_capture_region(self, selector_implementation):
        """Test that select_region_coordinates() returns a CaptureRegion object."""
        region = selector_implementation.select_region_coordinates(
            x=100,
            y=100,
            width=400,
            height=300,
            monitor=0
        )

        assert isinstance(region, CaptureRegion)
        assert region.x == 100
        assert region.y == 100
        assert region.width == 400
        assert region.height == 300
        assert region.monitor == 0
        assert region.selection_method == 'coordinates'

    def test_select_region_coordinates_validates_parameters(self, selector_implementation):
        """Test that select_region_coordinates() validates input parameters."""
        # Valid parameters should work
        region = selector_implementation.select_region_coordinates(
            x=0,
            y=0,
            width=100,
            height=100,
            monitor=0
        )
        assert isinstance(region, CaptureRegion)

    def test_select_region_coordinates_negative_x_raises_error(self, selector_implementation):
        """Test that negative x coordinate raises InvalidRegionError."""
        with pytest.raises(InvalidRegionError):
            selector_implementation.select_region_coordinates(
                x=-10,
                y=0,
                width=100,
                height=100,
                monitor=0
            )

    def test_select_region_coordinates_negative_y_raises_error(self, selector_implementation):
        """Test that negative y coordinate raises InvalidRegionError."""
        with pytest.raises(InvalidRegionError):
            selector_implementation.select_region_coordinates(
                x=0,
                y=-10,
                width=100,
                height=100,
                monitor=0
            )

    def test_select_region_coordinates_zero_width_raises_error(self, selector_implementation):
        """Test that zero width raises InvalidRegionError."""
        with pytest.raises(InvalidRegionError):
            selector_implementation.select_region_coordinates(
                x=0,
                y=0,
                width=0,
                height=100,
                monitor=0
            )

    def test_select_region_coordinates_zero_height_raises_error(self, selector_implementation):
        """Test that zero height raises InvalidRegionError."""
        with pytest.raises(InvalidRegionError):
            selector_implementation.select_region_coordinates(
                x=0,
                y=0,
                width=100,
                height=0,
                monitor=0
            )

    def test_select_region_coordinates_negative_width_raises_error(self, selector_implementation):
        """Test that negative width raises InvalidRegionError."""
        with pytest.raises(InvalidRegionError):
            selector_implementation.select_region_coordinates(
                x=0,
                y=0,
                width=-100,
                height=100,
                monitor=0
            )

    def test_select_region_coordinates_negative_height_raises_error(self, selector_implementation):
        """Test that negative height raises InvalidRegionError."""
        with pytest.raises(InvalidRegionError):
            selector_implementation.select_region_coordinates(
                x=0,
                y=0,
                width=100,
                height=-100,
                monitor=0
            )

    def test_select_region_coordinates_large_values(self, selector_implementation):
        """Test select_region_coordinates() with large coordinate values."""
        region = selector_implementation.select_region_coordinates(
            x=5000,
            y=3000,
            width=1920,
            height=1080,
            monitor=0
        )

        assert region.x == 5000
        assert region.y == 3000
        assert region.width == 1920
        assert region.height == 1080

    def test_select_region_coordinates_multiple_monitors(self, selector_implementation):
        """Test select_region_coordinates() with different monitor indices."""
        region1 = selector_implementation.select_region_coordinates(
            x=0, y=0, width=100, height=100, monitor=0
        )
        region2 = selector_implementation.select_region_coordinates(
            x=0, y=0, width=100, height=100, monitor=1
        )

        assert region1.monitor == 0
        assert region2.monitor == 1

    def test_select_region_coordinates_sets_selection_method(self, selector_implementation):
        """Test that selection_method is set to 'coordinates'."""
        region = selector_implementation.select_region_coordinates(
            x=0, y=0, width=100, height=100, monitor=0
        )

        assert region.selection_method == 'coordinates'


class TestIRegionSelectorGraphical:
    """
    Contract tests for graphical region selection.

    These tests require mocking or user interaction.
    """

    @pytest.fixture
    def selector_implementation(self):
        """Override in concrete test classes."""
        pytest.skip("Must be implemented by concrete test class")

    def test_graphical_selection_returns_valid_region(self, selector_implementation):
        """Test that graphical selection returns valid CaptureRegion."""
        pytest.skip("Requires user interaction or mocking")

    def test_graphical_selection_on_multimonitor(self, selector_implementation):
        """Test graphical selection on multi-monitor setup."""
        pytest.skip("Requires user interaction or mocking")

    def test_graphical_selection_respects_monitor_parameter(self, selector_implementation):
        """Test that monitor parameter is respected in graphical selection."""
        pytest.skip("Requires user interaction or mocking")

    def test_graphical_selection_handles_escape_key(self, selector_implementation):
        """Test that pressing Escape during selection raises RegionSelectionCancelledError."""
        pytest.skip("Requires user interaction or mocking")

    def test_graphical_selection_handles_window_close(self, selector_implementation):
        """Test that closing selection window raises RegionSelectionCancelledError."""
        pytest.skip("Requires user interaction or mocking")


class TestIRegionSelectorErrorHandling:
    """
    Contract tests for error handling in IRegionSelector implementations.
    """

    @pytest.fixture
    def selector_implementation(self):
        """Override in concrete test classes."""
        pytest.skip("Must be implemented by concrete test class")

    def test_coordinates_out_of_bounds_detected(self, selector_implementation):
        """Test that out-of-bounds coordinates are detected (if implementation validates)."""
        # Some implementations may validate against screen bounds
        # Others may defer validation to capture stage
        # This test documents expected behavior
        pytest.skip("Validation behavior depends on implementation")

    def test_invalid_monitor_index_handled(self, selector_implementation):
        """Test handling of invalid monitor index."""
        # Some implementations may validate monitor exists
        # Others may defer to capture stage
        pytest.skip("Validation behavior depends on implementation")


# NOTE: Concrete test classes will inherit from these and provide actual implementations
# Example:
# class TestSlurpRegionSelector(TestIRegionSelectorContract):
#     @pytest.fixture
#     def selector_implementation(self):
#         return SlurpRegionSelector()
