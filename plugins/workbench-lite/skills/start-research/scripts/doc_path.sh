#!/usr/bin/env bash
# doc_path.sh research <topic>: print (and create the dir of) the dated research brief path
# under docs/research at the git toplevel (the cwd outside a repo).
set -u

log_err() { echo "[ERR] $*" >&2; }

# slugify <text> [max=60]: lowercase ASCII, every other character is a separator, runs become
# one "-", trimmed, cut to <max> characters, trailing "-" trimmed again.
slugify() {
  local max="${2:-60}"
  printf '%s' "$1" \
    | LC_ALL=C tr '[:upper:]' '[:lower:]' \
    | LC_ALL=C tr -c 'a-z0-9' '-' \
    | LC_ALL=C sed -E 's/-+/-/g; s/^-//; s/-$//' \
    | LC_ALL=C cut -c1-"$max" \
    | LC_ALL=C sed -E 's/-$//'
}

USAGE="usage: doc_path.sh research <topic>"
KIND="${1-}"
TOPIC="${2-}"

if [ "$KIND" != research ] || [ -z "$TOPIC" ]; then
  log_err "$USAGE"
  exit 1
fi

slug="$(slugify "$TOPIC")"
if [ -z "$slug" ]; then
  log_err "topic produced an empty slug: $TOPIC"
  log_err "$USAGE"
  exit 1
fi

root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
dir="$root/docs/research"
mkdir -p "$dir" || { log_err "could not create dir: $dir"; exit 1; }

echo "$dir/$(date +%F)-$slug.md"
