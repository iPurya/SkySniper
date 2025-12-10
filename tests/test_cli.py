"""
Tests for CLI commands.
"""

import pytest
from unittest.mock import patch, AsyncMock
from click.testing import CliRunner

from skysniper.skysniper import cli


class TestCLI:
    """Tests for CLI commands."""

    @pytest.fixture
    def runner(self):
        """CLI test runner."""
        return CliRunner()

    def test_cli_help(self, runner):
        """Test CLI help command."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "SkySniper" in result.output
        assert "search" in result.output
        assert "monitor" in result.output
        assert "sources" in result.output

    def test_cli_version(self, runner):
        """Test CLI version command."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "SkySniper" in result.output or "version" in result.output.lower()

    def test_search_command_help(self, runner):
        """Test search command help."""
        result = runner.invoke(cli, ["search", "--help"])
        assert result.exit_code == 0
        assert "ORIGIN" in result.output
        assert "DESTINATION" in result.output
        assert "DATE" in result.output

    def test_sources_command(self, runner):
        """Test sources command."""
        result = runner.invoke(cli, ["sources"])
        assert result.exit_code == 0
        assert "Alibaba" in result.output
        assert "Ataair" in result.output

    def test_monitor_command_help(self, runner):
        """Test monitor command help."""
        result = runner.invoke(cli, ["monitor", "--help"])
        assert result.exit_code == 0
        assert "ORIGIN" in result.output
        assert "interval" in result.output

    def test_search_command_invalid_args(self, runner):
        """Test search command with missing arguments."""
        result = runner.invoke(cli, ["search", "THR"])
        assert result.exit_code != 0  # Should fail with missing args

    @patch("skysniper.skysniper.run_all_scrapers")
    def test_search_command_with_mock(self, mock_scrapers, runner):
        """Test search command with mocked scrapers."""
        # Mock returns empty list (no flights found)
        mock_scrapers.return_value = []

        result = runner.invoke(
            cli,
            ["search", "THR", "MHD", "2025-01-15", "--adults", "2"]
        )

        assert result.exit_code == 0
        assert "THR → MHD" in result.output
        assert "2025-01-15" in result.output
        assert "2 adult(s)" in result.output
        # Should show "no flights found" since we mocked empty results
        assert "No flights found" in result.output or mock_scrapers.called

    @patch("skysniper.skysniper.run_all_scrapers")
    def test_search_command_with_results(self, mock_scrapers, runner):
        """Test search command displays flight results."""
        from datetime import datetime
        from skysniper.scrapers.base import Flight

        # Mock returns a flight
        mock_flight = Flight(
            origin="THR",
            destination="MHD",
            departure_time=datetime(2025, 1, 15, 10, 0),
            arrival_time=datetime(2025, 1, 15, 11, 30),
            airline="Test Air",
            flight_number="TA123",
            price=5000000.0,
            currency="IRR",
            duration_minutes=90,
            source="test",
        )
        mock_scrapers.return_value = [mock_flight]

        result = runner.invoke(
            cli,
            ["search", "THR", "MHD", "2025-01-15"]
        )

        assert result.exit_code == 0
        assert "THR → MHD" in result.output
        # Should show cheapest flight info
        assert "Cheapest" in result.output or "Test Air" in result.output
