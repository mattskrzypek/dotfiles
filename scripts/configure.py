#!/usr/bin/env python3
"""Build managed overrides and back up every file before changing it."""
import configparser
import ast
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
BACKUPS = HOME / '.local/state/dotfiles/backups'
BEGIN = '# BEGIN DOTFILES MANAGED'
END = '# END DOTFILES MANAGED'


def profile():
    p = json.loads((ROOT / 'profile.json').read_text(encoding='utf-8'))
    if not re.fullmatch(r'[A-Za-z0-9 _-]+', p['font_family']):
        raise ValueError('Unsafe font family')
    for key in ('repo_packages', 'aur_packages', 'flatpak_packages', 'remove_packages'):
        if not isinstance(p[key], list) or not all(re.fullmatch(r'[A-Za-z0-9@._+-]+', x) for x in p[key]):
            raise ValueError(f'Invalid package list: {key}')
    if set(p['remove_packages']) & set(p['repo_packages'] + p['aur_packages']):
        raise ValueError('An installed package is also listed for removal')
    protected = {'hyprland', 'quickshell', 'chromium', 'foot', 'uwsm', 'sddm', 'yay', 'omarchy',
                 'networkmanager', 'pipewire', 'wireplumber', 'gnome-keyring', 'nautilus',
                 'docker', 'docker-compose', 'mise-bin', 'nvim', 'git', 'base', 'base-devel'}
    if set(p['remove_packages']) & protected or any(
            x.startswith(('linux-', 'lib', 'xdg-desktop-portal', 'nvidia', 'vulkan', 'omarchy-'))
            and x != 'libreoffice-fresh' for x in p['remove_packages']):
        raise ValueError('Removal list includes a protected system/development package')
    for key in ('remove_optional_apps', 'change_login_shell', 'serial_access'):
        if not isinstance(p[key], bool):
            raise ValueError(f'{key} must be boolean')
    return p


def target(rel):
    path = Path(rel)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError(f'Unsafe path: {rel}')
    dest = HOME / path
    for parent in dest.parents:
        if parent == HOME:
            break
        if parent.is_symlink():
            raise ValueError(f'Symlink parent refused: {parent}')
    if dest.is_dir():
        raise ValueError(f'Directory refused: {dest}')
    return dest


def text(rel, fallback=''):
    path = target(rel)
    return path.read_text(encoding='utf-8') if path.exists() else fallback


def block(original, addition, begin=BEGIN, end=END):
    original = re.sub(re.escape(begin) + r'.*?' + re.escape(end) + r'\n?', '', original, flags=re.S)
    return original.rstrip() + '\n\n' + begin + '\n' + addition.rstrip() + '\n' + end + '\n'


def jsonc(raw):
    # Skip comments only outside quoted strings, then trailing commas.
    cleaned = re.sub(r'("(?:\\.|[^"\\])*")|//[^\n]*|/\*.*?\*/',
                     lambda m: m[1] or '', raw, flags=re.S)
    cleaned = re.sub(r'("(?:\\.|[^"\\])*")|,(\s*[}\]])',
                     lambda m: m[1] if m[1] else m[2], cleaned)
    value = json.loads(cleaned)
    if not isinstance(value, dict):
        raise ValueError('Expected a JSON object')
    return value


def desktop_fonts():
    values = {}
    if shutil.which('gsettings') and os.environ.get('DBUS_SESSION_BUS_ADDRESS'):
        for key in ('font-name', 'document-font-name', 'monospace-font-name'):
            proc = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', key],
                                  capture_output=True, text=True)
            if proc.returncode == 0:
                values[key] = proc.stdout.strip()
    return values


