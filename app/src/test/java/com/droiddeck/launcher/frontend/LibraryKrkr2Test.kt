package com.droiddeck.launcher.frontend

import com.droiddeck.launcher.runtime.DesktopCatalog
import com.droiddeck.launcher.runtime.LinuxRuntime
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
class LibraryKrkr2Test {
    @get:Rule val temp = TemporaryFolder()

    @Test fun isOptionalAndUsesTheGlobalRomsFolder() {
        val context = RuntimeEnvironment.getApplication()
        SessionPrefs.setRomsDir(context, "")
        assertTrue(Library.emulators(context) { true }.single { it.id == "krkr2" }.games.isEmpty())
        val dir = File(temp.root, "krkr/中文 'Game'").apply { mkdirs() }
        val game = File(dir, "data.xp3").apply { writeText("game") }
        val cover = File(dir, "cover.png").apply { writeText("art") }
        SessionPrefs.setRomsDir(context, temp.root.path)
        val emu = Library.emulators(context) { it == "krkr2" }.single { it.id == "krkr2" }
        assertTrue(emu.installed)
        assertEquals("krkr2", Library.packageId(emu.id))
        assertEquals("/usr/local/bin/droiddeck-krkr2-run", emu.program)
        assertEquals(game, emu.games.single().hostPath)
        assertEquals(cover, emu.games.single().art)
        assertEquals(listOf("--xp3=/root/ROMs/krkr/中文 'Game'/data.xp3"),
            Library.launchArgs(emu.id, emu.games.single().guestPath))
        assertEquals(listOf("--game=/root/ROMs/krkr/Loose Game"),
            Library.launchArgs(emu.id, "/root/ROMs/krkr/Loose Game"))
        assertFalse(Library.emulators(context) { it == "emulators" }.single { it.id == "krkr2" }.installed)
        assertFalse(Library.installing("krkr2", "onsyuri"))
        assertTrue(Library.installing("krkr2", "krkr2"))
        SessionPrefs.setRomsDir(context, "")
        assertTrue(Library.emulators(context) { true }.single { it.id == "krkr2" }.games.isEmpty())
    }

    @Test fun uninstallPreservesGamesSavesAndOtherEmulators() {
        val context = RuntimeEnvironment.getApplication()
        val root = LinuxRuntime.rootDir(context)
        val engine = File(root, "opt/krkr2/krkr2").apply { parentFile!!.mkdirs(); writeText("binary") }
        val marker = File(root, ".droiddeck-pkg-krkr2").apply { writeText("installed") }
        val save = File(temp.root, "savedata/save.dat").apply { parentFile!!.mkdirs(); writeText("save") }
        val ons = File(root, ".droiddeck-pkg-onsyuri").apply { writeText("installed") }
        DesktopCatalog.remove(context, DesktopCatalog.krkr2Entry())
        assertFalse(engine.exists())
        assertFalse(marker.exists())
        assertEquals("save", save.readText())
        assertTrue(ons.exists())
    }
}
