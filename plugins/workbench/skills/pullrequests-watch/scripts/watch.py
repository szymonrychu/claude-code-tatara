"""Report PR/MR state, checks, and mergeability across code/ submodules, GitHub or GitLab.

The host is picked per repo from its origin (scm.adapter_for), so one run can mix
GitHub PRs and GitLab MRs. Every gh/glab call goes through the scm adapter.
"""

import argparse
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_lib"))

import common  # noqa: E402
import scm  # noqa: E402

PR_PAIR_RE = re.compile(r"^(?P<repo>[^#]+)#(?P<num>\d+)$")
SHA_PAIR_RE = re.compile(r"^(?P<repo>[^=]+)=(?P<sha>[0-9a-fA-F]+)$")

# A target the watch loop polls: (repo, its adapter, PR/MR number).
Target = tuple[str, scm.Adapter, int]
# A deploy target: (repo, its adapter, branch, pinned sha or None,
# detail prefix: "mr !N deploy" with --prs, "deploy" in branch mode).
DeployTarget = tuple[str, scm.Adapter, str, str | None, str]


def _now() -> float:
    return time.monotonic()


def _sleep(seconds: float) -> None:
    time.sleep(seconds)


def parse_pr_pairs(value) -> list[tuple[str, int]]:
    pairs = []
    for item in common.parse_repos(value):
        m = PR_PAIR_RE.match(item)
        if not m:
            raise common.RepoError(f"invalid --prs entry: {item}")
        pairs.append((m.group("repo"), int(m.group("num"))))
    return pairs


def parse_sha_pairs(value) -> dict[str, str]:
    pairs = {}
    for item in common.parse_repos(value):
        m = SHA_PAIR_RE.match(item)
        if not m:
            raise common.RepoError(f"invalid --sha entry: {item}")
        pairs[m.group("repo")] = m.group("sha")
    return pairs


def verdict_for(poll: dict, elapsed: float, grace: float) -> str:
    state = poll["state"]
    if state == "MERGED":
        return "merged"
    if state == "CLOSED":
        return "closed"
    if poll["mergeable"] == "conflict":
        return "conflict"
    checks = poll["checks"]
    if checks == "failed":
        return "failed"
    if checks == "passed":
        return "passed"
    if checks == "none":
        return "no-pipeline" if elapsed >= grace else "pending"
    return "pending"


def build_detail(
    adapter: scm.Adapter,
    n: int,
    poll: dict,
    waited: int | None = None,
    verdict: str | None = None,
) -> tuple[bool, str]:
    state = poll["state"]
    checks = poll["checks"]
    mergeable = poll["mergeable"]
    reviews = poll.get("reviews")  # unresolved review count: a flag, never a gate

    reasons = []
    if state == "OPEN":
        if mergeable == "conflict":
            files = adapter.conflict_files(n)
            if files:
                reasons.append("merge conflict in: " + ", ".join(files))
            else:
                reasons.append(f"merge conflict ({poll['merge_detail']})")
        elif mergeable == "blocked":
            reasons.append(f"not mergeable ({poll['merge_detail']})")
        if reviews:
            plural = "" if reviews == 1 else "s"
            reasons.append(f"{reviews} unresolved review discussion{plural}")
        if checks == "failed":
            reasons.extend(adapter.failed_reasons(poll))

    if verdict == "no-pipeline":
        reasons.append("no pipeline launched")
    if verdict == "timeout":
        reasons.append(f"timed out after {waited}s (last: checks={checks})")

    ok = verdict != "timeout" and not (
        state == "OPEN" and (checks == "failed" or mergeable == "conflict")
    )

    detail = f"state={state} checks={checks} mergeable={mergeable}"
    if reviews is not None:
        detail += f" reviews={reviews} unresolved"
    detail += f" url={poll['url']}"
    if waited is not None:
        detail += f" waited={waited}"
    if reasons:
        detail += " reasons: " + " ; ".join(reasons)
    return ok, detail


def verdict_for_deploy(poll: dict, elapsed: float, grace: float) -> str:
    checks = poll["checks"]
    if checks == "failed":
        return "failed"
    if checks == "passed":
        return "passed"
    if checks == "none":
        return "no-pipeline" if elapsed >= grace else "pending"
    return "pending"


def build_deploy_detail(
    adapter: scm.Adapter,
    poll: dict,
    waited: int | None = None,
    verdict: str | None = None,
) -> tuple[bool, str]:
    checks = poll["checks"]
    pipeline = poll["pipeline"] or {}

    reasons = adapter.deploy_failed_reasons(poll)
    if verdict == "no-pipeline":
        reasons.append("no pipeline launched")
    if verdict == "timeout":
        reasons.append(f"timed out after {waited}s (last: status={checks})")

    ok = checks != "failed" and verdict != "timeout"
    sha_display = (poll.get("sha") or pipeline.get("sha") or "")[:8]
    detail = (
        f"branch={poll['branch']} sha={sha_display} status={checks} "
        f"url={pipeline.get('web_url', '')}"
    )
    if waited is not None:
        detail += f" waited={waited}"
    if reasons:
        detail += " reasons: " + " ; ".join(reasons)
    return ok, detail


