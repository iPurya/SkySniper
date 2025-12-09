"""
Tests for CLI commands.
"""

import pytest
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

    def test_search_command(self, runner):
        """Test search command."""
        result = runner.invoke(
            cli,
            ["search", "THR", "MHD", "2025-01-15", "--adults", "2"]
        )
        assert result.exit_code == 0
        assert "THR → MHD" in result.output
        assert "2025-01-15" in result.output
        assert "2 adult(s)" in result.output

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

    def test_monitor_command(self, runner):
        """Test monitor command."""
        result = runner.invoke(
            cli,
            ["monitor", "THR", "MHD", "2025-01-15", "--interval", "60"]
        )
        assert result.exit_code == 0
        assert "THR → MHD" in result.output
        assert "Every 60 minutes" in result.output

    def test_search_command_invalid_args(self, runner):
        """Test search command with missing arguments."""
        result = runner.invoke(cli, ["search", "THR"])
        assert result.exit_code != 0  # Should fail with missing args
