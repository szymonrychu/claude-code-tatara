"""The python rule must not contradict the template's own python3 tooling."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COPIES = [ROOT / ".claude/rules/python.md", ROOT / "plugins/workbench/rules/python.md"]


def test_python_rule_matches_template_tooling():
    text = COPIES[0].read_text("utf-8")
    assert text == COPIES[1].read_text("utf-8")
    assert "never bare" not in text
    assert "uv.lock" in text
    assert "plugins/" in text and "scripts/" in text and "python3" in text
    assert text.index("mise run") < text.index("uv run")