def _adapter(repo: str, report: common.Report) -> scm.Adapter | None:
    """The repo's adapter; None after reporting it failed (unknown repo, bad
    origin) or skipped (local-only: no PR/MR host)."""
    try:
        adapter = scm.adapter_for(repo)
        if adapter is None:
            origin = scm.origin_url(repo) or "(no origin)"
            report.add(repo, "skipped", f"local-only: no PR/MR host for {origin}")
        return adapter
    except common.RepoError as exc:
        report.add(repo, "failed", str(exc))
        return None


def _report_check(repo: str, adapter: scm.Adapter, n: int, report: common.Report) -> None:
    ref = adapter.ref(n)
    try:
        ok, detail = build_detail(adapter, n, adapter.poll(n))
    except common.RepoError as exc:
        report.add(repo, "failed", f"{ref}: {exc}")
        return
    report.add(repo, "ok" if ok else "failed", f"{ref}: {detail}")


def process_pr(repo: str, n: int, report: common.Report) -> None:
    adapter = _adapter(repo, report)
    if adapter is not None:
        _report_check(repo, adapter, n, report)


def process_branch(repo: str, branch: str, report: common.Report) -> None:
    adapter = _adapter(repo, report)
    if adapter is None:
        return
    try:
        n = adapter.resolve_branch(branch)
    except common.RepoError as exc:
        report.add(repo, "failed", str(exc))
        return
    _report_check(repo, adapter, n, report)


def _report_deploy(
    repo: str, adapter: scm.Adapter, branch: str, sha: str | None, prefix: str, report
) -> None:
    try:
        poll = adapter.poll_deploy(branch, sha)
        ok, detail = build_deploy_detail(adapter, poll)
    except common.RepoError as exc:
        report.add(repo, "failed", f"deploy {branch}: {exc}")
        return
    report.add(repo, "ok" if ok else "failed", f"{prefix}: {detail}")


def process_deploy_pr(repo: str, n: int, report: common.Report) -> None:
    adapter = _adapter(repo, report)
    if adapter is None:
        return
    try:
        branch, sha = adapter.resolve_deploy(n)
    except common.RepoError as exc:
        report.add(repo, "failed", f"{adapter.ref(n)}: {exc}")
        return
    _report_deploy(repo, adapter, branch, sha, f"{adapter.ref(n)} deploy", report)


def process_deploy_branch(
    repo: str, branch: str | None, sha: str | None, report: common.Report
) -> None:
    adapter = _adapter(repo, report)
    if adapter is None:
        return
    try:
        branch = branch or adapter.deploy_branch()
    except common.RepoError as exc:
        report.add(repo, "failed", f"deploy: {exc}")
        return
    _report_deploy(repo, adapter, branch, sha, "deploy", report)


def _resolved(report: common.Report, repo: str, status: str, detail: str) -> None:
    """Record a resolved target and print it the moment it resolves.

    Watching is edge-triggered per target: the caller must be able to act on
    the first target that resolves without waiting for its siblings. The final
    report table still carries every row.
    """
    report.add(repo, status, detail)
    print(f"RESOLVED {repo:<20} {status:<10} {detail}", flush=True)


def watch_targets(
    targets: list[Target],
    report: common.Report,
    interval: float,
    timeout: float,
    grace: float,
) -> None:
    start = _now()
    pending = dict(enumerate(targets))
    seen_notes: dict[int, set] = {key: set() for key in pending}
    while pending:
        elapsed = _now() - start
        timed_out = elapsed >= timeout
        for key in list(pending):
            repo, adapter, n = pending[key]
            ref = adapter.ref(n)
            try:
                poll = adapter.poll(n)
                if isinstance(adapter, scm.GitLab):
                    for note in adapter.new_review_notes(n, seen_notes[key], poll["discussions"]):
                        print(adapter.format_new_note(n, note), flush=True)
                verdict = verdict_for(poll, elapsed, grace)
                if verdict == "pending" and not timed_out:
                    continue
                if verdict == "pending":
                    verdict = "timeout"
                ok, detail = build_detail(adapter, n, poll, waited=int(elapsed), verdict=verdict)
            except common.RepoError as exc:
                _resolved(report, repo, "failed", f"{ref}: {exc}")
            else:
                _resolved(report, repo, "ok" if ok else "failed", f"{ref}: {detail}")
            del pending[key]
        if pending and not timed_out:
            _sleep(interval)


def watch_deploy_targets(
    targets: list[DeployTarget],
    report: common.Report,
    interval: float,
    timeout: float,
    grace: float,
) -> None:
    start = _now()
    pending = dict(enumerate(targets))
    while pending:
        elapsed = _now() - start
        timed_out = elapsed >= timeout
        for key in list(pending):
            repo, adapter, branch, sha, prefix = pending[key]
            try:
                poll = adapter.poll_deploy(branch, sha)
                verdict = verdict_for_deploy(poll, elapsed, grace)
                if verdict == "pending" and not timed_out:
                    continue
                if verdict == "pending":
                    verdict = "timeout"
                ok, detail = build_deploy_detail(
                    adapter,
                    poll,
                    waited=int(elapsed),
                    verdict=verdict if verdict in ("timeout", "no-pipeline") else None,
                )
            except common.RepoError as exc:
                _resolved(report, repo, "failed", f"deploy {branch}: {exc}")
            else:
                _resolved(report, repo, "ok" if ok else "failed", f"{prefix}: {detail}")
            del pending[key]
        if pending and not timed_out:
            _sleep(interval)


