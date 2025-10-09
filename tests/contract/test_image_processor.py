"""
Contract tests for IImageProcessor interface.

Verifies that all implementations of IImageProcessor adhere to the contract.
These tests are run against each concrete implementation to ensure consistency.
"""

import pytest
from pathlib import Path
from uuid import uuid4
from datetime import datetime

from src.interfaces.screenshot_service import IImageProcessor
from src.models.entities import Screenshot, PrivacyZone
from src.lib.exceptions import ImageProcessingError


class TestIImageProcessorContract:
    """
    Contract test suite for IImageProcessor interface.

    All implementations of IImageProcessor MUST pass these tests.
    """

    @pytest.fixture
    def processor_implementation(self):
        """
        Override this fixture in concrete test classes to provide the implementation.

        Example:
            @pytest.fixture
            def processor_implementation(self):
                return PillowImageProcessor()
        """
        pytest.skip("Must be implemented by concrete test class")

    @pytest.fixture
    def sample_screenshot(self, tmp_path):
        """
        Create a sample Screenshot object for testing.

        This fixture should be overridden in concrete tests to provide a real image file.
        """
        pytest.skip("Must be implemented by concrete test class to provide real image")

    def test_interface_inheritance(self, processor_implementation):
        """Test that implementation inherits from IImageProcessor."""
        assert isinstance(processor_implementation, IImageProcessor)

    def test_optimize_image_returns_screenshot(self, processor_implementation, sample_screenshot):
        """Test that optimize_image() returns a Screenshot object."""
        optimized = processor_implementation.optimize_image(sample_screenshot, max_size_mb=2.0)

        assert isinstance(optimized, Screenshot)
        assert optimized.file_path.exists()

    def test_optimize_image_reduces_size_when_needed(self, processor_implementation, sample_screenshot):
        """Test that optimize_image() reduces file size when exceeding max_size_mb."""
        # If original is already small, this test may not apply
        original_size_mb = sample_screenshot.original_size_bytes / (1024 * 1024)

        if original_size_mb > 1.0:
            # Set max size smaller than original
            max_size_mb = original_size_mb * 0.5
            optimized = processor_implementation.optimize_image(sample_screenshot, max_size_mb=max_size_mb)

            # Optimized size should be smaller
            optimized_size_mb = optimized.optimized_size_bytes / (1024 * 1024)
            assert optimized_size_mb <= max_size_mb * 1.1  # Allow 10% tolerance

    def test_optimize_image_preserves_metadata(self, processor_implementation, sample_screenshot):
        """Test that optimize_image() preserves Screenshot metadata."""
        optimized = processor_implementation.optimize_image(sample_screenshot, max_size_mb=2.0)

        # Metadata should be preserved
        assert optimized.id == sample_screenshot.id
        assert optimized.timestamp == sample_screenshot.timestamp
        assert optimized.format == sample_screenshot.format
        assert optimized.source_monitor == sample_screenshot.source_monitor
        assert optimized.capture_method == sample_screenshot.capture_method

    def test_optimize_image_updates_size_fields(self, processor_implementation, sample_screenshot):
        """Test that optimize_image() updates optimized_size_bytes field."""
        optimized = processor_implementation.optimize_image(sample_screenshot, max_size_mb=2.0)

        # Original size should remain unchanged
        assert optimized.original_size_bytes == sample_screenshot.original_size_bytes

        # Optimized size should be set
        assert optimized.optimized_size_bytes > 0

        # File size should match optimized_size_bytes
        actual_size = optimized.file_path.stat().st_size
        assert actual_size == optimized.optimized_size_bytes

    def test_optimize_image_default_max_size(self, processor_implementation, sample_screenshot):
        """Test optimize_image() with default max_size_mb parameter."""
        # Should default to 2.0 MB
        optimized = processor_implementation.optimize_image(sample_screenshot)

        assert isinstance(optimized, Screenshot)
        assert optimized.file_path.exists()

    def test_optimize_image_very_small_limit(self, processor_implementation, sample_screenshot):
        """Test optimize_image() with very small size limit."""
        # Should aggressively compress to meet limit
        optimized = processor_implementation.optimize_image(sample_screenshot, max_size_mb=0.1)

        optimized_size_mb = optimized.optimized_size_bytes / (1024 * 1024)
        assert optimized_size_mb <= 0.15  # Allow some tolerance

    def test_optimize_image_maintains_aspect_ratio(self, processor_implementation, sample_screenshot):
        """Test that optimize_image() maintains aspect ratio when resizing."""
        original_ratio = sample_screenshot.resolution[0] / sample_screenshot.resolution[1]

        optimized = processor_implementation.optimize_image(sample_screenshot, max_size_mb=0.5)

        optimized_ratio = optimized.resolution[0] / optimized.resolution[1]

        # Aspect ratio should be approximately the same (within 1%)
        assert abs(original_ratio - optimized_ratio) / original_ratio < 0.01

    def test_apply_privacy_zones_returns_screenshot(self, processor_implementation, sample_screenshot):
        """Test that apply_privacy_zones() returns a Screenshot object."""
        zones = [
            PrivacyZone(
                name="Test Zone",
                x=10,
                y=10,
                width=100,
                height=100,
                monitor=0
            )
        ]

        processed = processor_implementation.apply_privacy_zones(sample_screenshot, zones)

        assert isinstance(processed, Screenshot)
        assert processed.file_path.exists()
        assert processed.privacy_zones_applied is True

    def test_apply_privacy_zones_empty_list(self, processor_implementation, sample_screenshot):
        """Test apply_privacy_zones() with empty zones list."""
        processed = processor_implementation.apply_privacy_zones(sample_screenshot, [])

        assert isinstance(processed, Screenshot)
        # With no zones, privacy_zones_applied might be False or True depending on implementation
        assert processed.file_path.exists()

    def test_apply_privacy_zones_multiple_zones(self, processor_implementation, sample_screenshot):
        """Test apply_privacy_zones() with multiple privacy zones."""
        zones = [
            PrivacyZone(name="Zone 1", x=10, y=10, width=50, height=50, monitor=0),
            PrivacyZone(name="Zone 2", x=100, y=100, width=80, height=80, monitor=0),
            PrivacyZone(name="Zone 3", x=200, y=50, width=60, height=120, monitor=0),
        ]

        processed = processor_implementation.apply_privacy_zones(sample_screenshot, zones)

        assert isinstance(processed, Screenshot)
        assert processed.privacy_zones_applied is True

    def test_apply_privacy_zones_preserves_metadata(self, processor_implementation, sample_screenshot):
        """Test that apply_privacy_zones() preserves Screenshot metadata."""
        zones = [PrivacyZone(name="Test", x=0, y=0, width=50, height=50, monitor=0)]

        processed = processor_implementation.apply_privacy_zones(sample_screenshot, zones)

        # Metadata should be preserved
        assert processed.id == sample_screenshot.id
        assert processed.timestamp == sample_screenshot.timestamp
        assert processed.format == sample_screenshot.format
        assert processed.source_monitor == sample_screenshot.source_monitor

    def test_calculate_image_hash_returns_string(self, processor_implementation, sample_screenshot):
        """Test that calculate_image_hash() returns a hash string."""
        hash_value = processor_implementation.calculate_image_hash(sample_screenshot)

        assert isinstance(hash_value, str)
        assert len(hash_value) > 0

    def test_calculate_image_hash_is_consistent(self, processor_implementation, sample_screenshot):
        """Test that calculate_image_hash() returns same hash for same image."""
        hash1 = processor_implementation.calculate_image_hash(sample_screenshot)
        hash2 = processor_implementation.calculate_image_hash(sample_screenshot)

        assert hash1 == hash2

    def test_calculate_image_hash_is_sha256_format(self, processor_implementation, sample_screenshot):
        """Test that hash is in SHA256 format (64 hex characters)."""
        hash_value = processor_implementation.calculate_image_hash(sample_screenshot)

        # SHA256 hash should be 64 hexadecimal characters
        assert len(hash_value) == 64
        assert all(c in '0123456789abcdef' for c in hash_value.lower())

    def test_calculate_image_hash_changes_with_content(self, processor_implementation, sample_screenshot):
        """Test that hash changes when image content changes."""
        hash_original = processor_implementation.calculate_image_hash(sample_screenshot)

        # Apply privacy zones to change content
        zones = [PrivacyZone(name="Change", x=0, y=0, width=100, height=100, monitor=0)]
        modified = processor_implementation.apply_privacy_zones(sample_screenshot, zones)

        hash_modified = processor_implementation.calculate_image_hash(modified)

        # Hashes should be different
        assert hash_original != hash_modified


