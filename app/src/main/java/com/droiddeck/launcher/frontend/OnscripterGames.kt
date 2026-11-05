package com.droiddeck.launcher.frontend

import java.io.File

internal object OnscripterGames {
    val folders = listOf("ons", "onsyuri", "onscripter")
    const val core = "/usr/lib/aarch64-linux-gnu/libretro/onsyuri_libretro.so"
    private val scripts = listOf("0.txt", "00.txt", "nscr_sec.dat", "nscript.___", "nscript.dat", "onscript.nt2", "onscript.nt3")

    fun scan(root: File): List<File> {
        fun script(dir: File) = scripts.asSequence().map { File(dir, it) }.firstOrNull { it.isFile }
        val found = linkedMapOf<String, File>()
        fun add(dir: File): Boolean {
            val entry = script(dir) ?: return false
            found.putIfAbsent(entry.canonicalPath, entry)
            return true
        }
        if (add(root)) return found.values.toList()
        for (dir in root.listFiles().orEmpty().filter { it.isDirectory }.sortedBy { it.name }) {
            if (dir.name.lowercase() in folders) {
                dir.walkTopDown().maxDepth(4).onEnter {
                    it.name.lowercase() !in setOf("bios", "firmware") && !add(it)
                }.forEach { }
            } else if (dir.name.lowercase() !in setOf("bios", "firmware")) add(dir)
        }
        return found.values.toList()
    }
}
