"""deliver: argument and env handling, the ssh/scp command shapes, verify and discover parsing.

subprocess.run is replaced by a recorder, so nothing touches the network.
"""

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import deliver  # noqa: E402


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for k in ("PILL_NAS_HOST", "PILL_NAS_USER", "PILL_NAS_DIR", "PILL_NAS_PORT"):
        monkeypatch.delenv(k, raising=False)


@pytest.fixture
def pdf(tmp_path):
    f = tmp_path / "my-pill.pdf"
    f.write_bytes(b"%PDF-1.4 tiny")
    return f


class Recorder:
    def __init__(self, replies=None):
        self.calls = []
        self.replies = list(replies or [])

    def __call__(self, cmd, **kw):
        self.calls.append((cmd, kw))
        rc, out, err = self.replies.pop(0) if self.replies else (0, "", "")
        return subprocess.CompletedProcess(cmd, rc, out, err)


def _install(monkeypatch, rec):
    monkeypatch.setattr(deliver.subprocess, "run", rec)
    return rec


def test_send_without_dir_is_usage_error(monkeypatch, pdf, capsys):
    rec = _install(monkeypatch, Recorder())
    assert deliver.main(["send", str(pdf)]) == 2
    assert "discover" in capsys.readouterr().err
    assert rec.calls == []


def test_send_missing_file_and_bad_name(monkeypatch, pdf, tmp_path):
    rec = _install(monkeypatch, Recorder())
    assert deliver.main(["send", str(tmp_path / "nope.pdf"), "--dir", "/b"]) == 2
    assert deliver.main(["send", str(pdf), "--dir", "/b", "--name", "../x.pdf"]) == 2
    assert rec.calls == []


def test_send_defaults_and_success(monkeypatch, pdf, capsys):
    size = pdf.stat().st_size
    rec = _install(monkeypatch, Recorder([(0, "", ""), (0, "", ""), (0, f"  {size}\n", "")]))
    monkeypatch.setenv("PILL_NAS_DIR", "/volume1/Books/pills")
    assert deliver.main(["send", str(pdf)]) == 0
    (mkdir, _), (scp, _), (verify, _) = rec.calls
    assert mkdir[0] == "ssh" and "BatchMode=yes" in mkdir and mkdir[-2] == "nas.lan"
    assert mkdir[-1] == "mkdir -p -- /volume1/Books/pills"
    assert scp[0] == "scp" and "BatchMode=yes" in scp
    assert scp[-2:] == [str(pdf), "nas.lan:/volume1/Books/pills/my-pill.pdf"]
    assert verify[-1] == "wc -c < /volume1/Books/pills/my-pill.pdf"
    out = capsys.readouterr().out
    assert f"delivered: nas.lan:/volume1/Books/pills/my-pill.pdf ({size} bytes)" in out


def test_send_env_overrides_and_flags_win(monkeypatch, pdf):
    size = pdf.stat().st_size
    rec = _install(monkeypatch, Recorder([(0, "", ""), (0, "", ""), (0, str(size), "")]))
    monkeypatch.setenv("PILL_NAS_HOST", "envhost")
    monkeypatch.setenv("PILL_NAS_USER", "envuser")
    monkeypatch.setenv("PILL_NAS_DIR", "/env/dir")
    monkeypatch.setenv("PILL_NAS_PORT", "2222")
    argv = ["send", str(pdf), "--host", "flaghost", "--dir", "/my books", "--name", "x.pdf"]
    assert deliver.main(argv) == 0
    (mkdir, _), (scp, _), _ = rec.calls
    assert mkdir[-2] == "envuser@flaghost" and ["-p", "2222"] == mkdir[5:7]
    assert mkdir[-1] == "mkdir -p -- '/my books'"
    assert ["-P", "2222"] == scp[5:7]
    assert scp[-1] == "envuser@flaghost:/my books/x.pdf"


def test_send_size_mismatch_fails(monkeypatch, pdf, capsys):
    _install(monkeypatch, Recorder([(0, "", ""), (0, "", ""), (0, "3", "")]))
    assert deliver.main(["send", str(pdf), "--dir", "/b"]) == 1
    assert "size mismatch" in capsys.readouterr().err


