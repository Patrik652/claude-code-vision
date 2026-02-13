"""Executable contract tests for IClaudeAPIClient using AnthropicAPIClient."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from PIL import Image

from src.interfaces.screenshot_service import IClaudeAPIClient
from src.lib.exceptions import APIError, AuthenticationError, OAuthConfigNotFoundError, PayloadTooLargeError
from src.models.entities import Screenshot
from src.services.claude_api_client import AnthropicAPIClient


@pytest.fixture()
def sample_screenshot(tmp_path: Path) -> Screenshot:
    img_path = tmp_path / "sample.png"
    Image.new("RGB", (120, 80), color="white").save(img_path)
    size = img_path.stat().st_size
    return Screenshot(
        id=uuid4(),
        timestamp=datetime.now(tz=UTC),
        file_path=img_path,
        format="png",
        original_size_bytes=size,
        optimized_size_bytes=size,
        resolution=(120, 80),
        source_monitor=0,
        capture_method="test",
        privacy_zones_applied=False,
    )


@pytest.fixture()
def client_implementation() -> AnthropicAPIClient:
    return AnthropicAPIClient(api_key="sk-test")


def test_interface_inheritance(client_implementation: AnthropicAPIClient) -> None:
    assert isinstance(client_implementation, IClaudeAPIClient)


def test_send_multimodal_prompt_returns_string(
    client_implementation: AnthropicAPIClient,
    sample_screenshot: Screenshot,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _post_ok(*_args, **_kwargs):
        return SimpleNamespace(status_code=200, text="ok", json=lambda: {"content": [{"text": "ok"}]})

    monkeypatch.setattr(
        "src.services.claude_api_client.requests.post",
        _post_ok,
    )

    response = client_implementation.send_multimodal_prompt("hello", sample_screenshot)

    assert response == "ok"


def test_send_multimodal_prompt_with_empty_text(
    client_implementation: AnthropicAPIClient,
    sample_screenshot: Screenshot,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _post_empty(*_args, **_kwargs):
        return SimpleNamespace(status_code=200, text="ok", json=lambda: {"content": [{"text": "empty-ok"}]})

    monkeypatch.setattr(
        "src.services.claude_api_client.requests.post",
        _post_empty,
    )

    assert client_implementation.send_multimodal_prompt("", sample_screenshot) == "empty-ok"


def test_send_multimodal_prompt_with_long_text(
    client_implementation: AnthropicAPIClient,
    sample_screenshot: Screenshot,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _post_long(*_args, **_kwargs):
        return SimpleNamespace(status_code=200, text="ok", json=lambda: {"content": [{"text": "long-ok"}]})

    monkeypatch.setattr(
        "src.services.claude_api_client.requests.post",
        _post_long,
    )

    response = client_implementation.send_multimodal_prompt("Analyze " * 150, sample_screenshot)
    assert isinstance(response, str)


def test_send_multimodal_prompt_validates_screenshot_exists(client_implementation: AnthropicAPIClient) -> None:
    missing = Screenshot(
        id=uuid4(),
        timestamp=datetime.now(tz=UTC),
        file_path=Path("/definitely/missing.png"),
        format="png",
        original_size_bytes=0,
        optimized_size_bytes=0,
        resolution=(10, 10),
        source_monitor=0,
        capture_method="test",
        privacy_zones_applied=False,
    )

    with pytest.raises(APIError, match="Screenshot file not found"):
        client_implementation.send_multimodal_prompt("x", missing)


def test_validate_oauth_token_returns_bool(client_implementation: AnthropicAPIClient) -> None:
    assert client_implementation.validate_oauth_token() is True


def test_validate_oauth_token_missing_config_raises_error(tmp_path: Path) -> None:
    client = AnthropicAPIClient(oauth_token_path=str(tmp_path / "missing.json"))

    with pytest.raises(OAuthConfigNotFoundError):
        client.validate_oauth_token()


def test_refresh_oauth_token_executes_without_error(client_implementation: AnthropicAPIClient) -> None:
    client_implementation.refresh_oauth_token()


def test_send_multimodal_prompt_invalid_token_raises_auth_error(
    client_implementation: AnthropicAPIClient,
    sample_screenshot: Screenshot,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _post_unauthorized(*_args, **_kwargs):
        return SimpleNamespace(status_code=401, text="bad", json=lambda: {})

    monkeypatch.setattr(
        "src.services.claude_api_client.requests.post",
        _post_unauthorized,
    )

    with pytest.raises(AuthenticationError):
        client_implementation.send_multimodal_prompt("x", sample_screenshot)


def test_send_multimodal_prompt_network_error_raises_api_error(
    client_implementation: AnthropicAPIClient,
    sample_screenshot: Screenshot,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import requests

    def _raise(*_a, **_k):
        raise requests.exceptions.ConnectionError()

    monkeypatch.setattr("src.services.claude_api_client.requests.post", _raise)

    with pytest.raises(APIError, match="Failed to connect"):
        client_implementation.send_multimodal_prompt("x", sample_screenshot)


def test_send_multimodal_prompt_too_large_raises_payload_error(
    client_implementation: AnthropicAPIClient,
    sample_screenshot: Screenshot,
) -> None:
    oversized = Screenshot(
        id=sample_screenshot.id,
        timestamp=sample_screenshot.timestamp,
        file_path=sample_screenshot.file_path,
        format=sample_screenshot.format,
        original_size_bytes=sample_screenshot.original_size_bytes,
        optimized_size_bytes=10 * 1024 * 1024,
        resolution=sample_screenshot.resolution,
        source_monitor=sample_screenshot.source_monitor,
        capture_method=sample_screenshot.capture_method,
        privacy_zones_applied=False,
    )

    with pytest.raises(PayloadTooLargeError):
        client_implementation.send_multimodal_prompt("x", oversized)


def test_refresh_token_invalid_credentials_raises_auth_error(tmp_path: Path) -> None:
    cfg = tmp_path / "oauth.json"
    cfg.write_text(json.dumps({}), encoding="utf-8")
    client = AnthropicAPIClient(oauth_token_path=str(cfg))

    with pytest.raises(AuthenticationError):
        client.refresh_oauth_token()


def test_full_multimodal_workflow(
    client_implementation: AnthropicAPIClient,
    sample_screenshot: Screenshot,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _post_done(*_args, **_kwargs):
        return SimpleNamespace(status_code=200, text="ok", json=lambda: {"content": [{"text": "done"}]})

    monkeypatch.setattr(
        "src.services.claude_api_client.requests.post",
        _post_done,
    )

    assert client_implementation.validate_oauth_token() is True
    response = client_implementation.send_multimodal_prompt("Describe", sample_screenshot)
    assert response == "done"


def test_token_refresh_workflow_with_missing_oauth_config(tmp_path: Path) -> None:
    client = AnthropicAPIClient(oauth_token_path=str(tmp_path / "missing.json"))

    with pytest.raises(OAuthConfigNotFoundError):
        client.refresh_oauth_token()
