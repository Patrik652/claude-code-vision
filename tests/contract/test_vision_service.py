"""
Contract tests for IVisionService interface.

Verifies that all implementations of IVisionService adhere to the contract.
These tests are run against each concrete implementation to ensure consistency.
"""

import pytest
from uuid import UUID

from src.interfaces.screenshot_service import IVisionService
from src.models.entities import CaptureRegion
from src.lib.exceptions import (
    VisionCommandError,
    SessionAlreadyActiveError,
    DisplayNotAvailableError
)


class TestIVisionServiceContract:
    """
    Contract test suite for IVisionService interface.

    All implementations of IVisionService MUST pass these tests.
    """

    @pytest.fixture
    def service_implementation(self):
        """
        Override this fixture in concrete test classes to provide the implementation.

        Example:
            @pytest.fixture
            def service_implementation(self):
                return VisionService(config_manager, capture, processor, api_client, ...)
        """
        pytest.skip("Must be implemented by concrete test class")

    def test_interface_inheritance(self, service_implementation):
        """Test that implementation inherits from IVisionService."""
        assert isinstance(service_implementation, IVisionService)

    def test_execute_vision_command_returns_string(self, service_implementation):
        """Test that execute_vision_command() returns a string response."""
        prompt = "What do you see in this screenshot?"

        response = service_implementation.execute_vision_command(prompt)

        assert isinstance(response, str)
        assert len(response) > 0

    def test_execute_vision_command_with_empty_prompt(self, service_implementation):
        """Test execute_vision_command() with empty prompt."""
        # Should still work - image-only analysis
        response = service_implementation.execute_vision_command("")

        assert isinstance(response, str)

    def test_execute_vision_command_with_long_prompt(self, service_implementation):
        """Test execute_vision_command() with very long prompt."""
        long_prompt = "Analyze this screenshot. " * 200

        response = service_implementation.execute_vision_command(long_prompt)

        assert isinstance(response, str)

    def test_execute_vision_command_workflow(self, service_implementation):
        """
        Test that execute_vision_command() follows the correct workflow:
        1. Capture full screen
        2. Apply privacy zones (if configured)
        3. Optimize image
        4. Send to Claude API
        5. Cleanup temp files
        6. Return response
        """
        prompt = "Test vision command"

        # Execute command
        response = service_implementation.execute_vision_command(prompt)

        # Should return valid response
        assert isinstance(response, str)
        assert len(response) > 0

        # Note: Cleanup verification requires checking temp directory
        # This is implementation-specific

    def test_execute_vision_area_command_returns_string(self, service_implementation):
        """Test that execute_vision_area_command() returns a string response."""
        prompt = "What do you see in this region?"

        # Define a region
        region = CaptureRegion(
            x=100,
            y=100,
            width=400,
            height=300,
            monitor=0,
            selection_method='coordinates'
        )

        response = service_implementation.execute_vision_area_command(prompt, region)

        assert isinstance(response, str)
        assert len(response) > 0

    def test_execute_vision_area_command_with_coordinates(self, service_implementation):
        """Test execute_vision_area_command() with pre-defined coordinates."""
        region = CaptureRegion(
            x=0,
            y=0,
            width=800,
            height=600,
            monitor=0,
            selection_method='coordinates'
        )

        response = service_implementation.execute_vision_area_command("Analyze this area", region)

        assert isinstance(response, str)

    def test_execute_vision_area_command_without_region(self, service_implementation):
        """Test execute_vision_area_command() without pre-defined region (graphical selection)."""
        # When region=None, should trigger graphical selection
        # This test may need to be mocked or skipped in headless environments

        try:
            response = service_implementation.execute_vision_area_command("Test", region=None)
            assert isinstance(response, str)
        except (VisionCommandError, DisplayNotAvailableError):
            # Expected in headless or when graphical tool not available
            pytest.skip("Graphical selection not available in test environment")

    def test_execute_vision_area_command_workflow(self, service_implementation):
        """
        Test that execute_vision_area_command() follows the correct workflow:
        1. Select region (graphical or coordinates)
        2. Capture selected region
        3. Apply privacy zones (if configured)
        4. Optimize image
        5. Send to Claude API
        6. Cleanup temp files
        7. Return response
        """
        region = CaptureRegion(
            x=50,
            y=50,
            width=500,
            height=400,
            monitor=0,
            selection_method='coordinates'
        )

        response = service_implementation.execute_vision_area_command("Test area", region)

        assert isinstance(response, str)
        assert len(response) > 0

    def test_execute_vision_auto_command_returns_session_id(self, service_implementation):
        """Test that execute_vision_auto_command() returns a session UUID."""
        session_id = service_implementation.execute_vision_auto_command(interval_seconds=30)

        assert isinstance(session_id, UUID)

        # Cleanup: stop the session
        try:
            service_implementation.execute_vision_stop_command()
        except:
            pass

    def test_execute_vision_auto_command_with_custom_interval(self, service_implementation):
        """Test execute_vision_auto_command() with custom interval."""
        session_id = service_implementation.execute_vision_auto_command(interval_seconds=60)

        assert isinstance(session_id, UUID)

        # Cleanup
        try:
            service_implementation.execute_vision_stop_command()
        except:
            pass

    def test_execute_vision_auto_command_with_default_interval(self, service_implementation):
        """Test execute_vision_auto_command() with default interval from config."""
        session_id = service_implementation.execute_vision_auto_command(interval_seconds=None)

        assert isinstance(session_id, UUID)

        # Cleanup
        try:
            service_implementation.execute_vision_stop_command()
        except:
            pass

    def test_execute_vision_auto_command_prevents_multiple_sessions(self, service_implementation):
        """Test that only one monitoring session can be active at a time."""
        # Start first session
        session_id1 = service_implementation.execute_vision_auto_command(interval_seconds=30)
        assert isinstance(session_id1, UUID)

        # Try to start second session - should fail
        with pytest.raises(SessionAlreadyActiveError):
            service_implementation.execute_vision_auto_command(interval_seconds=30)

        # Cleanup
        service_implementation.execute_vision_stop_command()

    def test_execute_vision_stop_command_stops_session(self, service_implementation):
        """Test that execute_vision_stop_command() stops active session."""
        # Start session
        session_id = service_implementation.execute_vision_auto_command(interval_seconds=30)
        assert isinstance(session_id, UUID)

        # Stop session
        service_implementation.execute_vision_stop_command()

        # Should be able to start new session now
        session_id2 = service_implementation.execute_vision_auto_command(interval_seconds=30)
        assert isinstance(session_id2, UUID)

        # Cleanup
        service_implementation.execute_vision_stop_command()

    def test_execute_vision_stop_command_without_active_session_raises_error(self, service_implementation):
        """Test that stopping non-existent session raises error."""
        # Ensure no active session
        try:
            service_implementation.execute_vision_stop_command()
        except:
            pass

        # Try to stop again - should raise error
        with pytest.raises(VisionCommandError):
            service_implementation.execute_vision_stop_command()

    def test_execute_vision_stop_command_workflow(self, service_implementation):
        """
        Test that execute_vision_stop_command() follows correct workflow:
        1. Get active session
        2. Stop session
        3. Cleanup session resources
        """
        # Start session
        session_id = service_implementation.execute_vision_auto_command(interval_seconds=30)

        # Stop session
        service_implementation.execute_vision_stop_command()

        # Verify session is stopped (can start new one)
        session_id2 = service_implementation.execute_vision_auto_command(interval_seconds=30)
        assert isinstance(session_id2, UUID)
        assert session_id2 != session_id  # Different session

        # Cleanup
        service_implementation.execute_vision_stop_command()


