# Krkr2 in DroidDeck

Krkr2 is a separate, optional Linux engine. Choose **Krkr2 → Install** in
Emulators & Apps. Installing DroidDeck, RetroArch, PPSSPP or ONS does not install
Krkr2. Its engine is not embedded in the APK.

Krkr2 uses the existing global **ROMs folder** setting. No second directory
setting is required. You can choose, change or clear that global directory in
DroidDeck. With no directory selected, the game list is empty.

Place each extracted game in `krkr/Game Name/`; `krkr2/` and `kirikiri/` are also
recognized. A directory containing `startup.tjs` takes precedence, then
`data.xp3`, `Start.xp3` or `startup.xp3` (archive names are case-insensitive).
A single other XP3 archive is accepted when unambiguous. Patch-only
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

Source: [2468785842/krkr2](https://github.com/2468785842/krkr2), based on dev
`3dcfb29aa8a7ed47981e1037db4b549dc310216a`. The recipe currently pins contribution
commit `72932a464b7a7e12c73354f9c1d424cafcaa8ac0` in
[realRurichan/krkr2](https://github.com/realRurichan/krkr2/tree/fix/psbfile-linux-launch).
It preserves the desktop `--game` / `--xp3` interface, pins vcpkg, omits Cocos'
unused x86-only FMOD backend, and retains Krkr2's OpenAL mixer. LLD resolves the
engine's static library cycles. Engine changes live in the contribution branch;
the packaging recipe only carries the Cocos ARM64 packaging changes.
The fixes are submitted in [upstream PR #54](https://github.com/2468785842/krkr2/pull/54).

The engine fixes optimized TJS empty-string accesses, Linux save directory
creation, deletion of missing save files, and Blend2D font-buffer ownership.
PSBFile now accepts files and Octet data, registers resources through the shared
PSB media registry, preserves the last successful data on failed reloads, and
rejects several invalid array/index/offset forms. This does not establish full
compatibility with the proprietary Windows plugin or PSB v4.
The root object preserves its native Dictionary type. KAG `emb escape=false`
executes expanded tags as documented by the existing KAGParser plugin, while
the default still escapes them. A phone test reached the visible game title
menu; full gameplay, audio/video and save compatibility remain separate checks.
The desktop key converter also maps Cocos `KEY_ENTER` to TJS `VK_RETURN`,
so normal Enter and the controller's A mapping reach game scripts.
`layerExBTOA.dll` now provides `Layer.clipAlphaRect`: alpha masks, destination
clipping, optional outside clearing, premultiplied colors and overlapping/shared
images are handled. This covers this method, not every method of that plugin.
An isolated phone game progressed through the previously failing character
transition and later scenes; full-game compatibility is not established.

Krkr2 sessions automatically map physical and on-screen controllers to keyboard
and mouse input. D-pad/left stick sends arrows, A sends Enter, B sends Esc,
Menu/Start sends a right mouse click for the game's own context-menu action,
right stick moves the pointer, X clicks the left mouse button, LB sends Page Up,
RB holds Ctrl, R3 sends Space, and Y opens the keyboard. Triggers scroll.
The Linux launcher enables `-controllerfocus=yes`: arrow keys navigate visible,
enabled KAG `ButtonLayer` controls by their position, including buttons whose
scripts disable normal focus. Modal dialogs constrain the selection; hidden,
clipped and disabled buttons are skipped. Enter confirms a selected button
through the existing hit-tested mouse click path, including mouse-only handlers,
without also sending Enter to that button. Independent text controls retain
their arrow input. This uses no game names, button names or fixed coordinates.
Custom menus that do not expose KAG buttons still need their own keyboard
handling or the right-stick pointer and X click.
Games decide what these inputs do; a game's right-click action can open its menu
or hide the message box, depending on its configuration. Typical KAG games use Ctrl for fast-forward
and Page Up for history. Releasing controls, leaving the profile, losing focus
or disconnecting a controller releases held inputs. Other emulator sessions
keep their normal controller input.

The optional `krkr2-arm64.yml` workflow builds the native ARM64 engine, verifies
its architecture and `--help`, and runs the upstream `psbfile-runtime` CTest.
It also registers `x11-keyboard-runtime`, which uses XTest to verify real key
down/up delivery for Return, keypad Enter, Escape, Down and Ctrl, then exits
normally. The keyboard fixture contains no commercial game files.
`x11-controller-focus-runtime` checks spatial navigation with a synthetic menu,
default-off behavior, reverse creation order, excluded buttons, text input,
modal focus and Enter activation.
`layer-alpha-runtime` checks mask pixels, clipping, clear values, negative and
extreme coordinates, shared/overlapping images, premultiplied RGB, invalid
arguments and normal event-loop exit using an original synthetic fixture.
Generated fixtures cover PSB v1/v2/v3, MDF, nested resources, directory listing,
file/memory constructors, reload behavior and malformed input. An additional
synthetic XP3 regression checks archive-root lookup, empty strings, binary saves
and deletion. Separate matching debug symbols are retained for crash diagnosis.
These checks do not replace gameplay testing in DroidDeck on a phone and are
not part of the mandatory APK build.
