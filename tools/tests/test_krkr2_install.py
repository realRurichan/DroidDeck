import hashlib
import io
import json
import tarfile
import os
from contextlib import contextmanager
from pathlib import Path
import shlex
import subprocess
import tempfile
from types import SimpleNamespace
import unittest


BIN = Path(__file__).resolve().parents[1] / 'linuxfs/overlay/usr/local/bin'
VERSION = '03aa34b-r1'
RELEASE_BASE = 'https://github.com/realRurichan/DroidDeck/releases/download/'


def release_url(version):
    return RELEASE_BASE + 'krkr2-linux-arm64-' + version + '/krkr2-linux-arm64.tar.gz'


def install_arguments(checksum, version=VERSION):
    return ['install-release', '--version', version, '--url', release_url(version), '--sha256', checksum]


class Krkr2InstallTest(unittest.TestCase):
    @contextmanager
    def installation(self, failure='', missing=False):
        with tempfile.TemporaryDirectory(prefix="krkr2 'install' ") as directory:
            root = Path(directory)
            commands = root / 'bin'
            commands.mkdir()
            recipe = root / 'recipe'
            recipe.mkdir()
            (recipe / 'runtime-packages.txt').write_text('libglx0\n')
            archive = root / 'engine.tar.gz'
            engine = b'#!/bin/sh\n[ "$FAILURE" != runtime ] || exit 8\necho engine\n'
            with tarfile.open(archive, 'w:gz') as package:
                member = tarfile.TarInfo('krkr2')
                member.mode = 0o755
                member.size = len(engine)
                package.addfile(member, io.BytesIO(engine))
            if failure == 'extract':
                archive.write_bytes(b'invalid archive')
            checksum = '0' * 64 if failure == 'checksum' else hashlib.sha256(archive.read_bytes()).hexdigest()
            (recipe / 'binary.env').write_text('touch "$SOURCED"\nexit 91\n')
            bodies = {
                'uname': 'echo aarch64',
                'apt-get': 'echo "apt-direct $*" >> "$CALLS"; exit 0',
                'dpkg-query': '[ "$MISSING" != 1 ] && [ "$FAILURE" != apt ] && printf installed',
                'droiddeck-root': 'echo "apt $*" >> "$CALLS"; [ "$FAILURE" != apt ]',
                'curl': 'echo "download $*" >> "$CALLS"\n'
                        '[ "$FAILURE" != download ] || exit 7\n'
                        'while [ "$1" != --output ]; do shift; done\ncp "$ARCHIVE" "$2"',
                'mv': 'echo "move $*" >> "$CALLS"\n'
                      '[ "$FAILURE" != place ] || [ "${1##*/}" != package ] || exit 9\nexec /bin/mv "$@"',
            }
            for name, body in bodies.items():
                command = commands / name
                command.write_text('#!/bin/sh\n' + body + '\n')
                command.chmod(0o755)
            target = root / 'installed'
            target.mkdir()
            (target / 'krkr2').write_text('previous engine')
            (target / '.engine-version').write_text('previous-r0\n')
            script = root / 'install.sh'
            script.write_text((BIN / 'droiddeck-krkr2-install').read_text()
                              .replace('/usr/local/lib/droiddeck-krkr2', shlex.quote(str(recipe)))
                              .replace('/root/.krkr2-install.XXXXXX', shlex.quote(str(root / '.krkr2-install.XXXXXX')))
                              .replace('/opt/krkr2', shlex.quote(str(target))))
            calls = root / 'calls'
            calls.touch()
            sourced = root / 'binary-env-sourced'
            env = dict(os.environ, PATH=str(commands) + os.pathsep + os.environ['PATH'],
                       FAILURE=failure, MISSING=str(int(missing)), ARCHIVE=str(archive),
                       CALLS=str(calls), SOURCED=str(sourced))
            yield SimpleNamespace(root=root, script=script, target=target, calls=calls,
                                  sourced=sourced, env=env, checksum=checksum)

    def run_installer(self, fixture, arguments):
        return subprocess.run(['bash', str(fixture.script)] + arguments,
                              env=fixture.env, capture_output=True, text=True, timeout=10)

    def install(self, failure='', missing=False, arguments=None):
        with self.installation(failure, missing) as fixture:
            if arguments is None:
                arguments = install_arguments(fixture.checksum)
            result = self.run_installer(fixture, arguments)
            return SimpleNamespace(result=result,
                                   engine=(fixture.target / 'krkr2').read_text(),
                                   version=(fixture.target / '.engine-version').read_text(),
                                   leftovers=list(fixture.root.glob('.krkr2-install.*')),
                                   calls=fixture.calls.read_text(),
                                   sourced=fixture.sourced.exists())

    def assert_rejected_without_changes(self, arguments):
        outcome = self.install(arguments=arguments)
        self.assertNotEqual(0, outcome.result.returncode, outcome.result.stdout)
        self.assertEqual('previous engine', outcome.engine)
        self.assertEqual('previous-r0\n', outcome.version)
        self.assertEqual([], outcome.leftovers)
        self.assertEqual('', outcome.calls)
        self.assertFalse(outcome.sourced)

    def test_success_downloads_verifies_and_installs_without_apt_when_libraries_exist(self):
        outcome = self.install()
        self.assertEqual(0, outcome.result.returncode, outcome.result.stderr)
        self.assertIn('echo engine', outcome.engine)
        self.assertEqual(VERSION + '\n', outcome.version)
        self.assertEqual([], outcome.leftovers)
        self.assertNotIn('apt ', outcome.calls)
        self.assertNotIn('apt-direct ', outcome.calls)
        self.assertIn('download ', outcome.calls)
        self.assertIn(release_url(VERSION), outcome.calls)
        self.assertFalse(outcome.sourced)
        self.assertIn('== STEP Verify Krkr2 download', outcome.result.stdout)

    def test_only_missing_runtime_libraries_are_installed(self):
        outcome = self.install(missing=True)
        self.assertEqual(0, outcome.result.returncode, outcome.result.stderr)
        self.assertIn('install -y -q --no-install-recommends libglx0', outcome.calls)
        self.assertNotIn('cmake', outcome.calls)

    def test_failures_preserve_an_existing_installation_and_clean_temporary_files(self):
        for failure in ('apt', 'download', 'checksum', 'extract', 'runtime', 'place'):
            with self.subTest(failure=failure):
                outcome = self.install(failure)
                self.assertNotEqual(0, outcome.result.returncode)
                self.assertIn('== FAIL Krkr2 installation', outcome.result.stdout)
                self.assertEqual('previous engine', outcome.engine)
                self.assertEqual('previous-r0\n', outcome.version)
                self.assertEqual([], outcome.leftovers)
                self.assertFalse(outcome.sourced)

    def test_legacy_entry_points_do_not_reinstall_a_bundled_version(self):
        for arguments in ([], ['install'], ['install'] + install_arguments('a' * 64)[1:]):
            with self.subTest(arguments=arguments):
                self.assert_rejected_without_changes(arguments)

    def test_invalid_versions_are_rejected_before_download_or_install(self):
        for version in ('', '../03aa34b-r1', '03aa34b r1', '03aa34b-r1/extra', '03aa34b-r1;true'):
            with self.subTest(version=version):
                self.assert_rejected_without_changes(install_arguments('a' * 64, version))

    def test_release_url_must_match_owner_repository_tag_version_and_asset(self):
        valid = release_url(VERSION)
        urls = (
            valid.replace('https://', 'http://', 1),
            valid.replace('github.com/', 'example.test/', 1),
            valid.replace('github.com/', 'github.com@example.test/', 1),
            valid.replace('/realRurichan/', '/another-owner/', 1),
            valid.replace('/DroidDeck/', '/another-repository/', 1),
            release_url('03aa34b-r2'),
            valid.replace('/krkr2-linux-arm64.tar.gz', '/another-asset.tar.gz'),
            valid + '?download=1',
            valid + '#fragment',
        )
        for url in urls:
            with self.subTest(url=url):
                arguments = install_arguments('a' * 64)
                arguments[4] = url
                self.assert_rejected_without_changes(arguments)

    def test_invalid_checksums_are_rejected_before_download_or_install(self):
        for checksum in ('', 'a' * 63, 'a' * 65, 'g' * 64, 'a' * 63 + '\n'):
            with self.subTest(checksum=repr(checksum)):
                self.assert_rejected_without_changes(install_arguments(checksum))

    def test_missing_duplicate_unknown_and_positional_arguments_are_rejected(self):
        valid = install_arguments('a' * 64)
        invalid = [
            ['install-release', '--version'],
            ['install-release', '--version', VERSION],
            valid[:-2],
            valid + ['--unknown', 'value'],
            valid + ['unexpected'],
        ]
        for flag, value in (('--version', VERSION), ('--url', release_url(VERSION)),
                            ('--sha256', 'a' * 64)):
            invalid.append(valid + [flag, value])
        for arguments in invalid:
            with self.subTest(arguments=arguments):
                self.assert_rejected_without_changes(arguments)

    def test_same_installer_accepts_new_release_parameters_and_records_installed_version(self):
        with self.installation() as fixture:
            installer_before = fixture.script.read_bytes()
            for version in (VERSION, '04bb45c-r2'):
                with self.subTest(version=version):
                    fixture.calls.write_text('')
                    result = self.run_installer(fixture, install_arguments(fixture.checksum, version))
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertIn('echo engine', (fixture.target / 'krkr2').read_text())
                    self.assertEqual(version + '\n', (fixture.target / '.engine-version').read_text())
                    self.assertIn(release_url(version), fixture.calls.read_text())
                    self.assertEqual([], list(fixture.root.glob('.krkr2-install.*')))
                    self.assertFalse(fixture.sourced.exists())
                    self.assertEqual(installer_before, fixture.script.read_bytes())

    def test_launcher_preserves_arguments_and_resource_working_directory(self):
        with tempfile.TemporaryDirectory(prefix='krkr2 launch ') as directory:
            root = Path(directory).resolve()
            binary = root / 'krkr2'
            binary.write_text('#!/usr/bin/python3\nimport json, os, sys\n'
                              'print(json.dumps([os.getcwd(), sys.argv[1:], '
                              'os.getenv("ALSA_CONFIG_PATH"), os.getenv("PULSE_SERVER")]))\n')
            binary.chmod(0o755)
            script = root / 'run.sh'
            script.write_text((BIN / 'droiddeck-krkr2-run').read_text()
                              .replace('/opt/krkr2', shlex.quote(str(root))))
            for server in ('', 'unix:/tmp/session audio/PS0'):
                for args in ([], ["--xp3=/root/ROMs/中文 'Game'/data.xp3"],
                             ['--game=/root/example', '--', '-controllerfocus=no']):
                    env = dict(os.environ, PULSE_SERVER=server, ALSA_CONFIG_PATH='/tmp/custom.conf')
                    result = subprocess.run(['bash', str(script)] + args, check=True,
                                            env=env, capture_output=True, text=True, timeout=10)
                    config = '/usr/local/lib/droiddeck-krkr2/asound.conf' if server else '/tmp/custom.conf'
                    self.assertEqual([str(root), ['-controllerfocus=yes'] + args, config, server],
                                     json.loads(result.stdout))


if __name__ == '__main__':
    unittest.main()
