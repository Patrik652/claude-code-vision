"""
Unit tests for desktop environment detection.

Tests the DesktopDetector utility that identifies X11 vs Wayland.
"""

import pytest
from unittest.mock import Mock, patch
import os

from src.lib.desktop_detector import (
    DesktopDetector,
    DesktopType,
    detect_desktop_type,
    is_x11,
    is_wayland,
    is_display_available
)


class TestDesktopDetector:
    """Unit tests for DesktopDetector class."""

    def test_detect_x11_from_xdg_session_type(self, monkeypatch):
        """Test X11 detection via XDG_SESSION_TYPE."""
        monkeypatch.setenv('XDG_SESSION_TYPE', 'x11')

        result = DesktopDetector.detect()

        assert result == DesktopType.X11

    def test_detect_wayland_from_xdg_session_type(self, monkeypatch):
        """Test Wayland detection via XDG_SESSION_TYPE."""
        monkeypatch.setenv('XDG_SESSION_TYPE', 'wayland')

        result = DesktopDetector.detect()

        assert result == DesktopType.WAYLAND

    def test_detect_wayland_from_wayland_display(self, monkeypatch):
        """Test Wayland detection via WAYLAND_DISPLAY."""
        monkeypatch.delenv('XDG_SESSION_TYPE', raising=False)
        monkeypatch.setenv('WAYLAND_DISPLAY', 'wayland-0')

        result = DesktopDetector.detect()

        assert result == DesktopType.WAYLAND

    def test_detect_x11_from_display(self, monkeypatch):
        """Test X11 detection via DISPLAY variable."""
        monkeypatch.delenv('XDG_SESSION_TYPE', raising=False)
        monkeypatch.delenv('WAYLAND_DISPLAY', raising=False)
        monkeypatch.setenv('DISPLAY', ':0')

        result = DesktopDetector.detect()

        assert result == DesktopType.X11

    def test_detect_unknown_when_no_env_vars(self, monkeypatch):
        """Test UNKNOWN detection when no environment variables set."""
        monkeypatch.delenv('XDG_SESSION_TYPE', raising=False)
        monkeypatch.delenv('WAYLAND_DISPLAY', raising=False)
        monkeypatch.delenv('DISPLAY', raising=False)

        # Mock loginctl to also fail
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()

            result = DesktopDetector.detect()

            assert result == DesktopType.UNKNOWN

    def test_detect_prefers_xdg_session_type(self, monkeypatch):
        """Test that XDG_SESSION_TYPE is preferred over other methods."""
        # Set conflicting variables
        monkeypatch.setenv('XDG_SESSION_TYPE', 'wayland')
        monkeypatch.setenv('DISPLAY', ':0')  # X11 indicator

        result = DesktopDetector.detect()

        # Should prefer XDG_SESSION_TYPE (wayland)
        assert result == DesktopType.WAYLAND

    def test_detect_wayland_overrides_x11_display(self, monkeypatch):
        """Test that WAYLAND_DISPLAY takes precedence over DISPLAY."""
        monkeypatch.delenv('XDG_SESSION_TYPE', raising=False)
        monkeypatch.setenv('WAYLAND_DISPLAY', 'wayland-0')
        monkeypatch.setenv('DISPLAY', ':0')

        result = DesktopDetector.detect()

        assert result == DesktopType.WAYLAND

    def test_detect_via_loginctl_x11(self, monkeypatch):
        """Test X11 detection via loginctl command."""
        monkeypatch.delenv('XDG_SESSION_TYPE', raising=False)
        monkeypatch.delenv('WAYLAND_DISPLAY', raising=False)
        monkeypatch.delenv('DISPLAY', raising=False)

        # Mock loginctl output
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout='Type=x11\n'
            )

            result = DesktopDetector.detect()

            assert result == DesktopType.X11

    def test_detect_via_loginctl_wayland(self, monkeypatch):
        """Test Wayland detection via loginctl command."""
        monkeypatch.delenv('XDG_SESSION_TYPE', raising=False)
        monkeypatch.delenv('WAYLAND_DISPLAY', raising=False)
        monkeypatch.delenv('DISPLAY', raising=False)

        # Mock loginctl output
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout='Type=wayland\n'
            )

            result = DesktopDetector.detect()

            assert result == DesktopType.WAYLAND

    def test_detect_via_loginctl_failure(self, monkeypatch):
        """Test fallback when loginctl fails."""
        monkeypatch.delenv('XDG_SESSION_TYPE', raising=False)
        monkeypatch.delenv('WAYLAND_DISPLAY', raising=False)
        monkeypatch.delenv('DISPLAY', raising=False)

        # Mock loginctl failure
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()

            result = DesktopDetector.detect()

            assert result == DesktopType.UNKNOWN

    def test_detect_via_loginctl_timeout(self, monkeypatch):
        """Test handling of loginctl timeout."""
        monkeypatch.delenv('XDG_SESSION_TYPE', raising=False)
        monkeypatch.delenv('WAYLAND_DISPLAY', raising=False)
        monkeypatch.delenv('DISPLAY', raising=False)

        # Mock loginctl timeout
        import subprocess
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired('loginctl', 2)

            result = DesktopDetector.detect()

            assert result == DesktopType.UNKNOWN

    def test_is_x11_returns_true_for_x11(self, monkeypatch):
        """Test is_x11() returns True for X11 environment."""
        monkeypatch.setenv('XDG_SESSION_TYPE', 'x11')

        assert DesktopDetector.is_x11() is True

    def test_is_x11_returns_false_for_wayland(self, monkeypatch):
        """Test is_x11() returns False for Wayland environment."""
        monkeypatch.setenv('XDG_SESSION_TYPE', 'wayland')

        assert DesktopDetector.is_x11() is False

    def test_is_wayland_returns_true_for_wayland(self, monkeypatch):
        """Test is_wayland() returns True for Wayland environment."""
        monkeypatch.setenv('XDG_SESSION_TYPE', 'wayland')

        assert DesktopDetector.is_wayland() is True

    def test_is_wayland_returns_false_for_x11(self, monkeypatch):
        """Test is_wayland() returns False for X11 environment."""
        monkeypatch.setenv('XDG_SESSION_TYPE', 'x11')

        assert DesktopDetector.is_wayland() is False

    def test_get_display_info_returns_dict(self, monkeypatch):
        """Test get_display_info() returns dictionary with display info."""
        monkeypatch.setenv('XDG_SESSION_TYPE', 'x11')
        monkeypatch.setenv('DISPLAY', ':0')
        monkeypatch.setenv('XDG_SESSION_DESKTOP', 'gnome')
        monkeypatch.setenv('XDG_CURRENT_DESKTOP', 'GNOME')

        info = DesktopDetector.get_display_info()

        assert isinstance(info, dict)
        assert 'desktop_type' in info
        assert 'xdg_session_type' in info
        assert 'wayland_display' in info
        assert 'display' in info
        assert 'xdg_session_desktop' in info
        assert 'xdg_current_desktop' in info
        assert info['desktop_type'] == 'x11'
        assert info['xdg_session_type'] == 'x11'
        assert info['display'] == ':0'

    def test_get_display_info_handles_missing_vars(self, monkeypatch):
        """Test get_display_info() handles missing environment variables."""
        monkeypatch.delenv('XDG_SESSION_TYPE', raising=False)
        monkeypatch.delenv('WAYLAND_DISPLAY', raising=False)
        monkeypatch.delenv('DISPLAY', raising=False)
        monkeypatch.delenv('XDG_SESSION_DESKTOP', raising=False)
        monkeypatch.delenv('XDG_CURRENT_DESKTOP', raising=False)

        info = DesktopDetector.get_display_info()

        assert isinstance(info, dict)
        assert info['xdg_session_type'] is None
        assert info['wayland_display'] is None
        assert info['display'] is None

    def test_is_display_available_x11(self, monkeypatch):
        """Test is_display_available() returns True for X11."""
        monkeypatch.setenv('XDG_SESSION_TYPE', 'x11')
        monkeypatch.setenv('DISPLAY', ':0')

        assert DesktopDetector.is_display_available() is True

    def test_is_display_available_wayland(self, monkeypatch):
        """Test is_display_available() returns True for Wayland."""
        monkeypatch.setenv('XDG_SESSION_TYPE', 'wayland')
        monkeypatch.setenv('WAYLAND_DISPLAY', 'wayland-0')

        assert DesktopDetector.is_display_available() is True

    def test_is_display_available_headless(self, monkeypatch):
        """Test is_display_available() returns False for headless."""
        monkeypatch.delenv('XDG_SESSION_TYPE', raising=False)
        monkeypatch.delenv('WAYLAND_DISPLAY', raising=False)
        monkeypatch.delenv('DISPLAY', raising=False)

        assert DesktopDetector.is_display_available() is False

    def test_is_display_available_unknown_type_with_display(self, monkeypatch):
        """Test is_display_available() with unknown type but DISPLAY set."""
        monkeypatch.delenv('XDG_SESSION_TYPE', raising=False)
        monkeypatch.delenv('WAYLAND_DISPLAY', raising=False)
        monkeypatch.setenv('DISPLAY', ':0')

        # Should still detect display is available
        assert DesktopDetector.is_display_available() is True


