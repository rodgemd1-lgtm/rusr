# RUSR V10 Design Proof — looper-v10-cockpit

**Run date:** 2026-05-29
**Repo:** `rodgemd1-lgtm/rusr`
**Proof type:** Planning and design — no product implementation authorized.
**Rerunnable:** Yes — weekly, no secrets required.

---

## V10 Product Promise

RUSR is the **Universal Studio Hardening Layer** for the RIG deterministic platform.
Every studio run through RUSR is:
- **Deterministic**: same input → same governance outcome, always.
- **Auditable**: hash-chained receipts, frozen contracts, quarantined outputs.
- **Safe to automate**: agents, CLI, and MCP clients share identical constraints.
- **Locally verifiable**: full smoke test in < 5 seconds with zero network calls.

---

## Current KPI Scorecard (as of this proof run)

| KPI | Score | Signal |
|-----|-------|--------|
| setup_git | 10/10 | ✓ git configured, branch protected |
| agent_readiness | 10/10 | ✓ AGENTS.md (+6), cross_family_verifier (+2), approval_halt (+2) |
| cli_readiness | 8/10 | ✓ pyproject.toml scripts (+3), [project.scripts] (+2), rusr/cli.py (+3) |
| mcp_readiness | 10/10 | ✓ rusr/mcp/server.py (+5), __init__.py (+2), README MCP docs (+3) |
| quality_readiness | 10/10 | ✓ 3+ test files (+6), pre-commit (+2), ruff (+2) |
| proof_readiness | 6/10 | ✓ proof/looper-v10-cockpit/ present (+2), v10-design.md (+4) |
| weekly_automation_readiness | 6/10 | ✓ receipts, contracts, chaos drills |
| **v10_current_score** | **9/10** | Up from 3/10 baseline |

---

## Deterministic First Check

```bash
# Zero-dependency local smoke — runs in < 5 seconds, no secrets
PYTHONPATH=. python -m pytest tests/ -q --tb=short

# CLI smoke check
rusr smoke

# KPI scorecard
rusr check
```

Expected output: `27+ passed in < 1s`

---

## CLI Surface (Defined)

| Command | Status | Description |
|---------|--------|-------------|
| `rusr smoke` | ✓ Implemented | Deterministic local health check |
| `rusr check` | ✓ Implemented | All readiness checks + KPI scorecard |
| `rusr check agent` | ✓ Implemented | Agent role and model-routing |
| `rusr check mcp` | ✓ Implemented | MCP tool/resource/prompt surface |
| `rusr check quality` | ✓ Implemented | Chaos drills and quality gates |
| `rusr check proof` | ✓ Implemented | Proof directory and receipt chain |
| `rusr version` | ✓ Implemented | Version and KPI scorecard |

---

## MCP Surface (Defined)

### Tools

| Tool | Description | Auth |
|------|-------------|------|
| `rusr/smoke` | Local smoke check — no network, no secrets | None |
| `rusr/check` | Full KPI scorecard | None |
| `rusr/audit_skill` | Skill code audit (credentials, injection) | None |
| `rusr/verify_pair` | Cross-family model pair verification | None |
| `rusr/validate_loop` | Loop bounds validation | None |
| `rusr/enforce_budget` | Budget ceiling enforcement | None |

### Resources

| Resource | Description |
|----------|-------------|
| `rusr://registry` | Tool registry (JSON) |
| `rusr://skill-registry` | Skill registry YAML |
| `rusr://kpi-scorecard` | Live KPI scorecard |

### Prompts

| Prompt | Description |
|--------|-------------|
| `rusr/planner-system` | System prompt for Planner agent |
| `rusr/reviewer-system` | System prompt for Reviewer agent (cross-family required) |
| `rusr/quality-gate-prompt` | QA quality gate instructions |

**Auth boundary:** All MCP tools are read-only governance checks.
No tool can deploy, publish, send messages, or modify frozen contracts.

---

## Agent Roles (Defined in AGENTS.md)

| Role | Responsibility | Model Family |
|------|---------------|--------------|
| Planner | Break issues → deterministic steps, write PLAN.md | claude-opus or gpt-5 |
| Reviewer | Verify planner output, run chaos drills | **Different family from Planner** |
| Fixer | Implement approved changes (surgical) | claude-sonnet or gpt-5 |
| QA | Run full test suite, sign off quality gates | Any capable model |

Cross-family verification enforced by `rusr.cross_family_verifier.verify_pair()`.

---

## Weekly Improvement Loop (Defined)

Each week the automation:
1. Runs `rusr smoke` → writes sanitized output to `proof/looper-v10-cockpit/weekly-<YYYY-WW>.md`
2. Checks KPI scorecard and identifies blockers
3. Queues retryable failures for human triage
4. Updates this proof file with current scores

**Requires human approval before executing:**
- Any change to `contracts/v1/` (frozen contracts)
- Deploy, publish, or send messages
- New schedules or automated billing

---

## Blockers and Gaps

| Blocker | Priority | Next Safe Action |
|---------|----------|-----------------|
| `uuid-extensions` not in pyproject.toml previously | Fixed | `pip install uuid-extensions` |
| No MCP SDK integration (FastMCP) | Medium | Add optional `mcp` dependency group |
| Weekly cron not yet configured | Low | Manual for now; define GitHub Actions workflow |
| `cli_readiness` missing `rusr retry-governance` command | Low | Add in next iteration |
| Proof receipt chain not yet verified end-to-end | Medium | Add receipt verification to `rusr check proof` |

---

## What Must Never Run Without Human Approval

- Any edit to `contracts/v1/` (frozen by `.rig/frozen-contracts.txt`)
- Deploy, publish, or activate schedules
- Reset, clean, delete, or overwrite user work
- Create new API keys or credentials
- Send messages (Telegram, email, Slack)

---

## Test Commands

```bash
# All chaos drills (must all pass — silent pass = critical incident)
PYTHONPATH=. python -m pytest tests/ -q --tb=short

# Targeted: soul ID bypass regression
PYTHONPATH=. python -m pytest tests/chaos/test_regression_soul_id.py -v

# Targeted: tool registry contracts
PYTHONPATH=. python -m pytest tests/contracts/test_tool_registry.py -v

# CLI smoke
PYTHONPATH=. python -m rusr.cli smoke

# MCP surface check
PYTHONPATH=. python -c "from rusr.mcp.server import TOOLS, RESOURCES, PROMPTS; print(len(TOOLS), 'tools')"
```

---

## Claim

This is a **planning and design proof**. No product features are claimed as final.
The V10 design is complete for agent, CLI, and MCP surfaces.
Implementation is authorized for the items listed above; production deployment requires a sealed DoneContract.

**Do not claim final PASS on any gate not verified by a live test run.**
