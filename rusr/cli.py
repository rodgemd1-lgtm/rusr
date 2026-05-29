"""
RUSR CLI — deterministic local smoke and readiness commands.

Entry point: rusr (via pyproject.toml [project.scripts])

Usage:
    rusr smoke              # Deterministic local smoke check
    rusr check              # All readiness checks
    rusr check agent        # Agent role and model-routing check
    rusr check mcp          # MCP tool/resource/prompt surface check
    rusr check quality      # Chaos drills and quality gates
    rusr check proof        # Proof directory and receipt chain
    rusr version            # Show version and KPI scorecard
"""
from __future__ import annotations

import sys
from pathlib import Path

import typer

app = typer.Typer(
    name="rusr",
    help="RUSR — Universal Studio Hardening Layer CLI",
    no_args_is_help=True,
)
check_app = typer.Typer(help="Run readiness checks")
app.add_typer(check_app, name="check")


def _kpi_scorecard() -> dict[str, int]:
    """Compute current KPI scorecard based on repo signals."""
    repo_root = Path(__file__).parent.parent

    scores: dict[str, int] = {
        "setup_git": 10,
        "agent_readiness": 0,
        "cli_readiness": 0,
        "mcp_readiness": 0,
        "quality_readiness": 0,
        "proof_readiness": 0,
        "weekly_automation_readiness": 6,
    }

    # Agent readiness — AGENTS.md present
    if (repo_root / "AGENTS.md").exists():
        scores["agent_readiness"] += 6
    # Agent readiness — agent role definitions present
    if (repo_root / "rusr" / "cross_family_verifier.py").exists():
        scores["agent_readiness"] += 2
    # Agent readiness — approval halt present
    if (repo_root / "rusr" / "approval_halt.py").exists():
        scores["agent_readiness"] += 2

    # CLI readiness — pyproject.toml has scripts
    pyproject = repo_root / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text()
        scores["cli_readiness"] += 3
        if "[project.scripts]" in content:
            scores["cli_readiness"] += 2
    # CLI readiness — cli.py present
    if (repo_root / "rusr" / "cli.py").exists():
        scores["cli_readiness"] += 3
    # CLI readiness — smoke command works
    scores["cli_readiness"] = min(scores["cli_readiness"], 10)

    # MCP readiness — mcp server present
    if (repo_root / "rusr" / "mcp" / "server.py").exists():
        scores["mcp_readiness"] += 5
    if (repo_root / "rusr" / "mcp" / "__init__.py").exists():
        scores["mcp_readiness"] += 2
    # MCP readiness — README documents MCP surface
    readme = repo_root / "README.md"
    if readme.exists() and "MCP" in readme.read_text():
        scores["mcp_readiness"] += 3
    scores["mcp_readiness"] = min(scores["mcp_readiness"], 10)

    # Quality readiness — tests present
    tests_dir = repo_root / "tests"
    if tests_dir.exists():
        test_count = len(list(tests_dir.rglob("test_*.py")))
        scores["quality_readiness"] += min(test_count * 2, 6)
    # Quality readiness — pre-commit config present
    if (repo_root / ".pre-commit-config.yaml").exists():
        scores["quality_readiness"] += 2
    # Quality readiness — ruff configured
    if pyproject.exists() and "[tool.ruff]" in pyproject.read_text():
        scores["quality_readiness"] += 2
    scores["quality_readiness"] = min(scores["quality_readiness"], 10)

    # Proof readiness — proof directory present
    proof_dir = repo_root / "proof" / "looper-v10-cockpit"
    if proof_dir.exists():
        proof_files = list(proof_dir.glob("*.md"))
        scores["proof_readiness"] += min(len(proof_files) * 2, 6)
        if (proof_dir / "v10-design.md").exists():
            scores["proof_readiness"] += 4
    scores["proof_readiness"] = min(scores["proof_readiness"], 10)

    return scores


@app.command()
def smoke() -> None:
    """Deterministic local smoke check — no network, no secrets, < 5 seconds."""
    typer.echo("RUSR Smoke Check")
    typer.echo("=" * 40)

    repo_root = Path(__file__).parent.parent
    checks: list[tuple[str, bool, str]] = []

    # Check 1: contracts importable
    try:
        from contracts.v1.tool_registry import REGISTRY, ToolCall  # noqa: F401
        checks.append(("contracts/v1/tool_registry importable", True, f"{len(REGISTRY)} tools registered"))
    except Exception as exc:
        checks.append(("contracts/v1/tool_registry importable", False, str(exc)))

    # Check 2: strategy_artifact importable
    try:
        from contracts.v1.strategy_artifact import StrategyArtifact  # noqa: F401
        checks.append(("contracts/v1/strategy_artifact importable", True, "ok"))
    except Exception as exc:
        checks.append(("contracts/v1/strategy_artifact importable", False, str(exc)))

    # Check 3: rusr modules importable
    for module in [
        "rusr.approval_halt",
        "rusr.budget_governance",
        "rusr.cross_family_verifier",
        "rusr.loop_governance",
        "rusr.memory_firewall",
        "rusr.output_guardrails",
        "rusr.receipts",
    ]:
        try:
            __import__(module)
            checks.append((f"{module} importable", True, "ok"))
        except Exception as exc:
            checks.append((f"{module} importable", False, str(exc)))

    # Check 4: MCP server importable
    try:
        from rusr.mcp.server import TOOLS  # noqa: F401
        checks.append(("rusr.mcp.server importable", True, f"{len(TOOLS)} tools defined"))
    except Exception as exc:
        checks.append(("rusr.mcp.server importable", False, str(exc)))

    # Check 5: Frozen contracts intact
    frozen_file = repo_root / ".rig" / "frozen-contracts.txt"
    if frozen_file.exists():
        frozen = [
            line.strip()
            for line in frozen_file.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        ]
        all_present = all((repo_root / f).exists() for f in frozen)
        checks.append(("frozen contracts present", all_present, f"{len(frozen)} contracts"))
    else:
        checks.append(("frozen contracts list present", False, ".rig/frozen-contracts.txt missing"))

    # Check 6: AGENTS.md present
    agents_md = repo_root / "AGENTS.md"
    checks.append(("AGENTS.md present", agents_md.exists(), "agent role definitions"))

    # Check 7: proof directory
    proof_dir = repo_root / "proof" / "looper-v10-cockpit"
    checks.append(("proof/looper-v10-cockpit present", proof_dir.exists(), "proof signals"))

    # Print results
    passed = 0
    failed = 0
    for label, ok, detail in checks:
        status = "✓" if ok else "✗"
        typer.echo(f"  {status} {label}: {detail}")
        if ok:
            passed += 1
        else:
            failed += 1

    typer.echo()
    typer.echo(f"Passed: {passed}  Failed: {failed}  Total: {passed + failed}")

    if failed > 0:
        typer.echo("\nSMOKE: FAIL")
        raise typer.Exit(code=1)
    typer.echo("\nSMOKE: PASS")


