package com.droiddeck.launcher.frontend

import java.io.File
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class KirikiriGamesTest {
    @get:Rule val temp = TemporaryFolder()

    private fun file(path: String) = File(temp.root, path).apply {
        parentFile!!.mkdirs()
        writeText("")
    }

    @Test fun prefersLooseStartupThenDataArchiveAndSkipsGameAssets() {
        val loose = file("krkr/中文 Game/startup.tjs").parentFile
        file("krkr/中文 Game/data.xp3")
        file("krkr/中文 Game/patch.xp3")
        file("krkr/中文 Game/assets/startup.tjs")
        val archive = file("krkr2/Another/data.xp3")
        file("krkr2/Another/voice.xp3")
        file("krkr2/Another/patch2.xp3")
        assertEquals(listOf(loose, archive), KirikiriGames.scan(temp.root))
    }

    @Test fun acceptsAnUnambiguousArchiveAndRejectsPatchOnlyAndAmbiguousFolders() {
        val game = file("kirikiri/Series/Example/Game.XP3")
        file("kirikiri/Patch only/patch.xp3")
        file("kirikiri/Ambiguous/voice.xp3")
        file("kirikiri/Ambiguous/image.xp3")
        file("krkr/bios/data.xp3")
        file("krkr/savedata/startup.tjs")
        file("Unrelated/deep/data.xp3")
        assertEquals(listOf(game), KirikiriGames.scan(temp.root))
    }

    @Test fun acceptsTheGlobalRomsFolderBeingOneGameOrContainingLooseGames() {
        val loose = file("Example/startup.tjs").parentFile
        assertEquals(listOf(loose), KirikiriGames.scan(temp.root))
        file("startup.tjs")
        assertEquals(listOf(temp.root), KirikiriGames.scan(temp.root))
    }

    @Test fun recognizesNamedStartupArchivesAlongsideResourceArchives() {
        val start = file("krkr/9-nine-九次九日九重色/Start.xp3")
        file("krkr/9-nine-九次九日九重色/video.xp3")
        file("krkr/9-nine-九次九日九重色/patch.tjs")
        val startup = file("krkr/Another/Startup.XP3")
        file("krkr/Another/voice.xp3")
        val data = file("krkr/Uppercase/DATA.XP3")
        file("krkr/Uppercase/image.xp3")
        assertEquals(setOf(start, startup, data), KirikiriGames.scan(temp.root).toSet())
    }
}
