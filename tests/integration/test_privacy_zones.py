"""
Integration tests for privacy zone redaction.

Tests the complete workflow of privacy zone application in screenshots.
"""

import pytest
from pathlib import Path
from PIL import Image
from uuid import uuid4
from datetime import datetime

from src.models.entities import Screenshot, PrivacyZone
from src.services.image_processor import PillowImageProcessor
from src.services.temp_file_manager import TempFileManager
from src.lib.exceptions import ImageProcessingError


class TestPrivacyZoneRedaction:
    """Integration tests for privacy zone redaction workflow."""

    @pytest.fixture
    def image_processor(self, tmp_path):
        """Create PillowImageProcessor instance."""
        temp_manager = TempFileManager(temp_dir=str(tmp_path / "temp"))
        return PillowImageProcessor(temp_manager)

    @pytest.fixture
    def test_screenshot(self, tmp_path):
        """Create a test screenshot with identifiable content."""
        # Create a colorful test image
        img = Image.new('RGB', (800, 600), color='white')
        pixels = img.load()

        # Draw red square in top-left (will be redacted)
        for x in range(50, 150):
            for y in range(50, 150):
                pixels[x, y] = (255, 0, 0)

        # Draw green square in center (will NOT be redacted)
        for x in range(350, 450):
            for y in range(250, 350):
                pixels[x, y] = (0, 255, 0)

        # Draw blue square in bottom-right (will be redacted)
        for x in range(650, 750):
            for y in range(450, 550):
                pixels[x, y] = (0, 0, 255)

        # Save image
        img_path = tmp_path / "test_screenshot.jpg"
        img.save(img_path, quality=95)

        return Screenshot(
            id=uuid4(),
            timestamp=datetime.now(),
            file_path=img_path,
            format="jpeg",
            original_size_bytes=img_path.stat().st_size,
            optimized_size_bytes=img_path.stat().st_size,
            resolution=(800, 600),
            source_monitor=0,
            capture_method="test",
            privacy_zones_applied=False
        )

    def test_single_privacy_zone_redaction(self, image_processor, test_screenshot):
        """Test that a single privacy zone is correctly redacted."""
        zones = [
            PrivacyZone(
                name="Top Left Red Square",
                x=50,
                y=50,
                width=100,
                height=100,
                monitor=0
            )
        ]

        # Apply privacy zones
        processed = image_processor.apply_privacy_zones(test_screenshot, zones)

        # Verify screenshot object
        assert processed.privacy_zones_applied is True
        assert processed.file_path.exists()

        # Load processed image and verify redaction
        img = Image.open(processed.file_path)
        pixels = img.load()

        # Check that redacted area is black
        assert pixels[75, 75] == (0, 0, 0), "Privacy zone should be black"
        assert pixels[100, 100] == (0, 0, 0), "Privacy zone should be black"

        # Check that non-redacted area is NOT black
        center_color = pixels[400, 300]
        assert center_color != (0, 0, 0), "Non-redacted area should not be black"

    def test_multiple_privacy_zones_redaction(self, image_processor, test_screenshot):
        """Test that multiple privacy zones are correctly redacted."""
        zones = [
            PrivacyZone(name="Red Square", x=50, y=50, width=100, height=100, monitor=0),
            PrivacyZone(name="Blue Square", x=650, y=450, width=100, height=100, monitor=0),
        ]

        processed = image_processor.apply_privacy_zones(test_screenshot, zones)

        # Load processed image
        img = Image.open(processed.file_path)
        pixels = img.load()

        # Both zones should be black
        assert pixels[75, 75] == (0, 0, 0), "First zone should be black"
        assert pixels[700, 500] == (0, 0, 0), "Second zone should be black"

        # Center should NOT be black
        assert pixels[400, 300] != (0, 0, 0), "Center should not be redacted"

    def test_overlapping_privacy_zones(self, image_processor, test_screenshot):
        """Test that overlapping privacy zones work correctly."""
        zones = [
            PrivacyZone(name="Zone 1", x=50, y=50, width=150, height=100, monitor=0),
            PrivacyZone(name="Zone 2", x=100, y=75, width=100, height=100, monitor=0),
        ]

        processed = image_processor.apply_privacy_zones(test_screenshot, zones)

        # Load processed image
        img = Image.open(processed.file_path)
        pixels = img.load()

        # Overlapping area should be black
        assert pixels[150, 100] == (0, 0, 0), "Overlapping area should be black"

    def test_privacy_zone_at_image_edges(self, image_processor, test_screenshot):
        """Test privacy zones at image boundaries."""
        zones = [
            PrivacyZone(name="Top Edge", x=0, y=0, width=800, height=50, monitor=0),
            PrivacyZone(name="Bottom Edge", x=0, y=550, width=800, height=50, monitor=0),
        ]

        processed = image_processor.apply_privacy_zones(test_screenshot, zones)

        # Should not raise errors
        assert processed.privacy_zones_applied is True
        assert processed.file_path.exists()

        # Verify edges are redacted
        img = Image.open(processed.file_path)
        pixels = img.load()
        assert pixels[400, 10] == (0, 0, 0), "Top edge should be black"
        assert pixels[400, 570] == (0, 0, 0), "Bottom edge should be black"

    def test_empty_privacy_zones_list(self, image_processor, test_screenshot):
        """Test applying empty privacy zones list."""
        processed = image_processor.apply_privacy_zones(test_screenshot, [])

        # Should return valid screenshot
        assert isinstance(processed, Screenshot)
        assert processed.file_path.exists()

    def test_privacy_zones_preserve_image_quality(self, image_processor, test_screenshot):
        """Test that privacy zones don't degrade non-redacted areas."""
        zones = [
            PrivacyZone(name="Small Zone", x=10, y=10, width=50, height=50, monitor=0)
        ]

        # Get original center pixel color
        original_img = Image.open(test_screenshot.file_path)
        original_pixels = original_img.load()
        original_center = original_pixels[400, 300]

        # Apply privacy zone
        processed = image_processor.apply_privacy_zones(test_screenshot, zones)

        # Check center pixel is unchanged
        processed_img = Image.open(processed.file_path)
        processed_pixels = processed_img.load()
        processed_center = processed_pixels[400, 300]

        assert processed_center == original_center, "Non-redacted areas should be unchanged"

    def test_privacy_zones_with_different_monitor_values(self, image_processor, test_screenshot):
        """Test privacy zones with monitor parameter."""
        zones = [
            PrivacyZone(name="Monitor 0", x=50, y=50, width=100, height=100, monitor=0),
            PrivacyZone(name="Monitor 1", x=200, y=200, width=100, height=100, monitor=1),
        ]

        # For single monitor screenshot, only monitor=0 zone should apply
        processed = image_processor.apply_privacy_zones(test_screenshot, zones)

        assert processed.privacy_zones_applied is True


