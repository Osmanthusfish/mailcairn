#!/usr/bin/env python3
"""Synthetic release checks against extracted source or an already running EXE.

Source: python scripts/smoke_release.py --source-dir EXTRACTED_SOURCE
        --work-dir NEW_DIRECTORY --report report.json --expected-version VERSION
Bundle: add --origin http://127.0.0.1:PORT --token-file DATA/.mailcairn-instance.json

Use a freshly launched, EMPTY synthetic archive. This deliberately refuses an
archive containing mail, receipts, or connections. It never prints a launch
token, server response, archive path, or mail content. Work files contain only
generated test mail and its backup. The source directory supplies the restore
implementation and an isolated HTTP helper; this does NOT test the native
Restore dialog, app.py startup, or a clean Windows installation. Running EXEs
are left running. Source helpers are shut down gracefully.

No dependency beyond Python 3.11+. Do not point this at a personal archive.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
from email import policy
from email.message import EmailMessage
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class SmokeFailure(Exception):
    """Only fixed, non-sensitive check names are exposed to the report."""


def require(condition, label):
    if not condition:
        raise SmokeFailure(label)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Client:
    def __init__(self, origin, token):
        parsed = urlsplit(origin)
        require(parsed.scheme == "http" and parsed.hostname == "127.0.0.1"
                and parsed.port and not parsed.username and not parsed.password
                and parsed.path in ("", "/") and not parsed.query and not parsed.fragment,
                "origin_must_be_loopback")
        require(isinstance(token, str) and re.fullmatch(r"[A-Za-z0-9_-]{43}", token),
                "invalid_token_file")
        self.origin = f"http://127.0.0.1:{parsed.port}"
        self.token = token
        self.cookie = ""
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    def request(self, path, method="GET", body=None, headers=None):
        actual = {"Origin": self.origin}
        if self.cookie:
            actual["Cookie"] = self.cookie
        actual.update(headers or {})
        try:
            response = self.opener.open(Request(self.origin + path, data=body,
                                               method=method, headers=actual), timeout=20)
        except HTTPError as error:
            response = error
        with response:
            # All fixtures are tiny. Refuse an unexpected large/private archive.
            content = response.read(16 * 1024 * 1024 + 1)
            require(len(content) <= 16 * 1024 * 1024, "response_size_bound")
            return response.status, response.headers, content

    def get(self, path):
        status, _, body = self.request(path)
        require(status == 200, "http_get_success")
        return json.loads(body)

    def post(self, path, body=b""):
        return self.request(path, "POST", body, {"X-MailCairn": "1"})

    def login(self):
        status, headers, _ = self.request("/api/session", "POST", b"",
                                          {"X-MailCairn-Token": self.token})
        require(status == 200, "session_login")
        cookie = headers.get("Set-Cookie", "")
        require("HttpOnly" in cookie and "SameSite=Strict" in cookie, "private_cookie")
        require(headers.get("Cache-Control") == "no-store"
                and headers.get("X-Content-Type-Options") == "nosniff", "private_headers")
        self.cookie = cookie.split(";", 1)[0]

    def job(self, path, body=b""):
        status, _, raw = self.post(path, body)
        require(status == 202, "job_accepted")
        job_id = json.loads(raw)["job_id"]
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            job = self.get("/api/jobs/" + job_id)
            if job["status"] != "running":
                require(job["status"] == "done", "job_finished")
                return job["result"]
            time.sleep(.05)
        raise SmokeFailure("job_timeout")


def fixture():
    attachment = "Synthetic attachment / 合成附件\nSMOKE-4917\n".encode("utf-8") + bytes(range(256))
    first = EmailMessage(policy=policy.SMTP)
    first["From"] = "Synthetic Sender <sender@example.invalid>"
    first["To"] = "Synthetic Reader <reader@example.invalid>"
    first["Subject"] = "Release smoke lighthouse4917 合成凭证"
    first["Date"] = "Mon, 09 Nov 2026 09:00:00 +0800"
    first["Message-ID"] = "<release-smoke-1@example.invalid>"
    first.set_content("Synthetic body lighthouse4917.\n合成正文可检索。\nFrom a preserved body line.\n")
    first.add_attachment(attachment, maintype="application", subtype="octet-stream",
                         filename="合成附件.bin")
    first.set_boundary("mailcairn-release-smoke-boundary")
    second = EmailMessage(policy=policy.default)
    second["From"] = "Synthetic Sender <sender@example.invalid>"
    second["To"] = "Synthetic Reader <reader@example.invalid>"
    second["Subject"] = "Release smoke harbor5826"
    second["Date"] = "Mon, 09 Nov 2026 10:00:00 +0800"
    second["Message-ID"] = "<release-smoke-2@example.invalid>"
    second.set_content("<html><body><p>Synthetic harbor5826.</p><p>Readable HTML.</p></body></html>",
                       subtype="html")
    messages = [first.as_bytes(), second.as_bytes()]
    envelope = b"From synthetic@example.invalid Mon Nov 09 09:00:00 2026\n"
    return messages, attachment, b"".join(envelope + raw for raw in messages)


def read_token(path):
    with path.open("rb") as stream:
        raw = stream.read(4097)
    require(len(raw) <= 4096, "invalid_token_file")
    value = raw.decode("utf-8").strip()
    if value.startswith("{"):
        value = json.loads(value)["token"]
    return value


def worker(source, folder, ready, backup):
    """Private child mode: token only enters a temporary local metadata file."""
    sys.path.insert(0, str(source.resolve()))
    from app import archive_lock
    from mailcairn import __version__
    from mailcairn.server import LocalServer
    from mailcairn.store import Store, restore_backup
    with archive_lock(folder):
        archive = folder / "archive.sqlite3"
        no_overwrite = None
        if backup:
            restore_backup(backup, archive)
            before = hashlib.sha256(archive.read_bytes()).digest()
            try:
                restore_backup(backup, archive)
            except ValueError:
                no_overwrite = hashlib.sha256(archive.read_bytes()).digest() == before
            else:
                no_overwrite = False
        server = LocalServer(("127.0.0.1", 0), Store(archive))
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": .05})
        thread.start()
        try:
            ready.write_text(json.dumps({"origin": server.origin, "token": server.token,
                                         "version": __version__, "no_overwrite": no_overwrite}), encoding="utf-8")
            sys.stdin.buffer.read(1)
        finally:
            server.sync_manager.stop()
            for job in server.jobs.values():
                job["cancel"].set()
            # Do not release the archive lock during an outstanding transaction.
            server.operation.acquire()
            server.operation.release()
            server.shutdown()
            thread.join()
            server.server_close()
            ready.unlink(missing_ok=True)


@contextmanager
def source_server(source, folder, backup=None):
    ready = folder.parent / (folder.name + "-ready.json")
    require(not folder.exists() and not ready.exists(), "source_helper_requires_new_directory")
    command = [sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--_worker",
               str(source.resolve()), str(folder), str(ready)]
    if backup:
        command.append(str(backup))
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, cwd=source)
    try:
        deadline = time.monotonic() + 20
        metadata = None
        while time.monotonic() < deadline and process.poll() is None:
            if ready.exists():
                try:
                    metadata = json.loads(ready.read_text(encoding="utf-8"))
                    break
                except (ValueError, OSError):
                    pass
            time.sleep(.05)
        require(metadata is not None, "source_helper_startup")
        yield Client(metadata["origin"], metadata["token"]), metadata
    finally:
        if process.stdin:
            process.stdin.close()  # EOF triggers orderly shutdown, including on failure.
        try:
            process.wait(timeout=60)
        except subprocess.TimeoutExpired:
            # Never forcibly terminate a writer; leave it to finish and fail the check.
            raise SmokeFailure("source_helper_shutdown_timeout") from None
        ready.unlink(missing_ok=True)
        require(process.returncode == 0, "source_helper_clean_exit")


def inspect_mail(client, messages, attachment):
    require(client.get("/api/stats")["messages"] == 2, "two_messages_preserved")
    for index, term in enumerate(("lighthouse4917", "harbor5826")):
        found = client.get("/api/messages?q=" + term)
        require(found["total"] == 1, "search_unique_result")
        row = found["messages"][0]["id"]
        detail = client.get(f"/api/messages/{row}")
        require(term in detail["body"] and "raw" not in detail, "readable_body")
        status, headers, raw = client.request(f"/api/messages/{row}/eml")
        require(status == 200 and raw == messages[index], "raw_bytes_exact")
        require(headers.get("Content-Disposition", "").startswith("attachment;"), "raw_download_header")
        if index == 0:
            require(len(detail["attachments"]) == 1, "attachment_count")
            item = detail["attachments"][0]
            require(item["name"] == "合成附件.bin", "unicode_attachment_name")
            status, headers, content = client.request(f"/api/messages/{row}/attachments/{item['index']}")
            require(status == 200 and content == attachment, "attachment_bytes_exact")
            require("filename*=UTF-8''" in headers.get("Content-Disposition", ""), "unicode_download_header")
    require(client.get("/api/messages?q=" + quote("合成正文"))["total"] == 1, "unicode_body_search")


def exercise(client, args, report):
    checks = report["checks"]
    require(client.request("/api/stats")[0] == 401, "authentication_required")
    require(client.request("/api/session", "POST", b"", {"X-MailCairn-Token": "wrong"})[0] == 401,
            "incorrect_token_rejected")
    client.login()
    stats = client.get("/api/stats")
    require(stats["messages"] == 0 and not stats["imports"], "refuse_nonempty_archive")
    require(not client.get("/api/connections")["connections"], "refuse_connected_archive")
    checks.append("authentication_and_empty_archive_guard")
    for headers in ({"Origin": "https://example.invalid"}, {"Host": "example.invalid"},
                    {"Sec-Fetch-Site": "cross-site"}):
        require(client.request("/api/stats", headers=headers)[0] == 403, "cross_site_rejected")
    require(client.request("/api/verify", "POST", b"")[0] == 403, "mutation_header_required")
    checks.append("host_origin_and_mutation_guards")
    status, headers, page = client.request("/")
    require(status == 200, "home_page_available")
    expected = args.expected_version
    server_version = headers.get("Server", "").strip()
    require(server_version == "MailCairn/" + expected, "http_version_matches_release")
    require(expected.encode() in page, "visible_version_matches_release")
    report["version"] = {"expected": expected, "http_server": server_version, "visible_page": True}
    for asset in ("/startup.js", "/app.js", "/i18n.js", "/style.css", "/fonts.css",
                  "/fonts/HankenGrotesk.ttf", "/fonts/Newsreader.ttf"):
        status, _, content = client.request(asset)
        require(status == 200 and len(content) > 100, "bundled_static_asset")
        if asset.endswith(".ttf"):
            require(content[:4] == b"\x00\x01\x00\x00", "bundled_font_signature")
    checks.append("version_and_bundled_assets")
    messages, attachment, mailbox = fixture()
    (args.work_dir / "synthetic.mbox").write_bytes(mailbox)
    result = client.job("/api/import?name=synthetic.mbox", mailbox)
    require((result["status"], result["total"], result["added"], result["duplicates"], result["skipped"])
            == ("complete", 2, 2, 0, 0), "mbox_import_receipt")
    receipt = client.get(f"/api/imports/{result['id']}/receipt")
    require(receipt["sha256"] == hashlib.sha256(mailbox).hexdigest() and len(receipt["items"]) == 2,
            "receipt_source_hash")
    inspect_mail(client, messages, attachment)
    checks.append("mbox_import_search_body_raw_attachment_and_receipt")
    duplicate = client.job("/api/import?name=duplicate.mbox", mailbox)
    require((duplicate["added"], duplicate["duplicates"]) == (0, 2), "duplicate_import")
    status, _, exported = client.request("/api/export")
    require(status == 200, "mbox_export")
    require(b"\n>From a preserved body line." in exported, "mbox_body_line_escaped")
    # MBOX quoting changes byte identity for raw From-lines. EML/backup are the
    # exact-byte paths; only an unchanged message can deduplicate on reimport.
    status, _, filtered = client.request("/api/export?q=harbor5826")
    require(status == 200 and messages[1] in filtered, "filtered_mbox_export")
    roundtrip = client.job("/api/import?name=exported.mbox", filtered)
    require((roundtrip["added"], roundtrip["duplicates"]) == (0, 1), "unchanged_export_roundtrip")
    checks.append("duplicate_mbox_escaping_and_unchanged_export_roundtrip")
    require(client.post("/api/import?name=invalid.zip", b"PK-synthetic")[0] == 400, "unsupported_file_rejected")
    require(client.post("/api/import?name=empty.mbox", b"")[0] == 400, "empty_file_rejected")
    failed = client.job("/api/import?name=broken.mbox", b"not a mailbox")
    require(failed["status"] == "failed", "malformed_mbox_receipt")
    recovery = client.job("/api/import?name=recovery.eml", messages[0])
    require((recovery["added"], recovery["duplicates"]) == (0, 1), "import_after_failure")
    checks.append("invalid_files_and_recovery")
    verified = client.job("/api/verify")
    require(verified["checked"] == 2 and verified["mismatches"] == []
            and verified["search_index"] == "ok", "archive_integrity")
    checks.append("archive_integrity")
    status, _, backup = client.request("/api/backup")
    require(status == 200 and backup.startswith(b"SQLite format 3\x00"), "sqlite_backup")
    backup_path = args.work_dir / "synthetic-backup.sqlite3"
    backup_path.write_bytes(backup)
    with source_server(args.source_dir, args.work_dir / "restored", backup_path) as (restored, metadata):
        require(metadata["version"] == expected, "restore_source_version")
        require(metadata["no_overwrite"] is True, "restore_cannot_overwrite")
        restored.login()
        inspect_mail(restored, messages, attachment)
        restored_receipt = restored.get(f"/api/imports/{result['id']}/receipt")
        require(restored_receipt == receipt, "restored_receipt_exact")
    checks.append("source_restore_no_overwrite_and_restored_http_readback")
    report["synthetic"] = {"messages": 2, "attachment_bytes": len(attachment),
                           "mbox_sha256": hashlib.sha256(mailbox).hexdigest(),
                           "backup_bytes": len(backup)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--origin")
    parser.add_argument("--token-file", type=Path)
    parser.add_argument("--work-dir", type=Path, required=True, help="New directory; never an existing archive")
    parser.add_argument("--report", type=Path, required=True, help="New JSON result file")
    parser.add_argument("--expected-version", required=True)
    args = parser.parse_args()
    report = {"status": "failed", "timestamp_utc": datetime.now(timezone.utc).isoformat(), "checks": [],
              "mode": "running_instance" if args.origin else "source_http_helper",
              "restore_mode": "extracted_source_helper_http",
              "limitations": ["Not a clean-machine test", "Native Restore dialog not exercised",
                              "Source helper does not exercise app.py or desktop startup",
                              "MBOX export quotes From-lines; EML and backup preserve exact raw bytes"]}
    try:
        require(bool(args.origin) == bool(args.token_file), "origin_and_token_file_required_together")
        require((args.source_dir / "mailcairn" / "server.py").is_file(), "extracted_source_required")
        require(not args.report.exists(), "report_must_be_new")
        args.work_dir = args.work_dir.resolve()
        args.work_dir.mkdir(parents=True, exist_ok=False)
        if args.origin:
            exercise(Client(args.origin, read_token(args.token_file)), args, report)
        else:
            with source_server(args.source_dir, args.work_dir / "source-archive") as (client, metadata):
                require(metadata["version"] == args.expected_version, "source_version_matches_release")
                exercise(client, args, report)
        report["status"] = "passed"
    except SmokeFailure as error:
        report["failed_check"] = str(error)
    except Exception:
        # Server errors and local exceptions can contain paths or credentials.
        report["failed_check"] = "unexpected_error_details_withheld"
    try:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except OSError:
        print("Release smoke failed: report could not be created.")
        return 1
    print(f"Release smoke {report['status']}: {len(report['checks'])} groups checked. "
          + ("" if report["status"] == "passed" else report["failed_check"]))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--_worker":
        try:
            worker(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]),
                   Path(sys.argv[5]) if len(sys.argv) > 5 else None)
        except Exception:
            raise SystemExit(1) from None
    else:
        raise SystemExit(main())
