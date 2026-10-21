"""ticket.py graph --todo and epic_graph (D8)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "start-development" / "scripts" / "ticket.py"


def cli(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True
    )


@pytest.fixture
def root(tmp_path):
    r = tmp_path / "plans"
    r.mkdir()
    return r


def epic(root, slug, phase="todo", blockers=(), uses=None):
    d = root / phase / slug
    (d / "tasks").mkdir(parents=True)
    bl = "[" + ", ".join(blockers) + "]"
    (d / "README.md").write_text(f"---\ntitle: {slug}\nblockers: {bl}\n---\n")
    if uses:
        (d / "tasks" / "t.md").write_text(f"---\ntitle: t\nuses: [{uses}]\n---\nb\n")


def contract(root, name, owner, consumers=()):
    (root / "contracts.json").write_text(
        json.dumps(
            [
                {
                    "name": name,
                    "kind": "node",
                    "owner": owner,
                    "file": "f",
                    "consumers": list(consumers),
                    "note": "",
                }
            ]
        )
    )


def graph(root):
    return cli("graph", "--todo", "--root", root)


def test_graph_ok(root):
    epic(root, "a")
    epic(root, "b", blockers=["a"])
    contract(root, "x", "a", ["b"])
    r = graph(root)
    assert (r.returncode, r.stdout.strip()) == (0, "graph: ok")


def test_cycle_reported(root):
    epic(root, "a", blockers=["b"])
    epic(root, "b", blockers=["a"])
    r = graph(root)
    assert r.returncode == 1 and "cycle: a -> b -> a" in r.stdout


def test_owner_after_consumer(root):
    epic(root, "own", blockers=["con"])
    epic(root, "con")
    contract(root, "x", "own", ["con"])
    r = graph(root)
    assert r.returncode == 1
    assert "contract x: owner own comes after consumer con" in r.stdout


def test_consumer_not_blocked_by_owner(root):
    epic(root, "own")
    epic(root, "con")
    contract(root, "x", "own", ["con"])
    r = graph(root)
    assert r.returncode == 1
    assert "contract x: consumer con is not blocked by owner own" in r.stdout


def test_transitive_and_uses_consumer(root):
    epic(root, "own")
    epic(root, "mid", blockers=["own"])
    epic(root, "con", blockers=["mid"], uses="x")
    contract(root, "x", "own")
    assert graph(root).stdout.strip() == "graph: ok"


def test_uses_consumer_unblocked(root):
    epic(root, "own")
    epic(root, "con", uses="x")
    contract(root, "x", "own")
    assert "consumer con is not blocked by owner own" in graph(root).stdout


def test_done_owner_is_fine(root):
    epic(root, "own", "done")
    epic(root, "con")
    contract(root, "x", "own", ["con"])
    assert graph(root).returncode == 0


def test_runnable_set(root):
    import importlib.util

    sys.path.insert(0, str(SCRIPT.parent))
    import ticket

    path = SCRIPT.parent / "ticket_cmds" / "graph.py"
    spec = importlib.util.spec_from_file_location("graph_mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod._T = ticket
    epic(root, "d", "done")
    epic(root, "a", blockers=["d"])
    epic(root, "b", blockers=["a"])
    epic(root, "c", "in-progress")
    g = mod.epic_graph(root)
    assert g["runnable"] == ["a"]
    assert ["b", "a"] in g["edges"] and g["cycles"] == []
    assert g["epics"]["c"] == "in-progress"
