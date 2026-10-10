# Matt's Omarchy dotfiles

Post-install setup for an **x86_64 Omarchy 4 desktop**. Reviewed against upstream tag `v4.0.4` (commit `c668141`). Older Omarchy releases using Hyprland `.conf` files are rejected before package changes. Finish the normal Omarchy installation and first-login setup first.

## Install

Open a terminal in the Omarchy desktop, as your normal user:

```bash
git clone https://github.com/mattskrzypek/dotfiles.git
cd dotfiles
bash install.sh --dry-run
bash install.sh
```

The dry run prints the installation and removal lists without changing the computer. Edit `profile.json` first if you want different software. Installation needs your sudo password and may ask you to review AUR builds. Account logins remain yours to complete. Log out and back in once setup completes.

To install without removing optional apps: `bash install.sh --keep-apps`.
To reapply settings without changing packages: `bash install.sh --config-only`.

## Your setup

- **VS Code**, **Kitty**, **Brave Origin** (not regular Brave), and **Bitwarden**.
- Zsh with a single-line Cyber Green Starship prompt (always-visible username/hostname, light grey path, neon green accents), suggestions, syntax highlighting, eza, zoxide, and mise integration. Existing `.zshrc` content is retained ahead of a managed block.
- Git/GitHub CLI, Python/pip/uv, Node/npm, ShellCheck/shfmt, with Omarchy's development tools retained.
- Syncthing and Ark; no LibreOffice or Obsidian.
- Betaflight and EdgeTX Buddy app-window shortcuts in Brave Origin; ExpressLRS Configurator from Flathub; DFU/USB tools and narrow STM32, CP210x, and CH340 access rules. Reconnect USB devices after logging back in. Web flashing also needs browser device permission; grant it when prompted.
- nmap, Wireshark, tcpdump, netcat, DNS tools, whois, and gobuster. Packet capture permissions are not broadened globally.
- Discord, Telegram, VLC, and OBS. OBS uses the desktop's existing PipeWire/portal screen sharing.

## Appearance and shortcuts

Cyber Green is a native Omarchy theme: near-black surfaces, green accents, readable pale-green text, the recolored Fat Pigeon circuit wallpaper, a compact top bar, rounded windows, gentle shadow/blur, restrained transparency, and smooth animations.

JetBrains Mono Nerd Font is selected through fontconfig, GTK, existing Qt font settings, Kitty, and VS Code. **Omarchy's default font sizes and monitor scaling are retained.** Existing app-specific sizes are also preserved. Websites and apps with bundled fonts may use their own typography.

`Super+Enter` opens Kitty, `Super+B` Brave Origin, `Super+C` VS Code, and `Super+E` the native Files app. `Super+H/J/K/L` focuses windows, `Super+Shift+H/J/K/L` swaps them, `Super+Q` closes a window, and `Super+M` opens btop. Omarchy's launcher, number workspaces, fullscreen, scratchpad, and screenshot bindings remain. Preinstalled app/webapp shortcuts are disabled, preventing bindings for removed apps from persisting.

The theme is installed locally under `~/.config/omarchy/themes/cyber-green` and selected through `omarchy-theme-set`; it appears in Omarchy's style menu. Omarchy generates terminal and editor themes from `colors.toml`, keeping them in sync when changing themes. The installer does not use Noctalia.

## Cleanup

The exact editable list is in `profile.json`. By default it removes installed copies of 1Password/CLI, Spotify, Signal, Obsidian, LibreOffice, Kdenlive, Pinta, Xournal++, Moonlight, LocalSend, Cliamp, and Omawrite. Requested apps such as OBS remain.

Only explicitly named packages are removed, without recursive dependency removal or orphan sweeping. Packages still required by another package are retained with pacman's explanation. Chromium and Foot remain as Omarchy base components, alongside the compositor, shell, display/login/lock services, networking, portals, drivers, boot/recovery components, printing, and development tools.

Only named bundled web shortcuts launched through Omarchy are removed; custom shortcuts are retained. Browser accounts, profiles, and application data are not deleted. Unused icon files may remain. Omarchy upgrades can reinstall a bundled app; `bash update.sh --apps` reapplies this cleanup explicitly.

## Manual updates

```bash
cd ~/dotfiles
bash update.sh          # fetch and reapply configuration only
bash update.sh --apps   # also update/install packages and reapply cleanup
```

Commit or stash local repository edits before updating. Updates use a fast-forward Git pull; nothing is scheduled automatically. To change the setup everywhere, edit and push this repository, then run the update script on each PC. Keep credentials, private keys, and personal files out of this public repository.

For local-only customizations, use `~/.config/hypr/dotfiles-local.lua`, `~/.config/kitty/dotfiles-local.conf`, and `~/.zshrc.local`. These files are not managed. The Starship prompt is saved in `config/starship.toml` and installed to `~/.config/starship.toml`; edit the repository copy to keep prompt changes across updates. Main generated files are regenerated on update; unrelated VS Code, GTK, Qt, and shell JSON settings are preserved. JSONC comments are removed when VS Code settings are rewritten; the originals are backed up.

## Recovery

Every configuration run prints its timestamped backup directory under `~/.local/state/dotfiles/backups`. Restore that run with:

```bash
bash restore.sh "$HOME/.local/state/dotfiles/backups/TIMESTAMP"
```

Restoration selects the prior Omarchy theme, restores backed-up files/defaults/font choices and removed web shortcuts, and removes files newly created by that run. Log out and back in afterward. Runs form a history; restore newest first to undo multiple runs.

Package installs/removals, the login shell, USB rules/group membership, and Syncthing service enablement are separate system changes and are not rolled back by file restoration. Successfully removed packages are recorded in the backup's `removed-packages.txt`; reinstall chosen packages with `yay -S PACKAGE`. Existing replaced USB rules receive a sibling timestamped backup in `/etc/udev/rules.d`.

If a terminal ever becomes unreadable, run:

```bash
printf '\033[0m\033]10;#d2f5dd\007\033]11;#080d0a\007'
```

Then inspect `~/.config/kitty/dotfiles-local.conf` and any `dark-theme.auto.conf`, `light-theme.auto.conf`, or `no-preference-theme.auto.conf` files in the Kitty directory: local and automatic themes can override palette colors. The installer leaves these personal files alone.

## Validation and limits

GitHub Actions checks shell syntax, ShellCheck, Lua syntax, configuration generation, backup restoration, preservation of font sizes/settings, and targeted shortcut removal. The installer checks the live compositor for configuration errors before cleanup. A real Omarchy installation is required to verify rendering, USB flashing, login behavior, and all upstream integrations; those cannot be tested from the Windows authoring workspace.

Upstream reference: [Omarchy custom themes](https://omarchy.org/manual/making-your-own-theme/), [browser defaults](https://omarchy.org/manual/browsers/), and [v4.0.4 source](https://github.com/omacom/omarchy/tree/v4.0.4).
