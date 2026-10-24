"""Pin: the only scratch and log locations the tooling names are `.scratchpad` and `.logs`
of the workbench root (design D6). Tracked non-test files of plugins/, scripts/ and
mise-tasks/ must not name /tmp/, TMPDIR, mktemp or a bare "the scratchpad" outside ALLOW."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from check_personal import _text, _tracked  # noqa: E402

HIT = re.compile(r"/tmp/|TMPDIR|mktemp|the scratchpad", re.IGNORECASE)
SCOPE = ("plugins/", "scripts/", "mise-tasks/")

_FALLBACK = "no-main-checkout fallback: with no checkout there is no .logs to land in"
ALLOW = {
    "plugins/workbench/skills/worktree-merge/scripts/suite-lock.sh":
        "transient lock dir created and removed within one run",
    "mise-tasks/lint/secrets": "transient staging dir created and removed within one run",
    "scripts/probes/claude-plugin-load.sh": "transient probe dir removed within one run",
    "plugins/workbench/scripts/run-tests.sh": _FALLBACK,
    "plugins/workbench/scripts/flake-hunt.sh": _FALLBACK,
    "plugins/workbench/hooks/worktree_lib.py": _FALLBACK,
    "plugins/workbench/hooks/bash-output-filter.py": _FALLBACK + " (docstring)",
    "plugins/workbench/skills/start-development/references/hooks.md": _FALLBACK + " (documented)",
}


def _scanned():
    for rel in _tracked(ROOT):
        parts = rel.split("/")
        if not rel.startswith(SCOPE) or "tests" in parts[:-1] or "CHANGELOG" in parts[-1].upper():
            continue
        yield rel


def test_scratch_and_log_locations():
    hits = {}
    for rel in _scanned():
        text = _text(ROOT / rel)
        if text and HIT.search(text):
            hits[rel] = [n for n, ln in enumerate(text.splitlines(), 1) if HIT.search(ln)]
    unexpected = {p: ls for p, ls in hits.items() if p not in ALLOW}
    assert not unexpected, f"name .scratchpad or .logs of the workbench root instead: {unexpected}"
    stale = sorted(p for p in ALLOW if p not in hits)
    assert not stale, f"allowlist entries with no real hit: {stale}"
    assert all(r.strip() for r in ALLOW.values())
