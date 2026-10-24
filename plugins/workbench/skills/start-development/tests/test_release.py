"""Release structure tests: plugin.json, README wording, the record documents.

The retirement assertions on personal project names are dropped: the template
carries no personal project names, so there is nothing left to retire.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MARKETPLACE = ROOT.parents[1] / ".claude-plugin" / "marketplace.json"
SD = ROOT / "skills" / "start-development"


def test_version_matches_changelog():
    """plugin.json == marketplace.json, and the newest CHANGELOG section matches."""
    meta = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert re.fullmatch(r"\d+\.\d+\.\d+", meta["version"])
    market = json.loads(MARKETPLACE.read_text())
    (entry,) = [e for e in market["plugins"] if e["name"] == meta["name"]]
    assert entry["version"] == meta["version"]
    changelog = ROOT / "CHANGELOG.md"
    if changelog.is_file():
        newest = re.search(r"^## v(\S+) - ", changelog.read_text(), re.M)
        assert newest and newest.group(1) == meta["version"]


def test_plugin_json_version_and_description():
    meta = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    desc = meta["description"]
    for word in (
        "one approval gate",
        "file-based epic tickets",
        "research skills",
        "epic-run",
        "review",
        "debugging",
        "verification hooks",
    ):
        assert word in desc, word
    for gone in ("seven-phase", "approval ledger", "tiered review", "verifier", "plan execution"):
        assert gone not in desc, gone


def test_manifests_do_not_mention_graphify():
    for path in (ROOT / ".claude-plugin" / "plugin.json", MARKETPLACE):
        text = path.read_text()
        assert "graphify" not in text.lower(), path.name


def test_marketplace_entry_has_no_stale_version():
    market = json.loads(MARKETPLACE.read_text())
    for entry in market["plugins"]:
        meta = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
        if entry["name"] == meta["name"]:
            assert entry["version"] == meta["version"]


def test_marketplace_description_matches_plugin_json():
    meta = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    market = json.loads(MARKETPLACE.read_text())
    (entry,) = [e for e in market["plugins"] if e["name"] == meta["name"]]
    assert entry["description"] == meta["description"]


def test_readme_wording():
    text = (ROOT / "README.md").read_text()
    assert "two approval gates" not in text
    assert "seven-phase" not in text
    for needle in (
        "research-code-internal",
        "research-code-external",
        "research-papers",
        "research-docs",
        "reuse-hunter",
        "record-writer",
        "## Documents",
        "doc_path.sh",
        "docs/research/",
    ):
        assert needle in text, needle
    assert re.search(r"docs/plans/<date>-<slug>-\{design,plan,tasks,record\}", text)


def test_readme_dispatch_phases_match_skill():
    """Every start-development row of the README dispatch table names an agent SKILL.md names."""
    readme = (ROOT / "README.md").read_text()
    skill = (SD / "SKILL.md").read_text()
    rows = re.findall(r"^\| `start-development` phase (\d) \| `(\S+)` \|", readme, re.M)
    assert rows
    packs = {f.stem for f in (ROOT.parent).glob("workbench-*/agents/*.md")}
    assert packs, "pack agents not found"
    for phase, agent in rows:
        assert agent not in packs, f"core README names pack agent {agent}"
        assert f"## Phase {phase} - " in skill, phase
        assert agent in skill, (agent, phase)
    for agent in ("planner", "implementer", "reviewer", "scope-auditor", "record-writer"):
        assert agent in {a for _, a in rows}, agent


def test_readme_names_the_new_flows():
    text = (ROOT / "README.md").read_text()
    for needle in (
        "start-review",
        "start-debugging",
        "verify-recorder.py",
        "## Verification",
        "supersedes engineering:debug",
    ):
        assert needle in text, needle


def test_readme_names_round_three():
    text = (ROOT / "README.md").read_text()
    for needle in (
        "concise-orchestrator",
        "/workbench:review",
        "/workbench:debug",
        "flake-hunt",
        "full output:",
        "references/hooks.md",
        "--only",
    ):
        assert needle in text, needle
    assert "intentionally forked" not in text


def test_readme_describes_the_lean_flow():
    text = (ROOT / "README.md").read_text()
    for needle in (
        "docs/plans/{todo,in-progress,done}/<epic>/",
        "tasks/<task>.md",
        "legacy dated files were removed",
        "skills/start-development/scripts/ticket.py",
        "integration worktree",
        "epic review before",
        "epic-run",
        "one implementer and one reviewer per task",
        "at most two fix rounds",
        "one scope audit per epic",
        "undelivered",
        "discovered",
        "verified head",
        "LSP and grep",
    ):
        assert needle in text, needle
    for gone in (
        "approvals.json",
        "approval ledger",
        "script+haiku verifier",
        "risk tier",
        "gate-only fix rounds",
        "time estimate",
        "heartbeat",
        "<epic>-<task>",
        "--<task>",
    ):
        assert gone not in text, gone
    assert "graphify" not in text.lower()
    assert "epic reached main" in text
    assert re.search(r"`scope-auditor` \| sonnet \|", text)


def test_readme_documents_the_template():
    """The README describes the template: skills, packs, hooks as shipped, nothing personal.

    New pins for the template README; the pins on dropped items (the migration section,
    the personal tree table, the private-infra commands) are replaced by these absences.
    """
    text = (ROOT / "README.md").read_text()
    for skill in sorted(
        p.name for p in (ROOT / "skills").iterdir() if p.is_dir() and not p.name.startswith("_")
    ):
        assert f"`{skill}`" in text or skill in text, skill
    for needle in (
        "workbench-infra",
        "workbench-observability",
        "workbench-secrets",
        "## Packs",
        "code/<component>",
        "<project>-<component>",
        "root marketplace",
        "trust dialog",
        "docs/research/",
    ):
        assert needle in text, needle
    assert "## Migration" not in text
    low = text.lower()
    for term in (
        "tat" + "ara",
        "spell" + "slinger",
        "szy" + "mon",
        "/us" + "ers/",
        "chart" + "-drift",
        "infra" + "-watch",
        "git-commit" + "-mr",
        "op-envs",
        "~/.claude/agents",
    ):
        assert term not in low, term
    meta = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    hooks = sorted(
        {
            Path(h["command"].split("/hooks/")[1].strip('"')).name
            for g in meta["hooks"].values()
            for e in g
            for h in e["hooks"]
        }
    )
    for hook in hooks:
        assert f"`{hook}`" in text, hook
