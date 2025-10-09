"""
Image Processor Implementation using Pillow.

Handles image optimization, privacy zone redaction, and hash calculation.
Implements IImageProcessor interface.
"""

import hashlib
from pathlib import Path
from typing import List
from PIL import Image, ImageDraw

from src.interfaces.screenshot_service import IImageProcessor
from src.models.entities import Screenshot, PrivacyZone
from src.lib.exceptions import ImageProcessingError
from src.lib.logging_config import get_logger
from src.services.temp_file_manager import TempFileManager

logger = get_logger(__name__)


class PillowImageProcessor(IImageProcessor):
    """
    Image processor implementation using Pillow (PIL).

    Handles:
    - Privacy zone redaction (black boxes)
    - Image optimization (resizing and compression)
    - Image hashing for change detection
    """

    def __init__(self, temp_manager: TempFileManager):
        """
        Initialize PillowImageProcessor.

        Args:
            temp_manager: TempFileManager instance for temp file handling
        """
        self.temp_manager = temp_manager
        logger.debug("PillowImageProcessor initialized")

    def apply_privacy_zones(self, screenshot: Screenshot, zones: List[PrivacyZone]) -> Screenshot:
        """
        Apply privacy zone redaction to screenshot.

        Args:
            screenshot: Screenshot to process
            zones: List of privacy zones to redact

        Returns:
            Screenshot with privacy zones blacked out

        Raises:
            ImageProcessingError: If processing fails
        """
        logger.info(f"Applying {len(zones)} privacy zone(s) to screenshot {screenshot.id}")

        if not screenshot.file_path.exists():
            raise ImageProcessingError(f"Screenshot file not found: {screenshot.file_path}")

        # If no zones, return original screenshot with flag set
        if not zones:
            logger.debug("No privacy zones to apply")
            screenshot.privacy_zones_applied = True
            return screenshot

        try:
            # Load image
            img = Image.open(screenshot.file_path)

            # Create drawing context
            draw = ImageDraw.Draw(img)

            # Apply each privacy zone
            for zone in zones:
                # Check if zone applies to this monitor
                if zone.monitor is not None and zone.monitor != screenshot.source_monitor:
                    logger.debug(f"Skipping zone '{zone.name}' (different monitor)")
                    continue

                # Draw black rectangle over zone
                draw.rectangle(
                    [(zone.x, zone.y), (zone.x + zone.width, zone.y + zone.height)],
                    fill='black'
                )
                logger.debug(f"Applied privacy zone '{zone.name}': ({zone.x},{zone.y}) {zone.width}x{zone.height}")

            # Create new temp file for processed image
            extension = screenshot.format if screenshot.format != 'jpeg' else 'jpg'
            new_path = self.temp_manager.create_temp_file(extension)

            # Save processed image
            save_kwargs = {}
            if screenshot.format in ['jpg', 'jpeg']:
                save_kwargs['quality'] = 85  # Use reasonable quality
                save_kwargs['format'] = 'JPEG'
            elif screenshot.format == 'png':
                save_kwargs['format'] = 'PNG'
            elif screenshot.format == 'webp':
                save_kwargs['format'] = 'WEBP'

            img.save(new_path, **save_kwargs)

            # Get new file size
            new_size = new_path.stat().st_size

            # Create new Screenshot object with updated path
            processed_screenshot = Screenshot(
                id=screenshot.id,
                timestamp=screenshot.timestamp,
                file_path=new_path,
                format=screenshot.format,
                original_size_bytes=screenshot.original_size_bytes,
                optimized_size_bytes=new_size,
                resolution=screenshot.resolution,
                source_monitor=screenshot.source_monitor,
                capture_method=screenshot.capture_method,
                privacy_zones_applied=True,
                capture_region=screenshot.capture_region
            )

            # Cleanup old file
            self.temp_manager.cleanup_temp_file(screenshot.file_path)

            logger.info(f"Privacy zones applied successfully, new size: {new_size} bytes")
            return processed_screenshot

        except Exception as e:
            raise ImageProcessingError(f"Failed to apply privacy zones: {e}")

    def optimize_image(self, screenshot: Screenshot, max_size_mb: float = 2.0) -> Screenshot:
        """
        Optimize screenshot to meet size constraints.

        Args:
            screenshot: Screenshot to optimize
            max_size_mb: Maximum size in megabytes

        Returns:
            Optimized screenshot (may be resized/recompressed)

        Raises:
            ImageProcessingError: If optimization fails
        """
        logger.info(f"Optimizing screenshot {screenshot.id} to max {max_size_mb} MB")

        if not screenshot.file_path.exists():
            raise ImageProcessingError(f"Screenshot file not found: {screenshot.file_path}")

        try:
            # Get current size
            current_size_mb = screenshot.file_path.stat().st_size / (1024 * 1024)

            # If already within limit, return as-is
            if current_size_mb <= max_size_mb:
                logger.info(f"Screenshot already within size limit ({current_size_mb:.2f} MB)")
                screenshot.optimized_size_bytes = screenshot.file_path.stat().st_size
                return screenshot

            # Load image
            img = Image.open(screenshot.file_path)
            original_width, original_height = img.size

            # Calculate target size
            max_size_bytes = max_size_mb * 1024 * 1024

            # Try compression first before resizing
            optimized_img = img
            quality = 85
            resize_factor = 1.0

            # Create temp file for optimized image
            extension = screenshot.format if screenshot.format != 'jpeg' else 'jpg'
            new_path = self.temp_manager.create_temp_file(extension)

            # Iteratively reduce quality/size until within limit
            max_iterations = 10
            for iteration in range(max_iterations):
                # Resize if needed
                if resize_factor < 1.0:
                    new_width = int(original_width * resize_factor)
                    new_height = int(original_height * resize_factor)
                    optimized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    logger.debug(f"Resized to {new_width}x{new_height} (factor={resize_factor:.2f})")

                # Save with current settings
                save_kwargs = {}
                if screenshot.format in ['jpg', 'jpeg']:
                    save_kwargs['quality'] = quality
                    save_kwargs['format'] = 'JPEG'
                    save_kwargs['optimize'] = True
                elif screenshot.format == 'png':
                    save_kwargs['format'] = 'PNG'
                    save_kwargs['optimize'] = True
                elif screenshot.format == 'webp':
                    save_kwargs['format'] = 'WEBP'
                    save_kwargs['quality'] = quality

                optimized_img.save(new_path, **save_kwargs)

                # Check size
                new_size = new_path.stat().st_size
                new_size_mb = new_size / (1024 * 1024)

                logger.debug(f"Iteration {iteration + 1}: size={new_size_mb:.2f} MB, quality={quality}, resize={resize_factor:.2f}")

                if new_size <= max_size_bytes:
                    # Success!
                    logger.info(f"Optimization successful: {new_size_mb:.2f} MB (quality={quality}, resize={resize_factor:.2f})")
                    break

                # Adjust parameters for next iteration
                if quality > 50:
                    # Reduce quality first
                    quality -= 10
                else:
                    # Then reduce size
                    resize_factor -= 0.1
                    if resize_factor < 0.3:
                        # Don't go below 30% of original size
                        logger.warning(f"Cannot optimize below {new_size_mb:.2f} MB without severe quality loss")
                        break

            # Get final resolution
            final_img = Image.open(new_path)
            final_resolution = final_img.size

            # Create new Screenshot object
            optimized_screenshot = Screenshot(
                id=screenshot.id,
                timestamp=screenshot.timestamp,
                file_path=new_path,
                format=screenshot.format,
                original_size_bytes=screenshot.original_size_bytes,
                optimized_size_bytes=new_path.stat().st_size,
                resolution=final_resolution,
                source_monitor=screenshot.source_monitor,
                capture_method=screenshot.capture_method,
                privacy_zones_applied=screenshot.privacy_zones_applied,
                capture_region=screenshot.capture_region
            )

            # Cleanup old file
            self.temp_manager.cleanup_temp_file(screenshot.file_path)

            return optimized_screenshot

        except Exception as e:
            raise ImageProcessingError(f"Failed to optimize image: {e}")

    def calculate_image_hash(self, screenshot: Screenshot) -> str:
        """
        Calculate hash of screenshot for change detection.

        Args:
            screenshot: Screenshot to hash

        Returns:
            SHA256 hash of image data

        Raises:
            ImageProcessingError: If hashing fails
        """
        logger.debug(f"Calculating hash for screenshot {screenshot.id}")

        if not screenshot.file_path.exists():
            raise ImageProcessingError(f"Screenshot file not found: {screenshot.file_path}")

        try:
            # Read file in binary mode
            with open(screenshot.file_path, 'rb') as f:
                file_data = f.read()

            # Calculate SHA256 hash
            hash_obj = hashlib.sha256()
            hash_obj.update(file_data)
            hash_value = hash_obj.hexdigest()

            logger.debug(f"Hash calculated: {hash_value}")
            return hash_value

        except Exception as e:
            raise ImageProcessingError(f"Failed to calculate image hash: {e}")
