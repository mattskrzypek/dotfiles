#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
[[ $# == 1 ]] || { echo 'Usage: bash restore.sh BACKUP_DIRECTORY' >&2; exit 2; }
python3 "$ROOT/scripts/configure.py" restore "$1"
echo 'Settings restored. Log out and back in. Package removal, the login shell, and USB rules are not rolled back.'
