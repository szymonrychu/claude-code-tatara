"""docs/dreaming must never name a session slug (D11): the hand-over target is found at run time."""

import re
from pathlib import Path

DOCS = Path(__file__).resolve().parents[2] / "docs" / "dreaming"
SLUG = re.compile(r"\bmx-\d+\b")


def test_docs_exist():
    assert sorted(p.name for p in DOCS.glob("*.md")) == [
        "README.md",
        "apply-skill.md",
        "change-request.md",
        "preset-system-append.md",
        "schedule-prompt.md",
    ]


def test_no_session_slug_in_dreaming_docs():
    hits = [
        f"{p.name}:{n}: {line.strip()}"
        for p in sorted(DOCS.glob("*.md"))
        for n, line in enumerate(p.read_text().splitlines(), 1)
        if SLUG.search(line)
    ]
    assert not hits, "\n".join(hits)
