"""Release-boundary regressions; all injected private values are synthetic."""
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import zlib

from scripts import package_release, release_check


def png_chunk(kind, payload=b""):
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)


def screenshot(*extra):
    return (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", struct.pack(">2I5B", 1, 1, 8, 2, 0, 0, 0))
            + b"".join(extra) + png_chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00")) + png_chunk(b"IEND"))


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name).resolve()
        self.root = self.folder / "source"
        self.root.mkdir()
        for name in release_check.REQUIRED:
            self.write(name, b"Synthetic release test\n")
        self.write("LICENSE", (release_check.ROOT / "LICENSE").read_bytes())

    def write(self, name, data):
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
        return target

    def problems(self):
        return release_check.check(self.root)["problems"]

    def test_clean_source_round_trips_deterministically_with_no_machine_zip_metadata(self):
        self.write("docs/screenshots/synthetic.png", screenshot())
        self.write("start-mailcairn.sh", "python3 app.py\n")
        first, second = self.folder / "first.zip", self.folder / "second.zip"
        result = package_release.create_release(first, self.root)
        package_release.create_release(second, self.root)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        self.assertEqual(result["sha256"], hashlib.sha256(first.read_bytes()).hexdigest())
        self.assertEqual(first.with_suffix(".zip.sha256").read_text().strip(), result["sha256"] + "  first.zip")
        with zipfile.ZipFile(first) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(archive.read("mailcairn/LICENSE"), (release_check.ROOT / "LICENSE").read_bytes())
            for entry in archive.infolist():
                self.assertTrue(entry.filename.startswith("mailcairn/"))
                self.assertNotIn("..", Path(entry.filename).parts)
                self.assertFalse(entry.extra)
                self.assertFalse(entry.comment)
                self.assertEqual(entry.date_time, (2026, 11, 9, 0, 0, 0))
            self.assertEqual(archive.getinfo("mailcairn/start-mailcairn.sh").external_attr >> 16, 0o100755)

    def test_archives_credentials_and_private_source_paths_block_packaging(self):
        for name in ("docs/archive.sqlite3", "docs/archive.db-wal", "docs/.mailcairn-sync.json",
                     "docs/.mailcairn-credentials.json", "docs/.mailcairn-instance.json",
                     "docs/.env", "docs/account.key", "private-notes.txt", "tests/private.txt"):
            with self.subTest(name=name):
                target = self.write(name, "SYNTHETIC private artifact")
                self.assertTrue(self.problems())
                with self.assertRaisesRegex(ValueError, "Release checks failed"):
                    package_release.create_release(self.folder / "blocked.zip", self.root)
                self.assertFalse((self.folder / "blocked.zip").exists())
                target.unlink()

    def test_ignored_work_archives_and_transient_files_never_enter_zip(self):
        ignored = ("data/private.eml", "work/private.sqlite3", ".git/config", "tests/__pycache__/private.pyc",
                   "docs/previous.zip", "docs/session.log", "docs/notes.tmp", "docs/draft.md~")
        for name in ignored:
            self.write(name, "SYNTHETIC excluded data")
        output = self.folder / "release.zip"
        package_release.create_release(output, self.root)
        with zipfile.ZipFile(output) as archive:
            for name in ignored:
                self.assertNotIn("mailcairn/" + name, archive.namelist())
            self.assertEqual(len(archive.namelist()), release_check.check(self.root)["files_checked"])

    def test_only_exact_reviewed_mail_fixtures_are_allowed(self):
        name = "tests/fixtures/sample.eml"
        target = self.write(name, (release_check.ROOT / name).read_bytes())
        self.assertEqual(self.problems(), [])
        target.write_bytes(target.read_bytes() + b"\nSYNTHETIC unreviewed change")
        self.assertTrue(any("changed mail fixture" in problem for problem in self.problems()))
        target.unlink()
        for name in ("tests/fixtures/private.eml", "docs/private.mbox"):
            target = self.write(name, "From: synthetic@example.com\n\nPrivate test")
            self.assertTrue(any("mail fixture" in problem for problem in self.problems()))
            target.unlink()

    def test_absolute_paths_in_json_and_markdown_are_rejected_without_echoing_them(self):
        # Construct sensitive-looking examples so this test source is itself portable.
        windows = "Q:" + chr(92) + "Users" + chr(92) + "synthetic-person" + chr(92) + "build"
        paths = (windows, windows.replace(chr(92), "/"), "/" + "home/synthetic-person/build",
                 "/" + "Users/synthetic-person/build", "/" + "tmp/build-private/output",
                 chr(92) * 2 + "synthetic-host" + chr(92) + "private-share")
        for value in paths:
            for name, text in (("docs/check.json", json.dumps({"source": value})), ("docs/check.md", value)):
                with self.subTest(name=name, value=value):
                    target = self.write(name, text)
                    problems = self.problems()
                    self.assertTrue(any("absolute path" in item for item in problems))
                    self.assertNotIn(value, "\n".join(problems))
                    target.unlink()

    def test_generic_examples_urls_and_upstream_legal_text_remain_valid(self):
        self.write("docs/examples.md", "Use D:\\MyMail\\archive. Visit https://example.com/a and file example notes.\n")
        self.write("licenses/desktop/Upstream-LICENSE.txt", "Copyright upstream. Example: " + "Q:" + chr(92) + "upstream/build")
        self.assertEqual(self.problems(), [])
        self.write("licenses/desktop/manifest.json", json.dumps({"source": "Q:" + chr(92) + "upstream/build"}))
        self.assertTrue(any("absolute path" in problem for problem in self.problems()))

    def test_current_account_name_in_release_metadata_is_detected(self):
        self.write("docs/check.json", json.dumps({"author": "synthetic-release-account"}))
        with patch.dict(os.environ, {"USERNAME": "synthetic-release-account"}):
            self.assertTrue(any("Local account name" in problem for problem in self.problems()))

    def test_screenshot_metadata_corruption_and_trailing_payload_block_release(self):
        for data in (screenshot(png_chunk(b"tEXt", b"Author\x00synthetic-person")),
                     screenshot(png_chunk(b"eXIf", b"synthetic-private-location")),
                     screenshot(png_chunk(b"iTXt", b"Comment\x00private")),
                     screenshot() + b"hidden trailing data", screenshot()[:-3], b"not a png"):
            with self.subTest(length=len(data)):
                self.write("docs/screenshots/check.png", data)
                self.assertTrue(self.problems())
        self.write("docs/screenshots/check.png", screenshot())
        self.assertEqual(self.problems(), [])

    def test_credential_like_text_and_remote_static_resources_remain_blocked(self):
        token = "ghp_" + "A" * 36
        self.write("docs/check.json", json.dumps({"token": token}))
        self.assertTrue(any("Possible credential" in item for item in self.problems()))
        (self.root / "docs/check.json").unlink()
        self.write("mailcairn/static/index.html", '<img src="https://tracking.invalid/image.png">')
        self.assertTrue(any("Unexpected external" in item for item in self.problems()))

    def test_links_are_rejected_and_never_read_for_packaging(self):
        target = self.write("docs/linked.md", "SYNTHETIC external file")
        real_is_link = release_check.is_link

        def pretend_link(path):
            return path == target or real_is_link(path)

        # Platform-neutral regression for the rejection path; real OS symlink
        # creation requires privileges on some Windows test environments.
        with patch.object(release_check, "is_link", side_effect=pretend_link), patch.object(package_release, "is_link", side_effect=pretend_link):
            result = release_check.check(self.root)
            self.assertTrue(any("Symlink or junction" in item for item in result["problems"]))
            with self.assertRaisesRegex(ValueError, "Symlink or junction"):
                package_release.create_release(self.folder / "linked.zip", self.root)
        self.assertFalse((self.folder / "linked.zip").exists())

    def test_failed_release_preserves_previous_zip_and_writes_no_temp_artifact(self):
        output = self.folder / "release.zip"
        output.write_bytes(b"previous reviewed release")
        self.write("docs/private.eml", "SYNTHETIC private mail")
        with self.assertRaises(ValueError):
            package_release.create_release(output, self.root)
        self.assertEqual(output.read_bytes(), b"previous reviewed release")
        self.assertFalse(list(self.folder.glob(".mailcairn-release-*")))
        with self.assertRaisesRegex(ValueError, "outside"):
            package_release.create_release(self.root / "release.zip", self.root)

    def test_package_uses_checked_snapshot_when_source_changes_during_validation(self):
        original = b"Reviewed synthetic README\n"
        target = self.write("README.md", original)
        real_check = release_check.check

        def mutate_after_snapshot(root, content):
            target.write_bytes(b"UNREVIEWED late change")
            return real_check(root, content=content)

        output = self.folder / "snapshot.zip"
        with patch.object(package_release, "check", side_effect=mutate_after_snapshot):
            package_release.create_release(output, self.root)
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(archive.read("mailcairn/README.md"), original)


if __name__ == "__main__":
    unittest.main()
