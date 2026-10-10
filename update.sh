#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
[[ $# == 0 || ( $# == 1 && $1 == --apps ) ]] || { echo 'Usage: bash update.sh [--apps]' >&2; exit 2; }
[[ -z $(git -C "$ROOT" status --porcelain) ]] || { echo 'Commit or stash your local changes before updating.' >&2; exit 1; }
git -C "$ROOT" pull --ff-only
if [[ ${1:-} == --apps ]]; then
  bash "$ROOT/install.sh"
  flatpak update --user --noninteractive
else
  bash "$ROOT/install.sh" --config-only
fi
