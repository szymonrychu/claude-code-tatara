"""SCM host detection and the gh/glab adapter shared by the pullrequests-* skills.

Every gh or glab call goes through an Adapter, which targets the repo explicitly
and never relies on the current directory or an inherited GH_HOST/GITLAB_HOST:

- gh: `-R [<host>/]<owner>/<repo>` (host omitted for github.com); `gh api`
  gets `--hostname <host>` off github.com instead; `gh repo <sub>` gets the
  target positionally, since it has no -R flag.
- glab: `glab api projects/<url-encoded slug>/...` as the old GitLab scripts
  did, `-R <slug>` on any other subcommand, and env `GITLAB_HOST=<host>` only
  for hosts other than gitlab.com.

Host detection (detect_host): the WORKBENCH_SCM_HOSTS map first (by `host:port`
when an http(s) origin names a non-default port, then by the bare hostname), then
the substring rule (github -> github, gitlab -> gitlab), else None (local-only).
The adapter's hostname keeps that port, so --hostname, `-R host/...` and
GITLAB_HOST reach the same server as the origin.

A host matched only by the substring rule is not trusted with global tokens: the
CLI env drops them, so gh/glab fall back to the auth stored for that exact host
and a hostile `gitlab.attacker.tld` origin never receives a GITLAB_TOKEN. Mapped
and default hosts keep the env as it is.
"""

import abc
import json
import os
import re
import subprocess
from collections.abc import Mapping
from urllib.parse import quote, urlsplit

import common

HOSTS_ENV = "WORKBENCH_SCM_HOSTS"
HOSTS = ("github", "gitlab")
VALID_SEMVER_LEVELS = ("patch", "minor", "major")
SEMVER_LABEL_COLORS = {"patch": "0e8a16", "minor": "fbca04", "major": "d93f0b"}

# Lines of a failed check's or job's log kept in a failure reason.
LOG_TAIL_LINES = 100

