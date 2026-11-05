# Krkr2 in DroidDeck

Krkr2 is a separate, optional Linux engine. Choose **Krkr2 → Install** in
Emulators & Apps. Installing DroidDeck, RetroArch, PPSSPP or ONS does not install
Krkr2. Its engine is not embedded in the APK.

Krkr2 uses the existing global **ROMs folder** setting. No second directory
setting is required. You can choose, change or clear that global directory in
DroidDeck. With no directory selected, the game list is empty.

Place each extracted game in `krkr/Game Name/`; `krkr2/` and `kirikiri/` are also
recognized. A directory containing `startup.tjs` takes precedence, then
`data.xp3`. A single other XP3 archive is accepted when unambiguous. Patch-only
and ambiguous archive folders are not listed. Keep all game assets and patches
together; do not rename patch archives into entry points. `cover.png` or
`cover.jpg` can be used as library artwork.

Selecting a game passes its directory or archive as one argument to Krkr2's
desktop launcher inside the Linux session. Opening Krkr2 without a game opens
its file browser. The engine is independent of RetroArch and needs no libretro
core. Compatibility depends on the game and its required plugins; Windows DLLs
are not automatically usable as native ARM64 plugins.

The installer downloads a pinned prebuilt ARM64 engine (about 40 MB), verifies
its SHA-256, extracts it and checks `--help` before replacing an existing engine.
Only missing runtime libraries are installed with apt; no compiler or vcpkg
build runs on the phone. A failed download, checksum or engine check leaves
the previous installation intact. It requires the Ubuntu ARM64 runtime and a
network connection. The package URL and checksum are in `binary.env`.

The engine and resources are installed under `/opt/krkr2`. Removing Krkr2 deletes
that installation and its marker, leaving the ROM directory and game saves
untouched. The runtime installation log is `logs/tools/krkr2.log`.

Source: [2468785842/krkr2](https://github.com/2468785842/krkr2), pinned to
`3dcfb29aa8a7ed47981e1037db4b549dc310216a` from the upstream development branch,
which provides the desktop `--game` / `--xp3` launch interface. The build recipe
pins vcpkg as well, omits Cocos' unused x86-only FMOD backend, and retains Krkr2's
own OpenAL audio mixer. It adds missing Linux header declarations and uses LLD
to resolve the engine's static library cycles. The original icon and upstream
license are retained.

The optional `krkr2-arm64.yml` workflow runs the same recipe on native ARM64,
checks the ELF architecture and `--help`, and runs a synthetic TJS game under
X11 using a path containing Unicode, spaces and quotes. It then saves a separate
engine artifact. This does not replace testing games in DroidDeck on a phone,
and is not part of the mandatory APK build.
