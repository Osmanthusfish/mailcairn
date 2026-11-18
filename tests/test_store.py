from contextlib import closing, contextmanager
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from mailcairn.parse import get_attachment
from mailcairn.store import Store, restore_backup
from tests.helpers import mbox, message


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "archive.sqlite3")
        self.addCleanup(self.temp.cleanup)

    def import_raw(self, raw, name="input.eml", **kwargs):
        path = self.root / name
        path.write_bytes(raw)
        return self.store.import_file(path, **kwargs)

    def test_duplicate_bytes_skip_but_duplicate_message_id_does_not(self):
        raw = message(message_id="<same@example.com>")
        changed = message(body="Corrected booking details.", message_id="<same@example.com>")
        receipt = self.import_raw(mbox(raw, raw, changed), "input.mbox")
        self.assertEqual((receipt["total"], receipt["added"], receipt["duplicates"], receipt["skipped"]), (3, 2, 1, 0))
        self.assertEqual(self.store.stats()["messages"], 2)
        again = self.import_raw(mbox(raw, raw, changed), "again.mbox")
        self.assertEqual((again["added"], again["duplicates"]), (0, 3))

    def test_raw_bytes_and_hash_preserved(self):
        raw = message(crlf=True).rstrip(b"\r\n")
        self.import_raw(raw)
        saved = self.store.message(1, raw=True)
        self.assertEqual(saved["raw"], raw)
        self.assertEqual(saved["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertNotIn("raw", self.store.message(1))

    def test_plain_preview_does_not_read_original_blob_and_preserves_metadata(self):
        raw = message("Large attachment metadata", "Saved text with original spacing.\n", attachment=("synthetic.bin", bytes(range(256)) * 64))
        self.import_raw(raw)
        expected = self.store.message(1, raw=True)
        self.assertEqual(expected.pop("raw"), raw)
        original_db = self.store.db

        @contextmanager
        def forbid_original_blob():
            with original_db() as db:
                db.set_authorizer(lambda action, table, column, *_:
                    sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_READ and table == "messages" and column == "raw" else sqlite3.SQLITE_OK)
                yield db

        with patch.object(self.store, "db", forbid_original_blob):
            self.assertEqual(self.store.message(1), expected)
            with self.assertRaises(sqlite3.DatabaseError):
                self.store.message(1, raw=True)
        self.assertEqual(self.store.message(1, raw=True)["raw"], raw)

    def test_partial_import_has_accurate_receipt_and_source_spans(self):
        good = message()
        malformed = b"nonsense body without header\n"
        huge = message("Huge", "x" * 6000)
        data = mbox(good, malformed, huge, good)
        receipt = self.import_raw(data, "partial.mbox", max_bytes=1000)
        self.assertEqual(receipt["status"], "partial")
        self.assertEqual((receipt["total"], receipt["added"], receipt["duplicates"], receipt["skipped"]), (4, 1, 1, 2))
        output = io.BytesIO()
        self.store.export_receipt(receipt["id"], output)
        report = json.loads(output.getvalue())
        self.assertEqual(len(report["items"]), 4)
        self.assertEqual(report["sha256"], hashlib.sha256(data).hexdigest())
        for item in report["items"]:
            span = data[item["offset"]:item["offset"] + item["length"]]
            if item["sha256"]:
                self.assertEqual(hashlib.sha256(span).hexdigest(), item["sha256"])
        self.assertEqual([item["ordinal"] for item in report["items"] if item["status"] == "skipped"], [2, 3])

    def test_invalid_file_creates_failed_receipt(self):
        result = self.import_raw(b"PK\x03\x04not mbox", "wrong.mbox")
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["total"], 0)
        self.assertEqual(self.store.stats()["messages"], 0)

    def test_cancel_then_reimport_finishes_without_duplicates(self):
        data = mbox(*(message(f"Item {i}", message_id=f"<{i}@example.com>") for i in range(6)))
        cancel = False

        def progress(info):
            nonlocal cancel
            cancel = info["total"] >= 2

        # Small batches make cancellation deterministic without exposing uncommitted progress.
        with patch("mailcairn.store.IMPORT_BATCH_ITEMS", 2):
            result = self.import_raw(data, "cancel.mbox", progress=progress, cancelled=lambda: cancel)
        self.assertEqual(result["status"], "cancelled")
        self.assertEqual(result["added"], 2)
        result = self.import_raw(data, "cancel.mbox")
        self.assertEqual((result["added"], result["duplicates"]), (4, 2))
        self.assertEqual(self.store.stats()["messages"], 6)

    def test_search_body_attachment_name_and_filters(self):
        self.import_raw(message("Trip", "Find the lantern at platform 8.", attachment=("invoice-berlin.txt", b"paid")))
        self.import_raw(message("Garden", "Plant the bulbs.", sender="Mia <mia@example.com>", date="Tue, 10 Nov 2026 08:00:00 +0000", message_id="<garden@example.com>"), "second.eml")
        self.assertEqual(self.store.search({"q": "lantern"})["total"], 1)
        self.assertEqual(self.store.search({"q": "invoice berlin"})["total"], 1)
        self.assertEqual(self.store.search({"attachments": "1"})["total"], 1)
        self.assertEqual(self.store.search({"sender": "MIA@EXAMPLE"})["total"], 1)
        self.assertEqual(self.store.search({"after": "2026-11-10", "before": "2026-11-10"})["total"], 1)
        self.assertEqual(self.store.search({"q": "lantern", "attachments": "1", "before": "2026-11-09"})["total"], 1)

    def test_cjk_substrings_and_combined_words(self):
        self.import_raw(message("保修确认", "咖啡机保修两年，可凭发票申请维修。"))
        self.assertEqual(self.store.search({"q": "发票"})["total"], 1)
        self.assertEqual(self.store.search({"q": "保修 发票"})["total"], 1)
        self.assertEqual(self.store.search({"q": "保修 海洋"})["total"], 0)

    def test_mixed_search_terms_keep_punctuation_and_latin_folding_consistent(self):
        self.import_raw(message("保修确认", "Café 咖啡机可凭发票申请维修。"))
        self.import_raw(message("保修确认", "No matching document here."), "negative.eml")
        self.import_raw(message("Other subject", "Café 发票"), "other.eml")
        for query in ("保修 发票", "保修，发票", "保修,发票", "保修_发票",
                      "保修 CAFÉ", "保修 CAFE", "保修 café"):
            with self.subTest(query=query):
                self.assertEqual([row["id"] for row in self.store.search({"q": query})["messages"]], [1])
        self.assertEqual(self.store.search({"q": "保修 海洋"})["total"], 0)

    def test_latin_filename_fragments_do_not_enable_body_substring_matching(self):
        self.import_raw(message("Repair", "Synthetic receipt", attachment=("维修invoice-2026.pdf", b"proof")))
        self.import_raw(message("Other", "prefixinvoice suffixinvoice 2026 pdf"), "body-only.eml")
        self.import_raw(message("Other attachment", "Synthetic receipt", attachment=("receipt-2026.pdf", b"other")), "negative.eml")
        for query in ("invoice", "INVOICE", "invoice-2026.pdf", "维修invoice-2026.pdf"):
            with self.subTest(query=query):
                self.assertEqual([row["id"] for row in self.store.search({"q": query})["messages"]], [1])
        self.assertEqual(self.store.search({"q": "invoice receipt"})["total"], 1)
        self.assertEqual(self.store.search({"q": "invoice missing"})["total"], 0)

    def test_mixed_search_and_across_fields_matches_export_readback(self):
        raw = message("保修确认", "Café purchase", attachment=("维修invoice-2026.pdf", b"original proof"))
        self.import_raw(raw)
        self.import_raw(message("保修确认", "Café purchase", attachment=("receipt-2026.pdf", b"other")), "missing-filename.eml")
        self.import_raw(message("Other", "Café purchase", attachment=("invoice-2026.pdf", b"other")), "missing-subject.eml")
        filters = {"q": "保修，CAFÉ invoice-2026.pdf", "attachments": "1"}
        self.assertEqual([row["id"] for row in self.store.search(filters)["messages"]], [1])
        output = io.BytesIO()
        self.assertEqual(self.store.export_mbox(filters, output), 1)
        exported = self.root / "matched.mbox"
        exported.write_bytes(output.getvalue())
        reopened = Store(self.root / "matched.sqlite3")
        receipt = reopened.import_file(exported)
        self.assertEqual((receipt["added"], receipt["skipped"]), (1, 0))
        saved = reopened.message(1, raw=True)
        self.assertEqual(saved["raw"], raw)
        self.assertEqual(get_attachment(saved["raw"], saved["attachments"][0]["index"]), b"original proof")
        self.assertEqual(reopened.search(filters)["total"], 1)

    def test_search_is_not_sql_or_fts_syntax(self):
        self.import_raw(message())
        for query in ("' OR 1=1 --", '" OR NEAR(*', "*", "; DROP TABLE messages;", "", "👀"):
            with self.subTest(query=query):
                result = self.store.search({"q": query})
                self.assertIn("total", result)
        self.assertEqual(self.store.stats()["messages"], 1)

    def test_date_validation_and_missing_dates(self):
        self.import_raw(message(date=None))
        self.assertEqual(self.store.search({"after": "2020-01-01"})["total"], 0)
        for filters in ({"after": "tomorrow"}, {"before": "2026-02-30"}, {"after": "2026-11-10", "before": "2026-11-09"}):
            with self.subTest(filters=filters):
                with self.assertRaises(ValueError):
                    self.store.search(filters)

    def test_page_boundaries_and_import_filter(self):
        self.import_raw(mbox(*(message(f"Item {i}", message_id=f"<{i}@example.com>") for i in range(55))), "pages.mbox")
        self.assertEqual(len(self.store.search({})["messages"]), 50)
        self.assertEqual(len(self.store.search({"offset": "50"})["messages"]), 5)
        self.assertEqual(self.store.search({"offset": "100"})["messages"], [])
        receipt = self.import_raw(message("Other import", message_id="<other@example.com>"), "other.eml")
        result = self.store.search({"import_id": str(receipt["id"])})
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["messages"][0]["subject"], "Other import")

    def test_export_then_reimport_retains_messages_and_attachment(self):
        raw = message(attachment=("ticket.txt", b"TICKET-ALPHA"))
        self.import_raw(raw)
        self.import_raw(message("Second", message_id="<second@example.com>"), "second.eml")
        output = io.BytesIO()
        self.assertEqual(self.store.export_mbox({}, output), 2)
        other = Store(self.root / "other.sqlite3")
        exported = self.root / "export.mbox"
        exported.write_bytes(output.getvalue())
        result = other.import_file(exported)
        self.assertEqual(result["added"], 2)
        saved = other.message(other.search({"attachments": "1"})["messages"][0]["id"], raw=True)
        self.assertEqual(get_attachment(saved["raw"], saved["attachments"][0]["index"]), b"TICKET-ALPHA")

    def test_export_removes_only_top_level_length_headers_and_reimports_all_mail(self):
        for index, newline in enumerate((b"\n", b"\r\n")):
            with self.subTest(newline=newline):
                source = Store(self.root / f"length-source-{index}.sqlite3")
                originals = [
                    newline.join((b"Subject: First", b"", b"First body", b"")),
                    newline.join((b"Subject: Length metadata", b"Content-Length: 6", b" folded metadata",
                                  b"content-length:\t999", b"\tmore metadata", b"X-After: retained", b"",
                                  b"Content-Length: body text, not a header", b"Last body line", b"")),
                    message("Last", attachment=("proof.txt", b"UNTOUCHED ATTACHMENT"), crlf=index == 1),
                ]
                for ordinal, raw in enumerate(originals):
                    path = self.root / f"length-{index}-{ordinal}.eml"
                    path.write_bytes(raw)
                    self.assertEqual(source.import_file(path)["status"], "complete")
                output = io.BytesIO()
                self.assertEqual(source.export_mbox({}, output), 3)
                exported = self.root / f"length-export-{index}.mbox"
                exported.write_bytes(output.getvalue())
                other = Store(self.root / f"length-target-{index}.sqlite3")
                result = other.import_file(exported)
                self.assertEqual((result["status"], result["added"], result["skipped"]), ("complete", 3, 0))
                for row_id, original in enumerate(originals, 1):
                    saved = source.message(row_id, raw=True)
                    self.assertEqual(saved["raw"], original, "Export must not rewrite stored originals")
                    self.assertEqual(saved["sha256"], hashlib.sha256(original).hexdigest())
                length_id = other.search({"q": "metadata"})["messages"][0]["id"]
                restored = other.message(length_id, raw=True)
                self.assertNotIn(b"folded metadata", restored["raw"])
                self.assertNotIn(b"more metadata", restored["raw"])
                self.assertIn(b"X-After: retained", restored["raw"])
                self.assertEqual(restored["body"], source.message(2)["body"])
                self.assertIn("Content-Length: body text, not a header", restored["body"])
                attached_id = other.search({"attachments": "1"})["messages"][0]["id"]
                attached = other.message(attached_id, raw=True)
                self.assertEqual(get_attachment(attached["raw"], attached["attachments"][0]["index"]), b"UNTOUCHED ATTACHMENT")
                self.assertEqual(other.verify()["search_index"], "ok")

    def test_export_applies_current_filters(self):
        self.import_raw(message("Trip", "lantern"))
        self.import_raw(message("Garden", "bulbs", message_id="<second@example.com>"), "second.eml")
        output = io.BytesIO()
        self.assertEqual(self.store.export_mbox({"q": "lantern"}, output), 1)
        self.assertNotIn(b"Subject: Garden", output.getvalue())

    def test_backup_restore_is_self_contained(self):
        raw = message("Backup receipt", "A durable archive.", attachment=("proof.txt", b"ORIGINAL PROOF"))
        self.import_raw(raw)
        backup = self.root / "backup.sqlite3"
        self.store.backup(backup)
        (self.root / "input.eml").unlink()
        restored_path = self.root / "restored" / "archive.sqlite3"
        restore_backup(backup, restored_path)
        restored = Store(restored_path)
        result = restored.search({"q": "durable"})
        self.assertEqual(result["total"], 1)
        saved = restored.message(result["messages"][0]["id"], raw=True)
        self.assertEqual(saved["raw"], raw)
        self.assertEqual(get_attachment(saved["raw"], saved["attachments"][0]["index"]), b"ORIGINAL PROOF")
        self.assertEqual(restored.verify()["mismatches"], [])

    def test_preindex_archive_reopens_without_rewriting_mail_or_changing_backup_schema(self):
        self.import_raw(message("保修确认", "Café purchase", attachment=("维修invoice-2026.pdf", b"proof")))
        self.import_raw(message("Other", "No attachment"), "other.eml")
        original = [self.store.message(row, raw=True) for row in (1, 2)]
        with self.store.db() as db:
            db.execute("DROP INDEX messages_attachment_names")
        before = self.root / "before-index.sqlite3"
        self.store.backup(before)

        # Existing schema-1 databases acquire the optional index on opening.
        reopened = Store(self.store.path)
        Store(self.store.path)  # Reopening again must remain idempotent.
        self.assertEqual([reopened.message(row, raw=True) for row in (1, 2)], original)
        with reopened.db() as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 1)
            indexes = {row["name"]: row for row in db.execute("PRAGMA index_list(messages)")}
            self.assertEqual(indexes["messages_attachment_names"]["partial"], 1)
            # Only attachment-bearing rows enter the filename index.
            indexed_ids = [row[0] for row in db.execute(
                "SELECT id FROM messages INDEXED BY messages_attachment_names WHERE attachment_count>0")]
            self.assertEqual(indexed_ids, [1])
        self.assertEqual(reopened.search({"q": "invoice"})["total"], 1)
        after = self.root / "after-index.sqlite3"
        reopened.backup(after)

        for name, backup in (("before", before), ("after", after)):
            with self.subTest(backup=name):
                with closing(sqlite3.connect(backup)) as db:
                    self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 1)
                restored_path = self.root / (name + "-restored.sqlite3")
                restore_backup(backup, restored_path)
                restored = Store(restored_path)
                self.assertEqual([restored.message(row, raw=True) for row in (1, 2)], original)
                self.assertEqual(restored.search({"q": "保修，CAFE invoice"})["total"], 1)
                verification = restored.verify()
                self.assertEqual(verification["mismatches"], [])
                self.assertEqual(verification["search_index"], "ok")
                self.assertEqual(verification["receipts"], "ok")

    def test_restore_never_overwrites_existing_archive(self):
        self.import_raw(message())
        backup = self.root / "backup.sqlite3"
        self.store.backup(backup)
        with self.assertRaises(ValueError):
            restore_backup(backup, self.store.path)
        self.assertEqual(self.store.stats()["messages"], 1)

    def test_verify_detects_modified_raw_and_restore_rejects_it(self):
        self.import_raw(message())
        with self.store.db() as db:
            db.execute("UPDATE messages SET raw=? WHERE id=1", (b"damaged original",))
        self.assertEqual(self.store.verify()["mismatches"], [1])
        backup = self.root / "bad-backup.sqlite3"
        self.store.backup(backup)
        with self.assertRaises(ValueError):
            restore_backup(backup, self.root / "restored.sqlite3")
        self.assertFalse((self.root / "restored.sqlite3").exists())

    def test_verify_detects_stale_search_index(self):
        self.import_raw(message())
        with self.store.db() as db:
            db.execute("UPDATE messages SET body='changed outside app' WHERE id=1")
        self.assertEqual(self.store.verify()["search_index"], "failed")

    def test_interrupted_receipt_recovered_on_startup(self):
        with self.store.db() as db:
            db.execute("INSERT INTO imports(name,status) VALUES('interrupted.mbox','running')")
        self.store.recover_interrupted()
        self.assertEqual(self.store.stats()["imports"][0]["status"], "interrupted")

    def test_missing_records_have_explicit_error(self):
        with self.assertRaises(KeyError):
            self.store.message(42)
        with self.assertRaises(KeyError):
            self.store.receipt(42)

    def test_unrelated_sqlite_file_is_not_adopted(self):
        path = self.root / "unrelated.sqlite3"
        with closing(sqlite3.connect(path)) as db:
            db.execute("CREATE TABLE unrelated(secret TEXT)")
            db.execute("INSERT INTO unrelated VALUES('synthetic test value')")
            db.commit()
        with self.assertRaises(ValueError):
            Store(path)
        with closing(sqlite3.connect(path)) as db:
            self.assertEqual(db.execute("PRAGMA application_id").fetchone()[0], 0)
            self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='messages'").fetchone())


if __name__ == "__main__":
    unittest.main()
