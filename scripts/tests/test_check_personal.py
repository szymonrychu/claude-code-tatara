"""Pins the personal-reference lint on fixture trees in temp git repos.

No private term appears here: fixtures use a throwaway term and its digest,
built at run time.
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "check_personal.py"
DENYLIST = SCRIPT.parent / "personal-denylist.json"
TERM = "zorblax"
SPLIT = "zor-blax-qux"


def _h(term: str) -> str:
    return hashlib.sha256(term.encode()).hexdigest()


def _repo(tmp_path: Path, files: dict[str, str | bytes], *, untracked=(), cfg=None) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    files = dict(files)
    if cfg is not None:
        files["scripts/personal-denylist.json"] = json.dumps(cfg)
    for name, body in files.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body if isinstance(body, bytes) else body.encode())
        if name not in untracked:
            subprocess.run(["git", "-C", str(tmp_path), "add", name], check=True)
    return tmp_path


def _run(root: Path):
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)], capture_output=True, text=True
    )
    return r.returncode, r.stdout.splitlines()


def _cfg(**kw):
    return {"patterns": [], "hashes": [_h(TERM), _h(SPLIT)], "allow": [], **kw}


def test_clean_tree_exits_zero(tmp_path):
    root = _repo(tmp_path, {"a.md": "nothing personal here\n"}, cfg=_cfg())
    assert _run(root) == (0, [])


@pytest.mark.parametrize(
    "text,term",
    [
        (f"hi {TERM.title()}", TERM),
        (f"x {TERM.upper()}, y", TERM),
        (f"path/{TERM}/file", TERM),
        (f"a {SPLIT} b", SPLIT),
        (f"a {SPLIT.upper()}-more", SPLIT),
    ],
)
def test_hash_hit_reports_digest_not_term(tmp_path, text, term):
    root = _repo(tmp_path, {"d/f.txt": f"ok\n{text}\n"}, cfg=_cfg())
    code, out = _run(root)
    assert code == 1
    assert out == [f"d/f.txt:2: {_h(term)}"]
    assert term not in "".join(out).lower()


@pytest.mark.parametrize(
    "text",
    [f"{TERM}s", f"un{TERM}", "zor blax", "zor-blax", "a_zorblax_b", f"{TERM}x-y", "zorblaxe"],
)
def test_word_boundaries(tmp_path, text):
    root = _repo(tmp_path, {"f.txt": text + "\n"}, cfg=_cfg())
    assert _run(root) == (0, [])


@pytest.mark.parametrize(
    "text,name",
    [
        ("/Users/bob/x", "/Users/"),
        ("ip 192.168.1.5", "192.168."),
        ("cd /home/alice/code", "/home/<name>"),
        ("nas.lan", ".lan"),
        ("harbor.example.com", "harbor."),
    ],
)
def test_shipped_generic_patterns_hit(tmp_path, text, name):
    shipped = json.loads(DENYLIST.read_text())
    root = _repo(tmp_path, {"d/f.txt": f"ok\n{text}\n"}, cfg=shipped)
    assert _run(root) == (1, [f"d/f.txt:2: {name}"])


@pytest.mark.parametrize(
    "text", ["/home/user/project", "plan.lang and file.lanes", "the harbor. Next"]
)
def test_shipped_generic_patterns_miss(tmp_path, text):
    shipped = json.loads(DENYLIST.read_text())
    root = _repo(tmp_path, {"f.txt": text + "\n"}, cfg=shipped)
    assert _run(root) == (0, [])


def test_tracked_only(tmp_path):
    root = _repo(tmp_path, {"u.txt": TERM, "ok.txt": "fine"}, untracked=("u.txt",), cfg=_cfg())
    assert _run(root) == (0, [])


def test_binary_and_undecodable_files_skipped(tmp_path):
    root = _repo(
        tmp_path,
        {"b.bin": b"\x00\x01" + TERM.encode(), "bad.txt": b"\xff\xfe" + TERM.encode()},
        cfg=_cfg(),
    )
    assert _run(root) == (0, [])


def test_allowlist_by_digest_and_line(tmp_path):
    cfg = _cfg(
        allow=[
            {"path": "LICENSE", "pattern": _h(TERM), "line_contains": "Copyright"},
            {"path": "README.md", "pattern": _h(TERM), "line_contains": "/workbench"},
            {"path": "docs/**"},
            {"path": "scripts/*.json"},
        ]
    )
    files = {
        "LICENSE": f"Copyright {TERM}\nmore {TERM} text\n",
        "README.md": f"clone host/{TERM}/workbench\nalso {TERM}\n",
        "docs/a/b.md": TERM,
        "other.py": TERM,
    }
    root = _repo(tmp_path, files, cfg=cfg)
    assert sorted(_run(root)[1]) == sorted(
        [f"LICENSE:2: {_h(TERM)}", f"README.md:2: {_h(TERM)}", f"other.py:1: {_h(TERM)}"]
    )


def test_custom_denylist_in_root_is_used(tmp_path):
    cfg = {
        "patterns": ["foo"],
        "allow": [{"path": "ok/*", "pattern": "foo"}, {"path": "scripts/*.json"}],
    }
    root = _repo(tmp_path, {"ok/a.txt": "foo", "bad/a.txt": f"foo\n{TERM}"}, cfg=cfg)
    assert _run(root) == (1, ["bad/a.txt:1: foo"])


LOCAL = "scripts/personal-allow.local.json"


def test_local_allow_file_accepts_project_vocabulary(tmp_path):
    local = json.dumps({"allow": [{"path": "docs/a.md", "pattern": _h(TERM)}]})
    root = _repo(tmp_path, {"docs/a.md": f"{TERM}\n", "b.md": TERM, LOCAL: local}, cfg=_cfg())
    assert _run(root) == (1, [f"b.md:1: {_h(TERM)}"])


def test_local_allow_file_only_adds(tmp_path):
    files = {"a.md": f"{TERM} foo\n"}
    cfg = _cfg(patterns=["foo"], allow=[{"path": "scripts/*.json"}])
    root = _repo(tmp_path / "plain", files, cfg=cfg)
    assert _run(root) == (1, ["a.md:1: foo", f"a.md:1: {_h(TERM)}"])
    local = json.dumps(
        {"allow": [{"path": "a.md", "pattern": _h(TERM)}], "patterns": [], "hashes": []}
    )
    root = _repo(tmp_path / "local", {**files, LOCAL: local}, cfg=cfg)
    assert _run(root) == (1, ["a.md:1: foo"])
    assert not (SCRIPT.parent / "personal-allow.local.json").exists()


def test_shipped_denylist_is_hashed_only():
    assert not (SCRIPT.parent / "personal-allow.local.json").exists()
    data = json.loads(DENYLIST.read_text())
    assert len(data["hashes"]) == 19
    assert all(len(h) == 64 and set(h) <= set("0123456789abcdef") for h in data["hashes"])
    assert {p if isinstance(p, str) else p["name"] for p in data["patterns"]} == {
        "/Users/",
        "/home/<name>",
        "harbor.",
        "192.168.",
        ".lan",
    }
    assert {a["path"] for a in data["allow"]} == {
        "LICENSE",
        "plugins/*/LICENSE",
        "README.md",
        "scripts/init_engine/*.py",
        "scripts/tests/init_engine/*.py",
        "docs/plans/**",
        "scripts/personal-denylist.json",
        "scripts/tests/test_check_personal.py",
    }


def test_shipped_tree_is_clean():
    root = SCRIPT.parents[1]
    assert _run(root) == (0, [])


def test_hashed_term_detected_without_echo(tmp_path):
    root = _repo(tmp_path, {"notes.txt": f"see {TERM.title()} here\n"}, cfg=_cfg())
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)], capture_output=True, text=True
    )
    assert r.returncode == 1
    assert _h(TERM) in r.stdout
    assert TERM not in (r.stdout + r.stderr).lower()
    assert all(TERM not in h for h in json.loads(DENYLIST.read_text())["hashes"])
