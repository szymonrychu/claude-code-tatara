"""ticket.py lint: the lean task rules (no approvals ledger, no owns/uses)."""

from ticket_repo_helpers import (
    cli,
    commit_all,
    epic_dir,
    git,
    mk_epic,
    mk_task,
    set_meta,
    ticket,
)

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


GOOD_NUMBERS = {
    "points": "3",
    "expected_minutes": "34",
    "expected_tokens": "2250000",
    "points_actual": "5",
    "actual_minutes": "41",
    "actual_tokens": "0",
    "actual_roles": "impl 30, review 11",
    "actual_role_tokens": "impl 1900000, review 400000",
}
BAD_NUMBERS = {
    "expected_minutes": "12.5",
    "actual_tokens": "-3",
    "points_actual": "4",
    "actual_roles": "impl two, review 1",
}


def _moved(repo, root, ep, phase):
    (root / phase).mkdir(exist_ok=True)
    git(repo, "mv", str(epic_dir(root, ep)), str(root / phase / ep))
    return epic_dir(root, ep)


def test_lint_numeric_estimate_fields(repo, root):
    ep = mk_epic(root)
    mk_task(root, ep, "alpha")
    commit_all(repo)
    alpha = _moved(repo, root, ep, "in-progress") / "tasks" / "alpha.md"
    set_meta(alpha, status="in-progress", **GOOD_NUMBERS)
    r = lint(root, ep)
    assert r.returncode == 0, r.stderr

    set_meta(alpha, **BAD_NUMBERS)
    r = lint(root, ep)
    assert r.returncode == 1
    bad = [ln for ln in r.stderr.splitlines() if "alpha" in ln]
    for key, value in BAD_NUMBERS.items():
        assert [ln for ln in bad if key in ln and value in ln], (key, r.stderr)
    for key in ("points", "expected_tokens", "actual_minutes", "actual_role_tokens"):
        assert not [ln for ln in bad if f"{key} " in ln or f"{key}:" in ln], (key, r.stderr)

    for key, value in (
        ("points", "21"),
        ("expected_tokens", "many"),
        ("actual_minutes", "1e3"),
        ("actual_role_tokens", "impl 5 review 2"),
        ("actual_roles", "fix 3"),
    ):
        set_meta(alpha, **{**GOOD_NUMBERS, key: value})
        r = lint(root, ep)
        assert r.returncode == 1 and key in r.stderr and value in r.stderr, (key, r.stderr)

    # unset is fine: the fields start empty
    set_meta(alpha, **{k: "" for k in GOOD_NUMBERS})
    assert lint(root, ep).returncode == 0

    # a done epic is history: its numbers are not checked
    old = mk_epic(root, "Old work")
    gamma = mk_task(root, old, "gamma")
    commit_all(repo)
    gamma = _moved(repo, root, old, "done") / "tasks" / "gamma.md"
    set_meta(gamma, status="done", **BAD_NUMBERS)
    r = lint(root, old)
    assert r.returncode == 0, r.stderr


def test_roles_round_trip():
    text = "impl 30, review 11"
    roles = ticket._parse_roles(text, "alpha", "actual_roles")
    assert roles == {"impl": 30, "review": 11}
    assert ticket._format_roles(roles) == text
    assert ticket._format_roles({"review": 2, "impl": 1}) == "impl 1, review 2"
