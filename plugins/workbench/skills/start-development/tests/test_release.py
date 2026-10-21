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
    assert "approval ledger" in meta["description"]
    assert "one approval gate" in meta["description"]
    assert "research skills" in meta["description"]
    for word in ("review", "debugging", "verification hooks"):
        assert word in meta["description"], word
    assert "seven-phase" not in meta["description"]
    for word in (
        "file-based epic tickets",
        "tiered review",
        "script+haiku verifier",
    ):
        assert word in meta["description"], word


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
    readme = (ROOT / "README.md").read_text()
    agents = (SD / "references" / "agents.md").read_text()
    table = re.findall(r"^\| `(\S+)` \| .*? \| (\d(?:, \d)*) \|$", agents, re.M)
    assert table
    # Agents shipped by an optional pack (plugins/workbench-*/agents) are documented in
    # that pack's README, not the core's; agents.md still lists their phase triggers.
    # Removed phase-row assertions (3 total, all moved to packs): tf-planner (phase 5),
    # helmfile-differ (phase 5), k8s-triage (phase 6). They are replaced by the absence
    # assertion below, and the skip set is pinned so no other agent can silently drop out.
    packs = {f.stem for f in (ROOT.parent).glob("workbench-*/agents/*.md")}
    assert packs, "pack agents not found"
    assert {a for a, _ in table} & packs == {"tf-planner", "helmfile-differ", "k8s-triage"}
    for agent, phases in table:
        if agent in packs:
            assert not re.search(rf"`{agent}`", readme), f"core README names pack agent {agent}"
            continue
        for ph in phases.split(", "):
            assert re.search(rf"`start-development` phase {ph}\W.*`{agent}`", readme), (agent, ph)


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
        "verifier",
        "heartbeat",
        "concise-orchestrator",
        "/workbench:review",
        "/workbench:debug",
        "approval ledger",
        "flake-hunt",
        "full output:",
        "references/hooks.md",
        "--only",
    ):
        assert needle in text, needle
    assert "intentionally forked" not in text


def test_readme_describes_1_0_0():
    text = (ROOT / "README.md").read_text()
    for needle in (
        "docs/plans/{todo,in-progress,done}/<epic>/",
        "tasks/<task>.md",
        "approvals.json",
        "legacy dated files were removed",
        "ticket.py",
        "<epic>-<task>",
        "integration worktree",
        "epic review before",
        "claude -p",
        "scripts/lib/claude_json.py",
        "scripts/triage.py",
        "scripts/verify-task.py",
        "skills/start-development/scripts/ticket.py",
        "risk tier",
        "script+haiku verifier",
        "gate-only fix rounds",
        "undelivered",
        "discovered",
        "AC evidence",
        "epic-close audit",
        "time estimate",
        "LSP and grep",
    ):
        assert needle in text, needle
    assert "graphify" not in text.lower()
    assert re.search(r"`verifier` \| haiku \|.*scripts/verify-task\.py", text)
    assert re.search(r"`scope-auditor` \| sonnet \|.*agent type", text)


def test_readme_names_epic_task_trees_and_integration():
    text = (ROOT / "README.md").read_text()
    assert "<epic>-<task>" in text
    assert "integration worktree" in text
    assert "--<task>" not in text
    assert "reaches main" in text


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
