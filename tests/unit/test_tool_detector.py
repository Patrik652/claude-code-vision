"""
Unit tests for screenshot tool detection.

Tests the ToolDetector utility that identifies available screenshot tools.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import subprocess

from src.lib.tool_detector import (
    ToolDetector,
    ScreenshotTool,
    detect_tool,
    detect_all_tools,
    get_preferred_tool
)


class TestToolDetector:
    """Unit tests for ToolDetector class."""

    def test_detect_tool_scrot_available(self):
        """Test detection of scrot when available."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = '/usr/bin/scrot'

            result = ToolDetector.detect_tool(ScreenshotTool.SCROT)

            assert result is True
            mock_which.assert_called_once_with('scrot')

    def test_detect_tool_scrot_not_available(self):
        """Test detection of scrot when not available."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = None

            result = ToolDetector.detect_tool(ScreenshotTool.SCROT)

            assert result is False

    def test_detect_tool_grim_available(self):
        """Test detection of grim when available."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = '/usr/bin/grim'

            result = ToolDetector.detect_tool(ScreenshotTool.GRIM)

            assert result is True
            mock_which.assert_called_once_with('grim')

    def test_detect_tool_import_available(self):
        """Test detection of ImageMagick import when available."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = '/usr/bin/import'

            result = ToolDetector.detect_tool(ScreenshotTool.IMPORT)

            assert result is True
            mock_which.assert_called_once_with('import')

    def test_detect_tool_unknown_returns_false(self):
        """Test that UNKNOWN tool type returns False."""
        result = ToolDetector.detect_tool(ScreenshotTool.UNKNOWN)

        assert result is False

    def test_detect_all_tools_none_available(self):
        """Test detect_all_tools() when no tools are available."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = None

            result = ToolDetector.detect_all_tools()

            assert result == []

    def test_detect_all_tools_one_available(self):
        """Test detect_all_tools() when one tool is available."""
        with patch('shutil.which') as mock_which:
            def which_side_effect(cmd):
                if cmd == 'scrot':
                    return '/usr/bin/scrot'
                return None

            mock_which.side_effect = which_side_effect

            result = ToolDetector.detect_all_tools()

            assert ScreenshotTool.SCROT in result
            assert ScreenshotTool.GRIM not in result
            assert ScreenshotTool.IMPORT not in result

    def test_detect_all_tools_multiple_available(self):
        """Test detect_all_tools() when multiple tools are available."""
        with patch('shutil.which') as mock_which:
            def which_side_effect(cmd):
                if cmd in ['scrot', 'grim']:
                    return f'/usr/bin/{cmd}'
                return None

            mock_which.side_effect = which_side_effect

            result = ToolDetector.detect_all_tools()

            assert ScreenshotTool.SCROT in result
            assert ScreenshotTool.GRIM in result
            assert ScreenshotTool.IMPORT not in result

    def test_detect_all_tools_all_available(self):
        """Test detect_all_tools() when all tools are available."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = '/usr/bin/tool'

            result = ToolDetector.detect_all_tools()

            assert len(result) == 3
            assert ScreenshotTool.SCROT in result
            assert ScreenshotTool.GRIM in result
            assert ScreenshotTool.IMPORT in result

    def test_get_preferred_tool_wayland(self):
        """Test get_preferred_tool() for Wayland environment."""
        with patch('shutil.which') as mock_which:
            def which_side_effect(cmd):
                return f'/usr/bin/{cmd}' if cmd == 'grim' else None

            mock_which.side_effect = which_side_effect

            result = ToolDetector.get_preferred_tool(desktop_type='wayland')

            assert result == ScreenshotTool.GRIM

    def test_get_preferred_tool_x11(self):
        """Test get_preferred_tool() for X11 environment."""
        with patch('shutil.which') as mock_which:
            def which_side_effect(cmd):
                return f'/usr/bin/{cmd}' if cmd == 'scrot' else None

            mock_which.side_effect = which_side_effect

            result = ToolDetector.get_preferred_tool(desktop_type='x11')

            assert result == ScreenshotTool.SCROT

    def test_get_preferred_tool_auto_prefers_scrot(self):
        """Test get_preferred_tool() with auto prefers scrot when available."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = '/usr/bin/tool'

            result = ToolDetector.get_preferred_tool(desktop_type='auto')

            assert result == ScreenshotTool.SCROT

    def test_get_preferred_tool_auto_fallback_to_grim(self):
        """Test get_preferred_tool() with auto falls back to grim."""
        with patch('shutil.which') as mock_which:
            def which_side_effect(cmd):
                return '/usr/bin/grim' if cmd == 'grim' else None

            mock_which.side_effect = which_side_effect

            result = ToolDetector.get_preferred_tool(desktop_type='auto')

            assert result == ScreenshotTool.GRIM

    def test_get_preferred_tool_auto_fallback_to_import(self):
        """Test get_preferred_tool() with auto falls back to import."""
        with patch('shutil.which') as mock_which:
            def which_side_effect(cmd):
                return '/usr/bin/import' if cmd == 'import' else None

            mock_which.side_effect = which_side_effect

            result = ToolDetector.get_preferred_tool(desktop_type='auto')

            assert result == ScreenshotTool.IMPORT

    def test_get_preferred_tool_none_available(self):
        """Test get_preferred_tool() when no tools are available."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = None

            result = ToolDetector.get_preferred_tool(desktop_type='auto')

            assert result is None

    def test_get_preferred_tool_wayland_fallback(self):
        """Test get_preferred_tool() for Wayland falls back when grim not available."""
        with patch('shutil.which') as mock_which:
            def which_side_effect(cmd):
                return '/usr/bin/scrot' if cmd == 'scrot' else None

            mock_which.side_effect = which_side_effect

            result = ToolDetector.get_preferred_tool(desktop_type='wayland')

            # Should fall back to scrot when grim not available
            assert result == ScreenshotTool.SCROT

    def test_verify_tool_works_scrot(self):
        """Test verify_tool_works() for scrot."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = '/usr/bin/scrot'

            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0)

                result = ToolDetector.verify_tool_works(ScreenshotTool.SCROT)

                assert result is True
                mock_run.assert_called_once()

    def test_verify_tool_works_not_installed(self):
        """Test verify_tool_works() when tool is not installed."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = None

            result = ToolDetector.verify_tool_works(ScreenshotTool.SCROT)

            assert result is False

    def test_verify_tool_works_fails_verification(self):
        """Test verify_tool_works() when tool verification fails."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = '/usr/bin/scrot'

            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=2)

                result = ToolDetector.verify_tool_works(ScreenshotTool.SCROT)

                assert result is False

    def test_verify_tool_works_accepts_exit_code_1(self):
        """Test verify_tool_works() accepts exit code 1 (some tools use this)."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = '/usr/bin/scrot'

            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=1)

                result = ToolDetector.verify_tool_works(ScreenshotTool.SCROT)

                assert result is True

    def test_verify_tool_works_timeout(self):
        """Test verify_tool_works() handles timeout."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = '/usr/bin/scrot'

            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired('scrot', 2)

                result = ToolDetector.verify_tool_works(ScreenshotTool.SCROT)

                assert result is False

    def test_verify_tool_works_file_not_found(self):
        """Test verify_tool_works() handles FileNotFoundError."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = '/usr/bin/scrot'

            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = FileNotFoundError()

                result = ToolDetector.verify_tool_works(ScreenshotTool.SCROT)

                assert result is False

    def test_get_tool_info_complete(self):
        """Test get_tool_info() returns complete information."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = '/usr/bin/scrot'

            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout='scrot 1.7\n'
                )

                info = ToolDetector.get_tool_info(ScreenshotTool.SCROT)

                assert info['tool'] == 'scrot'
                assert info['command'] == 'scrot'
                assert info['available'] is True
                assert info['works'] is True
                assert info['path'] == '/usr/bin/scrot'
                assert 'version' in info
                assert 'scrot' in info['version']

    def test_get_tool_info_not_available(self):
        """Test get_tool_info() when tool is not available."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = None

            info = ToolDetector.get_tool_info(ScreenshotTool.SCROT)

            assert info['available'] is False
            assert info['works'] is False
            assert info['path'] is None
            assert 'version' not in info

    def test_get_tool_version_success(self):
        """Test _get_tool_version() returns version string."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout='scrot 1.7\nCopyright...\n'
            )

            version = ToolDetector._get_tool_version(ScreenshotTool.SCROT)

            assert version == 'scrot 1.7'

    def test_get_tool_version_from_stderr(self):
        """Test _get_tool_version() handles version in stderr."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout='',
                stderr='grim version 1.4.0\n'
            )

            version = ToolDetector._get_tool_version(ScreenshotTool.GRIM)

            assert version == 'grim version 1.4.0'

    def test_get_tool_version_failure(self):
        """Test _get_tool_version() handles failure."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()

            version = ToolDetector._get_tool_version(ScreenshotTool.SCROT)

            assert version is None

    def test_get_installation_hints_scrot(self):
        """Test get_installation_hints() for scrot."""
        hints = ToolDetector.get_installation_hints(ScreenshotTool.SCROT)

        assert isinstance(hints, str)
        assert 'scrot' in hints.lower()
        assert 'apt' in hints.lower()
        assert 'dnf' in hints.lower()
        assert 'pacman' in hints.lower()

    def test_get_installation_hints_grim(self):
        """Test get_installation_hints() for grim."""
        hints = ToolDetector.get_installation_hints(ScreenshotTool.GRIM)

        assert isinstance(hints, str)
        assert 'grim' in hints.lower()
        assert 'wayland' in hints.lower()

    def test_get_installation_hints_import(self):
        """Test get_installation_hints() for ImageMagick."""
        hints = ToolDetector.get_installation_hints(ScreenshotTool.IMPORT)

        assert isinstance(hints, str)
        assert 'imagemagick' in hints.lower()


