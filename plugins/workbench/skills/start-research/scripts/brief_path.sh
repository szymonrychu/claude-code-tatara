#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=SCRIPTDIR/../../_lib/common.sh
source "$SCRIPT_DIR/../../_lib/common.sh"

TOPIC="${1-}"
if [ -z "$TOPIC" ]; then
  log_err "usage: brief_path.sh <topic>"
  exit 1
fi

slug="$(slugify "$TOPIC")"

if [ -z "$slug" ]; then
  log_err "topic produced an empty slug: $TOPIC"
  exit 1
fi

root="$(docs_root)" || exit 1
dir="$root/docs/research"
mkdir -p "$dir" || { log_err "could not create research dir: $dir"; exit 1; }
echo "$dir/$(date +%F)-$slug.md"
