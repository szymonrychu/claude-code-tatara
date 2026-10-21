"""ticket.py contract add/use/list: the cross-epic contracts registry (D8)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "start-development" / "scripts" / "ticket.py"
sys.path.insert(0, str(SCRIPT.parent / "ticket_cmds"))


def cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, cwd=cwd
    )


@pytest.fixture
def root(tmp_path):
    r = tmp_path / "plans"
    r.mkdir()
    return r


def add(root, name, owner="alpha", *extra):
    return cli(
        "contract",
        "add",
        name,
        "--root",
        root,
        "--kind",
        "node",
        "--owner",
        owner,
        "--file",
        "src/a.py",
        *extra,
    )


def reg(root):
    return json.loads((root / "contracts.json").read_text())


def test_add_writes_and_commits(root):
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    for k, v in (("user.email", "a@b"), ("user.name", "n")):
        subprocess.run(["git", "-C", str(root), "config", k, v], check=True)
    r = add(root, "cfg-key", "alpha", "--consumers", "beta,gamma", "--note", "n")
    assert r.returncode == 0, r.stderr
    assert reg(root) == [
        {
            "name": "cfg-key",
            "kind": "node",
            "owner": "alpha",
            "file": "src/a.py",
            "consumers": ["beta", "gamma"],
            "note": "n",
        }
    ]
    log = subprocess.run(
        ["git", "-C", str(root), "log", "--format=%s"], capture_output=True, text=True
    ).stdout
    assert "chore(ticket): alpha contract add cfg-key" in log


def test_add_refuses_other_owner(root):
    add(root, "x", "alpha")
    r = add(root, "x", "beta")
    assert r.returncode == 1 and "alpha" in r.stderr
    assert len(reg(root)) == 1


def test_readd_same_owner_updates_and_merges(root):
    add(root, "x", "alpha", "--consumers", "beta")
    r = cli(
        "contract",
        "add",
        "x",
        "--root",
        root,
        "--kind",
        "topic",
        "--owner",
        "alpha",
        "--file",
        "new.py",
        "--consumers",
        "gamma,beta",
    )
    assert r.returncode == 0, r.stderr
    c = reg(root)[0]
    assert (c["kind"], c["file"], c["consumers"]) == ("topic", "new.py", ["beta", "gamma"])


def test_add_refuses_task_owned_name(root):
    d = root / "todo" / "beta" / "tasks"
    d.mkdir(parents=True)
    (root / "todo" / "beta" / "README.md").write_text("---\ntitle: beta\n---\n")
    (d / "t.md").write_text("---\ntitle: t\nowns: [shared]\n---\nbody\n")
    r = add(root, "shared", "alpha")
    assert r.returncode == 1 and "beta" in r.stderr
    assert add(root, "shared", "beta").returncode == 0


def test_use_and_list(root):
    add(root, "x", "alpha")
    _use_adds_consumer_only_to_registry(root)
    add(root, "y", "alpha", "--consumers", "b,c")
    r = cli("contract", "list", "--root", root)
    assert "y node owner=alpha file=src/a.py consumers=b,c" in r.stdout.splitlines()
    j = cli("contract", "list", "--root", root, "--json")
    assert {c["name"] for c in json.loads(j.stdout)} == {"x", "y"}


def _use_adds_consumer_only_to_registry(root):
    r = cli("contract", "use", "x", "--root", root, "--epic", "beta")
    assert r.returncode == 0, r.stderr
    cli("contract", "use", "x", "--root", root, "--epic", "beta")
    assert reg(root)[0]["consumers"] == ["beta"]
    assert sorted(p.name for p in root.iterdir()) == ["contracts.json"]


def test_use_unknown_fails(root):
    assert cli("contract", "use", "nope", "--root", root, "--epic", "b").returncode == 1


def test_list_empty(root):
    assert cli("contract", "list", "--root", root).stdout == ""


def test_load_contracts_reader(root):
    import contract

    assert contract.load_contracts(root) == []
    add(root, "x")
    assert contract.load_contracts(root)[0]["name"] == "x"
