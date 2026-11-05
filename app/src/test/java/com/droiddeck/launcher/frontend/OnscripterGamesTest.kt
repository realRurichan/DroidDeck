package com.droiddeck.launcher.frontend

import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class OnscripterGamesTest {
    @get:Rule val temp = TemporaryFolder()

    private fun file(path: String): File = File(temp.root, path).apply {
        parentFile!!.mkdirs()
        writeText("")
    }

    @Test fun recognizesEverySupportedScriptAndKeepsUnicodeTitles() {
        val names = listOf("0.txt", "00.txt", "nscr_sec.dat", "nscript.___", "nscript.dat", "onscript.nt2", "onscript.nt3")
        val entries = names.mapIndexed { i, name -> file("ons/游戏 $i/$name") }
        assertEquals(entries, OnscripterGames.scan(temp.root))
    }

    @Test fun listsEachGameOnceAndDoesNotScanItsAssetFolders() {
        val entry = file("ons/Example/0.txt")
        file("ons/Example/00.txt")
        file("ons/Example/nscript.dat")
        file("ons/Example/assets/0.txt")
        assertEquals(listOf(entry), OnscripterGames.scan(temp.root))
    }

    @Test fun scansAliasesNestedGamesAndLooseGamesButNotUnrelatedFiles() {
        val entries = listOf(file("Loose/nscript.dat"), file("ons/Series/Game/0.txt"),
            file("onscripter/Another/00.txt"), file("onsyuri/Last/onscript.nt3"))
        file("ons/README.txt")
        file("ons/Not a game/arc.nsa")
        file("ons/bios/0.txt")
        file("firmware/nscript.dat")
        file("unrelated/deep/0.txt")
        assertEquals(entries, OnscripterGames.scan(temp.root))
    }

    @Test fun acceptsAGameDirectoryAsTheRomsRoot() {
        val entry = file("00.txt")
        file("assets/0.txt")
        assertEquals(listOf(entry), OnscripterGames.scan(temp.root))
    }
}
