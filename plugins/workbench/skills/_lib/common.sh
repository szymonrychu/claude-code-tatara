#!/usr/bin/env bash
# Shared bash helpers for workbench git/GitHub skills.
# Source this file; do not execute it directly.

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  echo "common.sh: must be sourced, not executed" >&2
  exit 1
fi

log_info() { echo "[INFO] $*" >&2; }
log_warn() { echo "[WARN] $*" >&2; }
log_err()  { echo "[ERR] $*" >&2; }

repo_root() {
  local start dir
  for start in "$PWD" "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; do
    dir="$start"
    while :; do
      if [ -d "$dir/code" ] && [ -f "$dir/.gitmodules" ]; then
        echo "$dir"
        return 0
      fi
      [ "$dir" = "/" ] && break
      dir="$(dirname "$dir")"
    done
  done
  return 1
}

# Root that holds docs/: the workbench when there is one, else the git toplevel.
docs_root() {
  local root
  if root="$(repo_root)"; then
    echo "$root"
    return 0
  fi
  if root="$(git rev-parse --show-toplevel 2>/dev/null)" && [ -n "$root" ]; then
    echo "$root"
    return 0
  fi
  log_err "docs root not found (no workbench and not a git repo)"
  return 1
}

# slugify <text> [max=60]: lowercase ASCII, every other character (non-ASCII
# letters included) is a separator, runs become one "-", trimmed, cut to <max>
# characters, trailing "-" trimmed again. Byte-identical to common.slugify.
slugify() {
  local max="${2:-60}"
  printf '%s' "$1" \
    | LC_ALL=C tr '[:upper:]' '[:lower:]' \
    | LC_ALL=C tr -c 'a-z0-9' '-' \
    | LC_ALL=C sed -E 's/-+/-/g; s/^-//; s/-$//' \
    | LC_ALL=C cut -c1-"$max" \
    | LC_ALL=C sed -E 's/-$//'
}

all_repos() {
  local root gm names
  root="$(repo_root)" || return 1
  gm="$root/.gitmodules"
  names=""
  if [ -f "$gm" ]; then
    names="$(grep '^[[:space:]]*path = code/' "$gm" | sed -E 's#.*path = code/##')"
  fi
  if [ -z "$names" ]; then
    names="$(find "$root/code" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | sed 's#.*/##' | sort)"
  fi
  printf '%s\n' "$names" | grep -v '^$'
}

resolve_repo() {
  local name="$1" root
  if [ -z "$name" ]; then
    log_err "resolve_repo: repo name required"
    return 1
  fi
  root="$(repo_root)" || { log_err "workbench root not found"; return 1; }
  if ! all_repos | grep -qx -- "$name"; then
    log_err "unknown repo: $name"
    return 1
  fi
  echo "$root/code/$name"
}

tracked_branch() {
  local name="$1" root val
  root="$(repo_root)" || return 1
  val="$(git config -f "$root/.gitmodules" --get "submodule.$name.branch" 2>/dev/null)"
  echo "${val:-main}"
}

worktree_path() {
  local branch="$1" repo="$2" root
  root="$(repo_root)" || return 1
  echo "$root/.worktrees/$branch/$repo"
}

REPORT_REPOS=()
REPORT_STATUSES=()
REPORT_DETAILS=()

report_add() {
  REPORT_REPOS+=("$1")
  REPORT_STATUSES+=("$2")
  REPORT_DETAILS+=("$3")
}

report_print() {
  local i
  printf '%-20s %-10s %s\n' "REPO" "STATUS" "DETAIL"
  for i in "${!REPORT_REPOS[@]}"; do
    printf '%-20s %-10s %s\n' "${REPORT_REPOS[$i]}" "${REPORT_STATUSES[$i]}" "${REPORT_DETAILS[$i]}"
  done
}

report_failed() {
  local s
  for s in "${REPORT_STATUSES[@]}"; do
    [ "$s" = "failed" ] && return 0
  done
  return 1
}
