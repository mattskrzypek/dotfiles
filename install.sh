#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
mode=install
keep_apps=false
for arg in "$@"; do
  case "$arg" in
    --dry-run) mode=plan ;;
    --config-only) mode=config ;;
    --keep-apps) keep_apps=true ;;
    *) echo "Usage: bash install.sh [--dry-run|--config-only] [--keep-apps]" >&2; exit 2 ;;
  esac
done
command -v python3 >/dev/null || { echo 'Python 3 is required.' >&2; exit 1; }
python3 "$ROOT/scripts/configure.py" validate
if [[ $mode == plan ]]; then
  python3 "$ROOT/scripts/configure.py" plan
  exit
fi
[[ $EUID != 0 ]] || { echo 'Run as your normal desktop user, without sudo.' >&2; exit 1; }
[[ $(uname -m) == x86_64 ]] || { echo 'This profile targets x86_64 PCs.' >&2; exit 1; }
for cmd in omarchy-theme-set omarchy-default-terminal omarchy-default-editor omarchy-default-browser; do
  command -v "$cmd" >/dev/null || { echo "Missing $cmd. Finish installing Omarchy first." >&2; exit 1; }
done
[[ -f $HOME/.config/hypr/hyprland.lua ]] || {
  echo 'This script requires Omarchy 4 with its Lua Hyprland configuration. Update older Omarchy before running it.' >&2
  exit 1
}
[[ -n ${HYPRLAND_INSTANCE_SIGNATURE:-} && -n ${DBUS_SESSION_BUS_ADDRESS:-} ]] || {
  echo 'Run this from a terminal inside your logged-in Omarchy desktop.' >&2
  exit 1
}
# Build and validate the configuration before any package changes.
python3 "$ROOT/scripts/configure.py" check
trap 'echo "Setup stopped at line $LINENO. Fix the reported error and rerun; prior successful package installs are retained." >&2' ERR
read_list() { python3 "$ROOT/scripts/configure.py" list "$1"; }
if [[ $mode == install ]]; then
  mapfile -t repo < <(read_list repo_packages)
  mapfile -t aur < <(read_list aur_packages)
  mapfile -t flatpaks < <(read_list flatpak_packages)
  sudo pacman -Syu --needed --noconfirm "${repo[@]}"
  # Omarchy may already supply its JetBrains font package; avoid its conflict
  # with Arch's full Nerd Font package.
  if ! fc-match -f '%{family}' 'JetBrainsMono Nerd Font' | grep -Fq 'JetBrains'; then
    sudo pacman -S --needed --noconfirm ttf-jetbrains-mono-nerd
  fi
  helper=$(command -v yay || command -v paru || true)
  [[ -n $helper ]] || { echo 'Install yay or paru first.' >&2; exit 1; }
  "$helper" -S --needed "${aur[@]}"
  flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
  flatpak install --user --noninteractive flathub "${flatpaks[@]}"
fi
for cmd in kitty code brave-origin zsh; do
  command -v "$cmd" >/dev/null || { echo "Missing $cmd. Run without --config-only to install applications." >&2; exit 1; }
done
backup=$(python3 "$ROOT/scripts/configure.py" apply)
echo "Configuration backup: $backup"
echo "Restore settings with: bash $ROOT/restore.sh $backup"
omarchy-default-terminal kitty
omarchy-default-editor code
if ! env -u BROWSER omarchy-default-browser brave-origin; then
  xdg-mime default brave-origin.desktop text/html x-scheme-handler/http x-scheme-handler/https
fi
xdg-mime default code.desktop text/plain
fc-cache -f
python3 "$ROOT/scripts/configure.py" fonts
omarchy-theme-set cyber-green
omarchy-theme-bg-set "$HOME/.config/omarchy/themes/cyber-green/backgrounds/fat-pigeon-green.png"
if [[ -n ${HYPRLAND_INSTANCE_SIGNATURE:-} ]]; then
  hyprctl reload
  errors=$(hyprctl configerrors)
  if [[ -n $errors && $errors != 'ok' ]]; then
    printf 'Hyprland reported: %s\nRestore using the backup above before logging out.\n' "$errors" >&2
    exit 1
  fi
fi
if [[ $(read_list change_login_shell) == true ]]; then
  current_shell=$(getent passwd "$(id -un)" | cut -d: -f7)
  [[ $current_shell == /usr/bin/zsh ]] || sudo usermod --shell /usr/bin/zsh "$(id -un)"
fi
if [[ $(read_list serial_access) == true ]]; then
  sudo usermod -aG uucp "$(id -un)"
  rule=/etc/udev/rules.d/70-dotfiles-fpv.rules
  if [[ -e $rule ]] && ! sudo cmp -s "$ROOT/config/70-dotfiles-fpv.rules" "$rule"; then
    sudo cp -a "$rule" "$rule.backup.$(date +%s)"
  fi
  sudo install -Dm644 "$ROOT/config/70-dotfiles-fpv.rules" "$rule"
  sudo udevadm control --reload-rules
fi
systemctl --user enable syncthing.service
if [[ $mode == install && $keep_apps == false && $(read_list remove_optional_apps) == true ]]; then
  # Explicit packages only: never autoremove libraries, drivers, or orphan packages.
  removed_log="$backup/removed-packages.txt"
  while IFS= read -r package; do
    if pacman -Q "$package" >/dev/null 2>&1; then
      if sudo pacman -R --noconfirm "$package"; then
        printf '%s\n' "$package" >> "$removed_log"
      else
        echo "Retained $package because package removal failed (see pacman's explanation)." >&2
      fi
    fi
  done < <(read_list remove_packages)
  python3 "$ROOT/scripts/configure.py" remove-webapps "$backup"
fi
echo 'Setup complete. Log out and back in for Zsh and USB group membership.'
echo 'Omarchy font sizes are unchanged. Updates are manual: bash update.sh'
echo 'Sign in to Brave Origin, Bitwarden, Discord and Telegram when ready.'
