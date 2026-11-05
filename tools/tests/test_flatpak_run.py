import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "linuxfs/overlay/usr/local/bin/droiddeck-flatpak-run"


class FlatpakRunTest(unittest.TestCase):
    def launch(self, app, session_bus):
        with tempfile.TemporaryDirectory(prefix="flatpak run ") as directory:
            root = Path(directory)
            output = root / "args.json"
            flatpak = root / "flatpak"
            flatpak.write_text("#!/usr/bin/python3\nimport json, os, sys\n"
                              "with open(os.environ['ARGS_OUTPUT'], 'w') as f: json.dump(sys.argv[1:], f)\n")
            flatpak.chmod(0o755)
            dbus = root / "dbus-run-session"
            dbus.write_text('#!/bin/sh\n[ "$1" = -- ] || exit 1\nshift\nexec "$@"\n')
            dbus.chmod(0o755)
            env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ['PATH'],
                       ARGS_OUTPUT=str(output), DBUS_SESSION_BUS_ADDRESS=session_bus,
                       GAMESCOPE_WAYLAND_DISPLAY="gamescope-0")
            subprocess.run(["bash", str(SCRIPT), app, "/root/ROMs/psp/Game 'test'.iso"],
                           env=env, check=True, capture_output=True, timeout=10)
            return json.loads(output.read_text())

    def test_psp_roms_are_exposed_with_and_without_an_existing_session_bus(self):
        for bus in ("", "unix:path=/test/bus"):
            with self.subTest(bus=bus):
                self.assertEqual([
                    "run", "--nosocket=wayland", "--socket=x11", "--filesystem=/root/ROMs:ro",
                    "org.ppsspp.PPSSPP", "/root/ROMs/psp/Game 'test'.iso",
                ], self.launch("org.ppsspp.PPSSPP", bus))

    def test_other_apps_do_not_receive_roms_permission(self):
        self.assertFalse(any(arg.startswith("--filesystem=")
                             for arg in self.launch("org.example.App", "unix:path=/test/bus")))


if __name__ == "__main__":
    unittest.main()