# GitHub statusCheckRollup: check-run conclusions and commit-status states that fail.
CHECK_FAILURE_CONCLUSIONS = frozenset(
    {"FAILURE", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED", "STARTUP_FAILURE"}
)
CHECK_FAILURE_STATES = frozenset({"FAILURE", "ERROR"})
_RUN_ID = re.compile(r"/actions/runs/(\d+)")

# GitLab head pipeline statuses; anything else is pending.
PIPELINE_PASSED_STATUSES = frozenset({"success", "skipped"})
PIPELINE_FAILED_STATUSES = frozenset({"failed", "canceled"})

# GitHub Actions run mapping: a conclusion in the failed set fails the run; a run
# not yet completed (or stale, or with an unknown conclusion) is pending.
RUN_FAILURE_CONCLUSIONS = frozenset(
    {"failure", "cancelled", "timed_out", "action_required", "startup_failure"}
)
RUN_SUCCESS_CONCLUSIONS = frozenset({"success", "skipped", "neutral"})
RUN_FIELDS = "databaseId,status,conclusion,headSha,url,workflowName"

# GitLab MR states in the GitHub vocabulary the watch reports.
MR_STATE_MAP = {"opened": "OPEN", "locked": "OPEN", "merged": "MERGED", "closed": "CLOSED"}

# Inherited pins that would redirect gh or glab to another host or repo.
_HOST_ENV_VARS = ("GH_HOST", "GH_REPO", "GITLAB_HOST", "GL_HOST", "GITLAB_URI")
# Tokens gh or glab send to whatever host they target; withheld from hosts that
# only the substring rule matched.
_GLOBAL_TOKEN_VARS = (
    "GITLAB_TOKEN",
    "GITLAB_ACCESS_TOKEN",
    "OAUTH_TOKEN",
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GH_ENTERPRISE_TOKEN",
    "GITHUB_ENTERPRISE_TOKEN",
)
_DEFAULT_PORTS = {"http": 80, "https": 443}
_PORT_SUFFIX = re.compile(r"(?P<host>.+):\d+")
_GITHUB_SLUG = re.compile(r"[\w.-]+/[\w.-]+", re.ASCII)
# The CLIs need no repo from cwd; run them somewhere that cannot be one.
_NEUTRAL_CWD = os.path.abspath(os.sep)
_SCP_LIKE = re.compile(r"^(?:[^@/\s]+@)?(?P<host>[^:/\s]+):(?P<path>.+)$")


class HostMapError(ValueError):
    """A malformed WORKBENCH_SCM_HOSTS entry; the skills exit 2 on it."""


class CLIError(common.RepoError):
    """A gh or glab call that exited non-zero; carries the CLI's stderr."""

    def __init__(self, message: str, stderr: str = "", returncode: int | None = None):
        super().__init__(message)
        self.stderr = stderr
        self.returncode = returncode


def host_map(env: Mapping[str, str] | None = None) -> dict[str, str]:
    """Parse WORKBENCH_SCM_HOSTS (`host=github|gitlab`, comma-separated) into
    {lowercased hostname: host}. Unset or empty is an empty map."""
    raw = (os.environ if env is None else env).get(HOSTS_ENV, "")
    mapping = {}
    for item in raw.split(","):
        entry = item.strip()
        if not entry:
            continue
        name, sep, value = entry.partition("=")
        name, value = name.strip().lower(), value.strip().lower()
        if not sep or not name or value not in HOSTS:
            raise HostMapError(
                f"{HOSTS_ENV}: malformed entry {entry!r} (want hostname=github or hostname=gitlab)"
            )
        mapping[name] = value
    return mapping


def _split_url(url: str) -> tuple[str | None, str]:
    """(lowercased hostname or None, path) for https, ssh:// and scp-like urls."""
    url = (url or "").strip()
    if "://" in url:
        parts = urlsplit(url)
        return parts.hostname or None, parts.path
    m = _SCP_LIKE.match(url)
    if m:
        return m.group("host").lower(), m.group("path")
    return None, url


def origin_host(url: str | None) -> str | None:
    """The hostname of an origin url, lowercased; None when it has none."""
    return _split_url(url or "")[0]


def origin_authority(url: str | None) -> str | None:
    """`host[:port]` of an origin url, lowercased; None when it has no host. The
    port is kept only for http(s) and only when it is not the scheme's default:
    an ssh port is the ssh daemon's, not the API's."""
    hostname = origin_host(url)
    url = (url or "").strip()
    if not hostname or "://" not in url:
        return hostname
    parts = urlsplit(url)
    try:
        port = parts.port
    except ValueError:
        return hostname
    if port is None or _DEFAULT_PORTS.get(parts.scheme) in (None, port):
        return hostname
    return f"[{hostname}]:{port}" if ":" in hostname else f"{hostname}:{port}"


def _mapped_host(authority: str, mapping: Mapping[str, str]) -> str | None:
    """The map's host for `host:port`, else for the bare hostname; None when unmapped."""
    if authority in mapping:
        return mapping[authority]
    m = _PORT_SUFFIX.fullmatch(authority)
    return mapping.get(m.group("host").strip("[]")) if m else None


def detect_host(origin: str | None, env: Mapping[str, str] | None = None) -> str | None:
    """'github', 'gitlab' or None (local-only) for an origin url."""
    mapping = host_map(env)
    hostname = origin_host(origin)
    if not hostname:
        return None
    mapped = _mapped_host(origin_authority(origin), mapping)
    if mapped:
        return mapped
    for host in HOSTS:
        if host in hostname:
            return host
    return None


def slug_from_url(url: str) -> str:
    """owner/repo (or group/sub/repo) from any host's url, without .git."""
    hostname, path = _split_url(url)
    slug = path.strip().strip("/")
    if slug.endswith(".git"):
        slug = slug[: -len(".git")].rstrip("/")
    if not hostname or "/" not in slug:
        raise common.RepoError(f"cannot parse owner/repo from url: {(url or '').strip()!r}")
    return slug


def number_from_url(url: str) -> int:
    """The PR/MR number at the end of a web url (`.../pull/12`, `.../merge_requests/7`)."""
    m = re.search(r"/(\d+)/?$", (url or "").strip())
    if not m:
        raise common.RepoError(f"no PR/MR number in url: {url!r}")
    return int(m.group(1))


def origin_url(repo: str) -> str:
    """The repo's origin url, or "" when it has no origin."""
    result = common.run(
        ["git", "remote", "get-url", "origin"], cwd=common.resolve_repo(repo), check=False
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def adapter_for(repo: str, env: Mapping[str, str] | None = None) -> "Adapter | None":
    """A GitHub or GitLab adapter for a code/ repo, or None when it is local-only."""
    origin = origin_url(repo)
    host = detect_host(origin, env)
    if host is None:
        return None
    cls = GitHub if host == "github" else GitLab
    return cls(repo, origin_authority(origin), slug_from_url(origin), env=env)


def _tail(text: str) -> str:
    return "\n".join(text.splitlines()[-LOG_TAIL_LINES:])


def _check_level(level: str) -> None:
    if level not in VALID_SEMVER_LEVELS:
        raise common.RepoError(f"invalid semver level: {level}")


class Adapter(abc.ABC):
    host = ""
    cli = ""
    noun = ""
    sigil = ""
    default_hostname = ""

    def __init__(self, repo: str, hostname: str, slug: str, env: Mapping[str, str] | None = None):
        self.repo = repo
        self.hostname = hostname
        self.slug = slug
        self._env = env

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.repo!r}, {self.hostname!r}, {self.slug!r})"

    def ref(self, n) -> str:
        return f"{self.noun.lower()} {self.sigil}{n}"

    @abc.abstractmethod
    def _target(self, args: list[str]) -> list[str]:
        """The CLI args with this repo's explicit target added."""

    def _trusted(self) -> bool:
        """True for the default host and for one WORKBENCH_SCM_HOSTS maps to this
        adapter's host kind; False for a host only the substring rule matched."""
        if self.hostname == self.default_hostname:
            return True
        return _mapped_host(self.hostname, host_map(self._env)) == self.host

    def _cli_env(self) -> dict[str, str]:
        env = dict(os.environ if self._env is None else self._env)
        dropped = _HOST_ENV_VARS if self._trusted() else _HOST_ENV_VARS + _GLOBAL_TOKEN_VARS
        for name in dropped:
            env.pop(name, None)
        return env

    def run(self, args: list[str]) -> subprocess.CompletedProcess:
        cmd = [self.cli, *self._target(list(args))]
        try:
            result = subprocess.run(
                cmd, cwd=_NEUTRAL_CWD, env=self._cli_env(), text=True, capture_output=True
            )
        except FileNotFoundError as e:
            raise common.RepoError(f"{self.cli} not found on PATH") from e
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            raise CLIError(
                f"{self.cli} {' '.join(args[:2])} failed ({result.returncode}): {stderr}",
                stderr=stderr,
                returncode=result.returncode,
            )
        return result

    def json(self, args: list[str]):
        stdout = self.run(args).stdout
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as e:
            raise common.RepoError(
                f"{self.cli} {' '.join(args[:2])} returned non-JSON output: {stdout[:200]!r}"
            ) from e

    # --- poll ops: one call per host, the vocabularies the watch reports ---
    #
    # poll(n) -> {state, checks, mergeable, merge_detail, url, head_sha, raw}:
    #   state         OPEN, MERGED or CLOSED (UNKNOWN when the host gives none)
    #   checks        passed, failed, pending or none
    #   mergeable     mergeable, conflict, unknown or blocked
    #   merge_detail  the host field behind `mergeable`, as `key=value`
    #                 (`mergeStateStatus=DIRTY`, `detailed_merge_status=conflict`)
    #   raw           the host's PR/MR object, for failed_reasons and later ops
    # list_open() -> [{n, url, title, body, created, checks, mergeable, raw}], oldest first.

    @abc.abstractmethod
    def resolve_branch(self, branch: str) -> int:
        """The PR/MR number for a branch; RepoError `branch <b>: no PR/MR found (...)`."""

    @abc.abstractmethod
    def poll(self, n) -> dict:
        """One normalized snapshot of PR/MR n."""

    @abc.abstractmethod
    def failed_reasons(self, poll: dict) -> list[str]:
        """`check|job '<name>' failed:` plus its log tail, per failed check; [] unless failed."""

    # --- post-merge deploy watch ---
    #
    # resolve_deploy(n) -> (target branch, merge commit sha); RepoError when unmerged.
    # deploy_branch() -> the branch --deploy --repos watches by default.
    # poll_deploy(branch, sha=None) -> {branch, sha, pipeline, checks}; `pipeline`
    #   is the host's newest pipeline/run summary ({web_url, ...}) or None.
    # deploy_failed_reasons(poll) -> `job|run '<name>' failed:` plus log tail, per failure.

    @abc.abstractmethod
    def resolve_deploy(self, n) -> tuple[str, str]:
        """(target branch, merge commit sha) of merged PR/MR n; unmerged is a RepoError."""

    @abc.abstractmethod
    def deploy_branch(self) -> str:
        """The branch a deploy watch uses when none is given."""

    @abc.abstractmethod
    def poll_deploy(self, branch: str, sha: str | None = None) -> dict:
        """The post-merge pipeline state of `branch` (pinned to `sha` when given)."""

    @abc.abstractmethod
    def deploy_failed_reasons(self, poll: dict) -> list[str]:
        """Failure reasons with log tails for a poll_deploy result; [] unless failed."""

    @abc.abstractmethod
    def conflict_files(self, n) -> list[str]:
        """Files of PR/MR n to name in a merge-conflict reason; [] when unknown."""

    @abc.abstractmethod
    def list_open(self) -> list[dict]:
        """Every open PR/MR, oldest first."""


