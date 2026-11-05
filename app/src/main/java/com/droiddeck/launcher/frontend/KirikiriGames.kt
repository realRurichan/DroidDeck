package com.droiddeck.launcher.frontend

import java.io.File

internal object KirikiriGames {
    val folders = setOf("krkr", "krkr2", "kirikiri")

    fun scan(root: File): List<File> {
        val found = linkedMapOf<String, File>()
        fun add(dir: File): Boolean {
            val files = dir.listFiles().orEmpty()
            val entry = when {
                files.any { it.isFile && it.name == "startup.tjs" } -> dir
                else -> listOf("data.xp3", "start.xp3", "startup.xp3").firstNotNullOfOrNull { name ->
                    files.firstOrNull { it.isFile && it.name.equals(name, true) }
                }
                    ?: files.filter { it.isFile && it.extension.equals("xp3", true) &&
                        !it.nameWithoutExtension.startsWith("patch", true) }.singleOrNull()
            } ?: return false
            found.putIfAbsent(entry.canonicalPath, entry)
            return true
        }
        if (add(root)) return found.values.toList()
        for (dir in root.listFiles().orEmpty().filter { it.isDirectory }.sortedBy { it.name }) {
            if (dir.name.lowercase() in folders) {
                dir.walkTopDown().maxDepth(4).onEnter {
                    it.name.lowercase() !in setOf("bios", "firmware", "savedata") && !add(it)
                }.forEach { }
            } else if (dir.name.lowercase() !in setOf("bios", "firmware", "savedata")) add(dir)
        }
        return found.values.toList()
    }
}
