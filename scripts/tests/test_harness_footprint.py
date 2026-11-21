"""Pins scripts/harness_footprint.py: always-loaded context measurement and report."""

from pathlib import Path

import harness_footprint as hf


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_counts_skill_descriptions_only(tmp_path):
    desc = "d" * 40
    _write(
        tmp_path / "plugins" / "p" / "skills" / "s" / "SKILL.md",
        f"---\nname: s\ndescription: {desc}\n---\n" + "b" * 4000,
    )
    skills = [s for s in hf.measure(tmp_path, None) if s.kind == "skill-description"]
    assert [s.chars for s in skills] == [40]
    assert skills[0].tokens == 10


def test_folded_description_joined(tmp_path):
    _write(
        tmp_path / "plugins" / "p" / "agents" / "a.md",
        "---\nname: a\ndescription: >\n  one two\n  three\n---\nbody\n",
    )
    agents = [s for s in hf.measure(tmp_path, None) if s.kind == "agent-description"]
    assert [s.chars for s in agents] == [len("one two three")]


def test_path_scoped_rules_excluded(tmp_path):
    _write(tmp_path / ".claude" / "rules" / "scoped.md", '---\npaths:\n  - "**/*.py"\n---\nx\n')
    _write(tmp_path / ".claude" / "rules" / "always.md", "always loaded\n")
    names = [s.name for s in hf.measure(tmp_path, None) if s.kind == "rule"]
    assert names == [".claude/rules/always.md"]


def test_missing_superpowers_dir_notes_absence(tmp_path):
    _write(tmp_path / "CLAUDE.md", "hello")
    out = hf.render(hf.measure(tmp_path, None), "2026-11-21")
    assert "superpowers: not found" in out


def test_superpowers_bootstrap_counted(tmp_path):
    sp = tmp_path / "sp"
    _write(sp / "skills" / "using-superpowers" / "SKILL.md", "---\ndescription: x\n---\nbody")
    kinds = {s.kind for s in hf.measure(tmp_path, sp)}
    assert {"session-start", "skill-description"} <= kinds


def test_render_totals(tmp_path):
    _write(tmp_path / "CLAUDE.md", "a" * 40)
    _write(tmp_path / "AGENTS.md", "a" * 400)
    _write(tmp_path / ".claude" / "rules" / "r.md", "a" * 8)
    sources = hf.measure(tmp_path, None)
    out = hf.render(sources, "2026-11-21")
    total = sum(s.tokens for s in sources)
    total_row = next(ln for ln in out.splitlines() if ln.startswith("| **Total**"))
    assert total_row.endswith(f"| {total} |")
    table = out.split("## Subtotals")[0].splitlines()
    rows = [ln for ln in table if ln.startswith("| ") and ".md |" in ln]
    toks = [int(r.split("|")[4]) for r in rows]
    assert toks == sorted(toks, reverse=True)
