"""start-development describes the plan flow: discovery, plan.md with a scope ladder, one gate,
an implementation plan for the agreed rung, then plan-run with one implementer and one reviewer.

The retired words below are named on purpose: this file pins their absence.
"""

import re
import subprocess
from pathlib import Path

SD = Path(__file__).resolve().parents[1]
ROOT = SD.parents[1]  # plugins/workbench
REPO = ROOT.parents[1]
SKILL = SD / "SKILL.md"
REFS = SD / "references"

LINK = re.compile(
    r"(?:\$\{CLAUDE_PLUGIN_ROOT\}/|plugins/[\w-]+/)?(?:references|templates)/[a-z-]+\.md"
)


def resolve(link):
    """A link named in SKILL.md: plugin-root, repo-relative (plugins/...) or skill-relative."""
    if link.startswith("${CLAUDE_PLUGIN_ROOT}/"):
        return ROOT / link.removeprefix("${CLAUDE_PLUGIN_ROOT}/")
    if link.startswith("plugins/"):
        return REPO / link
    return SD / link


KEPT = {"non-negotiables.md"}
DELETED_REFS = (
    "retro.md",
    "phase-4-execute.md",
    "phases-1-3.md",
    "phases-5-7.md",
    "run-handback.md",
    "approvals.md",
    "agents.md",
    "builder-check.md",
    "mode-flags.md",
    "multi-epic.md",
    "plan-inputs.md",
    "task-fields.md",
)
# retired vocabulary: absent from the skill and every reference
RETIRED_TERMS = (
    "task file",
    "builder check",
    "scope-auditor",
    "scope audit",
    "record-writer",
    "retro-writer",
    "record.md",
    "plan-execute",
    "heartbeat",
    "approvals.json",
    "verifier",
    "forward-merge",
    "apply-run",
    "epic-run",
    "workbench:planner",
)
FLOW_PINS = (
    # discovery feeds the plan-writer
    "start-discovery",
    "subagents",
    "plan-writer",
    "Plan inputs",
    # the scope ladder, from the MVP to the complete delivery
    "scope ladder",
    "MVP",
    "complete",
    # open questions with a recommended answer
    "recommended answer",
    "open questions",
    # one gate, batching plans
    "one gate",
    "a section and a worktree each",
    '"Pick a rung per plan and answer, or tell me what to change."',
    # the implementation plan: agreed rung only, no second gate
    "implementation-plan.md",
    "agreed rung only",
    "no second gate",
    # plan-run
    "plan-run",
    "one implementer",
    "sequential chunks",
    "one tree",
    "one reviewer",
    "whole diff",
    "under-delivery",
    "over-delivery",
    "at most two fix rounds",
    "SendMessage",
    "worktree-merger",
    "retro.md",
    "recommendations",
    "closing message",
)


def flat(text):
    return re.sub(r"\s+", " ", text)


