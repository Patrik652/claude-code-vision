"""
Google Gemini API Client Implementation.

Handles communication with Gemini API including:
- API key management
- Base64 image encoding
- Multimodal prompt construction
- API request/response handling

Implements IClaudeAPIClient interface for compatibility.
"""

import json
import base64
from pathlib import Path
from typing import Optional

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

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


class GeminiAPIClient(IClaudeAPIClient):
    """
    Google Gemini API client for sending multimodal prompts.

    Handles API key reading, image encoding, and API communication.
    Compatible with IClaudeAPIClient interface.
    """

    DEFAULT_CONFIG_PATH = Path.home() / ".config" / "claude-code-vision" / "config.yaml"
    MAX_IMAGE_SIZE_MB = 20.0  # Gemini API limit is more generous

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.0-flash-exp"
    ):
        """
        Initialize GeminiAPIClient.

        Args:
            api_key: Gemini API key (if None, will try to load from config)
            model_name: Gemini model to use (default: gemini-2.0-flash-exp)
        """
        self._api_key = api_key
        self.model_name = model_name
        self._model = None  # Lazy initialization

        logger.debug(f"GeminiAPIClient initialized: model={model_name}")

    def send_multimodal_prompt(self, text: str, screenshot: Screenshot) -> str:
        """
        Send text + image prompt to Gemini API.

        Args:
            text: User's text prompt
            screenshot: Screenshot to include

        Returns:
            Gemini's response text

        Raises:
            AuthenticationError: If API key invalid/expired
            APIError: If API call fails
            PayloadTooLargeError: If screenshot exceeds API limits
        """
        logger.info(f"Sending multimodal prompt to Gemini API: {len(text)} chars, screenshot={screenshot.id}")

        # Validate screenshot file exists
        if not screenshot.file_path.exists():
            raise APIError(f"Screenshot file not found: {screenshot.file_path}")

        # Check file size
        size_mb = screenshot.optimized_size_bytes / (1024 * 1024)
        if size_mb > self.MAX_IMAGE_SIZE_MB:
            raise PayloadTooLargeError(
                size_mb=size_mb,
                limit_mb=self.MAX_IMAGE_SIZE_MB
            )

        try:
            # Get API key and initialize model
            api_key = self._get_api_key()
            logger.debug(f"Got API key from _get_api_key: {api_key[:10]}...{api_key[-5:]} (length: {len(api_key)})")
            genai.configure(api_key=api_key)

            # Initialize model with safety settings
            if self._model is None:
                self._model = genai.GenerativeModel(
                    model_name=self.model_name,
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    }
                )

            # Read image file
            with open(screenshot.file_path, 'rb') as f:
                image_bytes = f.read()

            # Determine MIME type
            mime_type_map = {
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'webp': 'image/webp'
            }
            mime_type = mime_type_map.get(screenshot.format.lower(), 'image/png')

            # Create image part
            image_part = {
                'mime_type': mime_type,
                'data': image_bytes
            }

            # Construct prompt with image
            prompt_parts = [image_part]
            if text:
                prompt_parts.append(text)

            logger.debug(f"Sending request to Gemini API with model {self.model_name}")

            # Send request
            response = self._model.generate_content(
                prompt_parts,
                generation_config={
                    'temperature': 0.7,
                    'top_p': 0.95,
                    'top_k': 40,
                    'max_output_tokens': 8192,
                }
            )

            # Extract text from response
            # Check for blocked content first
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                if hasattr(response.prompt_feedback, 'block_reason'):
                    raise APIError(f"Content blocked by Gemini: {response.prompt_feedback.block_reason}")
                raise APIError(f"Content blocked: {response.prompt_feedback}")

            # Check if we have candidates
            if not response.candidates or len(response.candidates) == 0:
                raise APIError("No response candidates returned from Gemini API")

            # Get text from first candidate
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content.parts:
                response_text = ''.join(part.text for part in candidate.content.parts if hasattr(part, 'text'))
                if response_text:
                    logger.info(f"Received response: {len(response_text)} chars")
                    return response_text

            raise APIError("No text content in Gemini API response")

        except genai.types.generation_types.StopCandidateException as e:
            raise APIError(f"Content generation stopped: {e}")
        except genai.types.generation_types.BlockedPromptException as e:
            raise APIError(f"Prompt blocked by safety filters: {e}")
        except Exception as e:
            if "API_KEY_INVALID" in str(e) or "invalid API key" in str(e).lower():
                raise AuthenticationError("Invalid or expired Gemini API key")
            elif "quota" in str(e).lower():
                raise APIError(f"API quota exceeded: {e}")
            elif "not found" in str(e).lower():
                raise APIError(f"Model not found: {self.model_name}")
            else:
                raise APIError(f"Gemini API request failed: {e}")

    def validate_oauth_token(self) -> bool:
        """
        Check if API key is valid.

        Returns:
            True if key valid, False otherwise

        Raises:
            OAuthConfigNotFoundError: If config file missing
        """
        logger.debug("Validating Gemini API key")

        try:
            # Try to get API key
            api_key = self._get_api_key()

            # If we got a key, consider it valid
            # (Full validation would require a test API call)
            return len(api_key) > 0

        except OAuthConfigNotFoundError:
            raise
        except Exception as e:
            logger.warning(f"API key validation failed: {e}")
            return False

    def refresh_oauth_token(self) -> None:
        """
        Refresh expired API token.

        Note: Gemini uses static API keys, not refresh tokens.
        This method is a no-op for compatibility with the interface.

        Raises:
            AuthenticationError: If refresh fails
        """
        logger.warning("Gemini API uses static API keys - refresh not applicable")

        # Verify the current key is valid
        if not self.validate_oauth_token():
            raise AuthenticationError("API key is invalid and cannot be refreshed")

    def _get_api_key(self) -> str:
        """
        Get API key from cache or environment/config.

        Returns:
            API key string

        Raises:
            OAuthConfigNotFoundError: If API key not found
            AuthenticationError: If config invalid
        """
        # Use cached API key if available
        if self._api_key:
            return self._api_key

        # Try environment variable first
        import os
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')

        if api_key:
            self._api_key = api_key
            logger.debug("Gemini API key loaded from environment")
            return api_key

        # Try loading from config file
        try:
            import yaml

            if self.DEFAULT_CONFIG_PATH.exists():
                with open(self.DEFAULT_CONFIG_PATH, 'r') as f:
                    config = yaml.safe_load(f)

                # Look for gemini API key in config
                if config and 'gemini' in config:
                    gemini_config = config['gemini']
                    api_key = gemini_config.get('api_key') or gemini_config.get('apiKey')

                    if api_key:
                        self._api_key = api_key
                        logger.debug("Gemini API key loaded from config")
                        return api_key

        except Exception as e:
            logger.warning(f"Failed to load config: {e}")

        # No API key found
        raise OAuthConfigNotFoundError(
            "Gemini API key not found. Please set GEMINI_API_KEY environment variable "
            "or add 'gemini.api_key' to config.yaml"
        )
