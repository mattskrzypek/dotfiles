import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('configure', Path(__file__).resolve().parents[1] / 'scripts/configure.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        c.HOME = Path(self.temp.name)
        c.BACKUPS = c.HOME / '.local/state/dotfiles/backups'
        self.write('.config/hypr/hyprland.lua', 'require("default.hypr.omarchy")\nrequire("hypr.bindings")\n')
        self.write('.config/gtk-3.0/settings.ini', '[Settings]\ngtk-font-name=Sans 13\nother-setting=true\n')
        self.write('.config/Code/User/settings.json', '{// retained values\n"editor.fontSize":17,"a":"https://example.com",}')
        self.write('.zshrc', 'alias mine=true\n')

    def tearDown(self):
        self.temp.cleanup()

    def write(self, rel, data):
        path = c.HOME / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding='utf-8')

    def apply(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            c.apply()
        return Path(output.getvalue().strip())

    def test_repeat_and_restore_binary(self):
        before = (c.HOME / '.zshrc').read_bytes()
        first = self.apply()
        generated = c.build()
        second = self.apply()
        self.assertEqual(generated, c.build())
        self.assertNotIn('.zshrc', json.loads((second / 'manifest.json').read_text())['files'])
        c.restore(first, switch_theme=False)
        self.assertEqual(before, (c.HOME / '.zshrc').read_bytes())
        self.assertFalse((c.HOME / '.config/omarchy/themes/cyber-green/backgrounds/fat-pigeon-green.png').exists())

    def test_native_sizes_and_existing_settings(self):
        generated = c.build()
        kitty = generated['.config/kitty/kitty.conf'].decode()
        self.assertNotIn('font_size', kitty)
        settings = json.loads(generated['.config/Code/User/settings.json'])
        self.assertEqual(settings['editor.fontSize'], 17)
        self.assertEqual(settings['a'], 'https://example.com')
        self.assertIn('Font 13', generated['.config/gtk-3.0/settings.ini'].decode())
        self.assertIn('other-setting', generated['.config/gtk-3.0/settings.ini'].decode())
        self.assertNotIn('base-size', generated['.config/omarchy/themes/cyber-green/shell.bar.toml'].decode())

    def test_unknown_entry_rejected_before_write(self):
        self.write('.config/hypr/hyprland.lua', 'source = old.conf\n')
        with self.assertRaises(ValueError):
            self.apply()
        self.assertFalse(c.BACKUPS.exists())

    def test_path_escape_rejected(self):
        with self.assertRaises(ValueError):
            c.target('../elsewhere')

    def test_only_named_bundled_webapps_removed_and_restored(self):
        self.write('.local/share/applications/ChatGPT.desktop', '[Desktop Entry]\nName=ChatGPT\nExec=omarchy-launch-webapp https://chatgpt.com\n')
        self.write('.local/share/applications/Custom.desktop', '[Desktop Entry]\nName=Custom\nExec=omarchy-launch-webapp https://example.com\n')
        backup = self.apply()
        c.remove_webapps(backup)
        self.assertFalse((c.HOME / '.local/share/applications/ChatGPT.desktop').exists())
        self.assertTrue((c.HOME / '.local/share/applications/Custom.desktop').exists())
        c.restore(backup, switch_theme=False)
        self.assertTrue((c.HOME / '.local/share/applications/ChatGPT.desktop').exists())


if __name__ == '__main__':
    unittest.main()
