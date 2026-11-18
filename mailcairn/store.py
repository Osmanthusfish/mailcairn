"""SQLite archive, streaming ingestion, search and integrity receipts."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import errno
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
import re
import sqlite3

from .parse import HTML_TEXT_WARNING, MailFormatError, parse_message, records

APP_ID = 0x4D434152
SCHEMA = 1
IMPORT_BATCH_ITEMS = 100
IMPORT_BATCH_BYTES = 4 * 1024 * 1024
IMPORT_BATCH_SECONDS = 0.25
LIST_COLUMNS = "id, subject, sender, recipients, date_day, sent_at, attachment_count, labels, substr(body,1,180) AS snippet"
MESSAGE_COLUMNS = "id, sha256, subject, sender, recipients, date_header, date_day, sent_at, message_id, labels, body, attachment_names, attachment_count, attachments, warnings, bytes"


def now():
    return datetime.now(timezone.utc).isoformat()


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stored_message_hash(db, row_id):
    """Hash the stored original in bounded chunks without copying the BLOB."""
    digest = hashlib.sha256()
    with db.blobopen("messages", "raw", row_id, readonly=True) as raw:
        for chunk in iter(lambda: raw.read(256 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        existing = self.path.exists() and self.path.stat().st_size > 0
        with self.db() as db:
            if existing and db.execute("PRAGMA application_id").fetchone()[0] != APP_ID:
                raise ValueError("This file is not a MailCairn archive. Choose a new data directory.")
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, SCHEMA):
                raise ValueError("This archive uses a newer schema. Upgrade MailCairn before opening it.")
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript(f"""
                PRAGMA application_id={APP_ID};
                PRAGMA user_version={SCHEMA};
                CREATE TABLE IF NOT EXISTS messages(
                  id INTEGER PRIMARY KEY, sha256 TEXT NOT NULL UNIQUE,
                  subject TEXT NOT NULL, sender TEXT, recipients TEXT,
                  date_header TEXT, date_day TEXT, sent_at INTEGER,
                  message_id TEXT, labels TEXT, body TEXT,
                  attachment_names TEXT, attachment_count INTEGER,
                  attachments TEXT, warnings TEXT, raw BLOB NOT NULL, bytes INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS messages_date ON messages(sent_at DESC,id DESC);
                CREATE INDEX IF NOT EXISTS messages_attachment_names ON messages(attachment_names)
                  WHERE attachment_count>0;
                CREATE VIRTUAL TABLE IF NOT EXISTS mail_fts USING fts5(
                  subject,sender,recipients,body,attachment_names,
                  content='messages',content_rowid='id',tokenize='unicode61'
                );
                CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
                  INSERT INTO mail_fts(rowid,subject,sender,recipients,body,attachment_names)
                  VALUES(new.id,new.subject,new.sender,new.recipients,new.body,new.attachment_names);
                END;
                CREATE TABLE IF NOT EXISTS imports(
                  id INTEGER PRIMARY KEY, name TEXT, size INTEGER, sha256 TEXT,
                  status TEXT, total INTEGER DEFAULT 0, added INTEGER DEFAULT 0,
                  duplicates INTEGER DEFAULT 0, skipped INTEGER DEFAULT 0,
                  warning_count INTEGER DEFAULT 0, started TEXT, completed TEXT,
                  note TEXT DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS import_items(
                  import_id INTEGER, ordinal INTEGER, offset INTEGER, length INTEGER,
                  status TEXT, reason TEXT, message_row INTEGER, sha256 TEXT,
                  PRIMARY KEY(import_id,ordinal)
                );
            """)

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA synchronous=FULL")
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def recover_interrupted(self):
        with self.db() as db:
            db.execute("UPDATE imports SET status='interrupted',completed=?,note='The app stopped during import. Saved messages are safe; import the file again to finish.' WHERE status='running'", (now(),))

    def import_file(self, path, name=None, digest=None, progress=lambda info: None, cancelled=lambda: False, max_bytes=32 * 1024 * 1024):
        path = Path(path)
        name = name or path.name
        if not name.lower().endswith((".mbox", ".eml")):
            raise ValueError("Choose an extracted .mbox or .eml file.")
        if not isinstance(max_bytes, int) or max_bytes <= 0:
            raise ValueError("Message size limit must be positive.")
        size = path.stat().st_size
        digest = digest or file_hash(path)
        with self.db() as db:
            run = db.execute("INSERT INTO imports(name,size,sha256,status,started) VALUES(?,?,?,'running',?)", (name, size, digest, now())).lastrowid
        counts = dict(total=0, added=0, duplicates=0, skipped=0, warning_count=0)
        status, note = "complete", ""
        # One connection, bounded durable transactions. Never publish progress
        # until messages, receipt rows and counters have committed together.
        try:
            with self.db() as db:
                batch_items = batch_bytes = bytes_done = 0
                batch_started = time.monotonic()

                def commit_batch():
                    nonlocal batch_items, batch_bytes, batch_started
                    if not batch_items:
                        return
                    db.execute("UPDATE imports SET total=:total,added=:added,duplicates=:duplicates,skipped=:skipped,warning_count=:warning_count WHERE id=:run", {**counts, "run": run})
                    db.commit()
                    batch_items = batch_bytes = 0
                    batch_started = time.monotonic()
                    progress({**counts, "bytes_done": bytes_done, "import_id": run})

                for ordinal, offset, length, raw in records(path, name, max_bytes, cancelled):
                    if cancelled():
                        break
                    reason, row, sha = "", None, ""
                    item_status, values = "skipped", None
                    if raw is None:
                        reason = f"Message exceeds {max_bytes} byte limit; raw span not stored."
                    else:
                        sha = hashlib.sha256(raw).hexdigest()
                        existing = db.execute("SELECT id FROM messages WHERE sha256=?", (sha,)).fetchone()
                        if existing:
                            row, item_status = existing[0], "duplicate"
                        else:
                            try:
                                values = parse_message(raw)
                                item_status = "added"
                                reason = "; ".join(values["warnings"])
                            except MemoryError:
                                raise
                            except Exception as exc:
                                # Malformed individual MIME input must not abort
                                # the surrounding archive. Storage errors below
                                # deliberately remain fatal and roll back a batch.
                                reason = f"Cannot parse message: {str(exc)[:300]}"
                    if values is not None:
                        fields = ["subject", "sender", "recipients", "date_header", "date_day", "sent_at", "message_id", "labels", "body", "attachment_names"]
                        vals = [values[k] for k in fields]
                        row = db.execute("INSERT INTO messages(sha256," + ",".join(fields) + ",attachment_count,attachments,warnings,raw,bytes) VALUES(" + ",".join("?" for _ in range(16)) + ")", [sha, *vals, len(values["attachments"]), json.dumps(values["attachments"], ensure_ascii=False), json.dumps(values["warnings"], ensure_ascii=False), raw, len(raw)]).lastrowid
                    counts["total"] += 1
                    counts[{"added": "added", "duplicate": "duplicates", "skipped": "skipped"}[item_status]] += 1
                    counts["warning_count"] += int(item_status == "added" and bool(reason))
                    db.execute("INSERT INTO import_items VALUES(?,?,?,?,?,?,?,?)", (run, ordinal, offset, length, item_status, reason, row, sha))
                    batch_items += 1
                    batch_bytes += len(raw) if raw is not None else 0
                    bytes_done = min(offset + length, size)
                    if batch_items >= IMPORT_BATCH_ITEMS or batch_bytes >= IMPORT_BATCH_BYTES or time.monotonic() - batch_started >= IMPORT_BATCH_SECONDS:
                        commit_batch()
                commit_batch()
            if cancelled():
                status, note = "cancelled", "Stopped at a message boundary. Saved messages remain searchable. Re-import to continue."
            elif counts["skipped"]:
                status, note = "partial", "Some messages were not stored. Keep the source file and review the receipt."
        except Exception as exc:
            status, note = "failed", str(exc)[:500]
        with self.db() as db:
            db.execute("UPDATE imports SET status=?,note=?,completed=? WHERE id=?", (status, note, now(), run))
        return self.receipt(run)

    def stats(self):
        with self.db() as db:
            db.execute("BEGIN")
            result = dict(db.execute("SELECT count(*) AS messages,coalesce(sum(bytes),0) AS raw_bytes,coalesce(sum(attachment_count),0) AS attachments,min(nullif(date_day,'')) AS first_date,max(nullif(date_day,'')) AS last_date FROM messages").fetchone())
            result["imports"] = [dict(row) for row in db.execute("SELECT * FROM imports ORDER BY id DESC LIMIT 50")]
            result["archive_file"] = str(self.path.resolve())
            result["schema"] = SCHEMA
            return result

    @staticmethod
    def where(filters):
        conditions, args = [], []
        q = filters.get("q", "").strip()[:500]
        if q:
            # Apply the same punctuation boundaries to every query. Choose
            # matching per term so Chinese does not disable Latin FTS folding.
            words = re.findall(r"[^\W_]+", q, re.UNICODE)[:30]
            for word in words:
                if re.search(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]", word):
                    # unicode61 does not segment CJK; retain substring search.
                    conditions.append("instr(lower(subject || ' ' || sender || ' ' || recipients || ' ' || body || ' ' || attachment_names),lower(?))>0")
                    args.append(word)
                else:
                    # A Latin filename fragment can adjoin Chinese characters
                    # in one FTS token. Scan attachment names only for this
                    # fallback using its small partial index; UNION keeps the
                    # outer lookup on message IDs.
                    conditions.append("id IN (SELECT rowid FROM mail_fts WHERE mail_fts MATCH ? "
                                      "UNION SELECT id FROM messages WHERE attachment_count>0 "
                                      "AND instr(lower(attachment_names),lower(?))>0)")
                    args.extend(('"' + word + '"', word))
            if not words:
                conditions.append("0")
        if filters.get("sender"):
            conditions.append("instr(lower(sender),lower(?))>0")
            args.append(filters["sender"][:300])
        for key, op in (("after", ">="), ("before", "<=")):
            if filters.get(key):
                datetime.strptime(filters[key], "%Y-%m-%d")
                conditions.append(f"date_day {op} ? AND date_day<>''")
                args.append(filters[key])
        if filters.get("after") and filters.get("before") and filters["after"] > filters["before"]:
            raise ValueError("Start date must be on or before end date.")
        if filters.get("attachments") == "1":
            conditions.append("attachment_count>0")
        if filters.get("import_id"):
            conditions.append("id IN (SELECT message_row FROM import_items WHERE import_id=?)")
            args.append(int(filters["import_id"]))
        return (" WHERE " + " AND ".join(conditions)) if conditions else "", args

    def search(self, filters):
        where, args = self.where(filters)
        offset = max(0, int(filters.get("offset", 0)))
        with self.db() as db:
            db.execute("BEGIN")
            total = db.execute("SELECT count(*) FROM messages" + where, args).fetchone()[0]
            rows = db.execute("SELECT " + LIST_COLUMNS + " FROM messages" + where + " ORDER BY sent_at DESC,id DESC LIMIT 50 OFFSET ?", [*args, offset])
            return {"total": total, "offset": offset, "limit": 50, "messages": [dict(row) for row in rows]}

    def message(self, row_id, raw=False):
        with self.db() as db:
            db.execute("BEGIN")
            columns = MESSAGE_COLUMNS + (", raw" if raw else "")
            row = db.execute("SELECT " + columns + " FROM messages WHERE id=?", (row_id,)).fetchone()
            if row is None:
                raise KeyError("Message not found.")
            result = dict(row)
            result["attachments"] = json.loads(result["attachments"])
            result["warnings"] = json.loads(result["warnings"])
            if not raw:
                if HTML_TEXT_WARNING in result["warnings"]:
                    # Older archives retain source indentation in their derived
                    # body. Re-derive only the reader presentation from original
                    # MIME; do not rewrite source bytes, receipts or search index.
                    # MIME provenance is needed to preserve <pre> and plain text.
                    try:
                        original = db.execute("SELECT raw FROM messages WHERE id=?", (row_id,)).fetchone()[0]
                        result["body"] = parse_message(original)["body"]
                    except Exception:
                        # A parser change must never make an older message
                        # unreadable: its saved preview remains a safe fallback.
                        pass
            return result

    def receipt(self, run):
        with self.db() as db:
            db.execute("BEGIN")
            row = db.execute("SELECT * FROM imports WHERE id=?", (run,)).fetchone()
            if row is None:
                raise KeyError("Import receipt not found.")
            result = dict(row)
            result["issues"] = [dict(v) for v in db.execute("SELECT ordinal,offset,length,status,reason FROM import_items WHERE import_id=? AND (status='skipped' OR reason<>'') ORDER BY ordinal LIMIT 200", (run,))]
            return result

    def export_receipt(self, run, stream):
        with self.db() as db:
            # A running import can commit between writes to the output stream.
            # Read both counters and items from one explicit SQLite snapshot.
            db.execute("BEGIN")
            row = db.execute("SELECT * FROM imports WHERE id=?", (run,)).fetchone()
            if row is None:
                raise KeyError("Import receipt not found.")
            receipt = dict(row)
            receipt["format"] = "MailCairn import receipt v1"
            receipt["scope"] = "Describes recognized source records only, not completeness against a mail provider. SHA-256 proves byte identity, not authenticity."
            stream.write((json.dumps(receipt, ensure_ascii=False)[:-1] + ', "items": [').encode("utf-8"))
            for n, row in enumerate(db.execute("SELECT * FROM import_items WHERE import_id=? ORDER BY ordinal", (run,))):
                stream.write((("," if n else "") + json.dumps(dict(row), ensure_ascii=False)).encode("utf-8"))
            stream.write(b"]}")

    def export_mbox(self, filters, stream):
        where, args = self.where(filters)
        count = 0
        with self.db() as db:
            for row in db.execute("SELECT raw FROM messages" + where + " ORDER BY sent_at,id", args):
                stream.write(b"From MAILER-DAEMON Thu Jan 01 00:00:00 1970\n")
                raw = row[0]
                # EML may contain mboxcl length metadata. It is invalid after
                # envelope escaping and makes readers misidentify this mboxo
                # export. Remove only top-level length fields (and folding),
                # retaining the exact original in SQLite and EML downloads.
                separator = re.search(rb"\r?\n\r?\n", raw)
                header_end = separator.end() if separator else len(raw)
                headers = re.sub(rb"(?im)^Content-Length[ \t]*:[^\r\n]*(?:\r?\n[ \t][^\r\n]*)*(?:\r?\n|$)", b"", raw[:header_end])
                raw = re.sub(rb"(?m)^From ", b">From ", headers + raw[header_end:])
                stream.write(raw)
                if not raw.endswith(b"\n"):
                    stream.write(b"\n")
                count += 1
        return count

    def backup(self, target):
        target = Path(target).resolve()
        if target == self.path.resolve():
            raise ValueError("Backup destination must differ from the active archive.")
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".mailcairn-backup-", dir=target.parent) as folder:
            staged = Path(folder) / "snapshot.sqlite3"
            with self.db() as db:
                dest = sqlite3.connect(staged)
                try:
                    db.backup(dest)
                    dest.execute("PRAGMA journal_mode=DELETE")
                finally:
                    dest.close()
            with staged.open("r+b") as stream:
                os.fsync(stream.fileno())
            os.replace(staged, target)

    def verify(self, progress=lambda info: None, cancelled=lambda: False):
        checked, mismatches = 0, []
        with self.db() as db:
            integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
            total = db.execute("SELECT count(*) FROM messages").fetchone()[0]
            for row in db.execute("SELECT id,sha256 FROM messages"):
                if cancelled():
                    break
                if stored_message_hash(db, row["id"]) != row["sha256"]:
                    mismatches.append(row["id"])
                checked += 1
                if checked % 100 == 0:
                    progress({"checked": checked, "total": total})
            receipts = "ok" if receipts_consistent(db) else "failed"
            # rank=1 checks the external-content FTS index against messages.
            search_index = "ok"
            try:
                db.execute("INSERT INTO mail_fts(mail_fts,rank) VALUES('integrity-check',1)")
            except sqlite3.DatabaseError:
                search_index = "failed"
        return {"checked": checked, "total": total, "mismatches": mismatches, "sqlite": integrity, "search_index": search_index, "receipts": receipts, "cancelled": cancelled(), "verified_at": now(), "scope": "Stored message bytes, local search index and import-receipt consistency only. This cannot prove the original export contains every email in your account."}


def restore_backup(source, target):
    source, target = Path(source).resolve(), Path(target).resolve()
    if not source.is_file():
        raise ValueError("Backup does not exist.")
    if target.exists():
        raise ValueError("Restore requires a new data directory; an existing archive will never be overwritten.")
    target.parent.mkdir(parents=True, exist_ok=True)
    # Stage a consistent SQLite snapshot first, then validate exactly the bytes
    # that will be published. Failure leaves no half-restored target behind.
    with tempfile.TemporaryDirectory(prefix=".mailcairn-restore-", dir=target.parent) as folder:
        staged = Path(folder) / "archive.sqlite3"
        source_db = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)
        dest = sqlite3.connect(staged)
        try:
            if source_db.execute("PRAGMA application_id").fetchone()[0] != APP_ID or source_db.execute("PRAGMA user_version").fetchone()[0] != SCHEMA:
                raise ValueError("Not a supported MailCairn backup.")
            source_db.backup(dest)
            dest.execute("PRAGMA journal_mode=DELETE")
            if dest.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Backup failed SQLite integrity check.")
            for row_id, sha in dest.execute("SELECT id,sha256 FROM messages"):
                if stored_message_hash(dest, row_id) != sha:
                    raise ValueError("Backup contains a message hash mismatch.")
            try:
                dest.execute("INSERT INTO mail_fts(mail_fts,rank) VALUES('integrity-check',1)")
            except sqlite3.DatabaseError as exc:
                raise ValueError("Backup search index is inconsistent.") from exc
            if not receipts_consistent(dest):
                raise ValueError("Backup import receipts are inconsistent.")
            dest.commit()
        finally:
            dest.close()
            source_db.close()
        with staged.open("r+b") as stream:
            os.fsync(stream.fileno())
        # Atomic creation without overwrite, including a target created after
        # the initial existence check. A hard link requires the same filesystem.
        try:
            os.link(staged, target)
        except FileExistsError as exc:
            raise ValueError("Restore target already exists; it was not overwritten.") from exc
        except OSError as exc:
            if exc.errno in (errno.EPERM, errno.EXDEV, errno.ENOTSUP, errno.ENOSYS) or getattr(exc, "winerror", None) in (1, 50, 87):
                raise ValueError("This filesystem does not support atomic restore. Choose a local disk with hard-link support, such as NTFS, and retry.") from exc
            raise


def receipts_consistent(db):
    invalid = db.execute("""
        SELECT 1 FROM imports i LEFT JOIN (
          SELECT import_id, count(*) total,
            sum(status='added') added, sum(status='duplicate') duplicates,
            sum(status='skipped') skipped,
            sum(status='added' AND reason<>'') warning_count
          FROM import_items GROUP BY import_id
        ) c ON c.import_id=i.id
        WHERE i.status IS NULL OR i.status NOT IN ('running','complete','partial','failed','cancelled','interrupted')
          OR i.total IS NULL OR i.added IS NULL OR i.duplicates IS NULL OR i.skipped IS NULL OR i.warning_count IS NULL
          OR i.total<>coalesce(c.total,0) OR i.added<>coalesce(c.added,0)
          OR i.duplicates<>coalesce(c.duplicates,0) OR i.skipped<>coalesce(c.skipped,0)
          OR i.warning_count<>coalesce(c.warning_count,0)
        LIMIT 1
    """).fetchone()
    orphan = db.execute("""
        SELECT 1 FROM import_items r LEFT JOIN imports i ON i.id=r.import_id
        LEFT JOIN messages m ON m.id=r.message_row
        WHERE i.id IS NULL OR r.status IS NULL OR r.status NOT IN ('added','duplicate','skipped')
          OR r.ordinal IS NULL OR r.ordinal<1 OR r.offset IS NULL OR r.offset<0 OR r.length IS NULL OR r.length<0
          OR (r.status IN ('added','duplicate') AND (m.id IS NULL OR r.sha256 IS NULL OR m.sha256<>r.sha256))
          OR (r.status='skipped' AND r.message_row IS NOT NULL)
        LIMIT 1
    """).fetchone()
    return invalid is None and orphan is None
