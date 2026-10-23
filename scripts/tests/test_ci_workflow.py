"""Pins the GitHub Actions CI workflow: triggers, runner, SHA pins, commands, permissions."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
USES = re.compile(r"^\s*-?\s*uses:\s*(?P<action>[\w./-]+)@(?P<ref>\S+)\s*#\s*(?P<tag>v\d\S*)\s*$")


def _text() -> str:
    return WORKFLOW.read_text()


def _lines() -> list[str]:
    return _text().splitlines()


def test_triggers_are_push_and_pull_request():
    assert re.search(r"^on:\s*\n(?:\s+.*\n)*?\s+push:", _text(), re.M)
    assert re.search(r"^on:\s*\n(?:\s+.*\n)*?\s+pull_request:", _text(), re.M)


def test_runner_is_ubuntu_latest():
    assert "runs-on: ubuntu-latest" in _text()


def test_actions_are_pinned_by_full_sha_with_tag_comment():
    uses = [line for line in _lines() if "uses:" in line]
    found = {}
    for line in uses:
        m = USES.match(line)
        assert m, f"unpinned or uncommented action: {line!r}"
        assert re.fullmatch(r"[0-9a-f]{40}", m["ref"]), line
        found[m["action"]] = m["tag"]
    assert {"actions/checkout", "jdx/mise-action"} <= set(found)


def test_has_check_and_secrets_jobs():
    assert re.search(r"^jobs:\s*\n(?:.*\n)*?  check:", _text(), re.M)
    assert re.search(r"^  secrets:\s*$", _text(), re.M)
    assert re.search(r"^  e2e:\s*$", _text(), re.M)
    jobs = re.findall(r"^  ([\w-]+):\s*$", _text().split("\njobs:\n", 1)[1], re.M)
    assert jobs == ["check", "e2e", "secrets"]
    assert _text().count("runs-on: ubuntu-latest") == 3
    e2e = re.search(r"^  e2e:\s*\n((?:    .*\n|\s*\n)*)", _text(), re.M)
    assert e2e and re.search(r"^\s*-\s*run:\s*mise run e2e\s*$", e2e.group(1), re.M)


def test_runs_install_lint_and_test():
    text = _text()
    for cmd in ("mise install", "mise run lint", "mise run test"):
        assert re.search(rf"^\s*-\s*run:\s*{re.escape(cmd)}\s*$", text, re.M), cmd


def test_permissions_are_read_only_contents():
    assert re.search(r"^permissions:\s*\n\s+contents: read\s*$", _text(), re.M)
    assert not re.search(r"\b(write|admin)\b", _text())


def _check_job_steps(text: str) -> list[str]:
    m = re.search(r"^  check:\s*\n((?:    .*\n|\s*\n)*)", text, re.M)
    assert m, "no check job"
    return [s.strip() for s in re.findall(r"^\s*-\s*(?:run:\s*)?(.*)$", m.group(1), re.M)]


def _install_precedes(text: str) -> bool:
    steps = _check_job_steps(text)
    return (
        "mise install" in steps
        and steps.index("mise install") < steps.index("mise run lint")
        and steps.index("mise install") < steps.index("mise run test")
    )


def test_install_precedes_lint_and_test(tmp_path):
    assert _install_precedes(_text())
    broken = tmp_path / "ci.yml"
    broken.write_text(
        _text().replace(
            "      - run: mise install\n      - run: mise run lint\n",
            "      - run: mise run lint\n      - run: mise install\n",
            1,
        )
    )
    assert not _install_precedes(broken.read_text())
