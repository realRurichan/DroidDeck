import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest


BIN = Path(__file__).resolve().parents[1] / 'linuxfs/overlay/usr/local/bin'


class Krkr2InstallTest(unittest.TestCase):
    def install(self, failure=''):
        with tempfile.TemporaryDirectory(prefix="krkr2 'install' ") as directory:
            root = Path(directory)
            commands = root / 'bin'
            commands.mkdir()
            recipe = root / 'recipe'
            recipe.mkdir()
            (recipe / 'packages.txt').write_text('cmake\ngit\n')
            (recipe / 'build.sh').write_text(
                '#!/bin/bash\nset -eu\n[ "$FAILURE" != build ] || exit 8\n'
                'mkdir -p "$2"\nprintf "engine" > "$2/krkr2"\nchmod +x "$2/krkr2"\n')
            for name, body in {'uname': 'echo aarch64', 'apt-get': 'exit 0',
                               'droiddeck-root': '[ "$FAILURE" != apt ]'}.items():
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
            env = dict(os.environ, PATH=str(commands) + os.pathsep + os.environ['PATH'], FAILURE=failure)
            result = subprocess.run(['bash', str(script), 'install'], env=env, capture_output=True,
                                    text=True, timeout=10)
            return result, (target / 'krkr2').read_text(), list(root.glob('.krkr2-install.*'))

    def test_success_installs_the_engine_and_removes_build_files(self):
        result, engine, leftovers = self.install()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('engine', engine)
        self.assertEqual([], leftovers)

    def test_dependency_and_build_failures_preserve_an_existing_installation(self):
        for failure in ('apt', 'build'):
            with self.subTest(failure=failure):
                result, engine, leftovers = self.install(failure)
                self.assertNotEqual(0, result.returncode)
                self.assertIn('== FAIL Krkr2 installation', result.stdout)
                self.assertEqual('previous engine', engine)
                self.assertEqual([], leftovers)

    def test_launcher_preserves_arguments_and_resource_working_directory(self):
        with tempfile.TemporaryDirectory(prefix='krkr2 launch ') as directory:
            root = Path(directory)
            binary = root / 'krkr2'
            binary.write_text('#!/usr/bin/python3\nimport json, os, sys\n'
                              'print(json.dumps([os.getcwd(), sys.argv[1:]]))\n')
            binary.chmod(0o755)
            script = root / 'run.sh'
            script.write_text((BIN / 'droiddeck-krkr2-run').read_text()
                              .replace('/opt/krkr2', shlex.quote(str(root))))
            for args in ([], ["--xp3=/root/ROMs/中文 'Game'/data.xp3"]):
                result = subprocess.run(['bash', str(script)] + args, check=True,
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual([str(root), args], json.loads(result.stdout))


if __name__ == '__main__':
    unittest.main()
