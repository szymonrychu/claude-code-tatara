"""The epic review in the docs: start-development phase 5, start-review --single, interrogate."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SD_SKILL = ROOT / "skills" / "start-development" / "SKILL.md"
REVIEW_SKILL = ROOT / "skills" / "start-review" / "SKILL.md"
INTERROGATE_SKILL = ROOT / "skills" / "interrogate" / "SKILL.md"


_MOVED = ("phases-1-3.md", "phase-4-execute.md", "phases-5-7.md", "non-negotiables.md")


def sd_text(skill):
    """SKILL.md plus the reference files its blocks moved to. References come first, so a section
    heading resolves to its full text rather than to the pointer left in SKILL.md."""
    refs = skill.parent / "references"
    return "\n".join([*((refs / n).read_text() for n in _MOVED), skill.read_text()])


PHASE5_ORDER = [
    "ticket.py stage <epic> review",
    "start-review --single",
    "auditOnly: true",
    "args.epicReadme",
    "suite-lock.sh",
    "stage build",
    "ticket.py review <epic> --verdict",
    "ticket.py move <epic> done",
]


def section(path: Path, heading: str) -> str:
    text = sd_text(path) if path == SD_SKILL else path.read_text()
    m = re.search(rf"^## {re.escape(heading)}\s*$", text, re.M)
    assert m, f"{path.name} has no section {heading!r}"
    rest = text[m.end() :]
    nxt = re.search(r"^## ", rest, re.M)
    return re.sub(r"\s+", " ", rest[: nxt.start()] if nxt else rest)


def test_phase_five_runs_the_epic_review_in_order():
    sec = section(SD_SKILL, "Phase 5 - Verify")
    at = -1
    for s in PHASE5_ORDER:
        i = sec.find(s, at + 1)
        assert i != -1, f"Phase 5 lacks {s!r} after position {at}"
        at = i


def test_phase_five_runs_interrogate_for_panel_tier_tasks():
    sec = section(SD_SKILL, "Phase 5 - Verify")
    assert re.search(r"interrogate[^.]*`panel`[^.]*tier|`panel`[^.]*tier[^.]*interrogate", sec), sec


def test_phase_five_says_a_fail_verdict_goes_back_to_build():
    sec = section(SD_SKILL, "Phase 5 - Verify")
    assert "--verdict fail" in sec
    assert "--verdict pass" in sec


def test_start_review_step_four_defaults_to_single():
    sec = section(REVIEW_SKILL, "4. Two reviewers")
    assert "`--single`" in sec
    assert "default" in sec
    assert "one `reviewer`" in sec
    assert "`spec-reviewer`" in sec
    assert "`quality-reviewer`" in sec
    assert "spec and quality" in sec
    assert "`full` or `panel` tier" in sec
    assert "opus when any reviewed task ran on opus" not in REVIEW_SKILL.read_text()


def test_interrogate_when_to_use_names_panel_tier_and_epic_review():
    sec = section(INTERROGATE_SKILL, "When to use it")
    assert "`panel` tier" in sec
    assert "epic review" in sec


def test_phase_four_names_the_cost_mechanics():
    sec = section(SD_SKILL, "Phase 4 - Execute")
    for term in (
        "verify-task.py",
        "haiku",
        "acceptance condition",
        "skip",
        "light",
        "full",
        "panel",
        "gate-repeat",
        "processOnly",
        "undelivered",
        "discovered",
        "diffRead",
    ):
        assert term in sec, f"Phase 4 does not name {term!r}"


def test_verifier_table_row_names_haiku():
    lines = (SD_SKILL.parent / "references" / "agents.md").read_text().splitlines()
    row = next(line for line in lines if line.startswith("| `verifier`"))
    assert "haiku" in row


def test_scope_section_names_the_ledger_strike():
    sec = section(SD_SKILL, "Scope is not negotiable")
    for term in ("acceptance condition", "undelivered", "strikes the ledger item"):
        assert term in sec, term


def test_start_development_never_says_deferred():
    assert "deferred" not in sd_text(SD_SKILL).lower()


AGENTS_REF = SD_SKILL.parent / "references" / "agents.md"


def test_skill_keeps_headroom_under_the_cap():
    assert len(SD_SKILL.read_text().splitlines()) <= 470


def test_agents_reference_lists_every_dispatched_agent_type():
    js = (ROOT / "workflows" / "plan-execute.js").read_text()
    dispatched = set(re.findall(r"'workbench:([a-z-]+)'", js))
    assert {"verifier", "scope-auditor"} <= dispatched
    ref = AGENTS_REF.read_text()
    for agent in dispatched:
        assert f"| `{agent}` |" in ref, f"references/agents.md has no row for {agent}"
    assert "references/agents.md" in SD_SKILL.read_text()


def test_start_review_never_names_opus():
    assert "opus" not in REVIEW_SKILL.read_text().lower()


def test_discovered_wording_matches_phase_four_and_scope():
    text = " ".join(sd_text(SD_SKILL).split())
    assert "is a new epic task" not in text
    assert text.count("added as a new epic task") >= 2


def test_skill_uses_new_epic_task_wording_without_parking_words():
    from pathlib import Path

    text = sd_text(Path(__file__).resolve().parents[1] / "SKILL.md")
    flat_text = " ".join(text.split())
    assert flat_text.count("a new epic task") >= 2
    assert "todo task" not in flat_text
    assert "which become tasks" not in flat_text


def test_skill_has_no_offer_or_parking_wording():
    from pathlib import Path

    text = sd_text(Path(__file__).resolve().parents[1] / "SKILL.md")
    for phrase in ("may be offered", "did not approve", "non-delivery", "sweeps the rest later"):
        assert phrase not in text, phrase


def test_phase3_planner_told_to_write_estimate():
    text = " ".join(sd_text(SD_SKILL).split())
    assert "--estimate" in text
    assert "about an hour" in text


def test_start_development_line_cap():
    assert len(SD_SKILL.read_text().splitlines()) <= 470


NEW_AGENTS = (
    "implementer",
    "reviewer",
    "spec-reviewer",
    "quality-reviewer",
    "research-docs-purist",
    "research-practitioner",
    "research-prior-art-scout",
    "research-paper-scout",
    "research-reviewer",
    "planner",
)


def test_every_plan_execute_agent_has_a_row():
    agents = (ROOT / "skills" / "start-development" / "references" / "agents.md").read_text()
    assert "Read-only" not in agents.split("\n", 1)[0]
    for name in NEW_AGENTS:
        assert re.search(rf"^\| `{name}` \| .* \| \d(?:, \d)* \|$", agents, re.M), name
    js = (ROOT / "workflows" / "plan-execute.js").read_text()
    for name in set(re.findall(r"workbench:([a-z-]+)", js)):
        assert f"| `{name}` |" in agents, name


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


def test_readme_lists_remarks_tools():
    readme = (ROOT / "README.md").read_text()
    for cmd in (
        "rule",
        "args",
        "continue",
        "contract",
        "graph --todo",
        "roadmap",
        "facts",
        "decide",
        "questions",
        "amend",
        "worktrees --refresh",
        "reap --epic",
    ):
        assert f"`ticket.py {cmd}" in readme, cmd
    for word in (
        ".claude/workbench.json",
        "refRunners",
        "suites",
        "deploy",
        "overlapIgnore",
        "skills/start-development/references/workbench-config.md",
        "heartbeat.py --run <id>",
        "user-run-step",
    ):
        assert word in readme, word


def test_skill_names_reap_epic_and_fits():
    text = sd_text(SD_SKILL)
    assert "`ticket.py reap --epic <epic>`" in text
    assert len(SD_SKILL.read_text().splitlines()) <= 470


def test_no_circular_discussion_loop_reference():
    hosts = (ROOT / "skills" / "start-development" / "references" / "merge-hosts.md").read_text()
    loop = (ROOT / "skills" / "pullrequests-review-loop" / "SKILL.md").read_text()
    assert "discussion loop below" not in hosts
    flat = re.sub(r"\s+", " ", hosts)
    assert "reviews=" in flat and "GitLab review-discussion procedure" in flat
    assert "GitHub-only" in flat
    assert "per `merge-hosts.md`" not in loop


def test_readme_reap_task_needs_epic():
    readme = (ROOT / "README.md").read_text()
    assert "`ticket.py reap --epic <epic> --task <task-id>`" in readme
    assert "reap --task <epic>--<task>" not in readme
