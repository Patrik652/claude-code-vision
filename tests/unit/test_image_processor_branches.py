"""Additional branch coverage tests for PillowImageProcessor."""

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.lib.exceptions import ImageProcessingError
from src.models.entities import PrivacyZone, Screenshot
from src.services.image_processor import PillowImageProcessor
from src.services.temp_file_manager import TempFileManager


def _build_screenshot(path: Path, image_format: str = "jpeg") -> Screenshot:
    size = path.stat().st_size
    return Screenshot(
        id=uuid4(),
        timestamp=datetime.now(tz=UTC),
        file_path=path,
        format=image_format,
        original_size_bytes=size,
        optimized_size_bytes=size,
        resolution=(1200, 800),
        source_monitor=0,
        capture_method="test",
        privacy_zones_applied=False,
    )


@pytest.mark.parametrize("image_format", ["png", "webp"])
def test_apply_privacy_zones_supports_png_and_webp_branches(monkeypatch, tmp_path, image_format: str) -> None:
    source_path = tmp_path / f"source.{image_format}"
    source_path.write_bytes(b"source")

    temp_manager = TempFileManager(temp_dir=str(tmp_path / "temp"))
    processor = PillowImageProcessor(temp_manager=temp_manager)
    screenshot = _build_screenshot(source_path, image_format=image_format)
    zones = [PrivacyZone(name="redact", x=10, y=10, width=50, height=50, monitor=None)]

    fake_image = SimpleNamespace(save=lambda out_path, **_kwargs: Path(out_path).write_bytes(b"processed"))
    monkeypatch.setattr("src.services.image_processor.Image.open", lambda _path: fake_image)
    monkeypatch.setattr(
        "src.services.image_processor.ImageDraw.Draw",
        lambda _image: SimpleNamespace(rectangle=lambda *_args, **_kwargs: None),
    )

    processed = processor.apply_privacy_zones(screenshot, zones)

    assert processed.file_path.exists()
    assert processed.file_path.suffix == f".{image_format}"
    assert processed.privacy_zones_applied is True


def test_optimize_image_enters_resize_branch_when_size_not_reduced(monkeypatch, tmp_path) -> None:
    source_path = tmp_path / "source.jpg"
    source_path.write_bytes(b"x" * 300_000)

    temp_manager = TempFileManager(temp_dir=str(tmp_path / "temp"))
    processor = PillowImageProcessor(temp_manager=temp_manager)
    screenshot = _build_screenshot(source_path, image_format="jpeg")

    class FakeImage:
        def __init__(self, size):
            self.size = size
            self.resize_calls = 0

        def resize(self, size, _resampling):
            self.resize_calls += 1
            return FakeImage(size)

        def save(self, out_path, **_kwargs):
            Path(out_path).write_bytes(b"x" * 300_000)

    first_open = FakeImage((1400, 900))
    final_open = FakeImage((640, 480))
    images = [first_open, final_open]
    monkeypatch.setattr("src.services.image_processor.Image.open", lambda _path: images.pop(0))

    optimized = processor.optimize_image(screenshot, max_size_mb=0.0001)

    assert first_open.resize_calls > 0
    assert optimized.resolution == (640, 480)
    assert optimized.file_path.exists()


def test_calculate_image_hash_wraps_file_read_errors(monkeypatch, tmp_path) -> None:
    source_path = tmp_path / "source.jpg"
    source_path.write_bytes(b"content")

    temp_manager = TempFileManager(temp_dir=str(tmp_path / "temp"))
    processor = PillowImageProcessor(temp_manager=temp_manager)
    screenshot = _build_screenshot(source_path, image_format="jpeg")

    def _failing_open(*_args, **_kwargs):
        raise OSError("read failure")

    monkeypatch.setattr("builtins.open", _failing_open)

    with pytest.raises(ImageProcessingError, match="Failed to calculate image hash"):
        processor.calculate_image_hash(screenshot)
