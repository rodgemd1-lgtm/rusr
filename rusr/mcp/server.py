"""
RUSR MCP Server — Model Context Protocol tool/resource/prompt surface.

This module defines the MCP tools, resources, and prompts that RUSR
exposes to agent clients. It uses a lightweight, dependency-free design
so it can be imported without an MCP SDK.

To run as an actual MCP server, integrate with FastMCP or mcp-python-sdk.

Auth boundary: All tools are read-only governance checks.
No tool here can deploy, publish, send messages, or modify frozen contracts.

Smoke test:
    from rusr.mcp.server import TOOLS, RESOURCES, PROMPTS
    assert len(TOOLS) >= 6
"""
from __future__ import annotations

from typing import Any

# ── Tool definitions ──────────────────────────────────────────────────────────
# Each entry: name → {description, input_schema, handler}

def _tool_smoke(args: dict[str, Any]) -> dict[str, Any]:
    """Run local smoke check — no network, no secrets."""
    import subprocess
    import sys
    from pathlib import Path

    repo_root = Path(__file__).parent.parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "rusr.cli", "smoke"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONPATH": str(repo_root)},
        timeout=30,
    )
    return {
        "passed": result.returncode == 0,
        "output": result.stdout,
        "exit_code": result.returncode,
    }


def _tool_check(args: dict[str, Any]) -> dict[str, Any]:
    """Run full readiness check — returns KPI scorecard."""
    from rusr.cli import _kpi_scorecard
    scores = _kpi_scorecard()
    total = sum(scores.values())
    v10_score = round(total / len(scores))
    return {"scores": scores, "v10_current_score": v10_score}


def _tool_audit_skill(args: dict[str, Any]) -> dict[str, Any]:
    """Audit a skill code snippet for credentials and injection patterns."""
    from rusr.skill_registry.audit import audit_skill
    code = args.get("code", "")
    skill_id = args.get("skill_id", "unknown")
    findings = audit_skill(code, skill_id)
    return {
        "skill_id": skill_id,
        "finding_count": len(findings),
        "findings": [str(f) for f in findings],
        "clean": len(findings) == 0,
    }


def _tool_verify_pair(args: dict[str, Any]) -> dict[str, Any]:
    """Verify cross-family generator-verifier model pair."""
    from rusr.cross_family_verifier import VerifierCaptureError, get_model_family, verify_pair
    generator = args.get("generator", "")
    verifier = args.get("verifier", "")
    try:
        verify_pair(generator, verifier)
        return {
            "passed": True,
            "generator": generator,
            "generator_family": get_model_family(generator),
            "verifier": verifier,
            "verifier_family": get_model_family(verifier),
        }
    except VerifierCaptureError as exc:
        return {
            "passed": False,
            "error": str(exc),
            "generator": generator,
            "verifier": verifier,
        }


def _tool_validate_loop(args: dict[str, Any]) -> dict[str, Any]:
    """Validate a loop node dict for required bounds (max_iterations)."""
    from rusr.loop_governance import UnboundedLoopError, validate_loop_node
    node = args.get("node", {})
    try:
        loop = validate_loop_node(node)
        return {
            "valid": True,
            "max_iterations": loop.max_iterations,
            "until_conditions": loop.until_conditions,
            "on_max_reached": loop.on_max_reached.value,
        }
    except UnboundedLoopError as exc:
        return {"valid": False, "error": str(exc)}


def _tool_enforce_budget(args: dict[str, Any]) -> dict[str, Any]:
    """Enforce budget ceiling for a studio run."""
    from rusr.budget_governance import BudgetCeiling, BudgetExceeded, BudgetTier, enforce_budget
    tier_str = args.get("tier", "per_run")
    studio = args.get("studio", None)
    cost_so_far = float(args.get("cost_so_far", 0.0))
    new_cost = float(args.get("new_cost", 0.0))
    ceiling_usd = float(args.get("ceiling_usd", 50.0))

    try:
        tier = BudgetTier(tier_str)
    except ValueError:
        return {"error": f"Unknown tier: {tier_str}. Valid: {[t.value for t in BudgetTier]}"}

    ceiling = BudgetCeiling(tier=tier, studio=studio, ceiling_usd=ceiling_usd)
    try:
        result = enforce_budget(tier=tier, studio=studio, cost_so_far=cost_so_far, new_cost=new_cost, ceiling=ceiling)
        return result
    except BudgetExceeded as exc:
        return {"action": "halt", "error": str(exc)}


