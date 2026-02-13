"""Unit tests for TempFileManager lifecycle and cleanup behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.lib.exceptions import TempFileError
from src.services.temp_file_manager import TempFileManager


@pytest.fixture()
def manager(tmp_path: Path) -> TempFileManager:
    return TempFileManager(temp_dir=str(tmp_path / "temp"))


def test_init_creates_temp_directory(tmp_path: Path) -> None:
    temp_dir = tmp_path / "new-temp"
    assert not temp_dir.exists()

    mgr = TempFileManager(temp_dir=str(temp_dir))

    assert mgr.get_temp_dir() == temp_dir
    assert temp_dir.exists()


def test_create_temp_file_strips_dot_extension(manager: TempFileManager) -> None:
    path = manager.create_temp_file(".png")

    assert path.exists()
    assert path.suffix == ".png"
    assert path in manager.get_created_files()


def test_cleanup_temp_file_removes_file_and_tracking(manager: TempFileManager) -> None:
    path = manager.create_temp_file("jpg")
    assert path in manager.get_created_files()

    manager.cleanup_temp_file(path)

    assert not path.exists()
    assert path not in manager.get_created_files()


def test_cleanup_temp_file_when_cleanup_disabled(tmp_path: Path) -> None:
    mgr = TempFileManager(temp_dir=str(tmp_path / "temp"), cleanup_enabled=False)
    path = mgr.create_temp_file("png")

    mgr.cleanup_temp_file(path)

    assert path.exists()
    assert path in mgr.get_created_files()


def test_cleanup_temp_file_missing_file_is_noop(manager: TempFileManager) -> None:
    missing = manager.get_temp_dir() / "missing.png"
    manager.cleanup_temp_file(missing)


def test_cleanup_temp_file_raises_when_unlink_fails(
    manager: TempFileManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = manager.create_temp_file("png")

    def _unlink_fail(_self: Path, _missing_ok: bool = False):
        raise PermissionError("blocked")

    monkeypatch.setattr(Path, "unlink", _unlink_fail)

    with pytest.raises(TempFileError, match="Failed to cleanup temp file"):
        manager.cleanup_temp_file(path)


def test_cleanup_all_temp_files_removes_tracked_and_orphaned_files(manager: TempFileManager) -> None:
    tracked = manager.create_temp_file("png")
    orphaned = manager.get_temp_dir() / "screenshot_orphaned.png"
    orphaned.write_bytes(b"x")

    manager.cleanup_all_temp_files()

    assert not tracked.exists()
    assert not orphaned.exists()
    assert manager.get_created_files() == []


def test_cleanup_all_temp_files_when_disabled_keeps_files(tmp_path: Path) -> None:
    mgr = TempFileManager(temp_dir=str(tmp_path / "temp"), cleanup_enabled=False)
    path = mgr.create_temp_file("png")

    mgr.cleanup_all_temp_files()

    assert path.exists()


def test_cleanup_all_temp_files_aggregates_errors(
    manager: TempFileManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager.create_temp_file("png")

    class _UnlinkController:
        def __init__(self):
            self.calls = 0

        def __call__(self, _self: Path, _missing_ok: bool = False):
            self.calls += 1
            if self.calls == 1:
                raise PermissionError("blocked")

    controller = _UnlinkController()
    monkeypatch.setattr(Path, "unlink", controller)

    with pytest.raises(TempFileError, match="Cleanup completed with"):
        manager.cleanup_all_temp_files()


def test_create_temp_file_raises_temp_file_error_on_failure(
    manager: TempFileManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("src.services.temp_file_manager.tempfile.mkstemp", lambda **_kwargs: (_ for _ in ()).throw(OSError("disk full")))

    with pytest.raises(TempFileError, match="Failed to create temp file"):
        manager.create_temp_file("png")


def test_destructor_cleanup_calls_cleanup_all(manager: TempFileManager, monkeypatch: pytest.MonkeyPatch) -> None:
    manager.create_temp_file("png")
    called = {"value": False}

    def _cleanup():
        called["value"] = True

    monkeypatch.setattr(manager, "cleanup_all_temp_files", _cleanup)

    manager.__del__()

    assert called["value"] is True
