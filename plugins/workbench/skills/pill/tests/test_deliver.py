"""deliver: pod json parsing, parent-mount derivation, ranking and the kubectl command shapes.

subprocess.run is replaced by a recorder, so nothing touches a cluster.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import deliver  # noqa: E402

ENV = (
    "PILL_K8S_NAMESPACE",
    "PILL_K8S_POD",
    "PILL_K8S_SELECTOR",
    "PILL_K8S_CONTAINER",
    "PILL_K8S_DIR",
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for k in ENV:
        monkeypatch.delenv(k, raising=False)


@pytest.fixture
def pdf(tmp_path):
    f = tmp_path / "my-pill.pdf"
    f.write_bytes(b"%PDF-1.4 tiny")
    return f


def pod(name, container, mounts, phase="Running"):
    """mounts: (mountPath, volume source dict, readOnly[, subPath])."""
    vms, vols = [], []
    for i, m in enumerate(mounts):
        vm = {"name": f"v{i}", "mountPath": m[0]}
        if m[2]:
            vm["readOnly"] = True
        if len(m) > 3:
            vm["subPath"] = m[3]
        vms.append(vm)
        vols.append({"name": f"v{i}", **m[1]})
    return {
        "metadata": {"name": name},
        "spec": {"containers": [{"name": container, "volumeMounts": vms}], "volumes": vols},
        "status": {"phase": phase},
    }


def hp(path):
    return {"hostPath": {"path": path}}


CLUSTER = {
    "items": [
        pod(
            "audiobookshelf-abc",
            "audiobookshelf",
            [
                ("/config", {"persistentVolumeClaim": {"claimName": "abs-config"}}, False),
                ("/books", hp("/media/hdd/books"), True),
                ("/audiobooks", hp("/media/hdd/audiobooks"), True),
            ],
        ),
        pod(
            "jellyfin-xyz",
            "jellyfin",
            [("/config", hp("/data/jf"), False), ("/media", hp("/media/hdd"), False)],
        ),
        pod("navidrome-1", "navidrome", [("/media", hp("/media/hdd"), True)]),
        pod("sonarr-1", "sonarr", [("/media", hp("/media/hdd"), False)]),
        pod("beets-job", "beets", [("/media", hp("/media/hdd"), False)], phase="Succeeded"),
    ]
}


class Recorder:
    def __init__(self, replies=None):
        self.calls = []
        self.replies = list(replies or [])

    def __call__(self, cmd, **kw):
        self.calls.append(cmd)
        rc, out, err = self.replies.pop(0) if self.replies else (0, "", "")
        return subprocess.CompletedProcess(cmd, rc, out, err)


def _install(monkeypatch, replies):
    rec = Recorder(replies)
    monkeypatch.setattr(deliver.subprocess, "run", rec)
    return rec


GET = (0, json.dumps(CLUSTER), "")


def test_parent_mount_derives_books_dir_and_ranks_writable_first():
    cands = deliver.candidates(deliver.mounts_of(CLUSTER["items"]), "books")
    best = cands[0]
    assert (best.pod, best.container, best.dir, best.node_path) == (
        "jellyfin-xyz",
        "jellyfin",
        "/media/books",
        "/media/hdd/books",
    )
    assert best.source == "derived" and not best.read_only
    assert all(not c.read_only for c in cands[:4]) and all(c.read_only for c in cands[4:])
    # audiobooks rank after books among writable ones
    assert [c.dir for c in cands[:4]] == [
        "/media/books",
        "/media/books",
        "/media/audiobooks",
        "/media/audiobooks",
    ]
    assert not any(c.pod == "beets-job" for c in cands)
    direct = [c for c in cands if c.source == "direct"]
    assert {(c.pod, c.dir) for c in direct} == {
        ("audiobookshelf-abc", "/books"),
        ("audiobookshelf-abc", "/audiobooks"),
    }


def test_subpath_and_pvc_readonly():
    p = pod(
        "x",
        "x",
        [
            ("/lib", hp("/srv"), False, "books"),
            ("/ro", {"persistentVolumeClaim": {"claimName": "c", "readOnly": True}}, False),
        ],
    )
    m = deliver.mounts_of([p])
    assert m[0].host_path == "/srv/books" and not m[0].read_only
    assert m[1].pvc == "c" and m[1].read_only and m[1].host_path is None


def test_discover_prints_table_and_suggestion(monkeypatch, capsys):
    rec = _install(monkeypatch, [GET])
    assert deliver.main(["discover"]) == 0
    assert rec.calls == [["kubectl", "-n", "media", "get", "pods", "-o", "json"]]
    out = capsys.readouterr().out.splitlines()
    assert (
        out[1] == "rw\tjellyfin-xyz\tjellyfin\t/media/books\t/media/hdd/books\tderived from /media"
    )
    assert "ro\taudiobookshelf-abc\taudiobookshelf\t/books\t/media/hdd/books\tdirect" in out
    assert out[-1] == (
        "suggested: PILL_K8S_NAMESPACE=media PILL_K8S_POD=jellyfin-xyz "
        "PILL_K8S_CONTAINER=jellyfin PILL_K8S_DIR=/media/books"
    )


def test_discover_namespace_selector_match(monkeypatch):
    rec = _install(monkeypatch, [GET])
    monkeypatch.setenv("PILL_K8S_NAMESPACE", "lib")
    assert deliver.main(["discover", "-l", "app=x", "--match", "audiobooks"]) == 0
    assert rec.calls[0] == ["kubectl", "-n", "lib", "get", "pods", "-o", "json", "-l", "app=x"]


def test_discover_only_readonly_has_no_suggestion(monkeypatch, capsys):
    only_ro = {"items": [CLUSTER["items"][0]]}
    _install(monkeypatch, [(0, json.dumps(only_ro), "")])
    assert deliver.main(["discover"]) == 0
    cap = capsys.readouterr()
    assert "suggested" not in cap.out and "read-only" in cap.err


def test_discover_nothing_and_kubectl_failure(monkeypatch, capsys):
    _install(monkeypatch, [(0, '{"items": []}', "")])
    assert deliver.main(["discover"]) == 1
    assert "no running pod" in capsys.readouterr().err
    _install(monkeypatch, [(1, "", "error: You must be logged in")])
    assert deliver.main(["discover"]) == 1
    assert "kubectl get pods failed" in capsys.readouterr().err


def test_send_auto_target_success(monkeypatch, pdf, capsys):
    size = pdf.stat().st_size
    rec = _install(
        monkeypatch, [GET, (0, "tar 1.34", ""), (0, "", ""), (0, "", ""), (0, f"{size}\n", "")]
    )
    assert deliver.main(["send", str(pdf)]) == 0
    get, tar, mkdir, cp, stat = rec.calls
    ex = ["kubectl", "-n", "media", "exec", "jellyfin-xyz", "-c", "jellyfin", "--"]
    assert tar == ex + ["tar", "--version"]
    assert mkdir == ex + ["mkdir", "-p", "--", "/media/books"]
    assert cp == [
        "kubectl",
        "cp",
        str(pdf),
        "media/jellyfin-xyz:/media/books/my-pill.pdf",
        "-c",
        "jellyfin",
    ]
    assert stat == ex + ["stat", "-c", "%s", "/media/books/my-pill.pdf"]
    out = capsys.readouterr().out
    assert (
        f"delivered: media/jellyfin-xyz:/media/books/my-pill.pdf (container jellyfin, {size} bytes)"
        in out
    )
    assert "node path: /media/hdd/books/my-pill.pdf" in out


def test_send_never_mutates_beyond_target(monkeypatch, pdf):
    rec = _install(
        monkeypatch, [GET, (0, "", ""), (0, "", ""), (0, "", ""), (0, str(pdf.stat().st_size), "")]
    )
    assert deliver.main(["send", str(pdf)]) == 0
    verbs = [c[1:6] if c[1] == "-n" else c[1:2] for c in rec.calls]
    flat = " ".join(" ".join(v) for v in verbs)
    for banned in ("apply", "delete", "rollout", "patch", "scale", "edit", "label", "annotate"):
        assert banned not in flat


def test_send_env_pod_prefix_dir_and_name(monkeypatch, pdf, capsys):
    size = pdf.stat().st_size
    rec = _install(monkeypatch, [GET, (0, "", ""), (0, "", ""), (0, "", ""), (0, str(size), "")])
    monkeypatch.setenv("PILL_K8S_POD", "sonarr")
    monkeypatch.setenv("PILL_K8S_DIR", "/media/books/pills")
    assert deliver.main(["send", str(pdf), "--name", "x.pdf"]) == 0
    assert rec.calls[2][-1] == "/media/books/pills" and rec.calls[2][4] == "sonarr-1"
    assert rec.calls[3][3] == "media/sonarr-1:/media/books/pills/x.pdf"
    assert "node path: /media/hdd/books/pills/x.pdf" in capsys.readouterr().out


def test_send_dir_at_mount_root_skips_mkdir(monkeypatch, pdf):
    size = pdf.stat().st_size
    rec = _install(monkeypatch, [GET, (0, "", ""), (0, "", ""), (0, str(size), "")])
    assert deliver.main(["send", str(pdf), "--dir", "/media", "--pod", "jellyfin"]) == 0
    assert not any("mkdir" in c for c in rec.calls)


def test_send_skips_readonly_mount(monkeypatch, pdf, capsys):
    rec = _install(monkeypatch, [GET])
    argv = ["send", str(pdf), "--pod", "audiobookshelf", "--dir", "/books"]
    assert deliver.main(argv) == 2
    assert "no selected container mounts /books writable" in capsys.readouterr().err
    assert len(rec.calls) == 1
    rec = _install(monkeypatch, [GET])
    argv += ["-c", "audiobookshelf"]
    assert deliver.main(argv) == 2
    assert "read-only mount (/books)" in capsys.readouterr().err
    assert len(rec.calls) == 1


def test_send_auto_target_ignores_readonly(monkeypatch, pdf, capsys):
    _install(monkeypatch, [GET])
    assert deliver.main(["send", str(pdf), "--pod", "navidrome"]) == 2
    assert "no writable mount" in capsys.readouterr().err


def test_send_size_mismatch_fails(monkeypatch, pdf, capsys):
    _install(monkeypatch, [GET, (0, "", ""), (0, "", ""), (0, "", ""), (0, "3\n", "")])
    assert deliver.main(["send", str(pdf)]) == 1
    assert "size mismatch" in capsys.readouterr().err


def test_send_stat_fallback_to_ls(monkeypatch, pdf, capsys):
    size = pdf.stat().st_size
    ls = f"-rw-r--r-- 1 1000 1000 {size} Nov 4 12:00 /media/books/my-pill.pdf"
    rec = _install(
        monkeypatch,
        [GET, (0, "", ""), (0, "", ""), (0, "", ""), (1, "", "stat: not found"), (0, ls, "")],
    )
    assert deliver.main(["send", str(pdf)]) == 0
    assert rec.calls[-1][-2:] == ["-ln", "/media/books/my-pill.pdf"]
    ls_bad = ls.replace(str(size), "1")
    _install(
        monkeypatch, [GET, (0, "", ""), (0, "", ""), (0, "", ""), (1, "", ""), (0, ls_bad, "")]
    )
    assert deliver.main(["send", str(pdf)]) == 1
    assert "size mismatch" in capsys.readouterr().err


def test_send_verify_failure(monkeypatch, pdf, capsys):
    _install(
        monkeypatch,
        [GET, (0, "", ""), (0, "", ""), (0, "", ""), (1, "", ""), (1, "", "No such file")],
    )
    assert deliver.main(["send", str(pdf)]) == 1
    assert "verify failed" in capsys.readouterr().err


def test_send_no_tar(monkeypatch, pdf, capsys):
    nf = (126, "", 'exec: "tar": executable file not found in $PATH')
    rec = _install(monkeypatch, [GET, nf, nf])
    assert deliver.main(["send", str(pdf)]) == 1
    assert "kubectl cp needs tar" in capsys.readouterr().err
    assert not any(c[:2] == ["kubectl", "cp"] for c in rec.calls)


def test_send_cp_failure_stops(monkeypatch, pdf, capsys):
    rec = _install(
        monkeypatch, [GET, (0, "", ""), (0, "", ""), (1, "", "error: permission denied")]
    )
    assert deliver.main(["send", str(pdf)]) == 1
    assert len(rec.calls) == 4
    err = capsys.readouterr().err
    assert "kubectl cp failed" in err and "permission denied" in err


def test_send_usage_errors(monkeypatch, pdf, tmp_path, capsys):
    rec = _install(monkeypatch, [])
    assert deliver.main(["send", str(tmp_path / "nope.pdf")]) == 2
    assert deliver.main(["send", str(pdf), "--name", "../x.pdf"]) == 2
    assert rec.calls == []
    _install(monkeypatch, [GET])
    assert deliver.main(["send", str(pdf), "--pod", "nothere"]) == 2
    assert "no running pod 'nothere'" in capsys.readouterr().err


def test_send_dry_run_reads_only(monkeypatch, pdf, capsys):
    rec = _install(monkeypatch, [GET])
    assert deliver.main(["send", str(pdf), "--dry-run"]) == 0
    assert len(rec.calls) == 1 and rec.calls[0][3:5] == ["get", "pods"]
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 4 and lines[2].startswith("kubectl cp ")


def test_under():
    assert deliver.under("/media/books", "/media") == "books"
    assert deliver.under("/media", "/media/") == ""
    assert deliver.under("/mediax", "/media") is None
    assert deliver.under("/a/b", "/") == "a/b"
