"""start-review: the review skill and its single review checklist."""

import re
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[1]
ROOT = SKILL_DIR.parents[1]
SKILL = SKILL_DIR / "SKILL.md"
CHECKLIST = SKILL_DIR / "references" / "review-checklist.md"
PANEL = ROOT / "agents" / "panel-reviewer.md"
REVIEWERS = ("reviewer",)
RETIRED = ("spec-reviewer", "quality-reviewer", "plan-execute")
PERSONA = ROOT / "agents" / "research-reviewer.md"

CHECKLIST_H2 = [
    "Tests first",
    "Claims are not evidence",
    "Spec axis",
    "Quality axis",
    "Every finding",
    "Severity",
    "What you did not judge",
    "Bookkeeping",
]
CHECKLIST_PHRASES = [
    "would it fail if the behaviour were removed",
    "independent source",
    "asserts nothing",
    "list of claims",
    "Parking wording",
    "missing",
    "extra",
    "wrong",
    "quote the requirement line",
    "contract defined in two places",
    "evidence",
    "critical",
    "high",
    "medium",
    "cannot be trusted until fixed",
    "not certain",
    "declined",
    "cannotVerify",
    "processGaps",
]
SKILL_H2 = [
    "When to use it",
    "1. Pin the scope",
    "2. Intent",
    "3. Independent verification",
    "4. Two reviewers",
    "5. Validate findings",
    "6. Verdict",
    "After the verdict",
    "Rules",
]
SKILL_PHRASES = [
    "git rev-parse",
    "git diff --stat",
    "stop",
    "suite-lock.sh",
    "`reviewer`",
    "references/review-checklist.md",
    "400 words",
    "Act on",
    "Consider",
    "Noted",
    "Dismissed",
    "Declined",
    "Cannot verify",
    "workbench:interrogate",
    "never applied by the reviewer",
    "sonnet",
]


def h2s(text):
    return re.findall(r"^## (.+)$", text, re.M)


def sections(text):
    parts = re.split(r"^## ", text, flags=re.M)[1:]
    return {p.split("\n", 1)[0]: p for p in parts}


def frontmatter(path):
    text = path.read_text()
    assert text.startswith("---\n")
    end = text.index("\n---", 4)
    fm = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip().strip('"')
    return fm


def test_checklist_h1_and_section_order():
    text = CHECKLIST.read_text()
    assert text.startswith("# Review checklist\n")
    assert h2s(text) == CHECKLIST_H2


def test_checklist_preamble_names_the_three_readers():
    pre = CHECKLIST.read_text().split("\n## ", 1)[0]
    for reader in ("panel-reviewer", "start-review", *REVIEWERS):
        assert reader in pre
    text = CHECKLIST.read_text()
    for gone in RETIRED:
        assert gone not in text, gone


def test_checklist_required_phrases():
    text = CHECKLIST.read_text()
    for phrase in CHECKLIST_PHRASES:
        assert phrase in text, f"checklist missing {phrase!r}"


def test_checklist_bullets_are_single_short_ascii_lines():
    text = CHECKLIST.read_text()
    bullets = [ln for ln in text.splitlines() if ln.startswith("- ")]
    assert len(bullets) >= 20
    for ln in bullets:
        assert len(ln) < 200, ln
        assert ln.isascii(), ln
        assert ln == ln.rstrip(), f"trailing space: {ln!r}"
    assert not [ln for ln in text.splitlines() if re.match(r"\s+[-*] ", ln)]
    sec = sections(text)
    for name in CHECKLIST_H2:
        assert any(ln.startswith("- ") for ln in sec[name].splitlines()), name


def test_skill_frontmatter():
    fm = frontmatter(SKILL)
    assert fm["name"] == "start-review"
    desc = fm["description"]
    assert 0 < len(desc) < 1536
    assert desc.lower().startswith("review a branch, diff, mr or pr")


