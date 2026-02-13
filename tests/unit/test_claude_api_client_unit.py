"""Unit tests for AnthropicAPIClient error handling and request construction."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
import requests
from PIL import Image

from src.lib.exceptions import APIError, AuthenticationError, OAuthConfigNotFoundError, PayloadTooLargeError
from src.models.entities import Screenshot
from src.services.claude_api_client import AnthropicAPIClient


@pytest.fixture()
def sample_screenshot(tmp_path: Path) -> Screenshot:
    img_path = tmp_path / "shot.png"
    Image.new("RGB", (80, 60), color="white").save(img_path)
    size = img_path.stat().st_size
    return Screenshot(
        id=uuid4(),
        timestamp=datetime.now(tz=UTC),
        file_path=img_path,
        format="png",
        original_size_bytes=size,
        optimized_size_bytes=size,
        resolution=(80, 60),
        source_monitor=0,
        capture_method="test",
        privacy_zones_applied=False,
    )


def test_construct_multimodal_messages_includes_image_and_text() -> None:
    client = AnthropicAPIClient(api_key="sk-test")

    messages = client._construct_multimodal_messages("describe", "YWJj", "png")

    assert messages[0]["role"] == "user"
    content = messages[0]["content"]
    assert content[0]["source"]["media_type"] == "image/png"
    assert content[1]["type"] == "text"
    assert content[1]["text"] == "describe"


def test_get_api_key_reads_direct_key(tmp_path: Path) -> None:
    cfg = tmp_path / "oauth.json"
    cfg.write_text(json.dumps({"api_key": "sk-live-direct"}), encoding="utf-8")

    client = AnthropicAPIClient(oauth_token_path=str(cfg))

    assert client._get_api_key() == "sk-live-direct"


def test_get_api_key_reads_claude_oauth_access_token(tmp_path: Path) -> None:
    cfg = tmp_path / "oauth.json"
    cfg.write_text(json.dumps({"claudeAiOauth": {"accessToken": "sk-ant-oat-123"}}), encoding="utf-8")

    client = AnthropicAPIClient(oauth_token_path=str(cfg))

    assert client._get_api_key() == "sk-ant-oat-123"


def test_get_api_key_raises_when_config_missing(tmp_path: Path) -> None:
    client = AnthropicAPIClient(oauth_token_path=str(tmp_path / "missing.json"))

    with pytest.raises(OAuthConfigNotFoundError):
        client._get_api_key()


def test_get_api_key_raises_when_config_has_no_key(tmp_path: Path) -> None:
    cfg = tmp_path / "oauth.json"
    cfg.write_text("{}", encoding="utf-8")
    client = AnthropicAPIClient(oauth_token_path=str(cfg))

    with pytest.raises(AuthenticationError, match="No API key found"):
        client._get_api_key()


def test_send_multimodal_prompt_raises_for_unauthorized(
    monkeypatch: pytest.MonkeyPatch,
    sample_screenshot: Screenshot,
) -> None:
    client = AnthropicAPIClient(api_key="sk-test")

    def _post(*_args, **_kwargs):
        return SimpleNamespace(status_code=401, text="unauthorized", json=lambda: {})

    monkeypatch.setattr("src.services.claude_api_client.requests.post", _post)

    with pytest.raises(AuthenticationError):
        client.send_multimodal_prompt("hello", sample_screenshot)


def test_send_multimodal_prompt_raises_for_payload_too_large(
    monkeypatch: pytest.MonkeyPatch,
    sample_screenshot: Screenshot,
) -> None:
    client = AnthropicAPIClient(api_key="sk-test")

    def _post(*_args, **_kwargs):
        return SimpleNamespace(status_code=413, text="too large", json=lambda: {})

    monkeypatch.setattr("src.services.claude_api_client.requests.post", _post)

    with pytest.raises(PayloadTooLargeError):
        client.send_multimodal_prompt("hello", sample_screenshot)


def test_send_multimodal_prompt_raises_api_error_on_non_200(
    monkeypatch: pytest.MonkeyPatch,
    sample_screenshot: Screenshot,
) -> None:
    client = AnthropicAPIClient(api_key="sk-test")

    def _post(*_args, **_kwargs):
        return SimpleNamespace(status_code=500, text="boom", json=lambda: {})

    monkeypatch.setattr("src.services.claude_api_client.requests.post", _post)

    with pytest.raises(APIError, match="API request failed: 500"):
        client.send_multimodal_prompt("hello", sample_screenshot)


def test_send_multimodal_prompt_raises_on_timeout(
    monkeypatch: pytest.MonkeyPatch,
    sample_screenshot: Screenshot,
) -> None:
    client = AnthropicAPIClient(api_key="sk-test")

    def _post(*_args, **_kwargs):
        raise requests.exceptions.Timeout()

    monkeypatch.setattr("src.services.claude_api_client.requests.post", _post)

    with pytest.raises(APIError, match="timed out"):
        client.send_multimodal_prompt("hello", sample_screenshot)


def test_send_multimodal_prompt_returns_response_text(
    monkeypatch: pytest.MonkeyPatch,
    sample_screenshot: Screenshot,
) -> None:
    client = AnthropicAPIClient(api_key="sk-test")

    def _post(*_args, **_kwargs):
        return SimpleNamespace(
            status_code=200,
            text="ok",
            json=lambda: {"content": [{"text": "analysis result"}]},
        )

    monkeypatch.setattr("src.services.claude_api_client.requests.post", _post)

    response = client.send_multimodal_prompt("hello", sample_screenshot)

    assert response == "analysis result"
