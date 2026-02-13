"""Unit tests for ScreenshotCaptureFactory decision and wiring logic."""

from __future__ import annotations

import builtins
import sys
from types import ModuleType

import pytest

from src.lib.desktop_detector import DesktopType
from src.lib.exceptions import ScreenshotCaptureError
from src.lib.tool_detector import ScreenshotTool
from src.services.screenshot_capture.factory import ScreenshotCaptureFactory, create_screenshot_capture


class _DummyCapture:
    def __init__(self, temp_manager=None, **kwargs):
        self.temp_manager = temp_manager
        self.kwargs = kwargs


def _install_fake_capture_module(monkeypatch: pytest.MonkeyPatch, module_name: str, class_name: str) -> None:
    fake_module = ModuleType(module_name)
    fake_class = type(class_name, (), {"__init__": _DummyCapture.__init__})
    setattr(fake_module, class_name, fake_class)
    monkeypatch.setitem(sys.modules, module_name, fake_module)


def test_get_tool_from_name_maps_supported_values() -> None:
    assert ScreenshotCaptureFactory._get_tool_from_name("scrot") == ScreenshotTool.SCROT
    assert ScreenshotCaptureFactory._get_tool_from_name("grim") == ScreenshotTool.GRIM
    assert ScreenshotCaptureFactory._get_tool_from_name("import") == ScreenshotTool.IMPORT


def test_get_tool_from_name_is_case_insensitive() -> None:
    assert ScreenshotCaptureFactory._get_tool_from_name("ScRoT") == ScreenshotTool.SCROT


def test_get_tool_from_name_unknown_returns_none() -> None:
    assert ScreenshotCaptureFactory._get_tool_from_name("unknown") is None


def test_create_uses_preferred_tool_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel = object()

    monkeypatch.setattr("src.services.screenshot_capture.factory.DesktopDetector.detect", lambda: DesktopType.X11)
    monkeypatch.setattr(
        "src.services.screenshot_capture.factory.ToolDetector.detect_tool",
        lambda tool: tool == ScreenshotTool.SCROT,
    )
    monkeypatch.setattr(
        "src.services.screenshot_capture.factory.ScreenshotCaptureFactory._create_implementation",
        lambda **_kwargs: sentinel,
    )

    result = ScreenshotCaptureFactory.create(preferred_tool="scrot")

    assert result is sentinel


def test_create_falls_back_when_preferred_tool_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    monkeypatch.setattr("src.services.screenshot_capture.factory.DesktopDetector.detect", lambda: DesktopType.X11)
    monkeypatch.setattr("src.services.screenshot_capture.factory.ToolDetector.detect_tool", lambda _tool: False)
    monkeypatch.setattr(
        "src.services.screenshot_capture.factory.ToolDetector.get_preferred_tool",
        lambda _desktop: ScreenshotTool.GRIM,
    )

    def _fake_create(**kwargs):
        captured.update(kwargs)
        return "impl"

    monkeypatch.setattr("src.services.screenshot_capture.factory.ScreenshotCaptureFactory._create_implementation", _fake_create)

    result = ScreenshotCaptureFactory.create(preferred_tool="scrot")

    assert result == "impl"
    assert captured["tool"] == ScreenshotTool.GRIM


def test_create_raises_when_no_tool_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.services.screenshot_capture.factory.DesktopDetector.detect", lambda: DesktopType.X11)
    monkeypatch.setattr("src.services.screenshot_capture.factory.ToolDetector.get_preferred_tool", lambda _desktop: None)

    with pytest.raises(ScreenshotCaptureError, match="No screenshot tools available"):
        ScreenshotCaptureFactory.create(preferred_tool="auto")