class TestPrivacyZoneValidation:
    """Integration tests for privacy zone validation during application."""

    @pytest.fixture
    def image_processor(self, tmp_path):
        """Create PillowImageProcessor instance."""
        temp_manager = TempFileManager(temp_dir=str(tmp_path / "temp"))
        return PillowImageProcessor(temp_manager)

    @pytest.fixture
    def simple_screenshot(self, tmp_path):
        """Create a simple test screenshot."""
        img = Image.new('RGB', (400, 300), color='blue')
        img_path = tmp_path / "simple.jpg"
        img.save(img_path)

        return Screenshot(
            id=uuid4(),
            timestamp=datetime.now(),
            file_path=img_path,
            format="jpeg",
            original_size_bytes=img_path.stat().st_size,
            optimized_size_bytes=img_path.stat().st_size,
            resolution=(400, 300),
            source_monitor=0,
            capture_method="test",
            privacy_zones_applied=False
        )

    def test_privacy_zone_outside_image_bounds(self, image_processor, simple_screenshot):
        """Test privacy zone that extends beyond image boundaries."""
        zones = [
            PrivacyZone(name="Too Large", x=0, y=0, width=5000, height=5000, monitor=0)
        ]

        # Should handle gracefully (clip to image bounds)
        processed = image_processor.apply_privacy_zones(simple_screenshot, zones)
        assert processed.privacy_zones_applied is True

    def test_privacy_zone_partially_outside_bounds(self, image_processor, simple_screenshot):
        """Test privacy zone partially outside image."""
        zones = [
            PrivacyZone(name="Partial", x=350, y=250, width=100, height=100, monitor=0)
        ]

        # Should handle gracefully
        processed = image_processor.apply_privacy_zones(simple_screenshot, zones)
        assert processed.privacy_zones_applied is True


class TestPrivacyZoneMetadata:
    """Integration tests for privacy zone metadata handling."""

    @pytest.fixture
    def image_processor(self, tmp_path):
        """Create PillowImageProcessor instance."""
        temp_manager = TempFileManager(temp_dir=str(tmp_path / "temp"))
        return PillowImageProcessor(temp_manager)

    @pytest.fixture
    def test_screenshot(self, tmp_path):
        """Create test screenshot."""
        img = Image.new('RGB', (200, 200), color='white')
        img_path = tmp_path / "metadata_test.jpg"
        img.save(img_path)

        return Screenshot(
            id=uuid4(),
            timestamp=datetime.now(),
            file_path=img_path,
            format="jpeg",
            original_size_bytes=img_path.stat().st_size,
            optimized_size_bytes=img_path.stat().st_size,
            resolution=(200, 200),
            source_monitor=0,
            capture_method="test",
            privacy_zones_applied=False
        )

    def test_privacy_zones_update_flag(self, image_processor, test_screenshot):
        """Test that privacy_zones_applied flag is updated."""
        zones = [PrivacyZone(name="Test", x=10, y=10, width=50, height=50, monitor=0)]

        # Before
        assert test_screenshot.privacy_zones_applied is False

        # After
        processed = image_processor.apply_privacy_zones(test_screenshot, zones)
        assert processed.privacy_zones_applied is True

    def test_privacy_zones_preserve_other_metadata(self, image_processor, test_screenshot):
        """Test that other metadata is preserved."""
        zones = [PrivacyZone(name="Test", x=10, y=10, width=50, height=50, monitor=0)]

        original_id = test_screenshot.id
        original_timestamp = test_screenshot.timestamp
        original_monitor = test_screenshot.source_monitor

        processed = image_processor.apply_privacy_zones(test_screenshot, zones)

        assert processed.id == original_id
        assert processed.timestamp == original_timestamp
        assert processed.source_monitor == original_monitor


@pytest.mark.skip(reason="Requires full implementation")
class TestPrivacyZoneWithVisionWorkflow:
    """Integration tests for privacy zones in complete vision workflow."""

    def test_privacy_zones_applied_before_transmission(self):
        """Test that privacy zones are applied before sending to API."""
        pytest.skip("Requires VisionService implementation")

    def test_privacy_zones_with_area_capture(self):
        """Test privacy zones work with /vision.area command."""
        pytest.skip("Requires full /vision.area implementation")
