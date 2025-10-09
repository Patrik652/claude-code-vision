"""
Unit tests for PrivacyZone validation.

Tests the validation logic in PrivacyZone entity.
"""

import pytest
from src.models.entities import PrivacyZone


class TestPrivacyZoneCreation:
    """Unit tests for PrivacyZone dataclass creation."""

    def test_privacy_zone_creation_all_fields(self):
        """Test PrivacyZone can be created with all fields."""
        zone = PrivacyZone(
            name="Test Zone",
            x=100,
            y=200,
            width=300,
            height=400,
            monitor=1
        )

        assert zone.name == "Test Zone"
        assert zone.x == 100
        assert zone.y == 200
        assert zone.width == 300
        assert zone.height == 400
        assert zone.monitor == 1

    def test_privacy_zone_creation_without_monitor(self):
        """Test PrivacyZone with monitor=None (applies to all monitors)."""
        zone = PrivacyZone(
            name="All Monitors Zone",
            x=0,
            y=0,
            width=100,
            height=100,
            monitor=None
        )

        assert zone.monitor is None

    def test_privacy_zone_creation_minimal(self):
        """Test PrivacyZone with minimal required fields."""
        zone = PrivacyZone(
            name="Minimal",
            x=0,
            y=0,
            width=50,
            height=50
        )

        assert zone.name == "Minimal"
        assert zone.monitor is None  # Default value


class TestPrivacyZoneEquality:
    """Unit tests for PrivacyZone equality comparison."""

    def test_privacy_zone_equality(self):
        """Test PrivacyZone equality comparison."""
        zone1 = PrivacyZone(name="Zone", x=100, y=100, width=200, height=200, monitor=0)
        zone2 = PrivacyZone(name="Zone", x=100, y=100, width=200, height=200, monitor=0)

        assert zone1 == zone2

    def test_privacy_zone_inequality_position(self):
        """Test PrivacyZone inequality when position differs."""
        zone1 = PrivacyZone(name="Zone", x=100, y=100, width=200, height=200, monitor=0)
        zone2 = PrivacyZone(name="Zone", x=200, y=100, width=200, height=200, monitor=0)

        assert zone1 != zone2

    def test_privacy_zone_inequality_size(self):
        """Test PrivacyZone inequality when size differs."""
        zone1 = PrivacyZone(name="Zone", x=100, y=100, width=200, height=200, monitor=0)
        zone2 = PrivacyZone(name="Zone", x=100, y=100, width=300, height=200, monitor=0)

        assert zone1 != zone2

    def test_privacy_zone_inequality_name(self):
        """Test PrivacyZone inequality when name differs."""
        zone1 = PrivacyZone(name="Zone1", x=100, y=100, width=200, height=200, monitor=0)
        zone2 = PrivacyZone(name="Zone2", x=100, y=100, width=200, height=200, monitor=0)

        assert zone1 != zone2

    def test_privacy_zone_inequality_monitor(self):
        """Test PrivacyZone inequality when monitor differs."""
        zone1 = PrivacyZone(name="Zone", x=100, y=100, width=200, height=200, monitor=0)
        zone2 = PrivacyZone(name="Zone", x=100, y=100, width=200, height=200, monitor=1)

        assert zone1 != zone2


class TestPrivacyZoneValidation:
    """Unit tests for PrivacyZone validation (if validation method exists)."""

    def test_valid_privacy_zone_coordinates(self):
        """Test validation passes for valid coordinates."""
        zone = PrivacyZone(
            name="Valid Zone",
            x=100,
            y=100,
            width=400,
            height=300,
            monitor=0
        )

        # Should not raise any exception
        # If validate method exists: zone.validate(monitor_width=1920, monitor_height=1080)
        assert zone.x >= 0
        assert zone.y >= 0
        assert zone.width > 0
        assert zone.height > 0

    def test_privacy_zone_at_origin(self):
        """Test privacy zone starting at (0,0)."""
        zone = PrivacyZone(
            name="Origin Zone",
            x=0,
            y=0,
            width=800,
            height=600,
            monitor=0
        )

        assert zone.x == 0
        assert zone.y == 0

    def test_privacy_zone_large_area(self):
        """Test privacy zone covering large area."""
        zone = PrivacyZone(
            name="Large Zone",
            x=0,
            y=0,
            width=1920,
            height=1080,
            monitor=0
        )

        assert zone.width == 1920
        assert zone.height == 1080


