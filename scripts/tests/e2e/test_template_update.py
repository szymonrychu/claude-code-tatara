"""Pulling a template update: merge a template commit that changes a generated block, run
init:refresh, and end healthy with the user's AGENTS.md text intact."""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from helpers import git, run  # noqa: E402

NEW_RULE = "Template update marker: always cite the plan."


def test_template_update_roundtrip(template, engine, mise, tmp_path):
    upstream = tmp_path / "upstream"
    git("clone", "-q", "--no-hardlinks", str(template), str(upstream), cwd=tmp_path)
    git("config", "user.name", "E2E", cwd=upstream)
    git("config", "user.email", "e2e@example.com", cwd=upstream)
    engine(
        "new", "--name", "demo", "--component", "api:python",
        "--remote", f"local-bare:{tmp_path / 'remotes'}",
        "--purpose", "A booking service for dentists.", "--hard-rule", "No PII in logs",
        "--risk", "The payments path", "--harness", "cursor",
    )  # fmt: skip
    # the template changes a rule file and rebuilds its generated AGENTS.md block
    rule = upstream / "plugins/workbench/rules/tdd.md"
    rule.write_text(rule.read_text().rstrip("\n") + f"\n\n{NEW_RULE}\n")
    run(sys.executable, "scripts/harness/setup.py", "--root", str(upstream), cwd=upstream)
    assert NEW_RULE in (upstream / "AGENTS.md").read_text()
    git("add", "-A", cwd=upstream)
    git("commit", "-q", "-m", "template: new rule", cwd=upstream)

    git("remote", "add", "template", str(upstream), cwd=template)
    git("fetch", "-q", "template", cwd=template)
    merge = subprocess.run(
        ["git", "merge", "--no-edit", "template/main"], cwd=template, capture_output=True, text=True
    )
    if merge.returncode != 0:  # generated-block conflicts: take the project side, as documented
        conflicted = git("diff", "--name-only", "--diff-filter=U", cwd=template).splitlines()
        assert conflicted, merge.stdout + merge.stderr
        for path in conflicted:
            git("checkout", "--ours", "--", path, cwd=template)
            git("add", "--", path, cwd=template)
        git("commit", "-q", "--no-edit", cwd=template)

    mise("run", "init:refresh")

    agents = (template / "AGENTS.md").read_text()
    for kept in ("A booking service for dentists.", "No PII in logs", "The payments path"):
        assert kept in agents
    assert NEW_RULE in agents  # the regenerated rules block carries the template change
    assert "<<<<<<<" not in agents
    doc = run(sys.executable, "scripts/doctor.py", "--root", str(template), cwd=template).stdout
    assert "metarepo" in doc and "components: 1" in doc, doc
    r = mise("run", "lint", check=False)
    assert r.returncode == 0, (r.stdout, r.stderr)
