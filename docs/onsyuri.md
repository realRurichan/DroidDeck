# ONScripter Yuri through RetroArch

Select **ONScripter Yuri** in DroidDeck’s emulators list and choose **Install**.
The ONS core is optional and is not included in the APK. If the general Emulators
package is missing, it is installed first through the standard installer:
RetroArch with its cores and assets through apt, and PPSSPP through the Flatpak
helper on the packaged desktop. Both emulator cards show installation progress.
The ONS installation then downloads the pinned source and builds the core on the
device. Allow network access, free space
for compiler dependencies and a source checkout, and several minutes.

Then select a ROMs folder. Place each
extracted NScripter/ONScripter game under `ons/Game Name/`. `onsyuri/` and
`onscripter/` are also accepted. The ONScripter Yuri emulator page lists one entry
per game directory; selecting a game starts RetroArch with the installed core.
Opening the emulator itself opens the RetroArch menu.

Keep the game's assets, a suitable `default.ttf` font, and its original script
together. Recognized entry names are `0.txt`, `00.txt`, `nscr_sec.dat`,
`nscript.___`, `nscript.dat`, `onscript.nt2`, and `onscript.nt3`. Names are case
sensitive, matching the Linux engine. Archives must be extracted. Optional
`cover.png` or `cover.jpg` files appear as library artwork.

In RetroArch's Quick Menu → Core Options, set **Script Encoding** to **GBK**,
**SHIFTJIS**, or **UTF-8** as appropriate, save a game-specific option override,
and close/relaunch the content. The upstream default is GBK. The libretro port
uses core options rather than the standalone engine's `ons_args` file.
Mouse Mode and mouse sensitivity are also core options.

Use the game's own save/load menu. Upstream does not implement RetroArch save
states; saves are written in the game directory, which must be writable.
Keep that directory when moving or backing up a game. This engine supports
NScripter/ONScripter games, not arbitrary Windows visual novel executables.

## Installation and removal

The installer pins upstream commit `08f744b31cc1907b66a15f0402e62321a131ed81`
and its dependency commits. It builds the Linux ARM64 libretro target, then
installs the core and metadata. The APK contains only integration code and the
installer script; neither APK builds nor normal emulator installation build ONS.
No separate Android RetroArch APK or standalone ONS executable is installed.

Removing ONS deletes its core, metadata, notices and installation marker. It
preserves RetroArch, compiler dependencies, game files and game saves. The app
will not restore the core on the next session; installation is always explicit.

For developers, the optional cross-build helper can be run with an AArch64
GCC/G++ toolchain, Git, CMake and Make:

```sh
bash tools/onsyuri/build.sh --native build/onsyuri-core
```

The installed core lives at
`/usr/lib/aarch64-linux-gnu/libretro/onsyuri_libretro.so`; metadata is installed at
`/usr/share/libretro/info/onsyuri_libretro.info` and notices at
`/usr/share/doc/onsyuri/LICENSES.txt`.

Source and license: [OnscripterYuri](https://github.com/YuriSizuku/OnscripterYuri)
(GPL-2.0-or-later), with dependency licenses collected during installation.
