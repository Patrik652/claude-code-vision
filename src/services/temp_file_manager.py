"""
Temporary File Manager for Claude Code Vision.

Manages creation and cleanup of temporary screenshot files.
Implements ITempFileManager interface.
"""

import os
import tempfile
from pathlib import Path
from typing import List, Optional

from src.interfaces.screenshot_service import ITempFileManager
from src.lib.exceptions import TempFileError
from src.lib.logging_config import get_logger

logger = get_logger(__name__)


class TempFileManager(ITempFileManager):
    """
    Manages temporary files for screenshot storage.

    Creates files in configured temp directory (default: /tmp/claude-vision)
    and handles cleanup according to configuration settings.
    """

    def __init__(self, temp_dir: Optional[str] = None, cleanup_enabled: bool = True, keep_on_error: bool = False):
        """
        Initialize TempFileManager.

        Args:
            temp_dir: Directory for temp files. If None, uses /tmp/claude-vision
            cleanup_enabled: If True, cleanup temp files after use
            keep_on_error: If True, keep temp files when errors occur (for debugging)
        """
        self.temp_dir = Path(temp_dir or "/tmp/claude-vision")
        self.cleanup_enabled = cleanup_enabled
        self.keep_on_error = keep_on_error
        self._created_files: List[Path] = []  # Track files created in this session

        # Ensure temp directory exists
        self._ensure_temp_directory()

        logger.debug(f"TempFileManager initialized: dir={self.temp_dir}, cleanup={cleanup_enabled}")

    def _ensure_temp_directory(self) -> None:
        """
        Create temp directory if it doesn't exist.

        Raises:
            TempFileError: If directory creation fails
        """
        try:
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Temp directory ready: {self.temp_dir}")
        except Exception as e:
            raise TempFileError(f"Failed to create temp directory {self.temp_dir}: {e}") from e

    def create_temp_file(self, extension: str) -> Path:
        """
        Create temporary file for screenshot.

        Args:
            extension: File extension (e.g., 'jpg', 'png')

        Returns:
            Path to temp file

        Raises:
            TempFileError: If creation fails
        """
        # Ensure extension has no leading dot
        extension = extension.lstrip('.')

        try:
            # Create temporary file with specific extension
            fd, temp_path = tempfile.mkstemp(
                suffix=f'.{extension}',
                prefix='screenshot_',
                dir=str(self.temp_dir)
            )

            # Close the file descriptor (we just need the path)
            os.close(fd)

            path = Path(temp_path)
            self._created_files.append(path)

            logger.debug(f"Created temp file: {path}")
            return path

        except Exception as e:
            raise TempFileError(f"Failed to create temp file with extension '{extension}': {e}") from e

    def cleanup_temp_file(self, path: Path) -> None:
        """
        Delete temporary file.

        Args:
            path: Path to temp file

        Raises:
            TempFileError: If deletion fails (non-fatal)
        """
        if not self.cleanup_enabled:
            logger.debug(f"Cleanup disabled, keeping file: {path}")
            return

        try:
            if path.exists():
                path.unlink()

                # Remove from tracking list
                if path in self._created_files:
                    self._created_files.remove(path)

                logger.debug(f"Cleaned up temp file: {path}")
            else:
                logger.warning(f"Temp file already deleted: {path}")

        except Exception as e:
            # Non-fatal error - log but don't raise
            logger.error(f"Failed to cleanup temp file {path}: {e}")
            raise TempFileError(f"Failed to cleanup temp file {path}: {e}") from e

    def cleanup_all_temp_files(self) -> None:  # noqa: PLR0912
        """
        Delete all temporary files in temp directory.

        Raises:
            TempFileError: If cleanup fails (non-fatal)
        """
        if not self.cleanup_enabled:
            logger.debug("Cleanup disabled, keeping all files")
            return

        errors = []
        cleaned_count = 0

        try:
            # Clean up tracked files first
            for temp_file in list(self._created_files):
                try:
                    if temp_file.exists():
                        temp_file.unlink()
                        cleaned_count += 1
                        logger.debug(f"Cleaned up: {temp_file}")
                except Exception as e:
                    errors.append(f"{temp_file}: {e}")
                    logger.error(f"Failed to cleanup {temp_file}: {e}")

            # Clear tracking list
            self._created_files.clear()

            # Also cleanup any orphaned files in temp directory
            if self.temp_dir.exists():
                for temp_file in self.temp_dir.glob('screenshot_*'):
                    try:
                        if temp_file.is_file():
                            temp_file.unlink()
                            cleaned_count += 1
                            logger.debug(f"Cleaned up orphaned file: {temp_file}")
                    except Exception as e:
                        errors.append(f"{temp_file}: {e}")
                        logger.error(f"Failed to cleanup orphaned file {temp_file}: {e}")

            logger.info(f"Cleanup complete: {cleaned_count} files removed")

            if errors:
                error_msg = f"Cleanup completed with {len(errors)} errors:\n" + "\n".join(f"  - {e}" for e in errors)
                raise TempFileError(error_msg)

        except TempFileError:
            # Re-raise TempFileError
            raise
        except Exception as e:
            raise TempFileError(f"Failed to cleanup all temp files: {e}") from e

    def get_temp_dir(self) -> Path:
        """
        Get the temp directory path.

        Returns:
            Path to temp directory
        """
        return self.temp_dir

    def get_created_files(self) -> List[Path]:
        """
        Get list of files created in this session.

        Returns:
            List of temp file paths
        """
        return self._created_files.copy()

    def __del__(self) -> None:
        """Cleanup on object destruction if cleanup is enabled."""
        if self.cleanup_enabled and self._created_files:
            try:
                self.cleanup_all_temp_files()
            except Exception as e:
                logger.error(f"Error during cleanup in destructor: {e}")