def build():
    p = profile()
    font = p['font_family']
    entry = text('.config/hypr/hyprland.lua')
    marker = 'require("default.hypr.omarchy")'
    if marker not in entry:
        raise ValueError('Expected Omarchy 4 Lua entry point was not found; no files changed')
    entry = re.sub(r'^omarchy_preinstalled_bindings\s*=.*\n', '', entry, flags=re.M)
    entry = entry.replace(marker, 'omarchy_preinstalled_bindings = false\n' + marker)
    entry = block(entry, 'require("hypr.dotfiles")', '-- BEGIN DOTFILES MANAGED', '-- END DOTFILES MANAGED')
    result = {'.config/hypr/hyprland.lua': entry,
              '.config/hypr/dotfiles.lua': (ROOT / 'config/dotfiles.lua').read_text(encoding='utf-8')}
    # Keep native font sizes and shortcuts; own overrides precede user-local overrides.
    kitty = f'''include ~/.local/state/omarchy/current/theme/kitty.conf
font_family {font}
shell /usr/bin/zsh
background_opacity 0.93
include dotfiles-local.conf
'''
    result['.config/kitty/kitty.conf'] = kitty
    zsh = (ROOT / 'config/zshrc').read_text(encoding='utf-8')
    result['.zshrc'] = block(text('.zshrc'), zsh)
    result['.config/environment.d/90-dotfiles.conf'] = 'EDITOR=code\nVISUAL=code\nTERMINAL=kitty\nBROWSER=brave-origin\n'
    # Preserve existing GUI font size, changing only its family.
    for version in ('3.0', '4.0'):
        rel = f'.config/gtk-{version}/settings.ini'
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(text(rel, '[Settings]\n'))
        if not parser.has_section('Settings'):
            parser.add_section('Settings')
        native_font = desktop_fonts().get('font-name', "'Sans 10'")
        previous = parser.get('Settings', 'gtk-font-name', fallback=ast.literal_eval(native_font))
        size = re.search(r'(\d+(?:\.\d+)?)\s*$', previous)
        parser['Settings']['gtk-font-name'] = f'{font} {size[1] if size else "10"}'
        import io
        output = io.StringIO()
        parser.write(output)
        result[rel] = output.getvalue()
    for app in ('qt5ct', 'qt6ct'):
        rel = f'.config/{app}/{app}.conf'
        if target(rel).exists():
            parser = configparser.ConfigParser(interpolation=None)
            parser.optionxform = str
            parser.read_string(text(rel))
            if parser.has_section('Fonts'):
                for key in ('general', 'fixed'):
                    previous = parser.get('Fonts', key, fallback='')
                    if ',' in previous:
                        parser['Fonts'][key] = font + ',' + previous.split(',', 1)[1]
            output = io.StringIO()
            parser.write(output)
            result[rel] = output.getvalue()
    rel = '.config/fontconfig/conf.d/99-dotfiles-font.conf'
    result[rel] = '<?xml version="1.0"?><fontconfig>' + ''.join(
        f'<match target="pattern"><test name="family" qual="any"><string>{family}</string></test>'
        f'<edit name="family" mode="prepend_first" binding="strong"><string>{font}</string></edit></match>'
        for family in ('monospace', 'sans-serif', 'serif', 'system-ui')) + '</fontconfig>\n'
    rel = '.config/Code/User/settings.json'
    settings = jsonc(text(rel, '{}'))
    settings.update({'editor.fontFamily': f"'{font}', monospace", 'terminal.integrated.fontFamily': font,
                     'update.mode': 'none', 'window.titleBarStyle': 'custom'})
    result[rel] = json.dumps(settings, indent=2) + '\n'
    rel = '.vscode/argv.json'
    settings = jsonc(text(rel, '{}'))
    settings['password-store'] = 'gnome-libsecret'
    result[rel] = json.dumps(settings, indent=2) + '\n'
    rel = '.config/omarchy/shell.json'
    shell = jsonc(text(rel, '{"version":1}'))
    bar = shell.setdefault('bar', {})
    bar.update({'position': 'top', 'transparent': False, 'centerAnchor': 'omarchy.clock', 'layout': {
        'left': [{'id': 'omarchy.menu'}, {'id': 'omarchy.workspaces'}],
        'center': [{'id': 'omarchy.clock', 'format': 'HH:mm'}, {'id': 'omarchy.system-update'}],
        'right': [{'id': 'omarchy.tray'}, {'id': 'omarchy.bluetooth'}, {'id': 'omarchy.network'},
                  {'id': 'omarchy.audio'}, {'id': 'omarchy.power'}]}})
    result[rel] = json.dumps(shell, indent=2) + '\n'
    for file in (ROOT / 'theme').rglob('*'):
        if file.is_file():
            rel = '.config/omarchy/themes/cyber-green/' + file.relative_to(ROOT / 'theme').as_posix()
            result[rel] = file.read_bytes()
    for name, url in [('betaflight', 'https://app.betaflight.com'), ('edgetx-buddy', 'https://buddy.edgetx.org')]:
        result[f'.local/share/applications/dotfiles-{name}.desktop'] = (
            f'[Desktop Entry]\nType=Application\nName={"Betaflight" if name == "betaflight" else "EdgeTX Buddy"}\n'
            f'Exec=brave-origin --app={url}\nIcon=applications-engineering\nTerminal=false\nCategories=Utility;\n')
    for rel, data in result.items():
        target(rel)
        if rel.endswith('.toml'):
            tomllib.loads(data.decode() if isinstance(data, bytes) else data)
        if rel.endswith('.conf') and 'fontconfig/' in rel:
            ET.fromstring(data)
    return {k: v if isinstance(v, bytes) else v.encode('utf-8') for k, v in result.items()}


def snapshot(backup, rel, manifest):
    if rel in manifest['files']:
        return
    path = target(rel)
    if path.is_symlink():
        manifest['files'][rel] = {'symlink': os.readlink(path)}
    elif path.exists():
        copy = backup / 'files' / rel
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, copy)
        manifest['files'][rel] = {'saved': True}
    else:
        manifest['files'][rel] = {'saved': False}


