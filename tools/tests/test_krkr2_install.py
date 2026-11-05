import hashlib
import io
import json
import tarfile
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest


BIN = Path(__file__).resolve().parents[1] / 'linuxfs/overlay/usr/local/bin'


class Krkr2InstallTest(unittest.TestCase):
    def install(self, failure='', missing=False):
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
            (recipe / 'binary.env').write_text(
                'KRKR2_BINARY_URL=https://example.test/engine.tar.gz\nKRKR2_BINARY_SHA256=' + checksum + '\n')
            bodies = {
                'uname': 'echo aarch64',
                'apt-get': 'exit 0',
                'dpkg-query': '[ "$MISSING" != 1 ] && [ "$FAILURE" != apt ] && printf installed',
                'droiddeck-root': 'echo "apt $*" >> "$CALLS"; [ "$FAILURE" != apt ]',
                'curl': '[ "$FAILURE" != download ] || exit 7\n'
                        'while [ "$1" != --output ]; do shift; done\ncp "$ARCHIVE" "$2"',
                'mv': '[ "$FAILURE" != place ] || [ "${1##*/}" != package ] || exit 9\nexec /bin/mv "$@"',
            }
            for name, body in bodies.items():
                command = commands / name
                command.write_text('#!/bin/sh\n' + body + '\n')
                command.chmod(0o755)
            target = root / 'installed'
            target.mkdir()
            (target / 'krkr2').write_text('previous engine')
            script = root / 'install.sh'
            script.write_text((BIN / 'droiddeck-krkr2-install').read_text()
                              .replace('/usr/local/lib/droiddeck-krkr2', shlex.quote(str(recipe)))
                              .replace('/root/.krkr2-install.XXXXXX', shlex.quote(str(root / '.krkr2-install.XXXXXX')))
                              .replace('/opt/krkr2', shlex.quote(str(target))))
            calls = root / 'calls'
            calls.touch()
            env = dict(os.environ, PATH=str(commands) + os.pathsep + os.environ['PATH'],
                       FAILURE=failure, MISSING=str(int(missing)), ARCHIVE=str(archive), CALLS=str(calls))
            result = subprocess.run(['bash', str(script), 'install'], env=env, capture_output=True,
                                    text=True, timeout=10)
            return result, (target / 'krkr2').read_text(), list(root.glob('.krkr2-install.*')), calls.read_text()

    def test_success_downloads_verifies_and_installs_without_apt_when_libraries_exist(self):
        result, engine, leftovers, calls = self.install()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('echo engine', engine)
        self.assertEqual([], leftovers)
        self.assertEqual('', calls)
        self.assertIn('== STEP Verify Krkr2 download', result.stdout)

    def test_only_missing_runtime_libraries_are_installed(self):
        result, _, _, calls = self.install(missing=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('install -y -q --no-install-recommends libglx0', calls)
        self.assertNotIn('cmake', calls)

    def test_failures_preserve_an_existing_installation_and_clean_temporary_files(self):
        for failure in ('apt', 'download', 'checksum', 'extract', 'runtime', 'place'):
            with self.subTest(failure=failure):
                result, engine, leftovers, _ = self.install(failure)
                self.assertNotEqual(0, result.returncode)
                self.assertIn('== FAIL Krkr2 installation', result.stdout)
                self.assertEqual('previous engine', engine)
                self.assertEqual([], leftovers)

    def test_launcher_preserves_arguments_and_resource_working_directory(self):
        with tempfile.TemporaryDirectory(prefix='krkr2 launch ') as directory:
            root = Path(directory)
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
