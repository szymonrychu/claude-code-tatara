"""research-<persona> agents: method lives in agents/, the personas/ directory is gone."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
AGENTS = ROOT / "agents"
NAMES = ("docs-purist", "practitioner", "prior-art-scout", "paper-scout", "reviewer")
SECTIONS = ("## Lens", "## Source priorities", "## Emphasis", "## Output contract")


def split(path):
    text = path.read_text()
    assert text.startswith("---\n"), f"{path.name}: no frontmatter"
    end = text.index("\n---\n", 4)
    fm = {}
    for line in text[4:end].splitlines():
        if line[:1] not in (" ", "\t") and ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, text[end + 5 :]


@pytest.mark.parametrize("name", NAMES)
def test_agent_file_shape(name):
    path = AGENTS / f"research-{name}.md"
    assert path.is_file()
    fm, _ = split(path)
    assert fm["name"] == path.stem == f"research-{name}"
    assert ":" not in fm["name"]
    assert fm["model"] == "sonnet"
    assert fm["description"] not in ("", ">", "|") or "description:" in path.read_text()
    assert len(path.read_text().split("description:", 1)[1].split("tools:", 1)[0].strip()) > 10
    tools = [t.strip() for t in fm["tools"].strip("[]").split(",")]
    assert tools == ["Read", "Grep", "Glob", "WebSearch", "WebFetch", "Write"]
    assert "Bash" not in tools
    path.read_text().encode("ascii")


@pytest.mark.parametrize("name", NAMES)
def test_body_has_method_sections(name):
    _, body = split(AGENTS / f"research-{name}.md")
    for section in SECTIONS:
        assert section in body
    assert "output path" in body
    assert "topic" in body


def test_reviewer_takes_lens_briefs():
    _, body = split(AGENTS / "research-reviewer.md")
    assert "lens brief" in body


def test_no_body_duplicates_another():
    bodies = {n: split(AGENTS / f"research-{n}.md")[1] for n in NAMES}
    assert len(set(bodies.values())) == len(NAMES)


@pytest.mark.parametrize("name", NAMES)
def test_no_parking_wording(name):
    text = (AGENTS / f"research-{name}.md").read_text().lower()
    for word in ("follow-up", "followup", "todo", "later", "phase 2", "out of scope"):
        assert word not in text.replace("was later", "")