def _targets_from_args(args: argparse.Namespace, report: common.Report) -> list[Target]:
    targets: list[Target] = []
    if args.prs:
        for repo, n in parse_pr_pairs(args.prs):
            adapter = _adapter(repo, report)
            if adapter is not None:
                targets.append((repo, adapter, n))
        return targets
    for repo in common.parse_repos(args.repos):
        adapter = _adapter(repo, report)
        if adapter is None:
            continue
        try:
            targets.append((repo, adapter, adapter.resolve_branch(args.branch)))
        except common.RepoError as exc:
            report.add(repo, "failed", str(exc))
    return targets


def _deploy_targets_from_args(
    args: argparse.Namespace, report: common.Report
) -> list[DeployTarget]:
    targets: list[DeployTarget] = []
    if args.prs:
        for repo, n in parse_pr_pairs(args.prs):
            adapter = _adapter(repo, report)
            if adapter is None:
                continue
            try:
                branch, sha = adapter.resolve_deploy(n)
            except common.RepoError as exc:
                report.add(repo, "failed", f"{adapter.ref(n)}: {exc}")
                continue
            targets.append((repo, adapter, branch, sha, f"{adapter.ref(n)} deploy"))
        return targets
    shas = parse_sha_pairs(args.sha) if args.sha else {}
    for repo in common.parse_repos(args.repos):
        adapter = _adapter(repo, report)
        if adapter is None:
            continue
        try:
            branch = args.branch or adapter.deploy_branch()
        except common.RepoError as exc:
            report.add(repo, "failed", f"deploy: {exc}")
            continue
        targets.append((repo, adapter, branch, shas.get(repo), "deploy"))
    return targets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prs", help="comma-separated repo#number pairs, e.g. repo1#123,repo2#45 (PRs or MRs)"
    )
    parser.add_argument("--branch", help="branch name to resolve a PR/MR for, per repo")
    parser.add_argument("--repos", help="comma-separated submodule names")
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="print one snapshot and exit instead of waiting for the pipeline",
    )
    parser.add_argument("--interval", type=float, default=10.0, help="poll seconds")
    parser.add_argument("--timeout", type=float, default=1200.0, help="overall seconds")
    parser.add_argument("--grace", type=float, default=30.0, help="launch grace seconds")
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="watch the post-merge deploy (GitHub Actions push runs or GitLab pipeline) "
        "on the tracked branch instead of the PR/MR head checks",
    )
    parser.add_argument(
        "--sha",
        help="comma-separated repo=SHA pins for --deploy --repos, e.g. repo1=abc123,repo2=def456",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.prs and (args.branch or args.repos):
        parser.error("use --prs, or --branch/--repos, not both")
    if args.deploy:
        if not args.prs and not args.repos:
            parser.error(
                "provide --prs OR --repos (branch optional, defaults to "
                "tracked branch) with --deploy"
            )
        if args.sha and args.prs:
            parser.error("--sha is only valid with --deploy --repos, not --prs")
    else:
        if not args.prs and not (args.branch and args.repos):
            parser.error("provide --prs OR --branch and --repos")
        if args.sha:
            parser.error("--sha is only valid with --deploy")
    try:
        scm.host_map()
        if args.prs:
            parse_pr_pairs(args.prs)
        if args.sha:
            known = set(common.parse_repos(args.repos))
            unknown = sorted(r for r in parse_sha_pairs(args.sha) if r not in known)
            if unknown:
                parser.error(f"--sha references repos not in --repos: {', '.join(unknown)}")
    except (scm.HostMapError, common.RepoError) as exc:
        parser.error(str(exc))

    report = common.Report()
    if args.deploy:
        if args.no_wait:
            if args.prs:
                for repo, n in parse_pr_pairs(args.prs):
                    process_deploy_pr(repo, n, report)
            else:
                shas = parse_sha_pairs(args.sha) if args.sha else {}
                for repo in common.parse_repos(args.repos):
                    process_deploy_branch(repo, args.branch, shas.get(repo), report)
        else:
            targets = _deploy_targets_from_args(args, report)
            watch_deploy_targets(targets, report, args.interval, args.timeout, args.grace)
    elif args.no_wait:
        if args.prs:
            for repo, n in parse_pr_pairs(args.prs):
                process_pr(repo, n, report)
        else:
            for repo in common.parse_repos(args.repos):
                process_branch(repo, args.branch, report)
    else:
        targets = _targets_from_args(args, report)
        watch_targets(targets, report, args.interval, args.timeout, args.grace)
    report.print_and_exit()


if __name__ == "__main__":
    main()
