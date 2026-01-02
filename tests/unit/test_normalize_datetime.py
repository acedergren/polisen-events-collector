"""
Unit tests for datetime normalization function

PRIORITY: HIGH - This function is critical for data integrity
"""
import pytest
from collect_events import PolisenCollector


class TestNormalizeDatetime:
    """Test datetime normalization logic"""

    @pytest.mark.parametrize("input_dt,expected", [
        # Single-digit hours (0-9) - CRITICAL test cases
        ("2026-01-02 0:00:00 +01:00", "2026-01-02 00:00:00 +01:00"),
        ("2026-01-02 1:15:30 +01:00", "2026-01-02 01:15:30 +01:00"),
        ("2026-01-02 2:30:45 +01:00", "2026-01-02 02:30:45 +01:00"),
        ("2026-01-02 3:45:12 +01:00", "2026-01-02 03:45:12 +01:00"),
        ("2026-01-02 4:00:00 +01:00", "2026-01-02 04:00:00 +01:00"),
        ("2026-01-02 5:15:20 +01:00", "2026-01-02 05:15:20 +01:00"),
        ("2026-01-02 6:30:40 +01:00", "2026-01-02 06:30:40 +01:00"),
        ("2026-01-02 7:45:50 +01:00", "2026-01-02 07:45:50 +01:00"),
        ("2026-01-02 8:00:10 +01:00", "2026-01-02 08:00:10 +01:00"),
        ("2026-01-02 9:59:59 +01:00", "2026-01-02 09:59:59 +01:00"),

        # Double-digit hours (should not change)
        ("2026-01-02 10:00:00 +01:00", "2026-01-02 10:00:00 +01:00"),
        ("2026-01-02 11:30:00 +01:00", "2026-01-02 11:30:00 +01:00"),
        ("2026-01-02 12:00:00 +01:00", "2026-01-02 12:00:00 +01:00"),
        ("2026-01-02 19:56:53 +01:00", "2026-01-02 19:56:53 +01:00"),
        ("2026-01-02 23:59:59 +01:00", "2026-01-02 23:59:59 +01:00"),

        # Different timezones
        ("2026-01-02 5:30:00 +00:00", "2026-01-02 05:30:00 +00:00"),
        ("2026-01-02 8:45:12 -05:00", "2026-01-02 08:45:12 -05:00"),
        ("2026-01-02 3:15:30 +02:00", "2026-01-02 03:15:30 +02:00"),
        ("2026-01-02 7:00:00 -08:00", "2026-01-02 07:00:00 -08:00"),

        # Already normalized (no change)
        ("2026-01-02 09:38:09 +01:00", "2026-01-02 09:38:09 +01:00"),
        ("2026-01-02 05:00:00 +01:00", "2026-01-02 05:00:00 +01:00"),
    ])
    def test_normalize_datetime_variations(self, input_dt, expected):
        """Test datetime normalization with various inputs"""
        result = PolisenCollector.normalize_datetime(input_dt)
        assert result == expected, f"Failed for input: {input_dt}"

    def test_normalize_datetime_invalid_format_unchanged(self):
        """Invalid datetime formats should return unchanged"""
        invalid_inputs = [
            "invalid-date",
            "2026-01-02",  # Missing time
            "12:00:00",    # Missing date
            "",            # Empty string
            "not a datetime at all",
            "2026-13-45 99:99:99 +99:99",  # Invalid values
        ]
        for invalid in invalid_inputs:
            result = PolisenCollector.normalize_datetime(invalid)
            assert result == invalid, f"Should not modify invalid input: {invalid}"

    def test_normalize_datetime_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Midnight
        assert PolisenCollector.normalize_datetime(
            "2026-01-02 0:00:00 +01:00"
        ) == "2026-01-02 00:00:00 +01:00"

        # One second before 10 AM
        assert PolisenCollector.normalize_datetime(
            "2026-01-02 9:59:59 +01:00"
        ) == "2026-01-02 09:59:59 +01:00"

        # Exactly 10 AM (should not change)
        assert PolisenCollector.normalize_datetime(
            "2026-01-02 10:00:00 +01:00"
        ) == "2026-01-02 10:00:00 +01:00"

    def test_normalize_datetime_real_api_example(self):
        """Test with actual example from Polisen API"""
        # This is the exact format that caused the bug
        input_dt = "2026-01-02 9:38:09 +01:00"
        expected = "2026-01-02 09:38:09 +01:00"
        assert PolisenCollector.normalize_datetime(input_dt) == expected

    @pytest.mark.parametrize("timezone", [
        "+00:00",  # UTC
        "+01:00",  # CET
        "+02:00",  # CEST
        "-05:00",  # EST
        "-08:00",  # PST
        "+05:30",  # IST (half-hour offset)
        "+09:45",  # Nepal (quarter-hour offset)
    ])
    def test_normalize_datetime_various_timezones(self, timezone):
        """Test normalization works with various timezone offsets"""
        input_dt = f"2026-01-02 5:30:15 {timezone}"
        expected = f"2026-01-02 05:30:15 {timezone}"
        assert PolisenCollector.normalize_datetime(input_dt) == expected

    def test_normalize_datetime_preserves_double_digit(self):
        """Verify double-digit hours are preserved exactly"""
        for hour in range(10, 24):
            input_dt = f"2026-01-02 {hour}:30:45 +01:00"
            result = PolisenCollector.normalize_datetime(input_dt)
            assert result == input_dt, f"Modified double-digit hour: {hour}"
