"""
Unit tests for CaptureRegion validation.

Tests the validation logic in CaptureRegion entity.
"""

import pytest
from src.models.entities import CaptureRegion


class TestCaptureRegionValidation:
    """Unit tests for CaptureRegion.validate() method."""

    def test_validate_valid_region(self):
        """Test validation passes for valid region."""
        region = CaptureRegion(
            x=100,
            y=100,
            width=400,
            height=300,
            monitor=0,
            selection_method='coordinates'
        )

        # Should not raise any exception
        region.validate(monitor_width=1920, monitor_height=1080)

    def test_validate_region_at_origin(self):
        """Test validation for region starting at (0,0)."""
        region = CaptureRegion(
            x=0,
            y=0,
            width=800,
            height=600,
            monitor=0,
            selection_method='coordinates'
        )

        region.validate(monitor_width=1920, monitor_height=1080)

    def test_validate_region_at_bottom_right(self):
        """Test validation for region at bottom-right corner."""
        region = CaptureRegion(
            x=1120,
            y=480,
            width=800,
            height=600,
            monitor=0,
            selection_method='coordinates'
        )

        region.validate(monitor_width=1920, monitor_height=1080)

    def test_validate_full_screen_region(self):
        """Test validation for full-screen region."""
        region = CaptureRegion(
            x=0,
            y=0,
            width=1920,
            height=1080,
            monitor=0,
            selection_method='coordinates'
        )

        region.validate(monitor_width=1920, monitor_height=1080)

    def test_validate_negative_x_raises_error(self):
        """Test that negative x coordinate raises ValueError."""
        region = CaptureRegion(
            x=-10,
            y=0,
            width=400,
            height=300,
            monitor=0,
            selection_method='coordinates'
        )

        with pytest.raises(ValueError, match="Coordinates must be non-negative"):
            region.validate(monitor_width=1920, monitor_height=1080)

    def test_validate_negative_y_raises_error(self):
        """Test that negative y coordinate raises ValueError."""
        region = CaptureRegion(
            x=0,
            y=-10,
            width=400,
            height=300,
            monitor=0,
            selection_method='coordinates'
        )

        with pytest.raises(ValueError, match="Coordinates must be non-negative"):
            region.validate(monitor_width=1920, monitor_height=1080)

    def test_validate_zero_width_raises_error(self):
        """Test that zero width raises ValueError."""
        region = CaptureRegion(
            x=100,
            y=100,
            width=0,
            height=300,
            monitor=0,
            selection_method='coordinates'
        )

        with pytest.raises(ValueError, match="Dimensions must be positive"):
            region.validate(monitor_width=1920, monitor_height=1080)

    def test_validate_zero_height_raises_error(self):
        """Test that zero height raises ValueError."""
        region = CaptureRegion(
            x=100,
            y=100,
            width=400,
            height=0,
            monitor=0,
            selection_method='coordinates'
        )

        with pytest.raises(ValueError, match="Dimensions must be positive"):
            region.validate(monitor_width=1920, monitor_height=1080)

    def test_validate_negative_width_raises_error(self):
        """Test that negative width raises ValueError."""
        region = CaptureRegion(
            x=100,
            y=100,
            width=-400,
            height=300,
            monitor=0,
            selection_method='coordinates'
        )

        with pytest.raises(ValueError, match="Dimensions must be positive"):
            region.validate(monitor_width=1920, monitor_height=1080)

    def test_validate_negative_height_raises_error(self):
        """Test that negative height raises ValueError."""
        region = CaptureRegion(
            x=100,
            y=100,
            width=400,
            height=-300,
            monitor=0,
            selection_method='coordinates'
        )

        with pytest.raises(ValueError, match="Dimensions must be positive"):
            region.validate(monitor_width=1920, monitor_height=1080)

    def test_validate_exceeds_monitor_width_raises_error(self):
        """Test that region exceeding monitor width raises ValueError."""
        region = CaptureRegion(
            x=1600,
            y=100,
            width=800,  # 1600 + 800 = 2400 > 1920
            height=300,
            monitor=0,
            selection_method='coordinates'
        )

        with pytest.raises(ValueError, match="Region exceeds monitor width"):
            region.validate(monitor_width=1920, monitor_height=1080)

    def test_validate_exceeds_monitor_height_raises_error(self):
        """Test that region exceeding monitor height raises ValueError."""
        region = CaptureRegion(
            x=100,
            y=800,
            width=400,
            height=600,  # 800 + 600 = 1400 > 1080
            monitor=0,
            selection_method='coordinates'
        )

        with pytest.raises(ValueError, match="Region exceeds monitor height"):
            region.validate(monitor_width=1920, monitor_height=1080)

    def test_validate_x_at_monitor_edge(self):
        """Test region starting at right edge of monitor."""
        region = CaptureRegion(
            x=1920,
            y=0,
            width=1,
            height=100,
            monitor=0,
            selection_method='coordinates'
        )

        # Should fail - x=1920 with width=1 exceeds 1920
        with pytest.raises(ValueError, match="Region exceeds monitor width"):
            region.validate(monitor_width=1920, monitor_height=1080)

    def test_validate_y_at_monitor_edge(self):
        """Test region starting at bottom edge of monitor."""
        region = CaptureRegion(
            x=0,
            y=1080,
            width=100,
            height=1,
            monitor=0,
            selection_method='coordinates'
        )

        # Should fail - y=1080 with height=1 exceeds 1080
        with pytest.raises(ValueError, match="Region exceeds monitor height"):
            region.validate(monitor_width=1920, monitor_height=1080)


