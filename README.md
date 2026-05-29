# RUSR — Universal Studio Hardening Layer

RUSR is a product-grade agent, CLI, and MCP-ready hardening layer for the RIG deterministic platform.
It enforces governance, quality gates, and approval workflows across all RIG studios.

## V10 Product Promise

Every studio run through RUSR is deterministic, auditable, and safe to automate.
Agents, CLI users, and MCP clients share the same governed surface with identical constraints.

## Quick Start

```bash
# Install
pip install -e ".[dev,test]"

# Smoke check — deterministic local health check (no secrets, no network)
rusr smoke

# Check agent readiness
rusr check agent

# Check MCP readiness
rusr check mcp

# Run quality gates
rusr check quality
```

## CLI Surface

| Command | Description |
|---------|-------------|
| `rusr smoke` | Deterministic local smoke check — no network, no secrets |
| `rusr check` | Run all readiness checks (agent, CLI, MCP, quality, proof) |
| `rusr check agent` | Verify agent role and model-routing configuration |
| `rusr check mcp` | Verify MCP tool/resource/prompt surface |
| `rusr check quality` | Run chaos drills and quality gates |
| `rusr check proof` | Check proof directory and receipt chain |
| `rusr version` | Show RUSR version and KPI scorecard |

## MCP Surface

RUSR exposes the following MCP tools for agent clients:

| Tool | Description |
|------|-------------|
| `rusr/smoke` | Local smoke check — returns pass/fail with counts |
| `rusr/check` | Full readiness check — returns KPI scorecard |
| `rusr/audit_skill` | Audit a skill code snippet for credentials and injection |
| `rusr/verify_pair` | Verify cross-family generator-verifier pair |
| `rusr/validate_loop` | Validate a loop node for bounds |
| `rusr/enforce_budget` | Enforce budget ceiling for a studio run |

## Agent Roles

See [AGENTS.md](AGENTS.md) for agent role definitions, model routing, and quality gates.

## Architecture

```
rusr/
  cli.py              # Typer CLI entry point
  mcp/
    server.py         # MCP server (FastMCP-style tool definitions)
  approval_halt.py    # Layer 11: Approval gate — no auto-ship
  budget_governance.py# Layer 9: Budget ceilings
  cross_family_verifier.py # Layer 6: Cross-family model pairs
  loop_governance.py  # Layer 10: Bounded loops
  memory_firewall.py  # Layer 8: Namespace isolation
  output_guardrails.py# Layer 7: Trust levels and quarantine
  receipts.py         # Layers 14+17: Run receipts with hash chain
  retry_governance.py # Retry with backoff governance
  skill_registry/
    audit.py          # Skill auditing (credentials, injection)
    registry.yaml     # Registered skills

contracts/v1/         # Frozen Pydantic v2 contracts
  tool_registry.py    # Layer 1: Tool registry (soul_id enforcement)
  strategy_artifact.py# Strategy studio artifact contract

proof/
  looper-v10-cockpit/ # Sanitized V10 design proof (rerunnable weekly)

tests/
  chaos/              # 13 chaos drills — all must fail loudly
  contracts/          # Contract validation tests
```

## Deterministic First Check

```bash
# Zero-dependency local smoke — runs in < 5 seconds
PYTHONPATH=. python -m pytest tests/ -q --tb=short
```

## Weekly Improvement Loop

The weekly automation:
1. Runs `rusr smoke` — deterministic, no secrets
2. Checks runtime health across all KPIs
3. Updates `proof/looper-v10-cockpit/` with latest scores and blockers
4. Requires **human approval** before any schema change, deployment, or publish

**Must never run without human approval:**
- Any change to `contracts/v1/` (frozen contracts)
- Deploy, publish, or send messages
- Reset, clean, delete, or overwrite user work
- New schedules or automated billing actions

## Boundaries

- Do not print secrets, tokens, private exports, or browser session state.
- Do not deploy, publish, send messages, or activate new schedules from automation.
- Do not reset, clean, delete, or overwrite user work.
- Prefer deterministic scripts and local proof before agentic workflows.
