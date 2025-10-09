"""
Anthropic API Client Implementation.

Handles communication with Claude API including:
- OAuth token management
- Base64 image encoding
- Multimodal prompt construction
- API request/response handling

Implements IClaudeAPIClient interface.
"""

import json
import base64
from pathlib import Path
from typing import Optional

import requests

from src.interfaces.screenshot_service import IClaudeAPIClient
from src.models.entities import Screenshot
from src.lib.exceptions import (
    AuthenticationError,
    APIError,
    PayloadTooLargeError,
    OAuthConfigNotFoundError
)
from src.lib.logging_config import get_logger

logger = get_logger(__name__)


class AnthropicAPIClient(IClaudeAPIClient):
    """
    Anthropic API client for sending multimodal prompts to Claude.

    Handles OAuth token reading, image encoding, and API communication.
    """

    DEFAULT_OAUTH_PATH = Path.home() / ".claude" / "config.json"
    DEFAULT_API_ENDPOINT = "https://api.anthropic.com/v1/messages"
    MAX_IMAGE_SIZE_MB = 5.0  # Anthropic API limit

    def __init__(
        self,
        oauth_token_path: Optional[str] = None,
        api_endpoint: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize AnthropicAPIClient.

        Args:
            oauth_token_path: Path to OAuth config file (default: ~/.claude/config.json)
            api_endpoint: API endpoint URL (default: https://api.anthropic.com/v1/messages)
            api_key: API key (overrides OAuth token if provided)
        """
        self.oauth_token_path = Path(oauth_token_path).expanduser() if oauth_token_path else self.DEFAULT_OAUTH_PATH
        self.api_endpoint = api_endpoint or self.DEFAULT_API_ENDPOINT
        self._api_key = api_key  # Cache for API key

        logger.debug(f"AnthropicAPIClient initialized: endpoint={self.api_endpoint}")

    def send_multimodal_prompt(self, text: str, screenshot: Screenshot) -> str:
        """
        Send text + image prompt to Claude API.

        Args:
            text: User's text prompt
            screenshot: Screenshot to include

        Returns:
            Claude's response text

        Raises:
            AuthenticationError: If OAuth token invalid/expired
            APIError: If API call fails
            PayloadTooLargeError: If screenshot exceeds API limits
        """
        logger.info(f"Sending multimodal prompt to Claude API: {len(text)} chars, screenshot={screenshot.id}")

        # Validate screenshot file exists
        if not screenshot.file_path.exists():
            raise APIError(f"Screenshot file not found: {screenshot.file_path}")

        # Check file size
        size_mb = screenshot.optimized_size_bytes / (1024 * 1024)
        if size_mb > self.MAX_IMAGE_SIZE_MB:
            raise PayloadTooLargeError(
                f"Screenshot size ({size_mb:.2f} MB) exceeds API limit ({self.MAX_IMAGE_SIZE_MB} MB)"
            )

        try:
            # Get API key
            api_key = self._get_api_key()

            # Encode screenshot to base64
            image_data = self._encode_image_base64(screenshot)

            # Construct multimodal prompt
            messages = self._construct_multimodal_messages(text, image_data, screenshot.format)

            # Prepare API request
            # Determine if this is an OAuth token or API key
            if api_key.startswith('sk-ant-oat') or api_key.startswith('sk-ant-ort'):
                # OAuth token - use Authorization header
                headers = {
                    "authorization": f"Bearer {api_key}",
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
            else:
                # API key - use x-api-key header
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }

            payload = {
                "model": "claude-3-5-sonnet-20241022",  # Latest model with vision
                "max_tokens": 4096,
                "messages": messages
            }

            # Send request
            logger.debug(f"Sending request to {self.api_endpoint}")
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=payload,
                timeout=60
            )

            # Handle response
            if response.status_code == 401:
                raise AuthenticationError("Invalid or expired API key")
            elif response.status_code == 413:
                raise PayloadTooLargeError("Request payload too large")
            elif response.status_code != 200:
                error_msg = f"API request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise APIError(error_msg)

            # Parse response
            response_data = response.json()

            # Extract text from response
            if "content" in response_data and len(response_data["content"]) > 0:
                response_text = response_data["content"][0].get("text", "")
                logger.info(f"Received response: {len(response_text)} chars")
                return response_text
            else:
                raise APIError("No content in API response")

        except requests.exceptions.Timeout:
            raise APIError("API request timed out")
        except requests.exceptions.ConnectionError:
            raise APIError("Failed to connect to API endpoint")
        except requests.exceptions.RequestException as e:
            raise APIError(f"API request failed: {e}")
        except json.JSONDecodeError as e:
            raise APIError(f"Failed to parse API response: {e}")

    def validate_oauth_token(self) -> bool:
        """
        Check if OAuth token is valid.

        Returns:
            True if token valid, False otherwise

        Raises:
            OAuthConfigNotFoundError: If config file missing
        """
        logger.debug("Validating OAuth token")

        try:
            # Try to get API key
            api_key = self._get_api_key()

            # If we got a key, consider it valid
            # (Full validation would require a test API call)
            return len(api_key) > 0

        except OAuthConfigNotFoundError:
            raise
        except Exception as e:
            logger.warning(f"OAuth token validation failed: {e}")
            return False

    def refresh_oauth_token(self) -> None:
        """
        Refresh expired OAuth token.

        Note: Anthropic API uses static API keys, not refresh tokens.
        This method is a no-op for compatibility with the interface.

        Raises:
            AuthenticationError: If refresh fails
        """
        logger.warning("Anthropic API uses static API keys - refresh not applicable")

        # Verify the current key is valid
        if not self.validate_oauth_token():
            raise AuthenticationError("API key is invalid and cannot be refreshed")

    def _get_api_key(self) -> str:
        """
        Get API key from cache or OAuth config file.

        Returns:
            API key string

        Raises:
            OAuthConfigNotFoundError: If config file not found
            AuthenticationError: If config invalid
        """
        # Use cached API key if available
        if self._api_key:
            return self._api_key

        # Read from OAuth config file
        if not self.oauth_token_path.exists():
            raise OAuthConfigNotFoundError(
                f"OAuth config not found at {self.oauth_token_path}. "
                f"Please configure Claude Code authentication."
            )

        try:
            with open(self.oauth_token_path, 'r') as f:
                config = json.load(f)

            # Extract API key from config
            # Try multiple possible locations for the token
            api_key = None

            # Check for direct api_key or apiKey field
            api_key = config.get('api_key') or config.get('apiKey')

            # Check for Claude AI OAuth structure (.credentials.json format)
            if not api_key and 'claudeAiOauth' in config:
                oauth = config['claudeAiOauth']
                api_key = oauth.get('accessToken')

            # Check for nested oauth structure
            if not api_key and 'oauth' in config:
                oauth = config['oauth']
                api_key = oauth.get('accessToken') or oauth.get('access_token')

            if not api_key:
                raise AuthenticationError(
                    f"No API key found in {self.oauth_token_path}. "
                    f"Expected 'api_key', 'apiKey', or 'claudeAiOauth.accessToken' field."
                )

            # Cache the key
            self._api_key = api_key
            logger.debug("API key loaded successfully")

            return api_key

        except json.JSONDecodeError as e:
            raise AuthenticationError(f"Invalid JSON in OAuth config: {e}")
        except Exception as e:
            raise AuthenticationError(f"Failed to read OAuth config: {e}")

    def _encode_image_base64(self, screenshot: Screenshot) -> str:
        """
        Encode screenshot image to base64.

        Args:
            screenshot: Screenshot to encode

        Returns:
            Base64-encoded image data

        Raises:
            APIError: If encoding fails
        """
        try:
            with open(screenshot.file_path, 'rb') as f:
                image_bytes = f.read()

            encoded = base64.standard_b64encode(image_bytes).decode('utf-8')

            logger.debug(f"Image encoded to base64: {len(encoded)} chars")
            return encoded

        except Exception as e:
            raise APIError(f"Failed to encode image: {e}")

    def _construct_multimodal_messages(
        self,
        text: str,
        image_data: str,
        image_format: str
    ) -> list:
        """
        Construct multimodal messages array for API request.

        Args:
            text: User's text prompt
            image_data: Base64-encoded image data
            image_format: Image format ('png', 'jpg', 'jpeg', 'webp')

        Returns:
            Messages array for API request
        """
        # Determine media type
        media_type_map = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'webp': 'image/webp'
        }
        media_type = media_type_map.get(image_format.lower(), 'image/png')

        # Construct content array with image and text
        content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": image_data
                }
            }
        ]

        # Add text if provided
        if text:
            content.append({
                "type": "text",
                "text": text
            })

        # Construct messages array
        messages = [
            {
                "role": "user",
                "content": content
            }
        ]

        logger.debug(f"Constructed multimodal message: {len(content)} content blocks")
        return messages
