"""Fault-injection regressions for durable imports and safe archive recovery.

Fixtures are synthetic. These tests inspect externally observable SQLite state
after cancellation, a process exit, or a failed write; they do not assert SQL
statement counts or depend on timing for transaction boundaries.
"""
from collections import Counter
from contextlib import closing, contextmanager
from email.message import EmailMessage
import errno
import hashlib
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import tracemalloc
import unittest
from unittest.mock import patch

from mailcairn.parse import get_attachment
from mailcairn.store import Store, restore_backup
from tests.helpers import mbox, message


class ResilienceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "archive.sqlite3")

    def source(self, count=6):
        source = self.root / "synthetic.mbox"
        source.write_bytes(mbox(*(message(f"Durable {i}", body=f"unique marker{i}end",
                                         message_id=f"<durable-{i}@example.com>")
                                 for i in range(count))))
        return source

    def test_large_original_integrity_is_streamed_and_corruption_rejected_on_restore(self):
        source = self.root / "large.eml"
        source.write_bytes(message("Large synthetic message", body="x" * (8 * 1024 * 1024)))
        self.assertEqual(self.store.import_file(source)["added"], 1)
        tracemalloc.start()
        try:
            verified = self.store.verify()
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertEqual(verified["mismatches"], [])
        # This measures Python allocations, not SQLite native memory or RSS.
        self.assertLess(peak, 3 * 1024 * 1024)
        with self.store.db() as db:
            with db.blobopen("messages", "raw", 1, readonly=False) as blob:
                blob.seek(len(blob) - 1)
                blob.write(b"!")
        self.assertEqual(self.store.verify()["mismatches"], [1])
        backup = self.root / "corrupt.sqlite3"
        self.store.backup(backup)
        target = self.root / "restored" / "archive.sqlite3"
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            restore_backup(backup, target)
        self.assertFalse(target.exists())

    def assert_consistent(self, run):
        output = io.BytesIO()
        self.store.export_receipt(run, output)
        report = json.loads(output.getvalue())
        statuses = Counter(item["status"] for item in report["items"])
        self.assertEqual(report["total"], len(report["items"]))
        for field, status in (("added", "added"), ("duplicates", "duplicate"), ("skipped", "skipped")):
            self.assertEqual(report[field], statuses[status])
        with self.store.db() as db:
            for item in report["items"]:
                if item["status"] == "skipped":
                    self.assertIsNone(item["message_row"])
                else:
                    saved = db.execute("SELECT sha256,raw FROM messages WHERE id=?",
                                       (item["message_row"],)).fetchone()
                    self.assertIsNotNone(saved)
                    self.assertEqual(saved[0], item["sha256"])
                    self.assertEqual(hashlib.sha256(saved[1]).hexdigest(), saved[0])
        verified = self.store.verify()
        self.assertEqual(verified["mismatches"], [])
        self.assertEqual((verified["sqlite"], verified["search_index"], verified["receipts"]), ("ok", "ok", "ok"))
        return report

    def test_failed_receipt_insert_rolls_back_message_and_fts_together(self):
        # Abort the second receipt item, after its corresponding message INSERT.
        # Regardless of batching, it must never leave an unreceipted message.
        with self.store.db() as db:
            db.execute("""CREATE TRIGGER fail_receipt BEFORE INSERT ON import_items
                          WHEN new.ordinal=2 BEGIN
                          SELECT RAISE(ABORT, 'synthetic storage failure'); END""")
        source = self.source()
        failed = self.store.import_file(source)
        self.assertEqual(failed["status"], "failed")
        report = self.assert_consistent(failed["id"])
        self.assertEqual(self.store.stats()["messages"], report["added"])
        self.assertLess(report["added"], 2)
        with self.store.db() as db:
            db.execute("DROP TRIGGER fail_receipt")
        retried = self.store.import_file(source)
        self.assertEqual(retried["status"], "complete")
        self.assertEqual(retried["duplicates"], report["added"])
        self.assertEqual(self.store.stats()["messages"], 6)
        self.assert_consistent(retried["id"])

    def test_progress_describes_only_committed_searchable_mail(self):
        seen = []

        def progress(info):
            # Independent connections must see every message that UI counts show.
            receipt = self.store.receipt(info["import_id"])
            self.assertEqual((receipt["total"], receipt["added"]), (info["total"], info["added"]))
            self.assertEqual(self.store.search({})["total"], info["added"])
            seen.append(info["total"])

        result = self.store.import_file(self.source(210), progress=progress)
        self.assertTrue(seen)
        self.assertEqual(seen[-1], 210)
        self.assertEqual(seen, sorted(set(seen)))
        self.assert_consistent(result["id"])

    def test_process_exit_keeps_durable_receipts_and_reimport_finishes(self):
        source = self.source(240)
        program = """
import os, sys
from mailcairn import store as module
module.IMPORT_BATCH_ITEMS = 2
module.IMPORT_BATCH_BYTES = 1024 ** 3
module.IMPORT_BATCH_SECONDS = 3600
store = module.Store(sys.argv[1])
original = module.parse_message
seen = 0
def terminate_mid_batch(raw):
    global seen
    seen += 1
    if seen == 4:
        # Two records committed, a third uncommitted. No finally/rollback runs.
        os._exit(73)
    return original(raw)
module.parse_message = terminate_mid_batch
store.import_file(sys.argv[2])
"""
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, "-c", program, str(self.store.path), str(source)],
                                cwd=root, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 73, result.stderr.decode(errors="replace"))
        reopened = Store(self.store.path)
        reopened.recover_interrupted()
        receipt = reopened.stats()["imports"][0]
        self.assertEqual(receipt["status"], "interrupted")
        self.assertEqual(receipt["added"], 2, "The uncommitted third message must be rolled back after process exit")
        self.assertEqual(reopened.stats()["messages"], 2)
        self.assert_consistent(receipt["id"])
        retried = reopened.import_file(source)
        self.assertEqual((retried["status"], retried["duplicates"]), ("complete", receipt["added"]))
        self.assertEqual(reopened.stats()["messages"], 240)
        self.assert_consistent(retried["id"])

    def test_cancel_before_first_record_creates_empty_cancelled_receipt(self):
        result = self.store.import_file(self.source(), cancelled=lambda: True)
        self.assertEqual((result["status"], result["total"]), ("cancelled", 0))
        self.assertEqual(self.store.stats()["messages"], 0)
        self.assert_consistent(result["id"])

    def test_parser_exception_isolated_and_later_mail_is_imported(self):
        # A data-dependent exception in the stdlib parser must not discard the
        # rest of an archive. Unexpected programming exceptions still surface.
        from mailcairn import store as module
        real_parse = module.parse_message

        def malformed_header(raw):
            if b"Subject: Durable 1\n" in raw:
                from email.errors import HeaderParseError
                raise HeaderParseError("synthetic broken MIME header")
            return real_parse(raw)

        with patch.object(module, "parse_message", side_effect=malformed_header):
            result = self.store.import_file(self.source(3))
        self.assertEqual((result["status"], result["added"], result["skipped"]), ("partial", 2, 1))
        report = self.assert_consistent(result["id"])
        self.assertEqual(report["items"][1]["status"], "skipped")
        self.assertIn("MIME header", report["items"][1]["reason"])
        self.assertEqual(self.store.search({"q": "marker2end"})["total"], 1)

    def test_receipt_export_is_one_snapshot_while_import_advances(self):
        run = self.store.import_file(self.source(1))["id"]
        store = self.store

        class ConcurrentWriter(io.BytesIO):
            updated = False

            def write(self, data):
                if not self.updated:
                    self.updated = True
                    # A second connection commits after the JSON header has
                    # been read and before its item stream is consumed.
                    with store.db() as db:
                        row = db.execute("SELECT message_row,sha256 FROM import_items WHERE import_id=?", (run,)).fetchone()
                        db.execute("INSERT INTO import_items VALUES(?,?,?,?,?,?,?,?)",
                                   (run, 2, 0, 0, "duplicate", "", row[0], row[1]))
                        db.execute("UPDATE imports SET total=total+1,duplicates=duplicates+1 WHERE id=?", (run,))
                return super().write(data)

        output = ConcurrentWriter()
        self.store.export_receipt(run, output)
        report = json.loads(output.getvalue())
        self.assertEqual(report["total"], len(report["items"]))
        self.assertEqual(report["duplicates"], sum(item["status"] == "duplicate" for item in report["items"]))
        self.assertEqual(self.store.receipt(run)["total"], 2)

    def test_restore_rejects_stale_search_index_without_leaving_target(self):
        self.store.import_file(self.source(1))
        backup = self.root / "stale.sqlite3"
        self.store.backup(backup)
        with closing(sqlite3.connect(backup)) as db:
            db.execute("UPDATE messages SET body='unindexed replacement'")
            db.commit()
        before = backup.read_bytes()
        target = self.root / "restored" / "archive.sqlite3"
        with self.assertRaises(ValueError):
            restore_backup(backup, target)
        self.assertFalse(target.exists())
        self.assertEqual(backup.read_bytes(), before, "Restoring must not repair or mutate its source backup")
        self.assertEqual(list(target.parent.glob("*")), [])

    def test_failed_backup_publish_preserves_previous_good_backup(self):
        self.store.import_file(self.source(1))
        backup = self.root / "snapshot.sqlite3"
        self.store.backup(backup)
        before = backup.read_bytes()
        with patch("mailcairn.store.os.replace", side_effect=OSError("synthetic publish failure")):
            with self.assertRaises(OSError):
                self.store.backup(backup)
        self.assertEqual(backup.read_bytes(), before)
        self.assertEqual(list(self.root.glob(".mailcairn-backup-*")), [])

    def test_restore_publish_race_never_overwrites_the_new_target(self):
        self.store.import_file(self.source(1))
        backup = self.root / "snapshot.sqlite3"
        self.store.backup(backup)
        target = self.root / "restored" / "archive.sqlite3"
        sentinel = b"created by another process during restore"
        real_link = os.link

        def race(source, destination, *args, **kwargs):
            Path(destination).write_bytes(sentinel)
            return real_link(source, destination, *args, **kwargs)

        with patch("mailcairn.store.os.link", side_effect=race):
            with self.assertRaises((ValueError, FileExistsError)):
                restore_backup(backup, target)
        self.assertEqual(target.read_bytes(), sentinel)
        self.assertEqual(set(target.parent.iterdir()), {target})

    def test_restore_publish_failure_leaves_no_archive_or_sidecars(self):
        self.store.import_file(self.source(1))
        backup = self.root / "snapshot.sqlite3"
        self.store.backup(backup)
        target = self.root / "restored" / "archive.sqlite3"
        with patch("mailcairn.store.os.link", side_effect=OSError("synthetic destination failure")):
            with self.assertRaises(OSError):
                restore_backup(backup, target)
        self.assertFalse(target.exists())
        self.assertEqual(list(target.parent.iterdir()), [])

    def test_eml_mbox_roundtrip_keeps_unicode_and_binary_attachment(self):
        payload = bytes(range(256)) * 8
        raw = message("凭证 café", "Unicode body 雪", attachment=("凭证.bin", payload), crlf=True)
        source = self.root / "roundtrip.eml"
        source.write_bytes(raw)
        self.store.import_file(source)
        exported = io.BytesIO()
        self.assertEqual(self.store.export_mbox({}, exported), 1)
        path = self.root / "roundtrip.mbox"
        path.write_bytes(exported.getvalue())
        other = Store(self.root / "roundtrip.sqlite3")
        run = other.import_file(path)
        self.assertEqual((run["status"], run["added"]), ("complete", 1))
        saved = other.message(1, raw=True)
        self.assertEqual(saved["subject"], "凭证 café")
        self.assertEqual(saved["raw"], raw)
        self.assertEqual(get_attachment(saved["raw"], saved["attachments"][0]["index"]), payload)


    def test_search_count_and_page_share_one_snapshot(self):
        self.store.import_file(self.source(1))
        extra = self.root / "arriving.eml"
        extra.write_bytes(message("Concurrent arrival", message_id="<new@example.com>"))
        writer = Store(self.store.path)
        original = self.store.db
        inserted, callback_errors = [], []

        @contextmanager
        def concurrent_db():
            with original() as db:
                def between_count_and_page(sql):
                    if sql.startswith("SELECT id, subject") and not inserted:
                        inserted.append(True)
                        try:
                            writer.import_file(extra)
                        except Exception as error:
                            callback_errors.append(error)
                db.set_trace_callback(between_count_and_page)
                yield db

        with patch.object(self.store, "db", concurrent_db):
            page = self.store.search({})
        self.assertTrue(inserted, "The concurrent arrival must occur during the page query")
        self.assertEqual(callback_errors, [])
        self.assertEqual((page["total"], len(page["messages"])), (1, 1))
        self.assertEqual(self.store.search({})["total"], 2)

    def test_restore_without_atomic_filesystem_support_fails_cleanly(self):
        self.store.import_file(self.source(1))
        backup = self.root / "snapshot.sqlite3"
        self.store.backup(backup)
        target = self.root / "unsupported" / "archive.sqlite3"
        error = OSError(errno.ENOTSUP, "synthetic unsupported filesystem")
        with patch("mailcairn.store.os.link", side_effect=error):
            with self.assertRaisesRegex(ValueError, "atomic restore"):
                restore_backup(backup, target)
        self.assertFalse(target.exists())
        self.assertEqual(list(target.parent.iterdir()), [])

    def test_inconsistent_receipt_is_detected_and_not_restored(self):
        run = self.store.import_file(self.source(1))["id"]
        with self.store.db() as db:
            db.execute("UPDATE imports SET total=total+1 WHERE id=?", (run,))
        self.assertEqual(self.store.verify()["receipts"], "failed")
        backup = self.root / "bad-receipt.sqlite3"
        self.store.backup(backup)
        target = self.root / "rejected" / "archive.sqlite3"
        with self.assertRaisesRegex(ValueError, "receipts"):
            restore_backup(backup, target)
        self.assertFalse(target.exists())
        self.assertEqual(list(target.parent.iterdir()), [])


    def test_real_over_nested_mime_record_is_isolated_between_good_messages(self):
        outer = EmailMessage()
        outer["Subject"] = "Synthetic oversized MIME nesting"
        child = outer
        for _ in range(32):
            child.make_mixed()
            inner = EmailMessage()
            child.attach(inner)
            child = inner
        child.set_content("untrusted deeply nested body")
        source = self.root / "nested.mbox"
        source.write_bytes(mbox(message("Before nested record"), outer.as_bytes(),
                                message("After nested record", message_id="<after@example.com>")))
        result = self.store.import_file(source)
        self.assertEqual((result["status"], result["total"], result["added"], result["skipped"]),
                         ("partial", 3, 2, 1))
        self.assertEqual(self.store.search({"q": "After nested"})["total"], 1)
        report = self.assert_consistent(result["id"])
        self.assertIn("MIME nesting", report["items"][1]["reason"])


if __name__ == "__main__":
    unittest.main()
