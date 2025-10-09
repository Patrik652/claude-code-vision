"""
Contract tests for IClaudeAPIClient interface.

Verifies that all implementations of IClaudeAPIClient adhere to the contract.
These tests are run against each concrete implementation to ensure consistency.
"""

import pytest
from pathlib import Path
from uuid import uuid4
from datetime import datetime

from src.interfaces.screenshot_service import IClaudeAPIClient
from src.models.entities import Screenshot
from src.lib.exceptions import (
    AuthenticationError,
    APIError,
    PayloadTooLargeError,
    OAuthConfigNotFoundError
)


class TestIClaudeAPIClientContract:
    """
    Contract test suite for IClaudeAPIClient interface.

    All implementations of IClaudeAPIClient MUST pass these tests.
    """

    @pytest.fixture
    def client_implementation(self):
        """
        Override this fixture in concrete test classes to provide the implementation.

        Example:
            @pytest.fixture
            def client_implementation(self):
                return AnthropicAPIClient()
        """
        pytest.skip("Must be implemented by concrete test class")

    @pytest.fixture
    def sample_screenshot(self, tmp_path):
        """
        Create a sample Screenshot object for testing.

        This fixture should be overridden in concrete tests to provide a real image file.
        """
        pytest.skip("Must be implemented by concrete test class to provide real image")

    def test_interface_inheritance(self, client_implementation):
        """Test that implementation inherits from IClaudeAPIClient."""
        assert isinstance(client_implementation, IClaudeAPIClient)

    def test_send_multimodal_prompt_returns_string(self, client_implementation, sample_screenshot):
        """Test that send_multimodal_prompt() returns a string response."""
        text = "What do you see in this image?"

        response = client_implementation.send_multimodal_prompt(text, sample_screenshot)

        assert isinstance(response, str)
        assert len(response) > 0

    def test_send_multimodal_prompt_with_empty_text(self, client_implementation, sample_screenshot):
        """Test that send_multimodal_prompt() handles empty text prompt."""
        # Should still work - image-only analysis
        response = client_implementation.send_multimodal_prompt("", sample_screenshot)

        assert isinstance(response, str)
        # Response might be empty or contain a default message

    def test_send_multimodal_prompt_with_long_text(self, client_implementation, sample_screenshot):
        """Test send_multimodal_prompt() with long text prompt."""
        long_text = "Analyze this screenshot in detail. " * 100  # Long prompt

        response = client_implementation.send_multimodal_prompt(long_text, sample_screenshot)

        assert isinstance(response, str)

    def test_send_multimodal_prompt_validates_screenshot_exists(self, client_implementation, tmp_path):
        """Test that send_multimodal_prompt() validates screenshot file exists."""
        # Create screenshot with non-existent file
        invalid_screenshot = Screenshot(
            id=uuid4(),
            timestamp=datetime.now(),
            file_path=tmp_path / "nonexistent.jpg",
            format="jpeg",
            original_size_bytes=0,
            optimized_size_bytes=0,
            resolution=(800, 600),
            source_monitor=0,
            capture_method="test",
            privacy_zones_applied=False
        )

        with pytest.raises((APIError, FileNotFoundError)):
            client_implementation.send_multimodal_prompt("Test", invalid_screenshot)

    def test_validate_oauth_token_returns_bool(self, client_implementation):
        """Test that validate_oauth_token() returns boolean."""
        result = client_implementation.validate_oauth_token()

        assert isinstance(result, bool)

    def test_validate_oauth_token_with_valid_token(self, client_implementation):
        """Test validate_oauth_token() with valid token."""
        # This test assumes a valid token is configured
        # May need to be mocked or skipped in CI
        try:
            result = client_implementation.validate_oauth_token()
            # If we get here without error, result should be True
            assert isinstance(result, bool)
        except OAuthConfigNotFoundError:
            pytest.skip("OAuth config not found - expected in test environment")

    def test_validate_oauth_token_missing_config_raises_error(self, client_implementation, monkeypatch):
        """Test that validate_oauth_token() raises error when config missing."""
        # Mock missing config file
        monkeypatch.setenv('HOME', '/nonexistent')

        with pytest.raises(OAuthConfigNotFoundError):
            client_implementation.validate_oauth_token()

    def test_refresh_oauth_token_executes_without_error(self, client_implementation):
        """Test that refresh_oauth_token() can be called."""
        # This test may need to be mocked as it requires valid credentials
        try:
            client_implementation.refresh_oauth_token()
            # If we get here, refresh succeeded
        except AuthenticationError:
            # Expected if no valid refresh token available
            pytest.skip("No valid refresh token - expected in test environment")
        except OAuthConfigNotFoundError:
            # Expected if config file missing
            pytest.skip("OAuth config not found - expected in test environment")


