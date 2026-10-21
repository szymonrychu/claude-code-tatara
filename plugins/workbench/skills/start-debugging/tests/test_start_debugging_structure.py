"""Structure tests for the start-debugging skill and its loops reference."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SD = ROOT / "skills" / "start-debugging"
SKILL = SD / "SKILL.md"
LOOPS = SD / "references" / "loops.md"
GRAFANA = (
    ROOT.parent / "workbench-observability" / "skills" / "grafana-debugging-start" / "SKILL.md"
)

SECTIONS = [
    "## Iron law",
    "## Phase 0 - Intake",
    "## Phase 1 - Feedback loop",
    "## Phase 2 - Minimise",
    "## Phase 3 - Hypothesise",
    "## Phase 4 - Instrument and test",
    "## Phase 5 - Root cause",
    "## Phase 6 - Regression test, proven",
    "## Phase 7 - Fix",
    "## Phase 8 - Cleanup and record",
    "## Red flags",
    "## Agans' nine rules",
    "## Rules",
]

PHRASES = [
    "No fix without a root cause",
    "red-capable",
    "deterministic",
    "agent-runnable",
    "No red-capable command, no phase 2",
    "one at a time",
    "3-5",
    "falsifiable",
    "never fix just where the error appears",
    "[DEBUG-",
    "Measure first",
    "three failed fixes",
    "workbench:interrogate",
    "watch it fail",
    "pristine",
    "revert the fix",
    "lean path",
    "start-development",
    "grep",
    "doc_path.sh record",
    "quick fix for now",
    "one more attempt",
    "references/loops.md",
]


def sections(text):
    parts = re.split(r"^(?=## )", text, flags=re.M)
    return {p.splitlines()[0]: p for p in parts if p.startswith("## ")}


def test_frontmatter():
    text = SKILL.read_text()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m
    fm = m.group(1)
    assert re.search(r"^name: start-debugging$", fm, re.M)
    d = re.search(r'^description: "?(.*?)"?$', fm, re.M).group(1)
    assert len(d) < 1536
    for trig in (
        "error message",
        "stack trace",
        "failing test",
        "staging",
        "regression after a deploy",
        "health check",
    ):
        assert trig in d, trig


def test_section_order():
    text = SKILL.read_text()
    heads = [ln for ln in text.splitlines() if ln.startswith("## ")]
    assert [h for h in heads if h in SECTIONS] == SECTIONS


def test_phases_end_with_done_when():
    secs = sections(SKILL.read_text())
    for head in SECTIONS:
        if head.startswith("## Phase"):
            assert re.search(r"^Done when:", secs[head], re.M), head


def test_required_phrases():
    text = SKILL.read_text()
    for p in PHRASES:
        assert p in text, p


def test_length():
    assert len(SKILL.read_text().splitlines()) < 200


def test_references_exist():
    text = SKILL.read_text()
    names = set(re.findall(r"references/([\w.-]+\.md)", text))
    assert "loops.md" in names
    for n in names:
        assert (SD / "references" / n).is_file(), n


def test_loops_reference():
    text = LOOPS.read_text()
    assert text.startswith("# Feedback loops")
    for n in (
        "git bisect run",
        "git bisect start <bad> <good>",
        "grafana-debugging-start",
        "k8s-triage",
        "kubectl-logs-query",
        "50%",
        "## Flaky",
        "## Proofs",
        "pristine",
    ):
        assert n in text, n


def test_loops_route_live_signals():
    text = LOOPS.read_text()
    assert "workbench-observability" in text
    assert "when the workbench-observability pack is enabled" in text


def test_grafana_points_here():
    # the skill lives in the optional pack; skip when the pack is absent
    if GRAFANA.is_file():
        assert "start-debugging" in GRAFANA.read_text()


def test_files_are_plain_ascii():
    for f in (SKILL, LOOPS, *([GRAFANA] if GRAFANA.is_file() else [])):
        f.read_text().encode("ascii")
