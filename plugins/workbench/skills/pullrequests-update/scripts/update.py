#!/usr/bin/env python3
"""Create or update PRs and MRs for a branch across repos, with cross-linking.

The host (GitHub or GitLab) is detected per repo from its origin, so one run
can mix both. Every gh and glab call goes through scm.adapter_for.

Two-pass, agent-in-the-loop: the agent supplies a short body per repo via
--body repo=text. Pass 1 creates or edits each PR/MR with that body. Pass 2
rewrites every body to include a "Complementary PRs" (GitHub) or "Complementary
MRs" (GitLab) section linking the other PRs/MRs from this run, on either host.
A repo with no PR/MR host (local-only) is a skipped row, not a failure.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_lib"))
import common  # noqa: E402
import scm  # noqa: E402


def pr_title(body: str, branch: str) -> str:
    for line in body.splitlines():
        line = line.strip()
        if line:
            return line
    return branch


def _parse_pairs(values: list) -> dict:
    pairs = {}
    for item in values:
        repo, sep, text = item.partition("=")
        if sep:
            pairs[repo] = text
    return pairs


def apply_semver(adapter: scm.Adapter, n, level: str) -> tuple[str, bool]:
    """Apply (or skip) a semver:<level> label. Returns (outcome text, failed)."""
    if level not in scm.VALID_SEMVER_LEVELS:
        return f"semver failed (invalid level: {level})", True
    try:
        existing = adapter.semver_label(n)
    except common.RepoError as e:
        return f"semver failed (cannot read labels: {e})", True
    if existing:
        return f"semver skipped (has semver:{existing})", False
    try:
        adapter.ensure_label(level)
        adapter.apply_label(n, level)
    except common.RepoError as e:
        return f"semver failed ({adapter.cli} label failed: {e})", True
    return f"semver:{level} applied", False


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", required=True)
    parser.add_argument("--repos", required=True)
    parser.add_argument("--body", action="append", default=[], metavar="repo=text")
    parser.add_argument("--semver", action="append", default=[], metavar="repo=LEVEL")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        scm.host_map()
    except scm.HostMapError as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)
    repos = common.parse_repos(args.repos)
    bodies = _parse_pairs(args.body)
    semver_levels = _parse_pairs(args.semver)
    report = common.Report()

    pass1 = {}
    for repo in repos:
        if repo not in bodies:
            report.add(repo, "failed", "missing --body for repo")
            continue
        body = bodies[repo]
        try:
            adapter = scm.adapter_for(repo)
            if adapter is None:
                report.add(repo, "skipped", f"local-only: no PR/MR host for {scm.origin_url(repo)}")
                continue
            existing = adapter.find_open(args.branch)
            if existing:
                n, url = existing
                adapter.edit_body(n, body)
                status = "updated"
            else:
                url = adapter.create(args.branch, pr_title(body, args.branch), body)
                n = scm.number_from_url(url)
                status = "created"
        except common.RepoError as e:
            report.add(repo, "failed", f"PR/MR create/edit failed: {e}")
            continue
        pass1[repo] = {"adapter": adapter, "n": n, "url": url, "status": status}

    semver_failed = False
    for repo, info in pass1.items():
        adapter = info["adapter"]
        siblings = [v["url"] for r, v in pass1.items() if r != repo]
        combined = bodies[repo]
        if siblings:
            combined += f"\n\n## Complementary {adapter.noun}s\n"
            combined += "\n".join(f"- {u}" for u in siblings)
        try:
            adapter.edit_body(info["n"], combined)
        except common.RepoError as e:
            report.add(repo, "failed", f"cross-link update failed: {e}")
            continue

        if repo in semver_levels:
            outcome, failed = apply_semver(adapter, info["n"], semver_levels[repo])
            semver_failed = semver_failed or failed
        else:
            outcome = "-"
        report.add(repo, info["status"], f"{info['url']} | {outcome}")

    print(report.render())
    sys.exit(1 if (report.exit_code or semver_failed) else 0)


if __name__ == "__main__":
    main()