def _insert_before_dashdash(args: list[str], extra: list[str]) -> list[str]:
    at = args.index("--") if "--" in args else len(args)
    return args[:at] + extra + args[at:]


REVIEW_THREADS_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewThreads(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes { isResolved }
      }
    }
  }
}
"""


class GitHub(Adapter):
    host = "github"
    cli = "gh"
    noun = "PR"
    sigil = "#"
    default_hostname = "github.com"

    def __init__(self, repo: str, hostname: str, slug: str, env: Mapping[str, str] | None = None):
        """Rejects a slug that is not a plain owner/repo before it can reach a
        `gh api repos/<slug>/...` path (here or in a caller)."""
        owner, _, name = slug.partition("/")
        if not _GITHUB_SLUG.fullmatch(slug) or {owner, name} & {".", ".."}:
            raise common.RepoError(f"invalid GitHub slug: {slug!r} (want owner/repo)")
        super().__init__(repo, hostname, slug, env=env)

    @property
    def target(self) -> str:
        if self.hostname == self.default_hostname:
            return self.slug
        return f"{self.hostname}/{self.slug}"

    def _target(self, args: list[str]) -> list[str]:
        if args[:1] == ["api"]:
            if self.hostname == self.default_hostname:
                return args
            return _insert_before_dashdash(args, ["--hostname", self.hostname])
        if args[:1] == ["repo"]:
            return args[:2] + [self.target] + args[2:]
        return _insert_before_dashdash(args, ["-R", self.target])

    def find_open(self, branch: str) -> tuple[int, str] | None:
        prs = self.json(["pr", "list", "--head", branch, "--json", "number,url"])
        return (prs[0]["number"], prs[0]["url"]) if prs else None

    def create(self, branch: str, title: str, body: str) -> str:
        result = self.run(["pr", "create", "--head", branch, "--title", title, "--body", body])
        return result.stdout.strip()

    def edit_body(self, n, body: str) -> None:
        self.run(["pr", "edit", str(n), "--body", body])

    def semver_label(self, n) -> str | None:
        data = self.json(["pr", "view", str(n), "--json", "labels"])
        for label in data.get("labels", []):
            name = label.get("name", "")
            if name.startswith("semver:"):
                return name[len("semver:") :]
        return None

    def ensure_label(self, level: str) -> None:
        _check_level(level)
        self.run(
            ["label", "create", f"semver:{level}", "--color", SEMVER_LABEL_COLORS[level], "--force"]
        )

    def apply_label(self, n, level: str) -> None:
        self.run(["pr", "edit", str(n), "--add-label", f"semver:{level}"])

    @staticmethod
    def reduce_checks(rollup) -> str:
        """passed, failed, pending or none over a statusCheckRollup."""
        if not rollup:
            return "none"
        saw_pending = False
        for entry in rollup:
            conclusion = entry.get("conclusion")
            state = entry.get("state")
            status = entry.get("status")
            if conclusion:
                if conclusion in CHECK_FAILURE_CONCLUSIONS:
                    return "failed"
                if status and status != "COMPLETED":
                    saw_pending = True
            elif state:
                if state in CHECK_FAILURE_STATES:
                    return "failed"
                if state == "PENDING":
                    saw_pending = True
            else:
                saw_pending = True
        return "pending" if saw_pending else "passed"

    @staticmethod
    def mergeability(mergeable, merge_state_status) -> str:
        if mergeable == "CONFLICTING" or merge_state_status in ("DIRTY", "CONFLICTING"):
            return "conflict"
        if mergeable == "UNKNOWN":
            return "unknown"
        if mergeable == "MERGEABLE" and merge_state_status == "CLEAN":
            return "mergeable"
        return "blocked"

    def resolve_branch(self, branch: str) -> int:
        try:
            return int(self.json(["pr", "view", branch, "--json", "number"])["number"])
        except (common.RepoError, KeyError, TypeError, ValueError) as e:
            raise common.RepoError(f"branch {branch}: no PR found ({e})") from e

    def poll(self, n) -> dict:
        fields = "state,mergeable,mergeStateStatus,url,statusCheckRollup,headRefOid"
        data = self.json(["pr", "view", str(n), "--json", fields])
        merge_state_status = data.get("mergeStateStatus") or "UNKNOWN"
        poll = {
            "state": data.get("state") or "UNKNOWN",
            "checks": self.reduce_checks(data.get("statusCheckRollup")),
            "mergeable": self.mergeability(data.get("mergeable"), merge_state_status),
            "merge_detail": f"mergeStateStatus={merge_state_status}",
            "url": data.get("url") or "",
            "head_sha": data.get("headRefOid") or "",
            "raw": data,
        }
        if poll["state"] == "OPEN":
            # Informational, like GitLab: a graphql hiccup must not discard the
            # PR's valid CI and mergeability data, so reviews is simply absent.
            try:
                poll["reviews"] = self.unresolved_reviews(n)
            except common.RepoError:
                pass
        return poll

    def unresolved_reviews(self, n) -> int:
        """Unresolved review threads of PR n, outdated ones included (as GitLab
        counts them). One graphql call; more only for threads past the first 100."""
        owner, _, name = self.slug.partition("/")
        count, cursor = 0, None
        while True:
            args = [
                "api", "graphql", "-f", f"query={REVIEW_THREADS_QUERY}",
                "-F", f"owner={owner}", "-F", f"name={name}", "-F", f"number={n}",
            ]  # fmt: skip
            if cursor:
                args += ["-F", f"cursor={cursor}"]
            try:
                threads = self.json(args)["data"]["repository"]["pullRequest"]["reviewThreads"]
                count += sum(not t.get("isResolved") for t in threads["nodes"])
                page = threads["pageInfo"]
            except (KeyError, TypeError) as e:
                raise common.RepoError(f"PR {n}: unexpected reviewThreads response ({e})") from e
            if not page.get("hasNextPage"):
                return count
            cursor = page.get("endCursor")

    def _log_tail(self, entry: dict) -> str:
        details_url = entry.get("detailsUrl") or ""
        m = _RUN_ID.search(details_url)
        if not m:
            return f"no run id found (detailsUrl={details_url or 'none'})"
        run_id = m.group(1)
        try:
            return _tail(self.run(["run", "view", run_id, "--log-failed"]).stdout)
        except CLIError as e:
            return f"could not fetch log for run {run_id}: {e.stderr}"

    def failed_reasons(self, poll: dict) -> list[str]:
        if poll.get("checks") != "failed":
            return []
        reasons = []
        for entry in poll["raw"].get("statusCheckRollup") or []:
            if (
                entry.get("conclusion") in CHECK_FAILURE_CONCLUSIONS
                or entry.get("state") in CHECK_FAILURE_STATES
            ):
                name = entry.get("name") or "unknown check"
                reasons.append(f"check '{name}' failed:\n{self._log_tail(entry)}")
        return reasons

    # --- post-merge deploy watch: GitHub Actions push runs ---

    def resolve_deploy(self, n) -> tuple[str, str]:
        """(base branch, merge commit sha) of merged PR n; an unmerged PR is an error."""
        data = self.json(["pr", "view", str(n), "--json", "state,mergeCommit,baseRefName"])
        sha = (data.get("mergeCommit") or {}).get("oid")
        if data.get("state") != "MERGED" or not sha:
            raise common.RepoError(f"pr #{n} not merged yet - deploy-watch is a post-merge action")
        return data.get("baseRefName") or self.deploy_branch(), sha

    def default_branch(self) -> str:
        data = self.json(["repo", "view", "--json", "defaultBranchRef"])
        name = (data.get("defaultBranchRef") or {}).get("name")
        if not name:
            raise common.RepoError(f"{self.slug}: repo has no default branch")
        return name

    def deploy_branch(self) -> str:
        """The .gitmodules branch; the repo's default branch only when none is set."""
        return common.configured_branch(self.repo) or self.default_branch()

    def branch_tip(self, branch: str) -> str:
        data = self.json(["api", f"repos/{self.slug}/branches/{quote(branch, safe='')}"])
        sha = (data.get("commit") or {}).get("sha")
        if not sha:
            raise common.RepoError(f"branch {branch}: no head commit found")
        return sha

    @staticmethod
    def run_state(run: dict) -> str:
        """passed, failed or pending for one workflow run."""
        conclusion = run.get("conclusion")
        if conclusion in RUN_FAILURE_CONCLUSIONS:
            return "failed"
        if run.get("status") == "completed" and conclusion in RUN_SUCCESS_CONCLUSIONS:
            return "passed"
        return "pending"

    @staticmethod
    def reduce_runs(runs: list[dict]) -> str:
        """Any failed -> failed, any pending -> pending, else passed; none -> none."""
        if not runs:
            return "none"
        states = {GitHub.run_state(run) for run in runs}
        for state in ("failed", "pending"):
            if state in states:
                return state
        return "passed"

    def poll_deploy(self, branch: str, sha: str | None = None) -> dict:
        """Every push-event run of `sha` on `branch`; `sha` defaults to the branch tip."""
        sha = sha or self.branch_tip(branch)
        listed = self.json(
            [
                "run",
                "list",
                "--branch",
                branch,
                "--commit",
                sha,
                "--event",
                "push",
                "--limit",
                "100",
                "--json",
                RUN_FIELDS,
            ]
        )
        runs = [run for run in listed or [] if run.get("headSha") == sha]
        checks = self.reduce_runs(runs)
        shown = next((r for r in runs if self.run_state(r) == "failed"), runs[0] if runs else None)
        return {
            "branch": branch,
            "sha": sha,
            "pipeline": {"web_url": shown.get("url") or "", "id": shown.get("databaseId")}
            if shown
            else None,
            "checks": checks,
            "runs": runs,
        }

    def deploy_failed_reasons(self, poll: dict) -> list[str]:
        if poll.get("checks") != "failed":
            return []
        reasons = []
        for run in poll["runs"]:
            if self.run_state(run) != "failed":
                continue
            name = run.get("workflowName") or "unknown workflow"
            reasons.append(f"run '{name}' failed:\n{self._run_log_tail(run.get('databaseId'))}")
        return reasons

    def _run_log_tail(self, run_id) -> str:
        try:
            return _tail(self.run(["run", "view", str(run_id), "--log-failed"]).stdout)
        except CLIError as e:
            return f"could not fetch log for run {run_id}: {e.stderr}"

    def conflict_files(self, n) -> list[str]:
        try:
            data = self.json(["pr", "view", str(n), "--json", "files"])
        except common.RepoError:
            return []
        return [f["path"] for f in data.get("files", []) if f.get("path")]

    def list_open(self) -> list[dict]:
        fields = "number,url,title,body,createdAt,mergeable,mergeStateStatus,statusCheckRollup"
        prs = self.json(["pr", "list", "--state", "open", "--limit", "100", "--json", fields])
        items = [
            {
                "n": pr["number"],
                "url": pr.get("url") or "",
                "title": pr.get("title") or "",
                "body": pr.get("body") or "",
                "created": pr.get("createdAt") or "",
                "checks": self.reduce_checks(pr.get("statusCheckRollup")),
                "mergeable": self.mergeability(
                    pr.get("mergeable"), pr.get("mergeStateStatus") or "UNKNOWN"
                ),
                "raw": pr,
            }
            for pr in prs or []
        ]
        return sorted(items, key=lambda item: item["created"])


