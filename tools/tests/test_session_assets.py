import importlib.util
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile


spec = importlib.util.spec_from_file_location(
    'check_session_assets', Path(__file__).resolve().parents[1] / 'release/check_session_assets.py')
assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assets)


class SessionAssetsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.overlay = self.root / 'overlay'
        self.helper = self.overlay / 'usr/local/bin/droiddeck-login1'
        self.helper.parent.mkdir(parents=True)
        self.helper.write_bytes(b'current helper')
        self.apk = self.root / 'app.apk'
        self.name = 'assets/linuxfs/usr/local/bin/droiddeck-login1'

    def test_missing_required_helper_rejects_cached_bundle(self):
        with ZipFile(self.apk, 'w') as package:
            package.writestr('classes.dex', b'classes')
        self.assertEqual(['missing ' + self.name], assets.check(self.apk, self.overlay))

    def test_stale_helper_rejects_cached_bundle(self):
        with ZipFile(self.apk, 'w') as package:
            package.writestr(self.name, b'old helper')
        self.assertEqual(['stale ' + self.name], assets.check(self.apk, self.overlay))

    def test_current_helper_passes(self):
        with ZipFile(self.apk, 'w') as package:
            package.writestr(self.name, self.helper.read_bytes())
        self.assertEqual([], assets.check(self.apk, self.overlay))

    def test_krkr2_recipe_must_be_bundled_and_current(self):
        recipe = self.overlay / 'usr/local/lib/droiddeck-krkr2/prepare.py'
        recipe.parent.mkdir(parents=True)
        recipe.write_bytes(b'current recipe')
        name = 'assets/linuxfs/' + recipe.relative_to(self.overlay).as_posix()
        for content, expected in [(None, ['missing ' + name]),
                                  (b'old recipe', ['stale ' + name]),
                                  (b'current recipe', [])]:
            with self.subTest(content=content):
                with ZipFile(self.apk, 'w') as package:
                    package.writestr(self.name, self.helper.read_bytes())
                    if content is not None:
                        package.writestr(name, content)
                self.assertEqual(expected, assets.check(self.apk, self.overlay))

    def test_krkr2_recipe_must_be_extracted(self):
        path = 'usr/local/lib/droiddeck-krkr2/build.sh'
        recipe = self.overlay / path
        recipe.parent.mkdir(parents=True)
        recipe.write_bytes(b'build')
        mapping = '"usr/local/bin/droiddeck-login1" to "usr/local/bin/droiddeck-login1"'
        self.assertEqual(['not extracted at session start: ' + path],
                         assets.check_extraction(self.overlay, mapping))
        self.assertEqual([], assets.check_extraction(self.overlay, mapping + f'\n"{path}" to "{path}"'))

    def test_bundled_helper_must_also_be_extracted(self):
        self.assertEqual(['not extracted at session start: usr/local/bin/droiddeck-login1'],
                         assets.check_extraction(self.overlay, ''))
        mapping = '"usr/local/bin/droiddeck-login1" to "usr/local/bin/droiddeck-login1"'
        self.assertEqual([], assets.check_extraction(self.overlay, mapping))

    def test_helper_extracted_under_another_name_counts(self):
        mapping = '"usr/local/bin/droiddeck-login1" to "usr/local/bin/login1"'
        self.assertEqual([], assets.check_extraction(self.overlay, mapping))
        mapping = '"usr/local/bin/droiddeck-login1" to "usr/local/bin/sub/login1"'
        self.assertEqual(['not extracted at session start: usr/local/bin/droiddeck-login1'],
                         assets.check_extraction(self.overlay, mapping))