def save_manifest(backup, manifest):
    (backup / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')


def apply():
    generated = build()
    backup = BACKUPS / datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup.mkdir(parents=True, exist_ok=False)
    old_theme = text('.local/state/omarchy/current/theme.name').strip()
    manifest = {'theme': old_theme, 'desktop_fonts': desktop_fonts(), 'files': {}}
    # Native default commands write these; include their original state.
    for rel in ('.config/xdg-terminals.list', '.config/mimeapps.list', '.local/share/applications/mimeapps.list',
                '.local/state/omarchy/defaults/editor', '.local/state/omarchy/current/background'):
        snapshot(backup, rel, manifest)
    changed = []
    for rel, data in generated.items():
        dest = target(rel)
        if dest.is_symlink() or not dest.exists() or dest.read_bytes() != data:
            snapshot(backup, rel, manifest)
            changed.append((rel, data))
    save_manifest(backup, manifest)
    try:
        for rel, data in changed:
            dest = target(rel)
            dest.parent.mkdir(parents=True, exist_ok=True)
            temp = dest.with_name(dest.name + '.dotfiles-tmp')
            if temp.exists() or temp.is_symlink():
                raise ValueError(f'Temporary path already exists: {temp}')
            with temp.open('xb') as stream:
                stream.write(data)
            temp.chmod(0o600)
            temp.replace(dest)
    except Exception:
        restore(backup, switch_theme=False)
        raise
    print(backup)


def restore(backup, switch_theme=True):
    backup = Path(backup).resolve()
    if not backup.is_relative_to(BACKUPS.resolve()) or backup == BACKUPS.resolve():
        raise ValueError('Restore requires a backup under ~/.local/state/dotfiles/backups')
    manifest = json.loads((backup / 'manifest.json').read_text(encoding='utf-8'))
    for rel, item in manifest['files'].items():
        target(rel)
        if item.get('saved') and not (backup / 'files' / rel).is_file():
            raise ValueError(f'Missing backup file: {rel}')
    if switch_theme and manifest['theme']:
        subprocess.run(['omarchy-theme-set', manifest['theme']], check=True)
    if switch_theme:
        for key, value in manifest.get('desktop_fonts', {}).items():
            subprocess.run(['gsettings', 'set', 'org.gnome.desktop.interface', key, value], check=True)
    for rel, item in manifest['files'].items():
        dest = target(rel)
        if dest.exists() or dest.is_symlink():
            dest.unlink()
        dest.parent.mkdir(parents=True, exist_ok=True)
        if 'symlink' in item:
            dest.symlink_to(item['symlink'])
        elif item.get('saved'):
            shutil.copy2(backup / 'files' / rel, dest)


def remove_webapps(backup):
    backup = Path(backup).resolve()
    if not backup.is_relative_to(BACKUPS.resolve()):
        raise ValueError('Invalid backup directory')
    manifest = json.loads((backup / 'manifest.json').read_text(encoding='utf-8'))
    names = set(profile()['remove_webapps'])
    app_dir = HOME / '.local/share/applications'
    for path in app_dir.glob('*.desktop'):
        rel = path.relative_to(HOME).as_posix()
        content = text(rel)
        name = re.search(r'^Name=(.*)$', content, re.M)
        if name and name[1] in names and re.search(r'^Exec=omarchy-(launch-webapp|webapp-handler)', content, re.M):
            snapshot(backup, rel, manifest)
            save_manifest(backup, manifest)
            target(rel).unlink()
            print(f'Removed bundled shortcut: {name[1]}')


def main():
    command = sys.argv[1]
    p = profile()
    if command == 'validate':
        for path in (ROOT / 'theme').glob('*.toml'):
            tomllib.loads(path.read_text(encoding='utf-8'))
    elif command == 'list':
        value = p[sys.argv[2]]
        print('\n'.join(value) if isinstance(value, list) else str(value).lower())
    elif command == 'plan':
        for key in ('repo_packages', 'aur_packages', 'flatpak_packages', 'remove_packages', 'remove_webapps'):
            print(f'{key}: {", ".join(p[key])}')
        print('Theme: Cyber Green with Fat Pigeon wallpaper; native font sizes retained.')
    elif command == 'check':
        build()
    elif command == 'apply':
        apply()
    elif command == 'fonts':
        for key, value in desktop_fonts().items():
            previous = ast.literal_eval(value)
            size = re.search(r'(\d+(?:\.\d+)?)\s*$', previous)
            if size:
                subprocess.run(['gsettings', 'set', 'org.gnome.desktop.interface', key,
                                p['font_family'] + ' ' + size[1]], check=True)
    elif command == 'restore':
        restore(sys.argv[2])
    elif command == 'remove-webapps':
        remove_webapps(sys.argv[2])
    else:
        raise ValueError('Unknown command')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'Configuration failed: {exc}', file=sys.stderr)
        sys.exit(1)
