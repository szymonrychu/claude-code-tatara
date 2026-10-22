"""Init removes the template's own docs; `mise run init:update` then pulls a template change
into the project without them, ending lint-green with one commit."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from helpers import git, run  # noqa: E402

NEW_RULE = "Template update marker: always cite the plan."
TEMPLATE_MEMORY = "2099-01-01: template-only decision about brewing."
INIT_ARGS = (
    "new", "--name", "demo", "--component", "api:python",
    "--purpose", "A booking service for dentists.", "--hard-rule", "No PII in logs",
    "--risk", "The payments path", "--harness", "cursor",
)  # fmt: skip


def lines(root, *paths):
    return git("ls-files", *paths, cwd=root).splitlines()


def test_init_leaves_no_template_docs(template, engine, tmp_path):
    assert (template / "docs/plans/contracts.json").exists()
    engine(*INIT_ARGS, "--remote", f"local-bare:{tmp_path / 'remotes'}")
    assert sorted(lines(template, "docs/plans")) == [
        "docs/plans/done/.gitkeep",
        "docs/plans/in-progress/.gitkeep",
        "docs/plans/todo/.gitkeep",
    ]
    assert lines(template, "docs/research", "docs/handoffs") == []
    entries = [ln for ln in (template / "MEMORY.md").read_text().splitlines()[1:] if ln.strip()]
    assert len(entries) == 2 and "project initialised" in entries[-1], entries


def test_template_update_roundtrip(template, engine, mise, tmp_path):
    upstream = tmp_path / "upstream"
    git("clone", "-q", "--no-hardlinks", str(template), str(upstream), cwd=tmp_path)
    git("config", "user.name", "E2E", cwd=upstream)
    git("config", "user.email", "e2e@example.com", cwd=upstream)
    engine(*INIT_ARGS, "--remote", f"local-bare:{tmp_path / 'remotes'}")
    mine = template / "docs/plans/todo/my-epic/README.md"
    mine.parent.mkdir(parents=True)
    mine.write_text("# my epic\n")
    git("add", "-A", cwd=template)
    git("commit", "-q", "-m", "project: my epic", cwd=template)

    rule = upstream / "plugins/workbench/rules/tdd.md"
    rule.write_text(rule.read_text().rstrip("\n") + f"\n\n{NEW_RULE}\n")
    run(sys.executable, "scripts/harness/setup.py", "--root", str(upstream), cwd=upstream)
    skill = upstream / "plugins/workbench/skills/handoff/SKILL.md"
    skill.write_text(skill.read_text().rstrip("\n") + "\n\nTemplate plugin change marker.\n")
    done = upstream / "docs/plans/done/template-epic/README.md"
    done.parent.mkdir(parents=True)
    done.write_text("# template epic\n")
    memory = upstream / "MEMORY.md"
    memory.write_text(memory.read_text().rstrip("\n") + f"\n\n{TEMPLATE_MEMORY}\n")
    brief = upstream / "docs/research/template-brief.md"
    brief.parent.mkdir(parents=True, exist_ok=True)
    brief.write_text("template brief\n")
    contracts = upstream / "docs/plans/contracts.json"
    contracts.write_text(contracts.read_text().rstrip("\n") + "\n\n")
    git("add", "-A", cwd=upstream)
    git("add", "-f", "docs/research/template-brief.md", cwd=upstream)
    git("commit", "-q", "-m", "template: new rule and docs", cwd=upstream)

    before = git("rev-list", "--count", "--first-parent", "HEAD", cwd=template)
    mise("run", "init:update", "--", "--url", str(upstream))

    agents = (template / "AGENTS.md").read_text()
    assert NEW_RULE in agents and "<<<<<<<" not in agents
    for kept in ("A booking service for dentists.", "No PII in logs", "The payments path"):
        assert kept in agents
    assert (
        "Template plugin change marker."
        in (template / "plugins/workbench/skills/handoff/SKILL.md").read_text()
    )
    assert lines(template, "docs/plans/done/template-epic", "docs/research",
                 "docs/plans/contracts.json") == []  # fmt: skip
    assert TEMPLATE_MEMORY not in (template / "MEMORY.md").read_text()
    assert mine.read_text() == "# my epic\n"
    after = git("rev-list", "--count", "--first-parent", "HEAD", cwd=template)
    assert int(after) - int(before) == 1  # one update commit on the project line
    subject = git("log", "-1", "--format=%s", cwd=template)
    assert subject.startswith("chore(workbench): template update "), subject
    assert git("status", "--porcelain", cwd=template) == ""
    doc = run(sys.executable, "scripts/doctor.py", "--root", str(template), cwd=template).stdout
    assert "metarepo" in doc and "components: 1" in doc, doc
    r = mise("run", "lint", check=False)
    assert r.returncode == 0, (r.stdout, r.stderr)
