"""Tests for ticket.py args: the plan-execute args and named copy from one command (D10, D13)."""

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

SD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(SD / "scripts"))
import ticket  # noqa: E402
from test_ticket_run import cli, commit_all, git, mk_epic, mk_task  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "args_mod", SD / "scripts" / "ticket_cmds" / "args.py"
)
args_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(args_mod)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "proj"
    r.mkdir()
    git(r, "init", "-b", "main")
    git(r, "config", "user.email", "t@t")
    git(r, "config", "user.name", "t")
    (r / "a.py").write_text("x = 1\n")
    git(r, "add", ".")
    git(r, "commit", "-m", "init")
    return r


@pytest.fixture
def root(repo):
    return repo / "docs" / "plans"


def set_status(path, status):
    text = path.read_text()
    path.write_text(re.sub(r"(?m)^status: .*$", f"status: {status}", text, count=1))


@pytest.fixture
def epic(root):
    ep = mk_epic(root)
    a = mk_task(root, ep, "Alpha")
    b = mk_task(root, ep, "Beta", extra=("--depends-on", "alpha"))
    c = mk_task(root, ep, "Gamma")
    d = root / "todo" / ep
    (d / "approvals.json").write_text(
        json.dumps(
            [
                {
                    "id": "A1",
                    "text": "alpha only",
                    "decisions": [],
                    "tasks": ["alpha"],
                    "status": "approved",
                },
                {
                    "id": "A2",
                    "text": "alpha and beta",
                    "decisions": [],
                    "tasks": ["alpha", "beta"],
                    "status": "approved",
                },
            ]
        )
    )
    commit_all(root.parents[1])
    return ep, d, a, b, c


def test_args_strip_done_ids(epic, root):
    ep, d, a, b, c = epic
    set_status(a, "done")
    out = args_mod.build_args(d)
    assert out["epic"] == out["name"] == ep
    assert [t["id"] for t in out["tasks"]] == ["beta", "gamma"]
    assert all("alpha" not in t["dependsOn"] for t in out["tasks"])
    assert [x["id"] for x in out["approvals"]] == ["A2"]
    assert out["approvals"][0]["tasks"] == ["beta"]
    assert out["baseRef"] == ep
    assert out["mainCheckout"] == str(d.parents[3].resolve())
    assert out["verifierAgent"] == "workbench:verifier"
    assert out["rulingsFile"] == str(d / "rulings.json")
    assert out["designDoc"] == str(d / "design.md") and out["planDoc"] == str(d / "README.md")
    assert set(out["brief"]) == {"what", "how", "why"}
    assert out["lenses"]
    text = out["planText"]
    assert text.index("alpha") > text.index("do not re-audit, do not rebuild")
    assert "OPEN" in text and text.index("OPEN") < text.index("beta", text.index("OPEN"))
    # plan-execute takes one flat glob list (as validate-tasks.mjs builds it), not a per-repo map
    assert isinstance(out["overlapIgnore"], list) and out["overlapIgnore"]
    assert all(isinstance(g, str) for g in out["overlapIgnore"])
    assert "*README.md" in out["overlapIgnore"]


def test_plan_text_done_and_open(epic, root):
    ep, d, *_ = epic
    assert args_mod.build_args(d)["contextPack"] == ""
    facts = root / "facts.md"
    facts.write_text("facts\n")
    assert args_mod.build_args(d)["contextPack"] == str(facts)
    assert args_mod.build_args(d, "/x/pack.md")["contextPack"] == "/x/pack.md"


def test_no_open_tasks_fails(epic, root, tmp_path):
    ep, d, a, b, c = epic
    for p in (a, b, c):
        set_status(p, "done")
    with pytest.raises(ticket.TicketError, match=f"no open tasks in {ep}; nothing to run"):
        args_mod.build_args(d)
    out = tmp_path / "out"
    out.mkdir()
    r = cli("args", ep, "--root", root, "--out-dir", out)
    assert r.returncode == 1 and "nothing to run" in r.stderr
    assert list(out.iterdir()) == []


def test_writes_named_copy(epic, root, tmp_path):
    ep, d, a, *_ = epic
    set_status(a, "done")
    before = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root.parents[1], capture_output=True, text=True
    ).stdout
    out = tmp_path / "out"
    out.mkdir()
    r = cli("args", ep, "--root", root, "--out-dir", out)
    assert r.returncode == 0, r.stderr
    data = json.loads((out / f"{ep}-args.json").read_text())
    assert [t["id"] for t in data["tasks"]] == ["beta", "gamma"]
    last = r.stdout.strip().splitlines()[-1]
    assert last == str(out / f"plan-execute-{ep}.js")
    assert f"plan-execute:{ep}" in Path(last).read_text()
    after = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root.parents[1], capture_output=True, text=True
    ).stdout
    assert before == after


HARNESS = SD.parents[1] / "workflows" / "tests" / "harness.mjs"
PLAN_EXECUTE = SD.parents[1] / "workflows" / "plan-execute.js"
NODE_CHECK = """
import { runWorkflow } from %s
import { readFileSync } from 'node:fs'
const args = JSON.parse(readFileSync(process.argv[1], 'utf8'))
const wt = (id) => (args.epic ? args.epic + '--' : '/validate/') + id
for (const t of args.tasks) if (!t.worktree) t.worktree = wt(t.id)
const agent = async () => { throw new Error('stop') }
const r = await runWorkflow(%s, { args, agent })
if (!r.calls.length) {
  console.error(r.error ? r.error.message : 'plan-execute finished without reaching an agent')
  process.exit(1)
}
"""


def run_in_harness(args, tmp_path):
    f = tmp_path / "args-check.json"
    f.write_text(json.dumps(args))
    code = NODE_CHECK % (json.dumps(str(HARNESS)), json.dumps(str(PLAN_EXECUTE)))
    return subprocess.run(
        ["node", "--input-type=module", "-e", code, str(f)], capture_output=True, text=True
    )


def test_args_validate_in_harness(epic, root, tmp_path):
    ep, d, a, *_ = epic
    set_status(a, "done")
    readme = d / "README.md"
    text = readme.read_text()
    for k in ("What", "How", "Why"):
        text = re.sub(rf"(?m)^{k}:.*$", f"{k}: fixture {k.lower()}", text, count=1)
    readme.write_text(text)
    out = args_mod.build_args(d)
    # distinct files per task keep overlap detection out of the contract check
    for t in out["tasks"]:
        t["files"] = [f"{t['id']}.py"]
    r = run_in_harness(out, tmp_path)
    assert r.returncode == 0, r.stderr
    # a contract mismatch (overlapIgnore as a per-repo map) must be caught
    bad = dict(out, overlapIgnore={"proj": out["overlapIgnore"]})
    r = run_in_harness(bad, tmp_path)
    assert r.returncode != 0 and "overlapIgnore" in r.stderr
