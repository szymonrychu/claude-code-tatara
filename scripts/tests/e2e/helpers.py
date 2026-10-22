"""Shared e2e helpers."""

import json
import os
import random
import string
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def run(*args, cwd, check=True, **kw):
    p = subprocess.run(list(args), cwd=cwd, capture_output=True, text=True, **kw)
    if check:
        assert p.returncode == 0, f"{args}: {p.stdout}\n{p.stderr}"
    return p


def git(*args, cwd):
    return run("git", *args, cwd=cwd).stdout.strip()


def denylist_terms(tree: Path, *terms: str) -> None:
    """Add the digests of `terms` to the copy's denylist and commit, so the copy's own
    lint:personal rejects those words until init records them as project vocabulary."""
    sys.path.insert(0, str(REPO / "scripts"))
    from check_personal import DENYLIST, _digest  # noqa: PLC0415

    path = tree / DENYLIST
    cfg = json.loads(path.read_text())
    cfg["hashes"] = sorted({*cfg.get("hashes", []), *(_digest(t.lower()) for t in terms)})
    path.write_text(json.dumps(cfg, indent=2) + "\n")
    git("add", "-A", cwd=tree)
    git("commit", "-q", "-m", "denylist test terms", cwd=tree)


def secret_shaped() -> str:
    """A GitHub-token-shaped string built at run time, so no literal sits in this repo."""
    return "ghp_" + "".join(random.Random(7).choices(string.ascii_letters + string.digits, k=36))


def production_env() -> dict:
    """The e2e environment minus the file-transport grant: suites that assert production git
    behaviour must not see protocol.file.allow."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_CONFIG_")}
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    return env
