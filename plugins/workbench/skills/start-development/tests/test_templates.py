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
RETRO_H2 = ["Tasks", "Deltas", "Retro", "Improvements"]


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


def test_retro_template():
    t = read(SD / "templates" / "retro.md")
    assert t.isascii()
    assert t.splitlines()[0] == "# <Topic> retro"
    assert h2s(t) == RETRO_H2
    begin, end = "<!-- retro:generated:begin -->", "<!-- retro:generated:end -->"
    assert t.count(begin) == 1 and t.count(end) == 1
    assert t.index(begin) < t.index("## Tasks") < t.index("## Deltas") < t.index(end)
    assert t.index(end) < t.index("## Retro") < t.index("## Improvements")
    for phrase in ("Went well", "Went bad / could be improved", "tech debt", "workflow"):
        assert phrase.lower() in t.lower(), phrase


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


def test_retro_writer_agent():
    t = read(ROOT / "agents" / "retro-writer.md")
    assert t.isascii()
    m = re.match(r"---\n(.*?)\n---\n(.*)", t, re.S)
    assert m
    fm, body = m.groups()
    assert re.search(r"^name: retro-writer$", fm, re.M)
    assert re.search(r"^model: sonnet$", fm, re.M)
    assert re.search(r"^description: ", fm, re.M)
    tools = re.search(r"^tools: \[(.*)\]$", fm, re.M).group(1).split(", ")
    assert "Edit" in tools and "Write" not in tools
    flat = " ".join(body.split())
    for needle in (
        "## Inputs you are given",
        "The epic slug",
        "orchestrator's notes",
        "review rounds",
        "verification tail",
        "ticket.py retro --history",
        "ticket.py path <epic> retro",
        "the only file you write",
        "<!-- retro:generated:begin -->",
        "<!-- retro:generated:end -->",
        "never edit the generated block",
        "| Went well | Went bad / could be improved |",
        "potential improvements in the code",
        "delivered differently",
        "tech debt",
        "workflow",
        "recur",
        "100 words",
    ):
        assert needle in flat, needle


def test_retro_reference():
    t = read(SD / "references" / "retro.md")
    assert t.isascii()
    flat = " ".join(t.split())
    for needle in (
        "ticket.py move <epic> done",
        "ticket.py retro <epic>",
        "retro-writer",
        "record-writer",
        "ticket.py retro --history",
        "workflow",
        "planner",
        "Research inputs",
        "Bootstrap",
    ):
        assert needle in flat, needle


def test_plain_ascii_punctuation():
    for p in [
        *(SD / "templates").glob("*.md"),
        SD / "SKILL.md",
        ROOT / "agents" / "record-writer.md",
        ROOT / "agents" / "retro-writer.md",
        SD / "references" / "retro.md",
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
