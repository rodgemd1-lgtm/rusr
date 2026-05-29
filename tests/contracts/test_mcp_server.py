"""Tests for rusr.mcp.server — MCP tool/resource/prompt surface."""
from __future__ import annotations

import pytest


class TestMCPTools:
    """Verify MCP tool surface is complete and callable."""

    def test_tools_defined(self):
        """TOOLS dict must have >= 6 entries."""
        from rusr.mcp.server import TOOLS
        assert len(TOOLS) >= 6, f"Expected >= 6 MCP tools, got {len(TOOLS)}"

    def test_resources_defined(self):
        """RESOURCES dict must have >= 3 entries."""
        from rusr.mcp.server import RESOURCES
        assert len(RESOURCES) >= 3, f"Expected >= 3 MCP resources, got {len(RESOURCES)}"

    def test_prompts_defined(self):
        """PROMPTS dict must have >= 3 entries."""
        from rusr.mcp.server import PROMPTS
        assert len(PROMPTS) >= 3, f"Expected >= 3 MCP prompts, got {len(PROMPTS)}"

    def test_required_tools_present(self):
        """Required tools must be present by name."""
        from rusr.mcp.server import TOOLS
        required = {
            "rusr/smoke",
            "rusr/check",
            "rusr/audit_skill",
            "rusr/verify_pair",
            "rusr/validate_loop",
            "rusr/enforce_budget",
        }
        missing = required - set(TOOLS.keys())
        assert not missing, f"Missing required MCP tools: {missing}"

    def test_each_tool_has_description_and_schema(self):
        """Each tool must have a description and input_schema."""
        from rusr.mcp.server import TOOLS
        for name, defn in TOOLS.items():
            assert "description" in defn, f"Tool '{name}' missing description"
            assert "input_schema" in defn, f"Tool '{name}' missing input_schema"
            assert "handler" in defn, f"Tool '{name}' missing handler"

    def test_call_tool_check(self):
        """rusr/check tool returns a KPI scorecard dict."""
        from rusr.mcp.server import call_tool
        result = call_tool("rusr/check", {})
        assert "scores" in result
        assert "v10_current_score" in result
        assert isinstance(result["v10_current_score"], int)

    def test_call_tool_audit_skill_clean(self):
        """rusr/audit_skill returns clean for innocent code."""
        from rusr.mcp.server import call_tool
        result = call_tool("rusr/audit_skill", {"code": "def hello():\n    return 42\n", "skill_id": "hello"})
        assert result["clean"] is True
        assert result["finding_count"] == 0

    def test_call_tool_audit_skill_credential(self):
        """rusr/audit_skill detects hardcoded credential."""
        from rusr.mcp.server import call_tool
        result = call_tool(
            "rusr/audit_skill",
            {"code": 'api_key = "sk-abcdef1234567890abcdefgh1234"', "skill_id": "bad-skill"},
        )
        assert result["clean"] is False
        assert result["finding_count"] >= 1

    def test_call_tool_verify_pair_cross_family(self):
        """rusr/verify_pair passes for cross-family models."""
        from rusr.mcp.server import call_tool
        result = call_tool("rusr/verify_pair", {"generator": "claude-opus-4.7", "verifier": "gpt-5.5"})
        assert result["passed"] is True

    def test_call_tool_verify_pair_same_family(self):
        """rusr/verify_pair fails for same-family models."""
        from rusr.mcp.server import call_tool
        result = call_tool("rusr/verify_pair", {"generator": "claude-sonnet-4.5", "verifier": "claude-opus-4.7"})
        assert result["passed"] is False
        assert "error" in result

    def test_call_tool_validate_loop_valid(self):
        """rusr/validate_loop passes for bounded loop."""
        from rusr.mcp.server import call_tool
        result = call_tool("rusr/validate_loop", {"node": {"id": "loop1", "type": "loop", "max_iterations": 5}})
        assert result["valid"] is True
        assert result["max_iterations"] == 5

    def test_call_tool_validate_loop_unbounded(self):
        """rusr/validate_loop fails for unbounded loop."""
        from rusr.mcp.server import call_tool
        result = call_tool("rusr/validate_loop", {"node": {"id": "bad_loop", "type": "loop"}})
        assert result["valid"] is False
        assert "error" in result

    def test_call_tool_enforce_budget_ok(self):
        """rusr/enforce_budget returns ok when under ceiling."""
        from rusr.mcp.server import call_tool
        result = call_tool(
            "rusr/enforce_budget",
            {"tier": "per_run", "cost_so_far": 1.0, "new_cost": 0.50, "ceiling_usd": 20.0},
        )
        assert result["action"] == "ok"

    def test_call_tool_enforce_budget_halt(self):
        """rusr/enforce_budget returns halt when ceiling exceeded."""
        from rusr.mcp.server import call_tool
        result = call_tool(
            "rusr/enforce_budget",
            {"tier": "per_run", "cost_so_far": 19.50, "new_cost": 1.00, "ceiling_usd": 20.0},
        )
        assert result["action"] == "halt"

    def test_call_tool_unknown_returns_error(self):
        """Calling unknown tool returns error dict, not exception."""
        from rusr.mcp.server import call_tool
        result = call_tool("rusr/nonexistent", {})
        assert "error" in result

    def test_get_resource_registry(self):
        """rusr://registry resource returns tool registry dict."""
        from rusr.mcp.server import get_resource
        registry = get_resource("rusr://registry")
        assert isinstance(registry, dict)
        assert "cinema_studio_2_5" in registry

    def test_get_resource_kpi_scorecard(self):
        """rusr://kpi-scorecard resource returns score dict."""
        from rusr.mcp.server import get_resource
        scorecard = get_resource("rusr://kpi-scorecard")
        assert isinstance(scorecard, dict)
        assert "agent_readiness" in scorecard

    def test_get_prompt_planner_system(self):
        """rusr/planner-system prompt returns non-empty string."""
        from rusr.mcp.server import get_prompt
        prompt = get_prompt("rusr/planner-system")
        assert isinstance(prompt, str)
        assert len(prompt) > 20

    def test_get_prompt_unknown_returns_message(self):
        """Unknown prompt returns error message, not exception."""
        from rusr.mcp.server import get_prompt
        result = get_prompt("rusr/nonexistent")
        assert "Unknown prompt" in result