class TestIImageProcessorErrorHandling:
    """
    Contract tests for error handling in IImageProcessor implementations.
    """

    @pytest.fixture
    def processor_implementation(self):
        """Override in concrete test classes."""
        pytest.skip("Must be implemented by concrete test class")

    @pytest.fixture
    def invalid_screenshot(self, tmp_path):
        """Create an invalid Screenshot for error testing."""
        # Screenshot pointing to non-existent file
        return Screenshot(
            id=uuid4(),
            timestamp=datetime.now(),
            file_path=tmp_path / "nonexistent.jpg",
            format="jpeg",
            original_size_bytes=0,
            optimized_size_bytes=0,
            resolution=(0, 0),
            source_monitor=0,
            capture_method="test",
            privacy_zones_applied=False
        )

    def test_optimize_image_invalid_file_raises_error(self, processor_implementation, invalid_screenshot):
        """Test that optimizing non-existent file raises ImageProcessingError."""
        with pytest.raises(ImageProcessingError):
            processor_implementation.optimize_image(invalid_screenshot, max_size_mb=2.0)

    def test_apply_privacy_zones_invalid_file_raises_error(self, processor_implementation, invalid_screenshot):
        """Test that applying privacy zones to non-existent file raises ImageProcessingError."""
        zones = [PrivacyZone(name="Test", x=0, y=0, width=50, height=50, monitor=0)]

        with pytest.raises(ImageProcessingError):
            processor_implementation.apply_privacy_zones(invalid_screenshot, zones)

    def test_calculate_hash_invalid_file_raises_error(self, processor_implementation, invalid_screenshot):
        """Test that calculating hash of non-existent file raises ImageProcessingError."""
        with pytest.raises(ImageProcessingError):
            processor_implementation.calculate_image_hash(invalid_screenshot)


# NOTE: Concrete test classes will inherit from these and provide actual implementations
# Example:
# class TestPillowImageProcessor(TestIImageProcessorContract):
#     @pytest.fixture
#     def processor_implementation(self):
#         return PillowImageProcessor()
#
#     @pytest.fixture
#     def sample_screenshot(self, tmp_path):
#         # Create a real test image using Pillow
#         from PIL import Image
#         img = Image.new('RGB', (800, 600), color='red')
#         img_path = tmp_path / "test.jpg"
#         img.save(img_path, quality=95)
#         return Screenshot(...)
