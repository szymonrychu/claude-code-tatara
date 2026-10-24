"""The epic review in the docs: start-development phase 5, start-review --single, interrogate."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SD_SKILL = ROOT / "skills" / "start-development" / "SKILL.md"
REVIEW_SKILL = ROOT / "skills" / "start-review" / "SKILL.md"
INTERROGATE_SKILL = ROOT / "skills" / "interrogate" / "SKILL.md"
NON_NEGOTIABLES = SD_SKILL.parent / "references" / "non-negotiables.md"


def section(path: Path, heading: str) -> str:
    text = path.read_text()
    m = re.search(rf"^## {re.escape(heading)}\s*$", text, re.M)
    assert m, f"{path.name} has no section {heading!r}"
    rest = text[m.end() :]
    nxt = re.search(r"^## ", rest, re.M)
    return re.sub(r"\s+", " ", rest[: nxt.start()] if nxt else rest)


def test_phase_five_runs_interrogate_for_a_high_risk_diff():
    sec = section(SD_SKILL, "Phase 5 - Epic review")
    assert "workbench:interrogate" in sec and "high-risk" in sec


def test_phase_five_says_a_fail_verdict_goes_back_to_build():
    sec = section(SD_SKILL, "Phase 5 - Epic review")
    assert "--verdict fail" in sec
    assert "--verdict pass" in sec


def test_start_review_step_four_defaults_to_single():
    sec = section(REVIEW_SKILL, "4. The reviewer")
    assert "`--single`" in sec
    assert "default" in sec
    assert "one `reviewer`" in sec
    assert "the only path" in sec
    assert "workbench:interrogate" in sec
    for retired in ("spec-reviewer", "quality-reviewer"):
        assert retired not in sec, retired
    assert "spec and quality" in sec
    assert "`full` or `panel` tier" in sec
    assert "opus when any reviewed task ran on opus" not in REVIEW_SKILL.read_text()


def test_interrogate_when_to_use_names_panel_tier_and_epic_review():
    sec = section(INTERROGATE_SKILL, "When to use it")
    assert "`panel` tier" in sec
    assert "epic review" in sec


def test_scope_section_names_undelivered_as_a_finding():
    sec = section(NON_NEGOTIABLES, "Scope is not negotiable")
    for term in (
        "acceptance condition",
        "`undelivered`",
        "is a finding",
        "new task in the same epic",
    ):
        assert term in sec, term


def test_start_development_never_says_deferred():
    for p in (SD_SKILL, NON_NEGOTIABLES):
        assert "deferred" not in p.read_text().lower(), p.name


def test_discovered_becomes_a_task_in_the_same_epic():
    for p in (SD_SKILL, NON_NEGOTIABLES):
        text = " ".join(p.read_text().split())
        assert "new task in the same epic" in text, p.name
        assert "todo task" not in text
        assert "which become tasks" not in text


def test_skill_has_no_offer_or_parking_wording():
    text = SD_SKILL.read_text() + NON_NEGOTIABLES.read_text()
    for phrase in ("may be offered", "did not approve", "non-delivery", "sweeps the rest later"):
        assert phrase not in text, phrase


def test_start_review_never_names_opus():
    assert "opus" not in REVIEW_SKILL.read_text().lower()


NEW_AGENTS = (
    "implementer",
    "reviewer",
    "research-docs-purist",
    "research-practitioner",
    "research-prior-art-scout",
    "research-paper-scout",
    "research-reviewer",
    "planner",
)


def test_readme_agents_table_matches_files():
    """The README agents table lists exactly the core's agents/*.md, with their models.

    Renamed from test_readme_agents_table_lists_new_agents: that test only checked a
    subset (NEW_AGENTS) and let the table keep rows for agents that moved to the
    packs (helmfile-differ, tf-planner, k8s-triage) or lack rows for core agents
    (codebase-cartographer, worktree-merger, panel-reviewer).
    """
    readme = (ROOT / "README.md").read_text()
    sec = readme.split("\n## Agents", 1)[1].split("\n## ", 1)[0]
    sec = sec.split("\n### ", 1)[0]
    rows = dict(re.findall(r"^\| `([a-z-]+)` \| (\w+)", sec, re.M))
    files = {}
    for f in sorted((ROOT / "agents").glob("*.md")):
        m = re.search(r"^model: (\w+)", f.read_text(), re.M)
        # reviewers carry no model line: the caller sets it per call, the table says "per call"
        files[f.stem] = m.group(1) if m else "per"
    assert set(rows) == set(files), set(rows) ^ set(files)
    assert rows == files
    for name in NEW_AGENTS:
        assert name in rows, name


def test_readme_lists_ticket_tools():
    readme = (ROOT / "README.md").read_text()
    for cmd in (
        "tasks",
        "task",
        "amend",
        "questions",
        "roadmap",
        "close",
        "worktrees --refresh",
        "reap --epic",
    ):
        assert f"`ticket.py {cmd}" in readme, cmd
    for gone in ("rule", "args", "continue", "contract", "graph --todo", "facts", "decide"):
        assert f"`ticket.py {gone}" not in readme, gone
    for word in (
        ".claude/workbench.json",
        "refRunners",
        "suites",
        "deploy",
        "overlapIgnore",
        "skills/start-development/references/workbench-config.md",
        "user-run-step",
    ):
        assert word in readme, word


def test_no_circular_discussion_loop_reference():
    hosts = (ROOT / "skills" / "start-development" / "references" / "merge-hosts.md").read_text()
    loop = (ROOT / "skills" / "pullrequests-review-loop" / "SKILL.md").read_text()
    assert "discussion loop below" not in hosts
    flat = re.sub(r"\s+", " ", hosts)
    assert "reviews=" in flat and "GitLab review-discussion procedure" in flat
    assert "GitHub-only" in flat
    assert "per `merge-hosts.md`" not in loop