def test_skill_section_order_and_done_when():
    text = SKILL.read_text()
    assert h2s(text) == SKILL_H2
    sec = sections(text)
    for name in SKILL_H2:
        if name[0].isdigit():
            assert re.search(r"^Done when:", sec[name], re.M), name


def test_skill_required_phrases():
    text = SKILL.read_text()
    for phrase in SKILL_PHRASES:
        assert phrase in text, f"SKILL.md missing {phrase!r}"


def test_skill_is_short():
    assert len(SKILL.read_text().splitlines()) < 200


def test_referenced_files_exist():
    text = SKILL.read_text()
    names = set(re.findall(r"references/([\w.-]+\.md)", text))
    assert "review-checklist.md" in names
    for name in names:
        assert (SKILL_DIR / "references" / name).is_file(), name


def test_panel_reviewer_reads_the_checklist():
    text = PANEL.read_text()
    for phrase in ("review-checklist.md", "kind", "evidence", "declined", "cannotVerify"):
        assert phrase in text, phrase
    fm = frontmatter(PANEL)
    assert fm["name"] == "panel-reviewer"
    assert "Bash" in fm["tools"] and "Edit" not in fm["tools"]


MOVED = {
    "Spec axis": [
        "deferred that an agent could have done",
        "Verification that did not run or did not pass",
        "gap the summary mentions finding",
    ],
    "Quality axis": [
        "debt-marker comment",
        "stub or skipped test introduced",
        "reimplemented instead of reused",
    ],
}


def test_checklist_has_completeness_bullets():
    sec = sections(CHECKLIST.read_text())
    for name, phrases in MOVED.items():
        for phrase in phrases:
            assert phrase in sec[name], f"{name} missing {phrase!r}"


def test_reviewer_agents_exist():
    for name in REVIEWERS:
        path = ROOT / "agents" / f"{name}.md"
        assert path.is_file()
        assert frontmatter(path)["name"] == name


def test_debt_marker_bullet_names_no_literal_markers():
    bullet = next(ln for ln in CHECKLIST.read_text().splitlines() if "debt-marker comment" in ln)
    for word in ("TODO", "FIXME", "follow-up", "for later"):
        assert word not in bullet, word


@pytest.mark.parametrize("name", REVIEWERS)
def test_reviewer_agents_read_only_and_read_checklist(name):
    path = ROOT / "agents" / f"{name}.md"
    fm = frontmatter(path)
    assert fm["name"] == name
    assert fm["tools"] == "[Read, Grep, Glob, Bash]"
    assert "model" not in fm and "hooks" not in fm
    assert set(fm) <= {"name", "description", "tools"}
    text = path.read_text()
    assert "Edit" not in fm["tools"] and "Write" not in fm["tools"]
    body = text.split("\n---\n", 1)[1]
    assert "review-checklist.md" in body
    assert body.index("review-checklist.md") < 400
    assert path.read_text().isascii()


def test_reviewer_agents_do_not_copy_the_checklist():
    checklist = [ln for ln in CHECKLIST.read_text().splitlines() if ln.startswith("- ")]
    for name in REVIEWERS:
        text = (ROOT / "agents" / f"{name}.md").read_text()
        for ln in checklist:
            assert ln not in text, (name, ln)


def test_panel_reviewer_stays_persona_free():
    text = PANEL.read_text()
    for name in REVIEWERS:
        assert f"{name}.md" not in text
    assert "one member of an interrogate review panel" in text.lower()


def test_research_reviewer_persona_contract():
    text = PERSONA.read_text()
    for phrase in ("quote", "verified", "assumed", "unknown"):
        assert phrase in text, phrase
    assert h2s(text) == ["Lens", "Source priorities", "Emphasis", "Output contract"]


def test_all_five_files_are_ascii():
    for path in (SKILL, CHECKLIST, PANEL, PERSONA, Path(__file__)):
        assert path.read_text().isascii(), path


def test_start_review_skill_does_not_name_panel_reviewer():
    assert "panel-reviewer" not in (ROOT / "skills" / "start-review" / "SKILL.md").read_text()