def test_send_stops_on_first_failure(monkeypatch, pdf, capsys):
    rec = _install(monkeypatch, Recorder([(255, "", "Permission denied (publickey).")]))
    assert deliver.main(["send", str(pdf), "--dir", "/b"]) == 1
    assert len(rec.calls) == 1
    err = capsys.readouterr().err
    assert "mkdir failed" in err and "Permission denied" in err


def test_send_dry_run_runs_nothing(monkeypatch, pdf, capsys):
    rec = _install(monkeypatch, Recorder())
    assert deliver.main(["send", str(pdf), "--dir", "/b", "--dry-run"]) == 0
    assert rec.calls == []
    assert len(capsys.readouterr().out.strip().splitlines()) == 3


DISCOVER_OUT = "\n".join(
    [
        "MOUNT\tjellyfin\tjf\t/srv/jf/config\t/config",
        "MOUNT\tjellyfin\tjf\t/volume1/media\t/media",
        "MOUNT\taudiobookshelf\tabs\t/volume1/media/audiobooks\t/audiobooks",
        "MOUNT\taudiobookshelf\tabs\t/volume1/media/books\t/books",
        "JELLYFIN\tMovies\t/media/movies",
        "JELLYFIN\tBooks\t/media/books",
        "ABS\tAudiobooks\t/audiobooks",
        "ABS\tEbooks\t/books/pills",
        "NOTE\tsomething odd",
    ]
)


def test_discover_maps_and_ranks(monkeypatch, capsys):
    rec = _install(monkeypatch, Recorder([(0, DISCOVER_OUT, "")]))
    assert deliver.main(["discover", "--user", "admin"]) == 0
    cmd, kw = rec.calls[0]
    assert cmd[0] == "ssh" and cmd[-2:] == ["admin@nas.lan", "sh -s"]
    assert kw["input"] == deliver.DISCOVER_SH
    out = capsys.readouterr().out.splitlines()
    assert "note: something odd" in out
    rows = [line.split("\t") for line in out if line.startswith("/")]
    assert [r[0] for r in rows[:2]] == ["/volume1/media/books/pills", "/volume1/media/books"]
    assert rows[-1][0] == "/volume1/media/movies"
    assert out[-1] == "suggested: PILL_NAS_DIR=/volume1/media/books/pills"


def test_discover_without_docker_keeps_native_paths():
    cands, notes = deliver.parse_discover("NOTE\tdocker not usable\nJELLYFIN\tBooks\t/data/books\n")
    assert notes == ["docker not usable"]
    assert cands[0]["host_path"] == "/data/books"


def test_discover_nothing_found(monkeypatch, capsys):
    _install(monkeypatch, Recorder([(0, "", "")]))
    assert deliver.main(["discover"]) == 1
    assert "no Jellyfin or Audiobookshelf" in capsys.readouterr().err


def test_discover_ssh_failure(monkeypatch, capsys):
    _install(monkeypatch, Recorder([(255, "", "ssh: Could not resolve hostname")]))
    assert deliver.main(["discover"]) == 1
    assert "discover failed" in capsys.readouterr().err


def test_to_host_path_longest_prefix():
    mounts = [("/a", "/media"), ("/b", "/media/books"), ("/r", "/")]
    assert deliver.to_host_path("/media/books/x", mounts) == "/b/x"
    assert deliver.to_host_path("/media/tv", mounts) == "/a/tv"
    assert deliver.to_host_path("/other", mounts) == "/r/other"
    assert deliver.to_host_path("/mediax", [("/a", "/media")]) is None


def test_discover_script_is_read_only():
    banned = (
        " rm ",
        "mv ",
        "mkdir",
        "chmod",
        "chown",
        "> /",
        "tee ",
        "docker exec",
        "INSERT",
        "UPDATE",
        "DELETE",
    )
    for word in banned:
        assert word not in deliver.DISCOVER_SH, word
    assert "mode=ro" in deliver.DISCOVER_SH and "-readonly" in deliver.DISCOVER_SH