def test_create_passes_format_and_quality_to_implementation(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    monkeypatch.setattr("src.services.screenshot_capture.factory.DesktopDetector.detect", lambda: DesktopType.X11)
    monkeypatch.setattr(
        "src.services.screenshot_capture.factory.ToolDetector.get_preferred_tool",
        lambda _desktop: ScreenshotTool.SCROT,
    )

    def _fake_create(**kwargs):
        captured.update(kwargs)
        return "impl"

    monkeypatch.setattr("src.services.screenshot_capture.factory.ScreenshotCaptureFactory._create_implementation", _fake_create)

    ScreenshotCaptureFactory.create(image_format="jpeg", quality=77)

    assert captured["image_format"] == "jpeg"
    assert captured["quality"] == 77


def test_create_for_testing_instantiates_given_class_with_temp_manager() -> None:
    instance = ScreenshotCaptureFactory.create_for_testing(_DummyCapture, image_format="png")

    assert isinstance(instance, _DummyCapture)
    assert instance.temp_manager is not None
    assert instance.kwargs["image_format"] == "png"


def test_get_available_tools_delegates_to_detector(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = [ScreenshotTool.SCROT, ScreenshotTool.GRIM]
    monkeypatch.setattr("src.services.screenshot_capture.factory.ToolDetector.detect_all_tools", lambda: expected)

    assert ScreenshotCaptureFactory.get_available_tools() == expected


def test_get_recommended_tool_delegates_to_detector(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.services.screenshot_capture.factory.DesktopDetector.detect", lambda: DesktopType.WAYLAND)
    monkeypatch.setattr(
        "src.services.screenshot_capture.factory.ToolDetector.get_preferred_tool",
        lambda desktop: ScreenshotTool.GRIM if desktop == "wayland" else None,
    )

    assert ScreenshotCaptureFactory.get_recommended_tool() == ScreenshotTool.GRIM


def test_create_screenshot_capture_convenience_function_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.services.screenshot_capture.factory.ScreenshotCaptureFactory.create",
        lambda **kwargs: kwargs,
    )

    result = create_screenshot_capture(image_format="png", quality=88, preferred_tool="grim")

    assert result == {"image_format": "png", "quality": 88, "preferred_tool": "grim"}


def test_create_implementation_scrot_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_capture_module(
        monkeypatch,
        "src.services.screenshot_capture.x11_capture",
        "X11ScreenshotCapture",
    )

    instance = ScreenshotCaptureFactory._create_implementation(
        tool=ScreenshotTool.SCROT,
        desktop_type=DesktopType.X11,
        temp_manager=object(),
        image_format="png",
        quality=85,
    )

    assert instance.kwargs["image_format"] == "png"
    assert instance.kwargs["quality"] == 85


def test_create_implementation_grim_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_capture_module(
        monkeypatch,
        "src.services.screenshot_capture.wayland_capture",
        "WaylandScreenshotCapture",
    )

    instance = ScreenshotCaptureFactory._create_implementation(
        tool=ScreenshotTool.GRIM,
        desktop_type=DesktopType.WAYLAND,
        temp_manager=object(),
        image_format="jpeg",
        quality=70,
    )

    assert instance.kwargs["image_format"] == "jpeg"
    assert instance.kwargs["quality"] == 70


def test_create_implementation_import_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_capture_module(
        monkeypatch,
        "src.services.screenshot_capture.imagemagick_capture",
        "ImageMagickScreenshotCapture",
    )

    instance = ScreenshotCaptureFactory._create_implementation(
        tool=ScreenshotTool.IMPORT,
        desktop_type=DesktopType.X11,
        temp_manager=object(),
        image_format="webp",
        quality=60,
    )

    assert instance.kwargs["image_format"] == "webp"
    assert instance.kwargs["quality"] == 60


def test_create_implementation_unsupported_tool_raises() -> None:
    with pytest.raises(ScreenshotCaptureError, match="Unsupported screenshot tool"):
        ScreenshotCaptureFactory._create_implementation(
            tool=ScreenshotTool.UNKNOWN,
            desktop_type=DesktopType.X11,
            temp_manager=object(),
            image_format="png",
            quality=90,
        )


def test_create_implementation_import_error_is_wrapped(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__

    def _raising_import(name, *args, **kwargs):
        if name == "src.services.screenshot_capture.x11_capture":
            raise ImportError("missing module")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _raising_import)

    with pytest.raises(ScreenshotCaptureError, match="Failed to import screenshot capture implementation"):
        ScreenshotCaptureFactory._create_implementation(
            tool=ScreenshotTool.SCROT,
            desktop_type=DesktopType.X11,
            temp_manager=object(),
            image_format="png",
            quality=90,
        )