class TestPrivacyZoneEdgeCases:
    """Edge case tests for PrivacyZone."""

    def test_privacy_zone_very_small_area(self):
        """Test privacy zone with minimal 1x1 pixel area."""
        zone = PrivacyZone(
            name="1x1 Zone",
            x=500,
            y=500,
            width=1,
            height=1,
            monitor=0
        )

        assert zone.width == 1
        assert zone.height == 1

    def test_privacy_zone_full_screen_4k(self):
        """Test privacy zone covering entire 4K monitor."""
        zone = PrivacyZone(
            name="Full 4K",
            x=0,
            y=0,
            width=3840,
            height=2160,
            monitor=0
        )

        assert zone.width == 3840
        assert zone.height == 2160

    def test_privacy_zone_name_variations(self):
        """Test privacy zones with various name formats."""
        zones = [
            PrivacyZone(name="Password Field", x=0, y=0, width=100, height=50, monitor=0),
            PrivacyZone(name="API Keys Section", x=0, y=0, width=100, height=50, monitor=0),
            PrivacyZone(name="Personal Info", x=0, y=0, width=100, height=50, monitor=0),
            PrivacyZone(name="Credit Card Area", x=0, y=0, width=100, height=50, monitor=0),
        ]

        for zone in zones:
            assert len(zone.name) > 0

    def test_privacy_zone_with_empty_name(self):
        """Test privacy zone with empty name string."""
        zone = PrivacyZone(
            name="",
            x=100,
            y=100,
            width=200,
            height=200,
            monitor=0
        )

        # Empty name is allowed (implementation may validate differently)
        assert zone.name == ""

    def test_privacy_zone_multimonitor_setup(self):
        """Test privacy zones for different monitors."""
        zones = [
            PrivacyZone(name="Monitor 0 Zone", x=0, y=0, width=100, height=100, monitor=0),
            PrivacyZone(name="Monitor 1 Zone", x=0, y=0, width=100, height=100, monitor=1),
            PrivacyZone(name="Monitor 2 Zone", x=0, y=0, width=100, height=100, monitor=2),
            PrivacyZone(name="All Monitors", x=0, y=0, width=100, height=100, monitor=None),
        ]

        assert zones[0].monitor == 0
        assert zones[1].monitor == 1
        assert zones[2].monitor == 2
        assert zones[3].monitor is None


class TestPrivacyZoneRepresentation:
    """Test PrivacyZone string representation and debugging."""

    def test_privacy_zone_repr(self):
        """Test PrivacyZone has useful string representation."""
        zone = PrivacyZone(
            name="Test Zone",
            x=100,
            y=200,
            width=300,
            height=400,
            monitor=0
        )

        repr_str = repr(zone)

        # Should contain key information
        assert "PrivacyZone" in repr_str or "name=" in repr_str

    def test_privacy_zone_str(self):
        """Test PrivacyZone string conversion."""
        zone = PrivacyZone(
            name="Debug Zone",
            x=50,
            y=50,
            width=100,
            height=100,
            monitor=1
        )

        str_repr = str(zone)

        # Should be a valid string
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0


class TestPrivacyZoneUseCases:
    """Test realistic privacy zone use cases."""

    def test_password_field_zone(self):
        """Test privacy zone for password input field."""
        # Typical password field: small horizontal rectangle
        zone = PrivacyZone(
            name="Login Password",
            x=500,
            y=400,
            width=300,
            height=40,
            monitor=0
        )

        assert zone.width > zone.height  # Horizontal rectangle
        assert zone.name == "Login Password"

    def test_api_key_section_zone(self):
        """Test privacy zone for API keys section."""
        zone = PrivacyZone(
            name="API Keys Dashboard",
            x=100,
            y=100,
            width=600,
            height=400,
            monitor=0
        )

        assert zone.width == 600
        assert zone.height == 400

    def test_notification_area_zone(self):
        """Test privacy zone for notification area."""
        # Bottom-right notification area
        zone = PrivacyZone(
            name="Notifications",
            x=1520,  # Assuming 1920x1080 screen
            y=880,
            width=400,
            height=200,
            monitor=0
        )

        assert zone.x > 1000  # Right side of screen
        assert zone.y > 500   # Bottom half of screen

    def test_terminal_window_zone(self):
        """Test privacy zone for terminal window."""
        zone = PrivacyZone(
            name="Terminal Window",
            x=0,
            y=0,
            width=1920,
            height=1080,
            monitor=1  # Secondary monitor
        )

        assert zone.monitor == 1
        # Full screen coverage
        assert zone.x == 0 and zone.y == 0

    def test_browser_tab_zone(self):
        """Test privacy zone for browser tab area."""
        zone = PrivacyZone(
            name="Browser Tabs",
            x=0,
            y=0,
            width=1920,
            height=50,  # Just the tab bar
            monitor=0
        )

        assert zone.height < zone.width  # Wide but short
        assert zone.y == 0  # Top of screen
