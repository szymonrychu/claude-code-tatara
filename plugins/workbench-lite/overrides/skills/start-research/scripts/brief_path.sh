#!/usr/bin/env bash
# brief_path.sh <topic>: same as doc_path.sh research <topic>.
set -u

if [ -z "${1-}" ]; then
  echo "[ERR] usage: brief_path.sh <topic>" >&2
  exit 1
fi
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/doc_path.sh" research "$1"
