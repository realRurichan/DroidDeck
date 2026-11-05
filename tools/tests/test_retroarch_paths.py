from pathlib import Path
import runpy
import tempfile
import unittest

repair = runpy.run_path(str(Path(__file__).resolve().parents[1] /
    'linuxfs/overlay/usr/local/bin/droiddeck-retroarch-paths'))['repair']


class RetroArchPathsTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.config = self.root / 'root/.config/retroarch/retroarch.cfg'
        self.config.parent.mkdir(parents=True)
        for path in ('usr/lib/aarch64-linux-gnu/libretro', 'usr/share/libretro/info', 'usr/share/libretro/assets'):
            (self.root / path).mkdir(parents=True)

    def test_empty_defaults_use_installed_resources_and_keep_other_settings(self):
        original = ('libretro_directory = "~/.config/retroarch/cores"\n'
                    'libretro_info_path = "~/.config/retroarch/cores"\n'
                    'assets_directory = "~/.config/retroarch/assets"\nmenu_driver = "ozone"\n')
        self.config.write_text(original)
        self.assertTrue(repair(self.root))
        text = self.config.read_text()
        self.assertIn('libretro_directory = "/usr/lib/aarch64-linux-gnu/libretro"', text)
        self.assertIn('libretro_info_path = "/usr/share/libretro/info"', text)
        self.assertIn('assets_directory = "/usr/share/libretro/assets"', text)
        self.assertIn('menu_driver = "ozone"', text)
        self.assertEqual(original, self.config.with_name('retroarch.cfg.before-directory-repair').read_text())
        self.assertFalse(repair(self.root))

    def test_preserves_custom_paths_and_downloaded_cores(self):
        text = 'assets_directory = "/root/custom-assets"\nlibretro_directory = "~/.config/retroarch/cores"\n'
        self.config.write_text(text)
        cores = self.config.parent / 'cores'
        cores.mkdir()
        (cores / 'custom.so').write_bytes(b'core')
        repair(self.root)
        self.assertTrue(self.config.read_text().startswith(text))
        self.assertEqual(b'core', (cores / 'custom.so').read_bytes())

    def test_initial_config_uses_system_paths(self):
        self.assertTrue(repair(self.root))
        self.assertIn('/usr/share/libretro/assets', self.config.read_text())