def tracked(rel):
    out = subprocess.run(
        ["git", "ls-files", "--", rel], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    return [p for p in out.splitlines() if p]


def section(text, heading):
    m = re.search(rf"^## {re.escape(heading)}\s*$", text, re.M)
    assert m, f"SKILL.md has no section {heading!r}"
    rest = text[m.end() :]
    nxt = re.search(r"^## ", rest, re.M)
    return flat(rest[: nxt.start()] if nxt else rest)


def corpus():
    linked = {resolve(link) for link in LINK.findall(SKILL.read_text()) if "references/" in link}
    return flat(" ".join(p.read_text() for p in [SKILL, *sorted(linked)]))


def test_skill_is_lean():
    assert len(SKILL.read_text().splitlines()) <= 150
    names = {Path(p).name for p in tracked("plugins/workbench/skills/start-development/references")}
    assert names == KEPT, sorted(names ^ KEPT)
    for name in DELETED_REFS:
        if name in KEPT:
            continue
        assert not (REFS / name).exists(), f"references/{name} still exists"


def test_skill_phases_and_one_gate():
    text = SKILL.read_text()
    for n in range(1, 5):
        assert re.search(rf"^## Phase {n} - ", text, re.M), f"no Phase {n} heading"
    assert not re.search(r"^## Phase [05-9] - ", text, re.M)
    assert len(re.findall(r"^## The gate\s*$", text, re.M)) == 1
    assert text.index("## Phase 2 - ") < text.index("## The gate") < text.index("## Phase 3 - ")


def test_flow_pins_are_in_skill_or_references():
    body = corpus()
    missing = [p for p in FLOW_PINS if p.lower() not in body.lower()]
    assert not missing, missing


def test_gate_message_shape():
    gate = section(SKILL.read_text(), "The gate")
    for item in (
        "plan.md",
        "what and why",
        "rungs",
        "recommended rung",
        "numbered",
        "recommended answer",
        "lenses",
        "irreversible operation",
        "a section and a worktree each",
        '"Pick a rung per plan and answer, or tell me what to change."',
        "Everything after the gate runs unattended to merge",
    ):
        assert item in gate, f"the gate does not name {item!r}"


def test_phase_two_writes_the_plan():
    sec = section(SKILL.read_text(), "Phase 2 - Plan")
    for item in (
        "ticket.py check --title",
        "ticket.py new --title",
        "--repos",
        "workbench:plan-writer",
        "opus",
        "docs(plan): <plan> plan",
        "scope ladder",
        "(my call)",
        "workbench:interrogate",
    ):
        assert item in sec, f"Phase 2 does not name {item!r}"


def test_phase_three_writes_the_implementation_plan_for_the_agreed_rung():
    sec = section(SKILL.read_text(), "Phase 3 - Implementation plan")
    for item in (
        "same plan-writer",
        "SendMessage",
        "verbatim",
        "rung",
        "Agreed scope",
        "implementation-plan.md",
        "agreed rung only",
        "chunks",
        "no second gate",
    ):
        assert item in sec, f"Phase 3 does not name {item!r}"


def test_phase_four_hands_to_plan_run():
    sec = section(SKILL.read_text(), "Phase 4 - Run")
    for item in (
        "`plan-run`",
        "ticket.py move <plan> in-progress",
        "one `workbench:implementer`",
        "sequential",
        "workbench:reviewer",
        "whole diff",
        "at most two fix rounds",
        "worktree-merger",
        "ticket.py close",
        "retro.md",
        "never implement",
        "never merge",
    ):
        assert item in sec, f"Phase 4 does not name {item!r}"


def test_meta_and_component_modes_stay():
    text = flat(SKILL.read_text())
    assert "Component mode" in text and "Meta mode" in text
    assert "rebase plus fast-forward of the local main" in text
    assert "pushing main stays with the user" in text
    assert "references/merge-hosts.md" in text and "deploy-hook.py" in text
    assert "references/user-run-steps.md" in text


def test_every_named_reference_and_template_exists():
    text = SKILL.read_text()
    named = set(LINK.findall(text))
    assert named
    for rel in sorted(named):
        assert resolve(rel).is_file(), rel


def test_no_retired_terms_in_skill_or_references():
    body = corpus().lower()
    hits = [t for t in RETIRED_TERMS if t.lower() in body]
    assert not hits, hits
    assert not re.search(r"\bpoints\b|\bepics?\b", re.sub(r"\s+", " ", SKILL.read_text()), re.I)
    for p in sorted(REFS.glob("*.md")):
        if p.name == "tickets.md":
            continue
        assert not re.search(r"\bepics?\b|\bpoints\b", p.read_text(), re.I), p.name


def test_no_retired_words_outside_tests():
    retired = ("plan-execute", "heartbeat", "approvals.json", "apply-run", "forwardMerged")
    files = [p for p in SD.rglob("*") if p.is_file() and "tests" not in p.relative_to(SD).parts]
    files = [p for p in files if "__pycache__" not in p.parts]
    # ticket.py migrate reads the old epic files, so it is the one file that may name them
    files = [p for p in files if p != SD / "scripts" / "ticket_cmds" / "migrate.py"]
    hits = []
    for p in [*files, ROOT / "README.md", ROOT / ".claude-plugin" / "plugin.json"]:
        text = p.read_text(errors="ignore")
        hits += [f"{p.relative_to(ROOT)}: {w}" for w in retired if w in text]
    assert not hits, hits