TOOLS: dict[str, dict[str, Any]] = {
    "rusr/smoke": {
        "description": "Local smoke check — deterministic, no network, no secrets. Returns pass/fail.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
        "handler": _tool_smoke,
    },
    "rusr/check": {
        "description": "Full readiness check — returns current KPI scorecard for all dimensions.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
        "handler": _tool_check,
    },
    "rusr/audit_skill": {
        "description": "Audit a skill code snippet for hardcoded credentials and prompt injection patterns.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Skill source code to audit"},
                "skill_id": {"type": "string", "description": "Skill identifier"},
            },
            "required": ["code"],
        },
        "handler": _tool_audit_skill,
    },
    "rusr/verify_pair": {
        "description": "Verify that generator and verifier models are from different provider families.",
        "input_schema": {
            "type": "object",
            "properties": {
                "generator": {"type": "string", "description": "Generator model name"},
                "verifier": {"type": "string", "description": "Verifier model name"},
            },
            "required": ["generator", "verifier"],
        },
        "handler": _tool_verify_pair,
    },
    "rusr/validate_loop": {
        "description": "Validate a loop node dict. Must have max_iterations. Returns error if unbounded.",
        "input_schema": {
            "type": "object",
            "properties": {
                "node": {
                    "type": "object",
                    "description": "Loop node dict with keys: id, type, max_iterations, until_conditions",
                },
            },
            "required": ["node"],
        },
        "handler": _tool_validate_loop,
    },
    "rusr/enforce_budget": {
        "description": "Enforce budget ceiling for a studio run. Raises if cost would exceed ceiling.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tier": {"type": "string", "description": "Budget tier: per_step|per_run|per_studio_per_day|global_per_day"},
                "studio": {"type": "string", "description": "Studio name (optional)"},
                "cost_so_far": {"type": "number", "description": "Accumulated cost in USD"},
                "new_cost": {"type": "number", "description": "New cost to add in USD"},
                "ceiling_usd": {"type": "number", "description": "Budget ceiling in USD"},
            },
            "required": ["cost_so_far", "new_cost"],
        },
        "handler": _tool_enforce_budget,
    },
}


# ── Resource definitions ──────────────────────────────────────────────────────
# Resources are read-only data surfaces exposed to agent clients.

RESOURCES: dict[str, dict[str, Any]] = {
    "rusr://registry": {
        "description": "Tool registry — registered tools with capabilities and cost limits.",
        "mime_type": "application/json",
        "handler": lambda: __import__("contracts.v1.tool_registry", fromlist=["REGISTRY"]).REGISTRY,
    },
    "rusr://skill-registry": {
        "description": "Skill registry YAML — audited skill definitions.",
        "mime_type": "application/yaml",
        "handler": lambda: (
            __import__("pathlib").Path(__file__).parent.parent / "skill_registry" / "registry.yaml"
        ).read_text(),
    },
    "rusr://kpi-scorecard": {
        "description": "Current KPI scorecard — agent, CLI, MCP, quality, proof readiness.",
        "mime_type": "application/json",
        "handler": lambda: __import__("rusr.cli", fromlist=["_kpi_scorecard"])._kpi_scorecard(),
    },
}


# ── Prompt definitions ────────────────────────────────────────────────────────
# Prompts are reusable agent instruction templates.

PROMPTS: dict[str, dict[str, Any]] = {
    "rusr/planner-system": {
        "description": "System prompt for the Planner agent role.",
        "template": (
            "You are the RUSR Planner. Your job is to break issues into deterministic steps "
            "and write PLAN.md files. You must never implement features not in the approved plan. "
            "Always run `rusr smoke` before making any changes. "
            "Never edit contracts/v1/ without explicit human approval. "
            "Never print or commit secrets, tokens, or private exports."
        ),
    },
    "rusr/reviewer-system": {
        "description": "System prompt for the Reviewer agent role (must be cross-family from Planner).",
        "template": (
            "You are the RUSR Reviewer. Your job is to verify planner output by running chaos drills "
            "and confirming quality gates pass. You MUST be a different model family from the Planner. "
            "Run `PYTHONPATH=. python -m pytest tests/ -q` to verify all tests pass. "
            "Never make code changes — only comment and verify."
        ),
    },
    "rusr/quality-gate-prompt": {
        "description": "Prompt for QA role to run quality gates and produce proof.",
        "template": (
            "Run the RUSR quality gates:\n"
            "1. `PYTHONPATH=. python -m pytest tests/ -q --tb=short` — all chaos drills must pass\n"
            "2. `rusr smoke` — deterministic smoke check must exit 0\n"
            "3. `rusr check` — review KPI scorecard\n"
            "4. Update proof/looper-v10-cockpit/ with sanitized output\n"
            "Do not skip or comment out failing tests. Report all blockers."
        ),
    },
}


def call_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Call a registered MCP tool by name."""
    if name not in TOOLS:
        return {"error": f"Unknown tool: {name}. Available: {list(TOOLS.keys())}"}
    return TOOLS[name]["handler"](args)


def get_resource(name: str) -> Any:
    """Get a registered MCP resource by name."""
    if name not in RESOURCES:
        return {"error": f"Unknown resource: {name}. Available: {list(RESOURCES.keys())}"}
    return RESOURCES[name]["handler"]()


def get_prompt(name: str) -> str:
    """Get a registered MCP prompt template by name."""
    if name not in PROMPTS:
        return f"Unknown prompt: {name}. Available: {list(PROMPTS.keys())}"
    return PROMPTS[name]["template"]
