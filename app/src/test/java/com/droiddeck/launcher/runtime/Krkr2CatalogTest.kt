package com.droiddeck.launcher.runtime

import android.app.Application
import com.droiddeck.launcher.core.Downloader
import java.io.File
import java.util.function.BooleanSupplier
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28], application = Application::class)
class Krkr2CatalogTest {
    private val context get() = RuntimeEnvironment.getApplication()
    private val root get() = LinuxRuntime.rootDir(context)
    private val marker get() = File(root, ".droiddeck-pkg-krkr2")
    private val engine get() = File(root, "opt/krkr2/krkr2")

    @Before fun setUp() {
        root.mkdirs()
        marker.writeText("previous-version")
        engine.parentFile!!.mkdirs()
        engine.writeText("previous engine")
    }

    private fun manifest(version: String = "next-r1") = JSONObject()
        .put("schema", 1).put("id", "krkr2").put("version", version)
        .put("url", "https://github.com/realRurichan/DroidDeck/releases/download/krkr2-linux-arm64-$version/krkr2-linux-arm64.tar.gz")
        .put("sha256", "ABCDEF01".repeat(8)).put("size", 40_395_253L)

    @Test fun anUnavailableReleaseHasNoBundledVersionOrDownloadFallback() {
        val placeholder = DesktopCatalog.krkr2Entry()
        assertEquals("krkr2", placeholder.id)
        assertEquals("", placeholder.version)
        assertEquals("", placeholder.url)
        assertEquals("", placeholder.sha256)
        assertNull(DesktopCatalog.fetchKrkr2(download = { _, _ -> null }))
        assertNull(DesktopCatalog.fetchKrkr2(download = { _, _ -> "invalid JSON" }))
        assertNull(DesktopCatalog.fetchKrkr2(download = { _, _ -> throw java.io.IOException("offline") }))
    }

    @Test fun releaseMetadataIsValidatedAndChecksumNormalized() {
        val release = DesktopCatalog.parseKrkr2(manifest().toString())
        assertEquals("next-r1", release.version)
        assertEquals("abcdef01".repeat(8), release.sha256)
        assertEquals(40_395_253L, release.size)
        assertEquals("krkr2", release.kind)
        val invalid = listOf(
            "schema" to 2, "schema" to "1", "schema" to 1.5, "id" to "other",
            "version" to "", "version" to "../older", "version" to "old\n--url",
            "version" to 42, "version" to "x".repeat(129),
            "url" to "http://github.com/realRurichan/DroidDeck/releases/download/krkr2-linux-arm64-next-r1/krkr2-linux-arm64.tar.gz",
            "url" to "https://github.com/other/DroidDeck/releases/download/krkr2-linux-arm64-next-r1/krkr2-linux-arm64.tar.gz",
            "url" to "https://github.com/realRurichan/DroidDeck/releases/download/krkr2-linux-arm64-old-r1/krkr2-linux-arm64.tar.gz",
            "url" to manifest().getString("url") + "?redirect=other",
            "sha256" to "0".repeat(63), "sha256" to "g".repeat(64),
            "size" to 0, "size" to -1, "size" to "40395253", "size" to 1.5,
        )
        for ((field, value) in invalid) {
            assertThrows("$field=$value", Exception::class.java) {
                DesktopCatalog.parseKrkr2(manifest().put(field, value).toString())
            }
        }
        for (field in listOf("schema", "id", "version", "url", "sha256", "size")) {
            assertThrows("missing $field", Exception::class.java) {
                DesktopCatalog.parseKrkr2(manifest().apply { remove(field) }.toString())
            }
        }
    }

    @Test fun installResolvesAgainAndRecordsTheVersionActuallyPassedToTheInstaller() {
        var body = manifest("displayed-r1").toString()
        val requests = mutableListOf<String>()
        val download: (String, BooleanSupplier?) -> String? = { url, _ -> requests += url; body }
        val displayed = DesktopCatalog.fetchKrkr2(download = download)!!
        body = manifest("published-r2").toString()
        var invoked = false

        val problem = DesktopCatalog.installKrkr2(context, null, null, download) { argv, _, onLine ->
            invoked = true
            assertEquals(listOf("/bin/bash", "/usr/local/bin/droiddeck-krkr2-install", "install-release",
                "--version", "published-r2", "--url", manifest("published-r2").getString("url"),
                "--sha256", "abcdef01".repeat(8)), argv)
            assertEquals("previous-version", marker.readText())
            onLine("== STEP Install Krkr2")
            0
        }

        assertNull(problem)
        assertTrue(invoked)
        assertEquals("displayed-r1", displayed.version)
        assertEquals("published-r2", marker.readText())
        assertEquals(listOf(DesktopCatalog.KRKR2_CATALOG_URL, DesktopCatalog.KRKR2_CATALOG_URL), requests)
    }

    @Test fun failedReleaseLookupNeverStartsTheInstallerOrChangesTheExistingInstallation() {
        for (body in listOf(null, "invalid JSON", manifest().put("sha256", "bad").toString())) {
            val problem = DesktopCatalog.installKrkr2(context, null, null, { _, _ -> body }) { _, _, _ ->
                fail("Installer must not run without a valid current release")
                0
            }
            assertNotNull(problem)
            assertEquals("previous-version", marker.readText())
            assertEquals("previous engine", engine.readText())
        }
    }

    @Test fun failedAndCancelledInstallersDoNotRecordSuccess() {
        for (failure in listOf("exit", "message", "exception", "cancel")) {
            val cancelled = Downloader.Cancellation()
            val problem = DesktopCatalog.installKrkr2(context, cancelled, null,
                { _, _ -> manifest().toString() }) { _, _, onLine ->
                when (failure) {
                    "exit" -> 1
                    "message" -> { onLine("== FAIL Krkr2 installation"); 0 }
                    "exception" -> throw java.io.IOException("process failed")
                    else -> { cancelled.cancel(); 0 }
                }
            }
            assertNotNull(failure, problem)
            assertEquals(failure, "previous-version", marker.readText())
        }
    }

    @Test fun cancellationBeforeOrDuringReleaseLookupDoesNotLaunchAnInstaller() {
        for (beforeLookup in listOf(true, false)) {
            val cancelled = Downloader.Cancellation()
            if (beforeLookup) cancelled.cancel()
            var fetched = false
            val problem = DesktopCatalog.installKrkr2(context, cancelled, null, { _, token ->
                fetched = true
                assertSame(cancelled, token)
                cancelled.cancel()
                manifest().toString()
            }) { _, _, _ ->
                fail("A cancelled lookup must not launch an installer")
                0
            }
            assertNotNull(problem)
            assertEquals(!beforeLookup, fetched)
            assertEquals("previous-version", marker.readText())
        }
    }
}