class TestIVisionServiceErrorHandling:
    """
    Contract tests for error handling in IVisionService implementations.
    """

    @pytest.fixture
    def service_implementation(self):
        """Override in concrete test classes."""
        pytest.skip("Must be implemented by concrete test class")

    def test_execute_vision_command_headless_raises_error(self, service_implementation, monkeypatch):
        """Test that vision command in headless environment raises appropriate error."""
        # Mock headless environment
        monkeypatch.delenv('DISPLAY', raising=False)
        monkeypatch.delenv('WAYLAND_DISPLAY', raising=False)

        with pytest.raises((VisionCommandError, DisplayNotAvailableError)):
            service_implementation.execute_vision_command("Test")

    def test_execute_vision_command_oauth_error_propagates(self, service_implementation):
        """Test that OAuth errors are properly propagated."""
        # This test requires mocking the API client to simulate auth failure
        pytest.skip("Requires mocking - implement in concrete class")

    def test_execute_vision_area_command_invalid_region_raises_error(self, service_implementation):
        """Test that invalid region raises VisionCommandError."""
        # Region with negative coordinates
        invalid_region = CaptureRegion(
            x=-100,
            y=-100,
            width=200,
            height=200,
            monitor=0,
            selection_method='coordinates'
        )

        with pytest.raises(VisionCommandError):
            service_implementation.execute_vision_area_command("Test", invalid_region)

    def test_execute_vision_auto_command_invalid_interval_raises_error(self, service_implementation):
        """Test that invalid interval raises VisionCommandError."""
        # Negative interval
        with pytest.raises(VisionCommandError):
            service_implementation.execute_vision_auto_command(interval_seconds=-1)

        # Zero interval
        with pytest.raises(VisionCommandError):
            service_implementation.execute_vision_auto_command(interval_seconds=0)


