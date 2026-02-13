"""
Monitoring Session Manager Implementation.

Manages auto-monitoring sessions with background capture loops.
Implements IMonitoringSessionManager interface.
"""

import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone
from typing import Callable, Optional
from uuid import UUID, uuid4

from src.interfaces.screenshot_service import (
    IClaudeAPIClient,
    IConfigurationManager,
    IImageProcessor,
    IMonitoringSessionManager,
    IScreenshotCapture,
    ITempFileManager,
)
from src.lib.exceptions import SessionAlreadyActiveError, SessionNotFoundError
from src.lib.logging_config import get_logger
from src.models.entities import MonitoringSession

logger = get_logger(__name__)


class MonitoringSessionManager(IMonitoringSessionManager):
    """
    Manages auto-monitoring sessions with background capture loops.

    Features:
    - Start/stop/pause/resume monitoring sessions
    - Background capture loop with configurable intervals
    - Change detection using image hashing
    - Idle detection and auto-pause
    - Max duration auto-stop
    - Single active session enforcement
    """

    def __init__(
        self,
        config_manager: IConfigurationManager,
        temp_manager: ITempFileManager,
        capture: IScreenshotCapture,
        processor: IImageProcessor,
        api_client: IClaudeAPIClient,
        idle_seconds_provider: Optional[Callable[[], Optional[float]]] = None
    ):
        """
        Initialize MonitoringSessionManager.

        Args:
            config_manager: Configuration manager
            temp_manager: Temp file manager
            capture: Screenshot capture implementation
            processor: Image processor
            api_client: Claude API client
            idle_seconds_provider: Optional idle detector callback for testability
        """
        self.config_manager = config_manager
        self.temp_manager = temp_manager
        self.capture = capture
        self.processor = processor
        self.api_client = api_client

        self._active_session: Optional[MonitoringSession] = None
        self._capture_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._idle_seconds_provider = idle_seconds_provider or self._get_system_idle_seconds

        logger.info("MonitoringSessionManager initialized")

    def start_session(self, interval_seconds: Optional[int] = None) -> MonitoringSession:
        """
        Start a new monitoring session.

        Args:
            interval_seconds: Capture interval, or None to use config default

        Returns:
            MonitoringSession object

        Raises:
            SessionAlreadyActiveError: If a session is already active
            ValueError: If interval is invalid
        """
        with self._lock:
            # Check if session already active
            if self._active_session is not None:
                raise SessionAlreadyActiveError(
                    f"Session {self._active_session.id} is already active. "
                    "Stop it first with stop_session()."
                )

            # Load configuration
            config = self.config_manager.load_config()

            # Use default interval if not specified
            if interval_seconds is None:
                interval_seconds = config.monitoring.interval_seconds

            # Validate interval
            if interval_seconds <= 0:
                raise ValueError("Interval must be positive")

            # Create new session
            session = MonitoringSession(
                id=uuid4(),
                started_at=datetime.now(timezone.utc),
                interval_seconds=interval_seconds,
                is_active=True,
                capture_count=0,
                last_capture_at=None,
                paused_at=None,
                last_change_detected_at=None,
                previous_screenshot_hash=None,
                screenshots=[]
            )

            self._active_session = session
            self._stop_event.clear()

            # Start background capture thread
            self._capture_thread = threading.Thread(
                target=self._capture_loop,
                daemon=True,
                name=f"MonitoringSession-{session.id}"
            )
            self._capture_thread.start()

            logger.info(f"Monitoring session started: {session.id} (interval={interval_seconds}s)")
            return session

    def stop_session(self, session_id: UUID) -> None:
        """
        Stop a monitoring session.

        Args:
            session_id: Session ID to stop

        Raises:
            SessionNotFoundError: If session not found
        """
        with self._lock:
            if self._active_session is None or self._active_session.id != session_id:
                raise SessionNotFoundError(f"Session {session_id} not found")

            # Mark session as inactive
            self._active_session.is_active = False

            # Signal thread to stop
            self._stop_event.set()

            logger.info(f"Stopping monitoring session: {session_id}")

        # Wait for thread to finish (outside lock to avoid deadlock)
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=5.0)

        with self._lock:
            logger.info(
                f"Monitoring session stopped: {session_id} "
                f"(captures={self._active_session.capture_count})"
            )
            self._active_session = None
            self._capture_thread = None

    def pause_session(self, session_id: UUID) -> None:
        """
        Pause a monitoring session.

        Args:
            session_id: Session ID to pause

        Raises:
            SessionNotFoundError: If session not found
        """
        with self._lock:
            if self._active_session is None or self._active_session.id != session_id:
                raise SessionNotFoundError(f"Session {session_id} not found")

            if self._active_session.paused_at is None:
                self._active_session.paused_at = datetime.now(timezone.utc)
                logger.info(f"Monitoring session paused: {session_id}")
            else:
                logger.debug(f"Session {session_id} already paused")

    def resume_session(self, session_id: UUID) -> None:
        """
        Resume a paused monitoring session.

        Args:
            session_id: Session ID to resume

        Raises:
            SessionNotFoundError: If session not found
        """
        with self._lock:
            if self._active_session is None or self._active_session.id != session_id:
                raise SessionNotFoundError(f"Session {session_id} not found")

            if self._active_session.paused_at is not None:
                self._active_session.paused_at = None
                logger.info(f"Monitoring session resumed: {session_id}")
            else:
                logger.debug(f"Session {session_id} not paused")

    def get_active_session(self) -> Optional[MonitoringSession]:
        """
        Get the currently active monitoring session.

        Returns:
            MonitoringSession if active, None otherwise
        """
        with self._lock:
            return self._active_session

    def _capture_loop(self) -> None:
        """
        Background capture loop.

        Runs in separate thread, captures screenshots at intervals.
        """
        logger.info("Capture loop started")

        config = self.config_manager.load_config()
        max_duration_minutes = config.monitoring.max_duration_minutes
        idle_pause_minutes = config.monitoring.idle_pause_minutes
        change_detection_enabled = config.monitoring.change_detection

        session_start = datetime.now(timezone.utc)

        try:
            while not self._stop_event.is_set():
                with self._lock:
                    if self._active_session is None:
                        break

                    # Check max duration
                    if max_duration_minutes > 0:
                        elapsed = (datetime.now(timezone.utc) - session_start).total_seconds() / 60
                        if elapsed >= max_duration_minutes:
                            logger.info(
                                f"Max duration reached ({max_duration_minutes} min), "
                                "stopping session"
                            )
                            self._active_session.is_active = False
                            self._stop_event.set()
                            break

                    # Check if paused
                    self._maybe_update_idle_pause(idle_pause_minutes)
                    if self._active_session.paused_at is not None:
                        # Session is paused, skip capture
                        time.sleep(1)
                        continue

                    # Perform capture
                    try:
                        self._perform_capture(change_detection_enabled)
                    except Exception as e:
                        logger.error(f"Capture failed: {e}", exc_info=True)
                        # Continue monitoring despite error

                # Sleep for interval
                interval = self._active_session.interval_seconds if self._active_session else 30
                time.sleep(interval)

        except Exception as e:
            logger.error(f"Capture loop failed: {e}", exc_info=True)
        finally:
            logger.info("Capture loop stopped")

    def _perform_capture(self, change_detection_enabled: bool) -> None:
        """
        Perform a single capture.

        Args:
            change_detection_enabled: Whether to use change detection

        Note: Should be called while holding self._lock
        """
        try:
            config = self.config_manager.load_config()
            session = self._active_session
            if session is None:
                logger.debug("No active session available for capture; skipping")
                return

            # Capture full screen
            logger.debug("Capturing screenshot for monitoring")
            screenshot = self.capture.capture_full_screen(monitor=config.monitors.default)

            # Check for changes if enabled
            if change_detection_enabled and session.previous_screenshot_hash:
                current_hash = self.processor.calculate_image_hash(screenshot)

                if current_hash == session.previous_screenshot_hash:
                    logger.debug("No change detected, skipping transmission")
                    self.temp_manager.cleanup_temp_file(screenshot.file_path)
                    return

                session.previous_screenshot_hash = current_hash
                session.last_change_detected_at = datetime.now(timezone.utc)
            elif change_detection_enabled:
                # First capture, store hash
                session.previous_screenshot_hash = self.processor.calculate_image_hash(screenshot)

            # Apply privacy zones if configured
            if config.privacy.enabled and config.privacy.zones:
                screenshot = self.processor.apply_privacy_zones(screenshot, config.privacy.zones)

            # Optimize image
            screenshot = self.processor.optimize_image(screenshot, config.screenshot.max_size_mb)

            # Send to Claude API
            prompt = f"[Auto-monitoring capture #{session.capture_count + 1}]"
            response = self.api_client.send_multimodal_prompt(prompt, screenshot)

            logger.info(
                f"Auto-capture #{session.capture_count + 1} completed: "
                f"{len(response)} chars received"
            )

            # Update session stats
            session.capture_count += 1
            session.last_capture_at = datetime.now(timezone.utc)

            # Cleanup temp file
            self.temp_manager.cleanup_temp_file(screenshot.file_path)

        except Exception as e:
            logger.error(f"Capture failed: {e}", exc_info=True)
            raise

    def _maybe_update_idle_pause(self, idle_pause_minutes: int) -> None:
        """
        Pause/resume session based on system idle time.

        Args:
            idle_pause_minutes: Idle timeout in minutes (<=0 disables idle pause)
        """
        if idle_pause_minutes <= 0 or self._active_session is None:
            return

        idle_seconds = self._idle_seconds_provider()
        if idle_seconds is None:
            return

        idle_threshold_seconds = idle_pause_minutes * 60
        is_paused = self._active_session.paused_at is not None

        if idle_seconds >= idle_threshold_seconds and not is_paused:
            self._active_session.paused_at = datetime.now(timezone.utc)
            logger.info(
                "Monitoring session auto-paused due to idle timeout "
                f"({idle_pause_minutes} min)"
            )
        elif idle_seconds < idle_threshold_seconds and is_paused:
            self._active_session.paused_at = None
            logger.info("Monitoring session auto-resumed after activity detected")

    def _get_system_idle_seconds(self) -> Optional[float]:
        """
        Get system idle time in seconds.

        Returns:
            Idle duration in seconds, or None when unavailable.
        """
        # xprintidle is the most reliable lightweight option on X11.
        if not shutil.which("xprintidle"):
            return None

        try:
            result = subprocess.run(
                ["xprintidle"],
                capture_output=True,
                text=True,
                timeout=2,
                check=True
            )
            return float(result.stdout.strip()) / 1000.0
        except (subprocess.SubprocessError, ValueError):
            return None
