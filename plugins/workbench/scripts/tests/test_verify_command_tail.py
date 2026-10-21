"""Command ACs carry exit and tail so a negated grep cannot be read backwards."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_verify_task as base  # noqa: E402
from test_verify_task import Triage, ac, branch, by_id, commit, verify  # noqa: E402

repo = base.repo


def run(repo, *extra, triage=True):
    branch(repo)
    commit(repo, {"f.txt": "present line\nother\n"})
    acs = [
        ac("N1", "absent", "command", "! grep -q absent f.txt"),
        ac("N2", "present", "command", "! grep -q present f.txt; grep present f.txt; exit 1"),
        ac("N3", "negated present", "command", "grep present f.txt && ! grep -q present f.txt"),
        ac("N4", "many", "command", "seq 1 30"),
    ]
    return by_id(verify(repo, "true", *extra, triage=Triage() if triage else None, acs=acs))


def check(a):
    assert a["N1"]["met"] is True and a["N1"]["exit"] == 0
    assert a["N1"]["how"] == "ran ! grep -q absent f.txt verbatim: whole command exit 0"
    assert a["N2"]["met"] is False and a["N2"]["exit"] == 1
    assert "present line" in a["N2"]["tail"]
    assert a["N3"]["met"] is False and a["N3"]["exit"] == 1
    assert a["N4"]["tail"].splitlines() == [str(i) for i in range(21, 31)]
    assert all(len(x["tail"]) <= 1000 for x in a.values())


def test_command_ac_has_exit_and_tail(repo):
    check(run(repo))


def test_command_ac_no_triage_has_exit_and_tail(repo):
    check(run(repo, "--no-triage", triage=False))


def test_negated_grep_verbatim(repo):
    a = run(repo)
    assert a["N1"]["met"] is True and a["N1"]["exit"] == 0
    assert a["N1"]["how"] == "ran ! grep -q absent f.txt verbatim: whole command exit 0"
    assert a["N3"]["met"] is False and a["N3"]["exit"] == 1


def test_unmet_negated_grep_tail_shows_match(repo):
    a = run(repo, "--no-triage", triage=False)
    assert a["N2"]["met"] is False and a["N2"]["exit"] == 1
    assert "present line" in a["N2"]["tail"]


def test_tail_capped_at_1000_chars(repo):
    branch(repo)
    commit(repo, {"f.txt": "x\n"})
    cmd = "head -c 5000 /dev/zero | tr '\\0' a"
    out = verify(repo, "true", triage=Triage(), acs=[ac("L", "long", "command", cmd)])
    t = by_id(out)["L"]["tail"]
    assert len(t) == 1000