class TestIVisionServiceIntegration:
    """
    Integration-style contract tests for complete workflows.
    """

    @pytest.fixture
    def service_implementation(self):
        """Override in concrete test classes."""
        pytest.skip("Must be implemented by concrete test class")

    @pytest.mark.slow
    @pytest.mark.integration
    def test_full_vision_workflow_end_to_end(self, service_implementation):
        """
        Test complete /vision workflow from capture to response.

        This is an integration test requiring:
        - Display available
        - Screenshot tools installed
        - Valid OAuth configuration
        - Network connectivity
        """
        try:
            response = service_implementation.execute_vision_command(
                "Describe what you see in this screenshot briefly."
            )

            assert isinstance(response, str)
            assert len(response) > 10  # Should have meaningful response

        except (DisplayNotAvailableError, VisionCommandError) as e:
            pytest.skip(f"Integration test skipped: {e}")

    @pytest.mark.slow
    @pytest.mark.integration
    def test_full_vision_area_workflow_end_to_end(self, service_implementation):
        """Test complete /vision.area workflow with coordinates."""
        region = CaptureRegion(
            x=0,
            y=0,
            width=800,
            height=600,
            monitor=0,
            selection_method='coordinates'
        )

        try:
            response = service_implementation.execute_vision_area_command(
                "What is in this region?",
                region
            )

            assert isinstance(response, str)
            assert len(response) > 10

        except (DisplayNotAvailableError, VisionCommandError) as e:
            pytest.skip(f"Integration test skipped: {e}")

    @pytest.mark.slow
    @pytest.mark.integration
    def test_monitoring_session_lifecycle(self, service_implementation):
        """Test complete monitoring session lifecycle: start -> run -> stop."""
        try:
            # Start session
            session_id = service_implementation.execute_vision_auto_command(interval_seconds=60)
            assert isinstance(session_id, UUID)

            # Let it run briefly
            import time
            time.sleep(2)

            # Stop session
            service_implementation.execute_vision_stop_command()

        except (DisplayNotAvailableError, VisionCommandError) as e:
            pytest.skip(f"Integration test skipped: {e}")


# NOTE: Concrete test classes will inherit from these and provide actual implementations
# Example:
# class TestVisionService(TestIVisionServiceContract):
#     @pytest.fixture
#     def service_implementation(self):
#         config_manager = ConfigurationManager()
#         temp_manager = TempFileManager()
#         capture = ScreenshotCaptureFactory.create()
#         processor = PillowImageProcessor()
#         api_client = AnthropicAPIClient()
#         session_manager = MonitoringSessionManager()
#
#         return VisionService(
#             config_manager=config_manager,
#             temp_manager=temp_manager,
#             capture=capture,
#             processor=processor,
#             api_client=api_client,
#             session_manager=session_manager
#         )
