"""ticket.py lint: the lean task rules (no approvals ledger, no owns/uses)."""

from ticket_repo_helpers import cli, commit_all, epic_dir, git, mk_epic, mk_task, set_meta

DESIGN = """# Topic design

## Decisions

### D1: First call
Why.

### D2: Second call
Why.

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 First call | alpha |
| D2 Second call | {d2} |

## Open questions

none
"""


def lint(root, ep):
    return cli("lint", ep, "--root", root)


def test_lint_lean_rules(repo, root):
    ep = mk_epic(root)
    alpha = mk_task(root, ep, "alpha")
    mk_task(root, ep, "beta", extra=["--depends-on", "alpha"])
    commit_all(repo)
    d = epic_dir(root, ep)
    assert not (d / "approvals.json").exists()
    r = lint(root, ep)
    assert r.returncode == 0, r.stderr

    # legacy keys are never rejected
    set_meta(alpha, owns=["part"], uses=["other"], estimate="6", run="r1")
    assert lint(root, ep).returncode == 0, lint(root, ep).stderr

    design = d / "design.md"
    design.write_text(DESIGN.format(d2="`alpha`, beta"))
    r = lint(root, ep)
    assert r.returncode == 0, r.stderr
    design.write_text(DESIGN.format(d2="alpha, ghost"))
    r = lint(root, ep)
    assert r.returncode == 1 and "D2" in r.stderr and "ghost" in r.stderr
    design.write_text(DESIGN.format(d2="beta").replace("| D2 Second call | beta |\n", ""))
    r = lint(root, ep)
    assert r.returncode == 1 and "D2" in r.stderr and "Decision coverage" in r.stderr
    design.write_text(DESIGN.format(d2="beta"))

    good = alpha.read_text()

    def broken(text, needle):
        alpha.write_text(text)
        r = lint(root, ep)
        alpha.write_text(good)
        assert r.returncode == 1 and "alpha" in r.stderr and needle in r.stderr, r.stderr

    ac = "- AC1: it works [evidence: test:tests/test_x.py::test_works]"
    broken(good.replace(ac, ""), "acceptance condition")
    broken(good.replace("Do the thing.", ""), "Requirement")
    broken(good.replace("verify: ", 'verify: ""\nold_verify: ', 1), "verify")
    broken(good.replace("files: [alpha.py]", "files: []"), "files")
    broken(good.replace("depends_on: []", "depends_on: [beta]"), "cycle")
    assert lint(root, ep).returncode == 0

    # a done epic is history: a task written before these rules is not rejected
    old = mk_epic(root, "Old work")
    set_meta(mk_task(root, old, "gamma"), status="done", verify="")
    commit_all(repo)
    (root / "done").mkdir()
    git(repo, "mv", str(root / "todo" / old), str(root / "done" / old))
    r = lint(root, old)
    assert r.returncode == 0, r.stderr
