"""Unit tests for GeminiAPIClient key loading and response handling."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from PIL import Image

from src.lib.exceptions import APIError, OAuthConfigNotFoundError, PayloadTooLargeError
from src.models.entities import Screenshot
from src.services.gemini_api_client import GeminiAPIClient


class _FakeModel:
    def __init__(self, response: object) -> None:
        self._response = response

    def generate_content(self, _prompt_parts, generation_config=None):
        assert generation_config is not None
        return self._response


@pytest.fixture()
def sample_screenshot(tmp_path: Path) -> Screenshot:
    img_path = tmp_path / "shot.png"
    Image.new("RGB", (64, 64), color="white").save(img_path)
    size = img_path.stat().st_size
    return Screenshot(
        id=uuid4(),
        timestamp=datetime.now(tz=UTC),
        file_path=img_path,
        format="png",
        original_size_bytes=size,
        optimized_size_bytes=size,
        resolution=(64, 64),
        source_monitor=0,
        capture_method="test",
        privacy_zones_applied=False,
    )


def test_get_api_key_reads_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "gem-test-key")
    client = GeminiAPIClient(api_key=None)

    assert client._get_api_key() == "gem-test-key"


def test_get_api_key_raises_when_no_sources_available(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setattr(GeminiAPIClient, "DEFAULT_CONFIG_PATH", tmp_path / "missing.yaml")

    client = GeminiAPIClient(api_key=None)

    with pytest.raises(OAuthConfigNotFoundError):
        client._get_api_key()


def test_send_multimodal_prompt_missing_file_raises_api_error() -> None:
    client = GeminiAPIClient(api_key="gem-key")
    screenshot = Screenshot(
        id=uuid4(),
        timestamp=datetime.now(tz=UTC),
        file_path=Path("/definitely/missing/file.png"),
        format="png",
        original_size_bytes=0,
        optimized_size_bytes=0,
        resolution=(10, 10),
        source_monitor=0,
        capture_method="test",
        privacy_zones_applied=False,
    )

    with pytest.raises(APIError, match="Screenshot file not found"):
        client.send_multimodal_prompt("hello", screenshot)


def test_send_multimodal_prompt_large_payload_raises(sample_screenshot: Screenshot) -> None:
    client = GeminiAPIClient(api_key="gem-key")
    oversized = Screenshot(
        id=sample_screenshot.id,
        timestamp=sample_screenshot.timestamp,
        file_path=sample_screenshot.file_path,
        format=sample_screenshot.format,
        original_size_bytes=sample_screenshot.original_size_bytes,
        optimized_size_bytes=30 * 1024 * 1024,
        resolution=sample_screenshot.resolution,
        source_monitor=sample_screenshot.source_monitor,
        capture_method=sample_screenshot.capture_method,
        privacy_zones_applied=False,
    )

    with pytest.raises(PayloadTooLargeError):
        client.send_multimodal_prompt("hello", oversized)


def test_send_multimodal_prompt_returns_concatenated_text(
    monkeypatch: pytest.MonkeyPatch,
    sample_screenshot: Screenshot,
) -> None:
    client = GeminiAPIClient(api_key="gem-key")
    monkeypatch.setattr("src.services.gemini_api_client.genai.configure", lambda **_kwargs: None)

    response = SimpleNamespace(
        prompt_feedback=None,
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(parts=[SimpleNamespace(text="Part A"), SimpleNamespace(text=" + Part B")])
            )
        ],
    )
    client._model = _FakeModel(response)

    result = client.send_multimodal_prompt("hello", sample_screenshot)

    assert result == "Part A + Part B"


def test_send_multimodal_prompt_raises_when_blocked(
    monkeypatch: pytest.MonkeyPatch,
    sample_screenshot: Screenshot,
) -> None:
    client = GeminiAPIClient(api_key="gem-key")
    monkeypatch.setattr("src.services.gemini_api_client.genai.configure", lambda **_kwargs: None)

    response = SimpleNamespace(
        prompt_feedback=SimpleNamespace(block_reason="SAFETY"),
        candidates=[SimpleNamespace(content=SimpleNamespace(parts=[]))],
    )
    client._model = _FakeModel(response)

    with pytest.raises(APIError, match="Content blocked by Gemini"):
        client.send_multimodal_prompt("hello", sample_screenshot)


def test_send_multimodal_prompt_raises_on_empty_candidates(
    monkeypatch: pytest.MonkeyPatch,
    sample_screenshot: Screenshot,
) -> None:
    client = GeminiAPIClient(api_key="gem-key")
    monkeypatch.setattr("src.services.gemini_api_client.genai.configure", lambda **_kwargs: None)

    response = SimpleNamespace(prompt_feedback=None, candidates=[])
    client._model = _FakeModel(response)

    with pytest.raises(APIError, match="No response candidates"):
        client.send_multimodal_prompt("hello", sample_screenshot)