class TestConvenienceFunctions:
    """Test convenience functions for desktop detection."""

    def test_detect_desktop_type_function(self, monkeypatch):
        """Test detect_desktop_type() convenience function."""
        monkeypatch.setenv('XDG_SESSION_TYPE', 'wayland')

        result = detect_desktop_type()

        assert result == DesktopType.WAYLAND

    def test_is_x11_function(self, monkeypatch):
        """Test is_x11() convenience function."""
        monkeypatch.setenv('XDG_SESSION_TYPE', 'x11')

        assert is_x11() is True

    def test_is_wayland_function(self, monkeypatch):
        """Test is_wayland() convenience function."""
        monkeypatch.setenv('XDG_SESSION_TYPE', 'wayland')

        assert is_wayland() is True

    def test_is_display_available_function(self, monkeypatch):
        """Test is_display_available() convenience function."""
        monkeypatch.setenv('DISPLAY', ':0')

        assert is_display_available() is True


class TestDesktopTypeEnum:
    """Test DesktopType enum."""

    def test_desktop_type_values(self):
        """Test DesktopType enum values."""
        assert DesktopType.X11.value == "x11"
        assert DesktopType.WAYLAND.value == "wayland"
        assert DesktopType.UNKNOWN.value == "unknown"

    def test_desktop_type_equality(self):
        """Test DesktopType enum equality."""
        assert DesktopType.X11 == DesktopType.X11
        assert DesktopType.X11 != DesktopType.WAYLAND
        assert DesktopType.WAYLAND != DesktopType.UNKNOWN


class TestEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_case_insensitive_detection(self, monkeypatch):
        """Test that detection is case-insensitive."""
        # Mixed case
        monkeypatch.setenv('XDG_SESSION_TYPE', 'X11')

        result = DesktopDetector.detect()

        assert result == DesktopType.X11

    def test_wayland_in_xdg_session_type_substring(self, monkeypatch):
        """Test detection when 'wayland' appears in XDG_SESSION_TYPE."""
        monkeypatch.setenv('XDG_SESSION_TYPE', 'ubuntu-wayland')

        result = DesktopDetector.detect()

        assert result == DesktopType.WAYLAND

    def test_x11_in_xdg_session_type_substring(self, monkeypatch):
        """Test detection when 'x11' appears in XDG_SESSION_TYPE."""
        monkeypatch.setenv('XDG_SESSION_TYPE', 'ubuntu-x11')

        result = DesktopDetector.detect()

        assert result == DesktopType.X11

    def test_empty_environment_variables(self, monkeypatch):
        """Test handling of empty (not None) environment variables."""
        monkeypatch.setenv('XDG_SESSION_TYPE', '')
        monkeypatch.setenv('WAYLAND_DISPLAY', '')
        monkeypatch.setenv('DISPLAY', '')

        # Mock loginctl to fail
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()

            result = DesktopDetector.detect()

            assert result == DesktopType.UNKNOWN
