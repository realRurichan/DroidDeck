package com.droiddeck.launcher.frontend

import com.droiddeck.launcher.session.SessionPrefs
import java.io.File
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [33])
class LibraryOnscripterTest {
    @get:Rule val temp = TemporaryFolder()

    @Test fun launchesTheSelectedScriptWithRetroArchAndTheBundledCore() {
        val context = RuntimeEnvironment.getApplication()
        val game = File(temp.root, "ons/中文 Game").apply { mkdirs() }
        File(game, "0.txt").writeText("")
        File(game, "nscript.dat").writeText("")
        val cover = File(game, "cover.png").apply { writeText("cover") }
        SessionPrefs.setRomsDir(context, temp.root.path)
        val emu = Library.emulators(context) { it == "onsyuri" }.single { it.id == "onsyuri" }
        assertTrue(emu.installed)
        assertEquals("onsyuri", Library.packageId(emu.id))
        assertEquals("/usr/bin/retroarch", emu.program)
        val rom = emu.games.single()
        assertEquals("中文 Game", rom.name)
        assertEquals(cover, rom.art)
        assertEquals(listOf("-f", "-L", OnscripterGames.core, "/root/ROMs/ons/中文 Game/0.txt"),
            Library.launchArgs(emu.id, rom.guestPath))
        assertFalse(Library.emulators(context) { it == "emulators" }.single { it.id == "onsyuri" }.installed)
        assertFalse(Library.emulators(context) { false }.single { it.id == "onsyuri" }.installed)
    }

    @Test fun removingOnsPreservesRetroArchAndGames() {
        val context = RuntimeEnvironment.getApplication()
        val root = com.droiddeck.launcher.runtime.LinuxRuntime.rootDir(context)
        val paths = listOf("usr/lib/aarch64-linux-gnu/libretro/onsyuri_libretro.so",
            "usr/share/libretro/info/onsyuri_libretro.info", "usr/share/doc/onsyuri/LICENSES.txt",
            ".droiddeck-pkg-onsyuri")
        for (path in paths) File(root, path).apply { parentFile!!.mkdirs(); writeText("installed") }
        val retroarch = File(root, "usr/bin/retroarch").apply { parentFile!!.mkdirs(); writeText("retroarch") }
        val save = File(temp.root, "save1.dat").apply { writeText("save") }
        val entry = com.droiddeck.launcher.runtime.DesktopCatalog.onsyuriEntry()
        com.droiddeck.launcher.runtime.DesktopCatalog.remove(context, entry)
        paths.forEach { assertFalse(File(root, it).exists()) }
        assertEquals("retroarch", retroarch.readText())
        assertEquals("save", save.readText())
    }

    @Test fun onsInstallationIncludesTheSharedEmulatorsPackage() {
        assertTrue(Library.installing("onsyuri", "onsyuri"))
        assertTrue(Library.installing("retroarch", "onsyuri"))
        assertTrue(Library.installing("ppsspp", "onsyuri"))
        assertFalse(Library.installing("retroarch", null))
        assertTrue(Library.installing("retroarch", "emulators"))
        assertTrue(Library.installing("ppsspp", "emulators"))
        assertFalse(Library.installing("onsyuri", "emulators"))
    }

    @Test fun retroArchRemainsInstalledWhenOnlyItsDependencyStepSucceeded() {
        val emulators = Library.emulators(RuntimeEnvironment.getApplication()) { it == "retroarch" }
        assertTrue(emulators.single { it.id == "retroarch" }.installed)
        assertFalse(emulators.single { it.id == "onsyuri" }.installed)
        assertFalse(emulators.single { it.id == "ppsspp" }.installed)
    }

}