class TestIClaudeAPIClientErrorHandling:
    """
    Contract tests for error handling in IClaudeAPIClient implementations.
    """

    @pytest.fixture
    def client_implementation(self):
        """Override in concrete test classes."""
        pytest.skip("Must be implemented by concrete test class")

    @pytest.fixture
    def sample_screenshot(self, tmp_path):
        """Override in concrete test classes."""
        pytest.skip("Must be implemented by concrete test class")

    def test_send_multimodal_prompt_invalid_token_raises_auth_error(self, client_implementation, sample_screenshot, monkeypatch):
        """Test that invalid OAuth token raises AuthenticationError."""
        # Mock invalid token scenario
        # Implementation-specific: may need to mock token reading
        # with pytest.raises(AuthenticationError):
        #     client_implementation.send_multimodal_prompt("Test", sample_screenshot)
        pytest.skip("Implementation-specific test - requires mocking")

    def test_send_multimodal_prompt_network_error_raises_api_error(self, client_implementation, sample_screenshot):
        """Test that network errors raise APIError."""
        # Mock network failure scenario
        # Implementation-specific: may need to mock requests
        pytest.skip("Implementation-specific test - requires mocking")

    def test_send_multimodal_prompt_too_large_raises_payload_error(self, client_implementation, tmp_path):
        """Test that oversized payload raises PayloadTooLargeError."""
        # Create a very large screenshot
        large_screenshot = Screenshot(
            id=uuid4(),
            timestamp=datetime.now(),
            file_path=tmp_path / "large.jpg",
            format="jpeg",
            original_size_bytes=50 * 1024 * 1024,  # 50 MB
            optimized_size_bytes=50 * 1024 * 1024,
            resolution=(10000, 10000),
            source_monitor=0,
            capture_method="test",
            privacy_zones_applied=False
        )

        # Note: This test requires actual large file creation
        # May need to be implemented in concrete test class
        pytest.skip("Requires actual large file - implement in concrete class")

    def test_refresh_token_invalid_credentials_raises_auth_error(self, client_implementation):
        """Test that refresh with invalid credentials raises AuthenticationError."""
        # Mock invalid refresh token scenario
        pytest.skip("Implementation-specific test - requires mocking")


class TestIClaudeAPIClientIntegration:
    """
    Integration-style contract tests that verify end-to-end functionality.

    These tests may be slow and should be marked as such.
    """

    @pytest.fixture
    def client_implementation(self):
        """Override in concrete test classes."""
        pytest.skip("Must be implemented by concrete test class")

    @pytest.fixture
    def sample_screenshot(self, tmp_path):
        """Override in concrete test classes."""
        pytest.skip("Must be implemented by concrete test class")

    @pytest.mark.slow
    @pytest.mark.integration
    def test_full_multimodal_workflow(self, client_implementation, sample_screenshot):
        """
        Test complete workflow: validate token, send prompt, receive response.

        This is an integration test that requires:
        - Valid OAuth configuration
        - Network connectivity
        - Valid API key
        """
        try:
            # Step 1: Validate token
            is_valid = client_implementation.validate_oauth_token()
            if not is_valid:
                pytest.skip("Token not valid - skipping integration test")

            # Step 2: Send multimodal prompt
            response = client_implementation.send_multimodal_prompt(
                "Describe this image briefly.",
                sample_screenshot
            )

            # Step 3: Verify response
            assert isinstance(response, str)
            assert len(response) > 0

        except (OAuthConfigNotFoundError, AuthenticationError):
            pytest.skip("OAuth not configured - expected in test environment")
        except APIError as e:
            pytest.fail(f"API error during integration test: {e}")

    @pytest.mark.slow
    @pytest.mark.integration
    def test_token_refresh_workflow(self, client_implementation):
        """
        Test token refresh workflow.

        This is an integration test that requires valid refresh token.
        """
        try:
            # Attempt to refresh token
            client_implementation.refresh_oauth_token()

            # Verify token is now valid
            is_valid = client_implementation.validate_oauth_token()
            assert is_valid

        except (OAuthConfigNotFoundError, AuthenticationError):
            pytest.skip("OAuth not configured - expected in test environment")


# NOTE: Concrete test classes will inherit from these and provide actual implementations
# Example:
# class TestAnthropicAPIClient(TestIClaudeAPIClientContract):
#     @pytest.fixture
#     def client_implementation(self):
#         return AnthropicAPIClient()
#
#     @pytest.fixture
#     def sample_screenshot(self, tmp_path):
#         # Create a real test image
#         from PIL import Image
#         img = Image.new('RGB', (800, 600), color='blue')
#         img_path = tmp_path / "test.jpg"
#         img.save(img_path, quality=85)
#
#         return Screenshot(
#             id=uuid4(),
#             timestamp=datetime.now(),
#             file_path=img_path,
#             format="jpeg",
#             original_size_bytes=img_path.stat().st_size,
#             optimized_size_bytes=img_path.stat().st_size,
#             resolution=(800, 600),
#             source_monitor=0,
#             capture_method="test",
#             privacy_zones_applied=False
#         )
