"""Executable contract tests for IImageProcessor using PillowImageProcessor."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from PIL import Image

from src.interfaces.screenshot_service import IImageProcessor
from src.lib.exceptions import ImageProcessingError
from src.models.entities import PrivacyZone, Screenshot
from src.services.image_processor import PillowImageProcessor
from src.services.temp_file_manager import TempFileManager


@pytest.fixture()
def processor_implementation(tmp_path) -> PillowImageProcessor:
    temp_manager = TempFileManager(temp_dir=str(tmp_path / "temp"))
    return PillowImageProcessor(temp_manager=temp_manager)


@pytest.fixture()
def sample_screenshot(tmp_path) -> Screenshot:
    img = Image.new("RGB", (1200, 900), color="white")
    pixels = img.load()
    for x in range(200, 1000):
        for y in range(150, 750):
            pixels[x, y] = ((x * 17) % 255, (y * 13) % 255, ((x + y) * 7) % 255)

    img_path = tmp_path / "sample.jpg"
    img.save(img_path, quality=95)

    size = img_path.stat().st_size
    return Screenshot(
        id=uuid4(),
        timestamp=datetime.now(tz=UTC),
        file_path=img_path,
        format="jpeg",
        original_size_bytes=size,
        optimized_size_bytes=size,
        resolution=(1200, 900),
        source_monitor=0,
        capture_method="test",
        privacy_zones_applied=False,
    )


@pytest.fixture()
def invalid_screenshot(tmp_path) -> Screenshot:
    return Screenshot(
        id=uuid4(),
        timestamp=datetime.now(tz=UTC),
        file_path=tmp_path / "missing.jpg",
        format="jpeg",
        original_size_bytes=0,
        optimized_size_bytes=0,
        resolution=(0, 0),
        source_monitor=0,
        capture_method="test",
        privacy_zones_applied=False,
    )


def test_interface_inheritance(processor_implementation) -> None:
    assert isinstance(processor_implementation, IImageProcessor)


def test_optimize_image_returns_screenshot(processor_implementation, sample_screenshot) -> None:
    optimized = processor_implementation.optimize_image(sample_screenshot, max_size_mb=2.0)
    assert isinstance(optimized, Screenshot)
    assert optimized.file_path.exists()


def test_optimize_image_preserves_metadata(processor_implementation, sample_screenshot) -> None:
    optimized = processor_implementation.optimize_image(sample_screenshot, max_size_mb=0.2)
    assert optimized.id == sample_screenshot.id
    assert optimized.timestamp == sample_screenshot.timestamp
    assert optimized.format == sample_screenshot.format
    assert optimized.source_monitor == sample_screenshot.source_monitor
    assert optimized.capture_method == sample_screenshot.capture_method


def test_optimize_image_updates_size_fields(processor_implementation, sample_screenshot) -> None:
    optimized = processor_implementation.optimize_image(sample_screenshot, max_size_mb=0.2)
    assert optimized.original_size_bytes == sample_screenshot.original_size_bytes
    assert optimized.optimized_size_bytes == optimized.file_path.stat().st_size
    assert optimized.optimized_size_bytes > 0


def test_optimize_image_maintains_aspect_ratio(processor_implementation, sample_screenshot) -> None:
    original_ratio = sample_screenshot.resolution[0] / sample_screenshot.resolution[1]
    optimized = processor_implementation.optimize_image(sample_screenshot, max_size_mb=0.2)
    optimized_ratio = optimized.resolution[0] / optimized.resolution[1]
    assert abs(original_ratio - optimized_ratio) / original_ratio < 0.01


def test_apply_privacy_zones_returns_screenshot(processor_implementation, sample_screenshot) -> None:
    zones = [PrivacyZone(name="zone", x=10, y=10, width=100, height=100, monitor=0)]
    processed = processor_implementation.apply_privacy_zones(sample_screenshot, zones)
    assert isinstance(processed, Screenshot)
    assert processed.file_path.exists()
    assert processed.privacy_zones_applied is True


def test_apply_privacy_zones_empty_list_marks_applied(processor_implementation, sample_screenshot) -> None:
    processed = processor_implementation.apply_privacy_zones(sample_screenshot, [])
    assert processed.privacy_zones_applied is True
    assert processed.file_path.exists()


def test_apply_privacy_zones_preserves_metadata(processor_implementation, sample_screenshot) -> None:
    zones = [PrivacyZone(name="zone", x=0, y=0, width=50, height=50, monitor=0)]
    processed = processor_implementation.apply_privacy_zones(sample_screenshot, zones)
    assert processed.id == sample_screenshot.id
    assert processed.timestamp == sample_screenshot.timestamp
    assert processed.format == sample_screenshot.format
    assert processed.source_monitor == sample_screenshot.source_monitor


def test_calculate_image_hash_contract(processor_implementation, sample_screenshot) -> None:
    hash1 = processor_implementation.calculate_image_hash(sample_screenshot)
    hash2 = processor_implementation.calculate_image_hash(sample_screenshot)
    assert isinstance(hash1, str)
    assert len(hash1) == 64
    assert hash1 == hash2


def test_calculate_image_hash_changes_with_content(processor_implementation, sample_screenshot) -> None:
    hash_original = processor_implementation.calculate_image_hash(sample_screenshot)
    zones = [PrivacyZone(name="zone", x=0, y=0, width=120, height=120, monitor=0)]
    modified = processor_implementation.apply_privacy_zones(sample_screenshot, zones)
    hash_modified = processor_implementation.calculate_image_hash(modified)
    assert hash_original != hash_modified


@pytest.mark.parametrize(
    "operation",
    ["optimize", "privacy", "hash"],
)
def test_invalid_file_raises_image_processing_error(
    processor_implementation, invalid_screenshot, operation: str
) -> None:
    with pytest.raises(ImageProcessingError):
        _run_invalid_operation(processor_implementation, invalid_screenshot, operation)


def _run_invalid_operation(processor_implementation, invalid_screenshot, operation: str) -> None:
    if operation == "optimize":
        processor_implementation.optimize_image(invalid_screenshot, max_size_mb=2.0)
    elif operation == "privacy":
        processor_implementation.apply_privacy_zones(
            invalid_screenshot,
            [PrivacyZone(name="z", x=0, y=0, width=10, height=10, monitor=0)],
        )
    else:
        processor_implementation.calculate_image_hash(invalid_screenshot)