class TestConvenienceFunctions:
    """Test convenience functions for tool detection."""

    def test_detect_tool_function(self):
        """Test detect_tool() convenience function."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = '/usr/bin/scrot'

            result = detect_tool(ScreenshotTool.SCROT)

            assert result is True

    def test_detect_all_tools_function(self):
        """Test detect_all_tools() convenience function."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = '/usr/bin/tool'

            result = detect_all_tools()

            assert len(result) == 3

    def test_get_preferred_tool_function(self):
        """Test get_preferred_tool() convenience function."""
        with patch('shutil.which') as mock_which:
            def which_side_effect(cmd):
                return f'/usr/bin/{cmd}' if cmd == 'scrot' else None

            mock_which.side_effect = which_side_effect

            result = get_preferred_tool(desktop_type='x11')

            assert result == ScreenshotTool.SCROT


class TestScreenshotToolEnum:
    """Test ScreenshotTool enum."""

    def test_screenshot_tool_values(self):
        """Test ScreenshotTool enum values."""
        assert ScreenshotTool.SCROT.value == "scrot"
        assert ScreenshotTool.GRIM.value == "grim"
        assert ScreenshotTool.IMPORT.value == "import"
        assert ScreenshotTool.UNKNOWN.value == "unknown"

    def test_screenshot_tool_equality(self):
        """Test ScreenshotTool enum equality."""
        assert ScreenshotTool.SCROT == ScreenshotTool.SCROT
        assert ScreenshotTool.SCROT != ScreenshotTool.GRIM
        assert ScreenshotTool.GRIM != ScreenshotTool.UNKNOWN


class TestEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_case_sensitivity_in_desktop_type(self):
        """Test that desktop_type parameter is case-insensitive."""
        with patch('shutil.which') as mock_which:
            def which_side_effect(cmd):
                return f'/usr/bin/{cmd}' if cmd == 'grim' else None

            mock_which.side_effect = which_side_effect

            result_lower = ToolDetector.get_preferred_tool(desktop_type='wayland')
            result_upper = ToolDetector.get_preferred_tool(desktop_type='WAYLAND')
            result_mixed = ToolDetector.get_preferred_tool(desktop_type='Wayland')

            assert result_lower == ScreenshotTool.GRIM
            assert result_upper == ScreenshotTool.GRIM
            assert result_mixed == ScreenshotTool.GRIM

    def test_tools_mapping_completeness(self):
        """Test that TOOLS mapping includes all non-UNKNOWN tools."""
        assert ScreenshotTool.SCROT in ToolDetector.TOOLS
        assert ScreenshotTool.GRIM in ToolDetector.TOOLS
        assert ScreenshotTool.IMPORT in ToolDetector.TOOLS
        assert ScreenshotTool.UNKNOWN not in ToolDetector.TOOLS

    def test_subprocess_error_handling(self):
        """Test that subprocess errors are handled gracefully."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = '/usr/bin/scrot'

            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = subprocess.SubprocessError("Test error")

                result = ToolDetector.verify_tool_works(ScreenshotTool.SCROT)

                assert result is False
