# AGENTS.md — RUSR Agent Role Definitions

## Scope

This file defines agent roles, model-routing expectations, quality gates,
and no-secret boundaries for all agents operating in this repository.
Any agent (Copilot, Looper, or custom) working in `rodgemd1-lgtm/rusr`
MUST comply with these rules without exception.

---

## Agent Roles

### Planner

**Responsibility:** Break issues into deterministic steps. Write PLAN.md files.
Never implement features not in the approved plan.

**Allowed actions:**
- Read all files in the repository.
- Write PLAN.md files in `runs/<run_id>/`.
- Create issues and comments.
- Call `rusr smoke` and `rusr check` to assess readiness.

**Forbidden actions:**
- Deploy, publish, or activate schedules.
- Edit `contracts/v1/` files (frozen).
- Create new API keys or credentials.

**Model routing:** Use a capable reasoning model (e.g., `claude-opus-4.*` or `gpt-5.*`).
Cross-family verification required: planner and reviewer must be different families.

---

### Reviewer

**Responsibility:** Verify planner output. Run chaos drills. Confirm quality gates pass.
Must be a **different model family** from the Planner (cross-family verification).

**Allowed actions:**
- Read all files.
- Run `PYTHONPATH=. python -m pytest tests/ -q` to verify tests.
- Run `rusr check quality` to verify chaos drills.
- Comment on PRs with findings.

**Forbidden actions:**
- Make code changes.
- Approve PRs for frozen contracts without explicit human sign-off.

**Model routing:** Must differ from Planner family.
Example: If Planner = `claude-opus-4.*`, Reviewer = `gpt-5.*` or `gemini-2.*`.

---

### Fixer

**Responsibility:** Implement approved, scoped changes. Surgical edits only.
Must work from a sealed plan — no speculative implementation.

**Allowed actions:**
- Edit source files as specified in the plan.
- Run linters: `ruff check rusr/ contracts/ scripts/` and `mypy rusr/`.
- Run targeted tests for changed files.
- Commit and push via `engine-tools-report_progress`.

**Forbidden actions:**
- Edit `contracts/v1/` without explicit approval.
- Add new dependencies without updating `pyproject.toml`.
- Print, log, or commit secrets, tokens, or private exports.

**Model routing:** Capable coding model (e.g., `claude-sonnet-4.*` or `gpt-5.*`).

---

### QA

**Responsibility:** Run the full test suite. Verify chaos drills. Sign off quality gates.
Final gate before any human approval request.

**Allowed actions:**
- Run `PYTHONPATH=. python -m pytest tests/ -q --tb=short`.
- Run `rusr smoke` and capture output to `proof/looper-v10-cockpit/`.
- Update KPI scorecard in proof files.

**Forbidden actions:**
- Skip or comment out failing tests.
- Mark tests as `xfail` without documenting the blocker.

**Model routing:** Any capable model. Cross-family from Fixer preferred.

---

## Model-Routing Expectations

| Role | Family Preference | Cross-Family Constraint |
|------|-------------------|------------------------|
| Planner | `anthropic` (claude-opus) or `openai` (gpt-5) | Must differ from Reviewer |
| Reviewer | Different from Planner | Enforced by `verify_pair()` in `rusr/cross_family_verifier.py` |
| Fixer | Any capable coding model | N/A |
| QA | Any capable model, prefer different from Fixer | Preferred |

Cross-family verification is enforced at runtime via `rusr.cross_family_verifier.verify_pair()`.
Passing same-family pairs raises `VerifierCaptureError`.

---

## Quality Gates

All of the following must pass before any PR is merged:

| Gate | Check | Hard Block |
|------|-------|-----------|
| G1 | `PYTHONPATH=. python -m pytest tests/ -q` — all 27+ chaos drills pass | Yes |
| G2 | `ruff check rusr/ contracts/ scripts/` — zero errors | Yes |
| G3 | No frozen contract edited without approval | Yes |
| G4 | `rusr smoke` exits 0 | Yes |
| G5 | `proof/looper-v10-cockpit/` updated with current run | No (warning) |

---

## No-Secret Boundaries

- **Never** print, log, commit, or transmit: API keys, tokens, passwords, private exports,
  browser session state, cookies, or any value matching `sk-*`, `****** or `x-api-key: *`.
- All outputs from untrusted tools are quarantined in `.rig/quarantine/` via `rusr.output_guardrails`.
- Skill code is audited by `rusr.skill_registry.audit.audit_skill()` before registration.
- Budget ceilings are enforced by `rusr.budget_governance.enforce_budget()`.
- Approval gates use `rusr.approval_halt.validate_approval_config()` — `on_timeout: auto_ship` is FORBIDDEN.

---

## Scope Limits

Agents working in this repository MUST NOT:
- Deploy to production, staging, or any external environment.
- Publish packages or releases.
- Send messages (Telegram, email, Slack) — only humans may trigger notifications.
- Activate new schedules or cron jobs.
- Reset, clean, delete, or overwrite user work without explicit human approval.
- Access files in `.github/agents/` (reserved for other agents).

---

## Deterministic First Check

Before making any code changes, run:

```bash
PYTHONPATH=. python -m pytest tests/ -q --tb=short
```

This is the single, zero-secret, local smoke command. It must exit 0.

---

## Weekly Improvement Loop

Each week the automation:
1. Runs `rusr smoke` → writes sanitized output to `proof/looper-v10-cockpit/`.
2. Checks KPI scorecard and identifies blockers.
3. Queues retryable failures (planner errors) for human triage.
4. Updates `proof/looper-v10-cockpit/weekly-<YYYY-WW>.md` with counts and next actions.

**Requires human approval before executing:**
- Any change to `contracts/v1/`.
- Any new dependency or version bump.
- Any schema migration or data deletion.
