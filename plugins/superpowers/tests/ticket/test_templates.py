"""Structure tests for the plan, implementation-plan and retro templates."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "workbench"
SD = ROOT / "skills" / "start-development"
TEMPLATES = ROOT.parent / "superpowers" / "templates"

PLAN_KEYS = ["title", "repos", "created", "owner", "rung"]
PLAN_H2 = [
    "What and why",
    "Scope ladder",
    "Agreed scope",
    "Non-goals",
    "Design",
    "Decisions",
    "Open questions",
    "Research",
    "Irreversible operations",
]
IMPL_H2 = [
    "Agreed rung",
    "Approach",
    "Chunk <k>: <name> (model: <sonnet|opus>)",
    "Files to delete",
    "Final verify",
    "After merge",
]
STEP_FIELDS = ["Files", "Covers", "Test first", "Change", "Verify"]
RETRO_H2 = ["Review", "What went well", "What went wrong or could improve", "Recommendations"]
NEW_TEMPLATES = ("plan.md", "implementation-plan.md", "retro.md")
# em and en dash, smart quotes, right arrow
FANCY = "[" + "".join(map(chr, (0x2014, 0x2013, 0x2018, 0x2019, 0x201C, 0x201D, 0x2192))) + "]"


def read(p):
    assert p.is_file(), f"missing {p}"
    return p.read_text()


def h1s(text):
    return re.findall(r"^# (.+?)\s*$", text, re.M)


def h2s(text):
    return re.findall(r"^## (.+?)\s*$", text, re.M)


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    assert m, "no frontmatter"
    return m.group(1), m.group(2)


def section(text, name):
    m = re.search(rf"^## {re.escape(name)}\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert m, name
    return m.group(1)


def test_plan_template():
    fm, body = frontmatter(read(TEMPLATES / "plan.md"))
    assert re.findall(r"^([a-z]+):", fm, re.M) == PLAN_KEYS
    assert h1s(body) == ["<title>"]
    assert h2s(body) == PLAN_H2
    ladder = section(body, "Scope ladder")
    assert "### Rung <n>: <MVP|...|complete> - <name>" in ladder
    assert "- <n>.<m>: <item>" in ladder
    questions = section(body, "Open questions")
    assert "- Q<n>: <question> [recommended: <answer>]" in questions
    assert "[answer: <text>]" in questions


def test_implementation_plan_template():
    text = read(TEMPLATES / "implementation-plan.md")
    assert not text.startswith("---")
    assert h1s(text) == ["<title> implementation plan"]
    assert h2s(text) == IMPL_H2
    chunk = section(text, "Chunk <k>: <name> (model: <sonnet|opus>)")
    assert "### S<n>: <title>" in chunk
    assert re.findall(r"^- ([A-Z][a-z ]+?):", chunk, re.M) == STEP_FIELDS


def test_retro_template():
    text = read(TEMPLATES / "retro.md")
    assert h1s(text) == ["<title> retro"]
    assert h2s(text) == RETRO_H2
    assert "retro:generated" not in text
    recs = section(text, "Recommendations").lower()
    for name in ("discovered and not built", "out-of-scope ideas", "impossible at planning time"):
        assert name in recs, name
    assert "none" in recs


def test_every_section_carries_an_instruction():
    for name in NEW_TEMPLATES:
        parts = re.split(r"^## .+$", read(TEMPLATES / name), flags=re.M)[1:]
        assert parts and all(p.strip() for p in parts), name


def test_templates_have_no_parking_words_or_estimates():
    for name in NEW_TEMPLATES:
        text = read(TEMPLATES / name).lower()
        for word in ("deferred", "later", "wontfix", "follow-up", "points", "estimate", "epic"):
            assert word not in text, (name, word)


def test_plain_ascii_punctuation():
    for p in [*(TEMPLATES / n for n in NEW_TEMPLATES), SD / "SKILL.md"]:
        assert not re.search(FANCY, read(p)), p


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
        "anti-pattern - where - the step's Verify or Test first that pins the fix",
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
