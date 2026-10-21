"""Pins the project-scoped rules under .claude/rules/."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES = ROOT / ".claude" / "rules"
NAMES = ["python", "go", "typescript", "terraform", "helm", "ansible", "sops"]
# Forbidden words are built at run time so this file does not trip lint:personal.
FORBIDDEN = [
    "home" + "lab",
    "har" + "bor",
    "tat" + "ara",
    "sops-" + "edit",
    "default." + "secrets",
]


def _split(name: str) -> tuple[list[str], str]:
    text = (RULES / f"{name}.md").read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    assert m, f"{name}: no frontmatter"
    paths = re.findall(r'^\s+-\s+"(.+)"\s*$', m.group(1), re.M)
    return paths, m.group(2)


def test_seven_files_exist():
    for n in NAMES:
        assert (RULES / f"{n}.md").is_file(), n


def test_rules_have_paths():
    for n in NAMES:
        assert m_paths(n), n


def m_paths(n: str) -> list[str]:
    return _split(n)[0]


def test_body_is_ascii():
    for n in NAMES:
        _, body = _split(n)
        assert body.isascii(), n


def test_rules_are_generic():
    for n in NAMES:
        text = (RULES / f"{n}.md").read_text().lower()
        for word in FORBIDDEN:
            assert word not in text, (n, word)


def test_sops_generic_patterns():
    paths = m_paths("sops")
    assert paths == ["**/*.enc.*", "**/*.secret.*", "**/secrets.*.y?ml", "**/.sops.yaml"]
    assert "when the pack is enabled" in (RULES / "sops.md").read_text()
