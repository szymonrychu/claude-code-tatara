"""Structure tests for the design/record templates, the builder check and record-writer."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SD = ROOT / "skills" / "start-development"

DESIGN_H2 = [
    "Summary",
    "Intent and why",
    "Goals",
    "Non-goals",
    "Anti-goals",
    "Constraints",
    "Decisions",
    "Research",
    "Research inputs",
    "Decision coverage",
    "Review focus",
    "Left to the builder",
    "Assumptions and unknown facts",
    "Open questions",
    "Irreversible operations in scope",
]
RECORD_H2 = [
    "Asked",
    "Shipped",
    "Tasks",
    "Rulings",
    "Discovered and blocked",
    "Not pushed",
    "Lessons routed to",
]


def read(p):
    assert p.is_file(), f"missing {p}"
    return p.read_text()


def h2s(text):
    return re.findall(r"^## (.+?)\s*$", text, re.M)


def test_design_template():
    t = read(SD / "templates" / "design.md")
    assert t.splitlines()[0] == "# <Topic> design"
    assert h2s(t) == DESIGN_H2
    assert "(my call)" in t
    assert "### D<n>" in t
    assert "| Decision | Tasks |" in t
    for gone in ("approval ids", "ledger", "| Part | Owner", "Contracts", "owns", "uses"):
        assert gone not in t, gone
    assert (
        t.index("## Research\n")
        < t.index("## Research inputs")
        < t.index("## Decision coverage")
        < t.index("## Review focus")
        < t.index("## Left to the builder")
    )


def test_plan_template_is_gone():
    assert not (SD / "templates" / "plan.md").exists()


def test_record_template():
    t = read(SD / "templates" / "record.md")
    assert t.splitlines()[0] == "# <Topic> record"
    assert h2s(t) == RECORD_H2
    assert "Lessons routed to" in t


def test_builder_check():
    t = " ".join((SD / "SKILL.md").read_text().split())
    assert "builder check" in t
    assert "one general-purpose agent on sonnet" in t
    assert "Report only the questions you would still need answered before building" in t
    assert "(my call)" in t
    for ph in ("<epic-dir>", "README.md", "design.md", "tasks/"):
        assert ph in t, ph


def test_record_writer_agent():
    t = read(ROOT / "agents" / "record-writer.md")
    m = re.match(r"---\n(.*?)\n---\n(.*)", t, re.S)
    assert m
    fm, body = m.groups()
    assert re.search(r"^name: record-writer$", fm, re.M)
    assert re.search(r"^model: sonnet$", fm, re.M)
    tools = re.search(r"^tools: \[(.*)\]$", fm, re.M).group(1).split(", ")
    assert "Write" in tools and "Edit" not in tools
    assert "templates/record.md" in body and "ticket.py path" in body


def test_plain_ascii_punctuation():
    for p in [
        *(SD / "templates").glob("*.md"),
        SD / "SKILL.md",
        ROOT / "agents" / "record-writer.md",
    ]:
        assert not re.search(r"[\u2014\u2013\u2018\u2019\u201c\u201d\u2192]", read(p)), p


PLAN_INPUTS_POINTER = "${CLAUDE_PLUGIN_ROOT}/skills/start-development/SKILL.md"
POINTERS = [
    *(
        ROOT / "skills" / n / "SKILL.md"
        for n in (
            "research-docs",
            "research-code-external",
            "research-code-internal",
            "research-papers",
            "start-research",
            "start-discovery",
        )
    ),
    ROOT / "agents" / "reuse-hunter.md",
]


def test_plan_inputs_defined_once_in_phase_one():
    skill = (SD / "SKILL.md").read_text()
    phase1 = " ".join(skill[skill.index("## Phase 1") : skill.index("## Phase 2")].split())
    assert "## Plan inputs" in phase1
    for fmt in (
        "name - file:symbol - which plan items need it",
        "item - what provides it instead - source",
        "anti-pattern - where - the acceptance condition",
        "adopted / rejected, one line each",
    ):
        assert fmt in phase1, fmt
    assert "args.existing" not in skill and "args.doNotBuild" not in skill


def test_other_files_point_to_plan_inputs_instead_of_restating():
    for p in POINTERS:
        text = " ".join(read(p).split())
        assert PLAN_INPUTS_POINTER in text, p
        assert "references/plan-inputs.md" not in text, p
        assert "which plan items need it" not in text, p
        assert "what provides it instead" not in text, p


def test_task_template_has_no_retired_shared_parts_wording():
    text = (ROOT / "skills" / "start-development" / "templates" / "task.md").read_text()
    assert "shared parts" not in text
    assert "existing code to reuse" in text