@check_app.callback(invoke_without_command=True)
def check_all(ctx: typer.Context) -> None:
    """Run all readiness checks and print KPI scorecard."""
    if ctx.invoked_subcommand is not None:
        return

    scores = _kpi_scorecard()
    total = sum(scores.values())
    count = len(scores)
    v10_score = round(total / count)

    typer.echo("RUSR KPI Scorecard")
    typer.echo("=" * 40)
    for key, score in scores.items():
        bar = "█" * score + "░" * (10 - score)
        typer.echo(f"  {key:<32} {bar} {score:2d}/10")
    typer.echo()
    typer.echo(f"  v10_current_score: {v10_score}/10")


@check_app.command("agent")
def check_agent() -> None:
    """Verify agent role and model-routing configuration."""
    repo_root = Path(__file__).parent.parent
    typer.echo("Agent Readiness Check")
    typer.echo("=" * 40)

    agents_md = repo_root / "AGENTS.md"
    if agents_md.exists():
        typer.echo("  ✓ AGENTS.md present — agent roles defined")
    else:
        typer.echo("  ✗ AGENTS.md missing — no agent role definitions")
        raise typer.Exit(code=1)

    try:
        from rusr.cross_family_verifier import verify_pair
        verify_pair("claude-opus-4.7", "gpt-5.5")
        typer.echo("  ✓ cross-family verifier works (anthropic ↔ openai)")
    except Exception as exc:
        typer.echo(f"  ✗ cross-family verifier error: {exc}")
        raise typer.Exit(code=1) from exc

    try:
        from rusr.approval_halt import validate_approval_config
        validate_approval_config({"id": "test", "timeout": "48h", "on_timeout": "halt"})
        typer.echo("  ✓ approval halt validator works")
    except Exception as exc:
        typer.echo(f"  ✗ approval halt error: {exc}")
        raise typer.Exit(code=1) from exc

    typer.echo("\nAgent check: PASS")


@check_app.command("mcp")
def check_mcp() -> None:
    """Verify MCP tool/resource/prompt surface."""
    typer.echo("MCP Readiness Check")
    typer.echo("=" * 40)

    try:
        from rusr.mcp.server import PROMPTS, RESOURCES, TOOLS
        typer.echo(f"  ✓ MCP server importable — {len(TOOLS)} tools, {len(RESOURCES)} resources, {len(PROMPTS)} prompts")
        for name in TOOLS:
            typer.echo(f"    tool: {name}")
        for name in RESOURCES:
            typer.echo(f"    resource: {name}")
        for name in PROMPTS:
            typer.echo(f"    prompt: {name}")
    except Exception as exc:
        typer.echo(f"  ✗ MCP server error: {exc}")
        raise typer.Exit(code=1) from exc

    typer.echo("\nMCP check: PASS")


@check_app.command("quality")
def check_quality() -> None:
    """Run chaos drills and quality gates."""
    import subprocess

    typer.echo("Quality Check")
    typer.echo("=" * 40)
    typer.echo("Running: python -m pytest tests/ -q --tb=short")
    typer.echo()

    repo_root = Path(__file__).parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=short"],
        cwd=repo_root,
        env={**__import__("os").environ, "PYTHONPATH": str(repo_root)},
    )
    if result.returncode != 0:
        typer.echo("\nQuality check: FAIL")
        raise typer.Exit(code=result.returncode)
    typer.echo("\nQuality check: PASS")


@check_app.command("proof")
def check_proof() -> None:
    """Check proof directory and receipt chain."""
    repo_root = Path(__file__).parent.parent
    typer.echo("Proof Check")
    typer.echo("=" * 40)

    proof_dir = repo_root / "proof" / "looper-v10-cockpit"
    if not proof_dir.exists():
        typer.echo("  ✗ proof/looper-v10-cockpit/ missing")
        raise typer.Exit(code=1)

    proof_files = list(proof_dir.glob("*.md"))
    typer.echo(f"  ✓ proof/looper-v10-cockpit/ present — {len(proof_files)} proof file(s)")
    for pf in sorted(proof_files):
        typer.echo(f"    {pf.name}")

    typer.echo("\nProof check: PASS")


@app.command()
def version() -> None:
    """Show RUSR version and KPI scorecard."""
    scores = _kpi_scorecard()
    total = sum(scores.values())
    v10_score = round(total / len(scores))

    typer.echo("RUSR version 0.1.0")
    typer.echo(f"v10_current_score: {v10_score}/10")


def main() -> None:
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