NOTE_BODY_TRUNC_LEN = 200


class GitLab(Adapter):
    host = "gitlab"
    cli = "glab"
    noun = "MR"
    sigil = "!"
    default_hostname = "gitlab.com"

    @property
    def project(self) -> str:
        """The url-encoded slug for `glab api projects/<project>/...`."""
        return quote(self.slug, safe="")

    def _target(self, args: list[str]) -> list[str]:
        if args[:1] == ["api"]:
            return args
        return _insert_before_dashdash(args, ["-R", self.slug])

    def _cli_env(self) -> dict[str, str]:
        env = super()._cli_env()
        if self.hostname != self.default_hostname:
            env["GITLAB_HOST"] = self.hostname
        return env

    def find_open(self, branch: str) -> tuple[int, str] | None:
        source = quote(branch, safe="/")
        mrs = self.json(
            ["api", f"projects/{self.project}/merge_requests?source_branch={source}&state=opened"]
        )
        return (mrs[0]["iid"], mrs[0]["web_url"]) if mrs else None

    def create(self, branch: str, title: str, body: str) -> str:
        created = self.json(
            [
                "api",
                "--method",
                "POST",
                f"projects/{self.project}/merge_requests",
                "-f",
                f"source_branch={branch}",
                "-f",
                f"target_branch={common.tracked_branch(self.repo)}",
                "-f",
                f"title={title}",
                "-f",
                f"description={body}",
            ]
        )
        return created["web_url"]

    def edit_body(self, n, body: str) -> None:
        self.run(
            [
                "api",
                "--method",
                "PUT",
                f"projects/{self.project}/merge_requests/{n}",
                "-f",
                f"description={body}",
            ]
        )

    def semver_label(self, n) -> str | None:
        data = self.json(["api", f"projects/{self.project}/merge_requests/{n}"])
        for name in data.get("labels", []):
            if name.startswith("semver:"):
                return name[len("semver:") :]
        return None

    def ensure_label(self, level: str) -> None:
        _check_level(level)
        try:
            self.run(
                [
                    "api",
                    "--method",
                    "POST",
                    f"projects/{self.project}/labels",
                    "-f",
                    f"name=semver:{level}",
                    "-f",
                    f"color=#{SEMVER_LABEL_COLORS[level]}",
                ]
            )
        except CLIError as e:
            if "409" not in e.stderr:
                raise

    def apply_label(self, n, level: str) -> None:
        self.run(
            [
                "api",
                "--method",
                "PUT",
                f"projects/{self.project}/merge_requests/{n}",
                "-f",
                f"add_labels=semver:{level}",
            ]
        )

    @staticmethod
    def reduce_checks(pipeline) -> str:
        """passed, failed, pending or none over an MR's head_pipeline."""
        if not pipeline:
            return "none"
        status = pipeline.get("status")
        if status in PIPELINE_PASSED_STATUSES:
            return "passed"
        if status in PIPELINE_FAILED_STATUSES:
            return "failed"
        return "pending"

    @staticmethod
    def mergeability(detailed_merge_status, has_conflicts) -> str:
        if detailed_merge_status == "conflict" or has_conflicts:
            return "conflict"
        if detailed_merge_status == "mergeable":
            return "mergeable"
        if detailed_merge_status in ("checking", "unchecked"):
            return "unknown"
        return "blocked"

    def resolve_branch(self, branch: str) -> int:
        source = quote(branch, safe="")
        try:
            mrs = self.json(
                [
                    "api",
                    f"projects/{self.project}/merge_requests?source_branch={source}&state=opened",
                ]
            )
            return int(mrs[0]["iid"])
        except (common.RepoError, IndexError, KeyError, TypeError, ValueError) as e:
            raise common.RepoError(f"branch {branch}: no MR found ({e})") from e

    def poll(self, n) -> dict:
        data = self.json(["api", f"projects/{self.project}/merge_requests/{n}"])
        detailed_merge_status = data.get("detailed_merge_status") or "unknown"
        discussions = self.discussions(n)
        return {
            "state": MR_STATE_MAP.get(data.get("state"), "UNKNOWN"),
            "checks": self.reduce_checks(data.get("head_pipeline")),
            "mergeable": self.mergeability(detailed_merge_status, data.get("has_conflicts")),
            "merge_detail": f"detailed_merge_status={detailed_merge_status}",
            "url": data.get("web_url") or "",
            "head_sha": data.get("sha") or "",
            "raw": data,
            "discussions": discussions,
            "reviews": self.count_unresolved(discussions),
        }

    # --- review discussions: informational flags, never a gate ---

    def discussions(self, n) -> list:
        """The MR's discussions. Degrades to [] on any API error: a hiccup here
        must not discard the MR's valid CI and mergeability data."""
        try:
            found = self.json(
                ["api", f"projects/{self.project}/merge_requests/{n}/discussions?per_page=100"]
            )
        except common.RepoError:
            return []
        return found if isinstance(found, list) else []

    @staticmethod
    def count_unresolved(discussions: list) -> int:
        """Discussions holding a resolvable, unresolved, non-system note."""
        return sum(
            any(
                note.get("resolvable") and not note.get("resolved", False)
                for note in discussion.get("notes", [])
                if not note.get("system")
            )
            for discussion in discussions
        )

    def unresolved_reviews(self, n, discussions: list | None = None) -> int:
        """Unresolved review discussions of MR n (fetched unless `discussions` is given)."""
        return self.count_unresolved(self.discussions(n) if discussions is None else discussions)

    def new_review_notes(self, n, seen: set, discussions: list | None = None) -> list:
        """Non-system notes of MR n whose ids are not in `seen`; adds them to `seen`."""
        new = []
        for discussion in self.discussions(n) if discussions is None else discussions:
            for note in discussion.get("notes", []):
                nid = note.get("id")
                if note.get("system") or nid is None or nid in seen:
                    continue
                seen.add(nid)
                new.append(note)
        return new

    def format_new_note(self, n, note: dict) -> str:
        author = (note.get("author") or {}).get("username", "unknown")
        body = (note.get("body") or "").strip().replace("\n", " ")
        if len(body) > NOTE_BODY_TRUNC_LEN:
            body = body[:NOTE_BODY_TRUNC_LEN].rstrip() + "..."
        return f"[{self.repo} !{n}] new review comment from {author}: {body}"

    def _log_tail(self, job: dict) -> str:
        jid = job.get("id")
        try:
            return _tail(self.run(["api", f"projects/{self.project}/jobs/{jid}/trace"]).stdout)
        except CLIError as e:
            return f"could not fetch log for job {jid}: {e.stderr}"

    def pipeline_failed_reasons(self, pipeline_id) -> list[str]:
        """One `job '<name>' failed:` reason with a log tail per failed job of a pipeline."""
        jobs = self.json(["api", f"projects/{self.project}/pipelines/{pipeline_id}/jobs"])
        return [
            f"job '{job.get('name') or 'unknown job'}' failed:\n{self._log_tail(job)}"
            for job in jobs
            if job.get("status") == "failed"
        ]

    def failed_reasons(self, poll: dict) -> list[str]:
        if poll.get("checks") != "failed":
            return []
        return self.pipeline_failed_reasons((poll["raw"].get("head_pipeline") or {}).get("id"))

    # --- post-merge deploy watch: GitLab pipelines ---

    def resolve_deploy(self, n) -> tuple[str, str]:
        """(target branch, merge_commit_sha) of merged MR n; an unmerged MR is an error."""
        data = self.json(["api", f"projects/{self.project}/merge_requests/{n}"])
        sha = data.get("merge_commit_sha")
        if not sha:
            raise common.RepoError(
                f"mr !{n} not merged yet (no merge_commit_sha) - "
                "deploy-watch is a post-merge action"
            )
        return data.get("target_branch") or common.tracked_branch(self.repo), sha

    def deploy_branch(self) -> str:
        return common.tracked_branch(self.repo)

    def deploy_failed_reasons(self, poll: dict) -> list[str]:
        if poll.get("checks") != "failed":
            return []
        return self.pipeline_failed_reasons((poll["pipeline"] or {}).get("id"))

    def poll_deploy(self, branch: str, sha: str | None = None) -> dict:
        """The newest pipeline on `branch` (pinned to `sha` when given)."""
        query = f"ref={quote(branch, safe='')}"
        if sha:
            query += f"&sha={sha}"
        query += "&per_page=1"
        data = self.json(["api", f"projects/{self.project}/pipelines?{query}"])
        pipeline = data[0] if data else None
        return {
            "branch": branch,
            "sha": sha,
            "pipeline": pipeline,
            "checks": self.reduce_checks(pipeline),
        }

    def conflict_files(self, n) -> list[str]:
        """GitLab names no conflicting files; the reason keeps detailed_merge_status."""
        return []

    def list_open(self) -> list[dict]:
        mrs = self.json(
            [
                "api",
                f"projects/{self.project}/merge_requests"
                "?state=opened&order_by=created_at&sort=asc&per_page=100",
            ]
        )
        items = [
            {
                "n": mr["iid"],
                "url": mr.get("web_url") or "",
                "title": mr.get("title") or "",
                "body": mr.get("description") or "",
                "created": mr.get("created_at") or "",
                "checks": self.reduce_checks(mr.get("head_pipeline")),
                "mergeable": self.mergeability(
                    mr.get("detailed_merge_status") or "unknown", mr.get("has_conflicts")
                ),
                "raw": mr,
            }
            for mr in mrs or []
        ]
        return sorted(items, key=lambda item: item["created"])