class TestCaptureRegionDataclass:
    """Unit tests for CaptureRegion dataclass properties."""

    def test_capture_region_creation(self):
        """Test CaptureRegion can be created with all fields."""
        region = CaptureRegion(
            x=100,
            y=200,
            width=300,
            height=400,
            monitor=1,
            selection_method='graphical'
        )

        assert region.x == 100
        assert region.y == 200
        assert region.width == 300
        assert region.height == 400
        assert region.monitor == 1
        assert region.selection_method == 'graphical'

    def test_capture_region_equality(self):
        """Test CaptureRegion equality comparison."""
        region1 = CaptureRegion(
            x=100, y=100, width=400, height=300,
            monitor=0, selection_method='coordinates'
        )
        region2 = CaptureRegion(
            x=100, y=100, width=400, height=300,
            monitor=0, selection_method='coordinates'
        )

        assert region1 == region2

    def test_capture_region_inequality(self):
        """Test CaptureRegion inequality comparison."""
        region1 = CaptureRegion(
            x=100, y=100, width=400, height=300,
            monitor=0, selection_method='coordinates'
        )
        region2 = CaptureRegion(
            x=200, y=100, width=400, height=300,
            monitor=0, selection_method='coordinates'
        )

        assert region1 != region2

    def test_capture_region_selection_methods(self):
        """Test different selection methods."""
        graphical = CaptureRegion(
            x=0, y=0, width=100, height=100,
            monitor=0, selection_method='graphical'
        )
        coordinates = CaptureRegion(
            x=0, y=0, width=100, height=100,
            monitor=0, selection_method='coordinates'
        )

        assert graphical.selection_method == 'graphical'
        assert coordinates.selection_method == 'coordinates'


class TestCaptureRegionEdgeCases:
    """Edge case tests for CaptureRegion."""

    def test_validate_very_small_region(self):
        """Test validation of 1x1 pixel region."""
        region = CaptureRegion(
            x=500,
            y=500,
            width=1,
            height=1,
            monitor=0,
            selection_method='coordinates'
        )

        region.validate(monitor_width=1920, monitor_height=1080)

    def test_validate_very_large_region(self):
        """Test validation of region matching entire 4K monitor."""
        region = CaptureRegion(
            x=0,
            y=0,
            width=3840,
            height=2160,
            monitor=0,
            selection_method='coordinates'
        )

        region.validate(monitor_width=3840, monitor_height=2160)

    def test_validate_with_different_monitor_sizes(self):
        """Test validation against different monitor sizes."""
        region = CaptureRegion(
            x=0, y=0, width=1024, height=768,
            monitor=0, selection_method='coordinates'
        )

        # Should work with 1024x768
        region.validate(monitor_width=1024, monitor_height=768)

        # Should fail with smaller monitor
        with pytest.raises(ValueError):
            region.validate(monitor_width=800, monitor_height=600)
