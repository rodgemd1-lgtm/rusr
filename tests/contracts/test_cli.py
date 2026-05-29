"""Tests for rusr.cli — CLI smoke and readiness commands."""
from __future__ import annotations

import pytest
from typer.testing import CliRunner

from rusr.cli import app


runner = CliRunner()


class TestCLISmoke:
    """Verify CLI smoke command."""

    def test_smoke_exits_zero(self):
        """rusr smoke must exit 0 in a complete repo."""
        result = runner.invoke(app, ["smoke"])
        assert result.exit_code == 0, f"Smoke failed:\n{result.output}"

    def test_smoke_output_contains_pass(self):
        """rusr smoke output must contain SMOKE: PASS."""
        result = runner.invoke(app, ["smoke"])
        assert "SMOKE: PASS" in result.output

    def test_smoke_counts_checks(self):
        """rusr smoke must report passed and failed counts."""
        result = runner.invoke(app, ["smoke"])
        assert "Passed:" in result.output
        assert "Failed: 0" in result.output


class TestCLICheck:
    """Verify CLI check commands."""

    def test_check_all_shows_scorecard(self):
        """rusr check must show KPI scorecard."""
        result = runner.invoke(app, ["check"])
        assert result.exit_code == 0
        assert "v10_current_score" in result.output
        assert "agent_readiness" in result.output
        assert "cli_readiness" in result.output
        assert "mcp_readiness" in result.output

    def test_check_agent_passes(self):
        """rusr check agent must pass."""
        result = runner.invoke(app, ["check", "agent"])
        assert result.exit_code == 0
        assert "PASS" in result.output

    def test_check_mcp_passes(self):
        """rusr check mcp must pass with >= 6 tools."""
        result = runner.invoke(app, ["check", "mcp"])
        assert result.exit_code == 0
        assert "PASS" in result.output
        assert "rusr/smoke" in result.output
        assert "rusr/check" in result.output

    def test_check_proof_passes(self):
        """rusr check proof must pass when proof directory exists."""
        result = runner.invoke(app, ["check", "proof"])
        assert result.exit_code == 0
        assert "PASS" in result.output

    def test_version_shows_score(self):
        """rusr version must show v10_current_score."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "v10_current_score" in result.output
